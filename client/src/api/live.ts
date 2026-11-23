import { useSyncExternalStore } from "react";
import { SIM_URL, toWebSocketUrl } from "../config";
import { fetchNetwork } from "./sim";
import type { Frame, Network, SimEvent, SimState } from "./types";

export type Connection = "connecting" | "open" | "stalled" | "reconnecting";

export interface LoggedEvent extends SimEvent {
  seq: number;
  receivedAt: number;
}

export interface LiveSnapshot {
  network: Network | null;
  networkError: string | null;
  state: SimState | null;
  frame: Frame | null;
  events: LoggedEvent[];
  connection: Connection;
  lastMessageAt: number | null;
}

type FrameListener = (frame: Frame, receivedAt: number) => void;
type EventListener = (events: LoggedEvent[]) => void;

const MAX_EVENTS = 300;
const STALL_MS = 4000;

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null;

class LiveStore {
  private snapshot: LiveSnapshot = {
    network: null,
    networkError: null,
    state: null,
    frame: null,
    events: [],
    connection: "connecting",
    lastMessageAt: null,
  };
  private listeners = new Set<() => void>();
  private frameListeners = new Set<FrameListener>();
  private eventListeners = new Set<EventListener>();
  private socket: WebSocket | null = null;
  private retryDelay = 500;
  private retryTimer: number | undefined;
  private started = false;
  private seq = 0;
  private freshConnection = false;

  start(): void {
    if (this.started) return;
    this.started = true;
    void this.loadNetwork();
    this.connect();
    window.setInterval(() => this.checkStall(), 1000);
  }

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getSnapshot = (): LiveSnapshot => this.snapshot;

  onFrame(listener: FrameListener): () => void {
    this.frameListeners.add(listener);
    return () => this.frameListeners.delete(listener);
  }

  onEvents(listener: EventListener): () => void {
    this.eventListeners.add(listener);
    return () => this.eventListeners.delete(listener);
  }

  applyState(state: SimState): void {
    this.update({ state });
  }

  private update(patch: Partial<LiveSnapshot>): void {
    this.snapshot = { ...this.snapshot, ...patch };
    for (const listener of this.listeners) listener();
  }

  private async loadNetwork(): Promise<void> {
    while (!this.snapshot.network) {
      try {
        const network = await fetchNetwork();
        this.update({ network, networkError: null });
        return;
      } catch (error) {
        this.update({ networkError: error instanceof Error ? error.message : String(error) });
        await new Promise((resolve) => window.setTimeout(resolve, 2500));
      }
    }
  }

  private connect(): void {
    const socket = new WebSocket(toWebSocketUrl(SIM_URL, "/ws"));
    this.socket = socket;
    socket.onopen = () => {
      this.retryDelay = 500;
      this.freshConnection = true;
      this.update({ connection: "open", lastMessageAt: Date.now() });
      if (!this.snapshot.network) void this.loadNetwork();
    };
    socket.onmessage = (message) => this.receive(message.data);
    socket.onclose = () => {
      if (this.socket !== socket) return;
      this.socket = null;
      this.update({ connection: "reconnecting" });
      window.clearTimeout(this.retryTimer);
      this.retryTimer = window.setTimeout(() => this.connect(), this.retryDelay);
      this.retryDelay = Math.min(this.retryDelay * 2, 8000);
    };
    socket.onerror = () => socket.close();
  }

  private checkStall(): void {
    const { connection, lastMessageAt } = this.snapshot;
    if (connection === "open" && lastMessageAt !== null && Date.now() - lastMessageAt > STALL_MS) {
      this.update({ connection: "stalled" });
    }
  }

  private receive(data: unknown): void {
    if (typeof data !== "string") return;
    let parsed: unknown;
    try {
      parsed = JSON.parse(data);
    } catch {
      return;
    }
    if (!isRecord(parsed)) return;
    const now = Date.now();
    const connection: Connection = "open";
    if (parsed.type === "state") {
      this.update({ state: parsed as unknown as SimState, connection, lastMessageAt: now });
      return;
    }
    if (parsed.type !== "frame") return;
    const frame = parsed as unknown as Frame;
    const previous = this.snapshot.frame;
    const restarted = previous !== null && (frame.scenario !== previous.scenario || frame.t + 1 < previous.t);
    const incoming = frame.events.map((event) => ({ ...event, seq: ++this.seq, receivedAt: now }));
    // The first frame after (re)connecting carries the server's whole event history.
    let events = restarted || this.freshConnection ? [] : this.snapshot.events;
    this.freshConnection = false;
    if (incoming.length) events = [...incoming.reverse(), ...events].slice(0, MAX_EVENTS);
    this.update({ frame, events, connection, lastMessageAt: now });
    for (const listener of this.frameListeners) listener(frame, now);
    if (incoming.length) for (const listener of this.eventListeners) listener(incoming);
  }
}

export const live = new LiveStore();

export function useLive(): LiveSnapshot {
  return useSyncExternalStore(live.subscribe, live.getSnapshot);
}
