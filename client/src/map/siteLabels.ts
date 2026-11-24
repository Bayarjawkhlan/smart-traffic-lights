import type { Map as MapLibreMap } from "maplibre-gl";
import type { LngLat } from "../api/types";

const PIN_RADIUS = 9;
const OFFSET = 15;
const GAP = 4;
const EDGE_LEFT = 6;
// keeps names clear of the zoom controls
const EDGE_RIGHT = 46;

interface Label {
  center: LngLat;
  element: HTMLElement;
  text: HTMLElement;
  width: number;
  height: number;
}

type Side = "above" | "below";

interface Box {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

const overlap = (a: Box, b: Box, gap: number) =>
  a.left < b.right + gap && b.left < a.right + gap && a.top < b.bottom + gap && b.top < a.bottom + gap;

export class SiteLabels {
  private map: MapLibreMap;
  private labels = new Map<string, Label>();
  private order: string[] = [];
  private selected: string | null = null;
  private active: string | null = null;
  private resizes = new ResizeObserver(() => this.measure());

  constructor(map: MapLibreMap) {
    this.map = map;
    map.on("move", this.layout);
    map.on("resize", this.layout);
  }

  add(id: string, center: LngLat, element: HTMLElement, text: HTMLElement): void {
    this.labels.set(id, { center, element, text, width: 0, height: 0 });
    this.resizes.observe(text);
    const activate = () => this.activate(id);
    const release = () => this.active === id && this.activate(null);
    element.addEventListener("pointerenter", activate);
    element.addEventListener("pointerleave", release);
    element.addEventListener("focus", () => element.matches(":focus-visible") && activate());
    element.addEventListener("blur", release);
  }

  show(order: string[], selected: string | null): void {
    this.order = order;
    this.selected = selected;
    this.layout();
  }

  destroy(): void {
    this.map.off("move", this.layout);
    this.map.off("resize", this.layout);
    this.resizes.disconnect();
  }

  private activate(id: string | null): void {
    this.active = id;
    this.layout();
  }

  private measure(): void {
    for (const label of this.labels.values()) {
      label.width = label.text.offsetWidth;
      label.height = label.text.offsetHeight;
    }
    this.layout();
  }

  private layout = (): void => {
    const { clientWidth, clientHeight } = this.map.getContainer();
    const pins = new Map(
      [...this.labels].map(([id, { center }]) => {
        const { x, y } = this.map.project(center);
        return [id, { x, y, box: { left: x - PIN_RADIUS, right: x + PIN_RADIUS, top: y - PIN_RADIUS, bottom: y + PIN_RADIUS } }];
      }),
    );
    const placed: Box[] = [];
    const asked = [this.active, this.selected].filter((id) => id !== null);
    const visible = new Set<string>();

    for (const id of new Set([...asked, ...this.order])) {
      const label = this.labels.get(id);
      const pin = pins.get(id);
      if (!label || !pin) continue;
      const half = label.width / 2;
      const inside = Math.min(Math.max(pin.x, half + EDGE_LEFT), clientWidth - half - EDGE_RIGHT);
      const reach = Math.max(0, half - PIN_RADIUS);
      const shift = Math.round(Math.min(Math.max(inside - pin.x, -reach), reach) - half);
      const left = pin.x + shift;
      const boxOn = (side: Side): Box => {
        const top = side === "below" ? pin.y + OFFSET : pin.y - OFFSET - label.height;
        return { left, right: left + label.width, top, bottom: top + label.height };
      };
      const sides: Side[] = this.order.indexOf(id) % 2 === 1 ? ["below", "above"] : ["above", "below"];
      const free = sides.filter((side) => {
        const box = boxOn(side);
        const inMap = box.left >= 0 && box.right <= clientWidth && box.top >= 0 && box.bottom <= clientHeight;
        return inMap && !placed.some((other) => overlap(box, other, GAP));
      });
      const clear = free.find((side) => ![...pins].some(([other, p]) => other !== id && overlap(boxOn(side), p.box, 0)));
      const side = clear ?? (asked.includes(id) ? free[0] : undefined);
      if (!side) continue;
      placed.push(boxOn(side));
      visible.add(id);
      label.element.dataset.side = side;
      label.text.style.setProperty("--shift", `${shift}px`);
    }
    for (const [id, { element }] of this.labels) element.classList.toggle("is-named", visible.has(id));
  };
}
