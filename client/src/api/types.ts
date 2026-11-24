export type LngLat = [number, number];

export interface LineFeature<P> {
  type: "Feature";
  id?: number | string;
  properties: P;
  geometry: { type: "LineString"; coordinates: LngLat[] };
}

export interface LineCollection<P> {
  type: "FeatureCollection";
  features: LineFeature<P>[];
}

export interface RoadProps {
  id: string;
  name: string;
  nameEn: string;
  lanes: number;
  main: boolean;
  speed: number;
}

export interface SidewalkProps {
  id: string;
}

export interface CrossingProps {
  id: string;
  site: string | null;
  tls: string;
  link: number;
}

export interface SignalHeadProps {
  site: string | null;
  tls: string;
  links: number[];
  lane: string;
}

export type Direction = "northbound" | "eastbound" | "southbound" | "westbound";

export interface ApproachInfo {
  id: string;
  street: string;
  streetEn: string;
  direction: Direction;
  label: string;
}

export interface CrosswalkInfo {
  id: string;
  label: string;
  streets: { en: string; mn: string }[];
  length: number;
}

export interface PhaseInfo {
  index: number;
  state: string;
  approaches: string[];
  crosswalks: string[];
}

export type SiteKind = "intersection" | "midblock";

export interface SiteInfo {
  id: string;
  nameEn: string;
  nameMn: string;
  kind: SiteKind;
  tls: string;
  center: LngLat;
  approaches: ApproachInfo[];
  crosswalks: CrosswalkInfo[];
  neighbours: string[];
  phases: PhaseInfo[];
}

export interface CorridorInfo {
  id: string;
  nameEn: string;
  nameMn: string;
  axis: "ew" | "ns";
  sites: string[];
}

export interface ScenarioInfo {
  label: string;
  duration: number;
  incident?: { site: string; approach: string; start: number; end: number };
  ped_focus?: string;
}

export interface ControllerInfo {
  name: string;
  label: string;
}

export interface Network {
  bounds: [LngLat, LngLat];
  sites: SiteInfo[];
  corridors?: CorridorInfo[];
  roads: LineCollection<RoadProps>;
  sidewalks: LineCollection<SidewalkProps>;
  crossings: LineCollection<CrossingProps>;
  signalHeads: LineCollection<SignalHeadProps>;
  scenarios: Record<string, ScenarioInfo>;
  controllers: ControllerInfo[];
}

export interface Caps {
  pedestrianHard: number;
  vehicleSoft: number;
  vehicleHard: number;
}

export interface SimState {
  type: "state";
  scenario: string;
  controller: string;
  speed: number;
  paused: boolean;
  caps: Caps;
  explainAvailable: boolean;
}

export type Stage = "green" | "clearance" | "yellow" | "all-red";

export interface ApproachFrame {
  id: string;
  queue: number;
  wait: number;
  spillback: boolean;
  blocked: boolean;
}

export interface CrosswalkFrame {
  id: string;
  waiting: number;
  wait: number;
  button: boolean;
}

export interface SiteFrame {
  id: string;
  state: string;
  phase: number;
  target: number | null;
  stage: Stage;
  flashing: number[];
  greenFor: number;
  approaches: ApproachFrame[];
  crosswalks: CrosswalkFrame[];
  pressures: Record<string, number>;
  caps: Caps;
}

export type OverrideRule = "pedestrian-hard-cap" | "vehicle-hard-cap" | "vehicle-soft-cap";

export interface Metrics {
  t: number;
  avgVehicleWait: number;
  maxVehicleWait: number;
  vehiclesPerHour: number;
  avgPedestrianWait: number;
  maxPedestrianWait: number;
  spillbackMinutes: number;
  overrides: Partial<Record<OverrideRule, number>>;
  overrideCount: number;
  teleports: number;
  departed: number;
  arrived: number;
}

export interface OverrideDetail {
  t: number;
  site: string;
  rule: OverrideRule;
  subject: string;
  wait: number;
  proposed: number;
  applied: number;
}

export type EventKind = "override" | "button" | "incident" | "controller" | "caps";

export interface SimEvent {
  t: number;
  kind: EventKind;
  text: string;
  site?: string;
  override?: OverrideDetail;
}

export type VehicleKind = 0 | 1 | 2;

export type VehicleTuple = [id: number, lon: number, lat: number, angle: number, kind: VehicleKind, stopped: 0 | 1];
export type PersonTuple = [id: number, lon: number, lat: number];

export interface Frame {
  type: "frame";
  t: number;
  scenario: string;
  controller: string;
  sites: SiteFrame[];
  congestion: Record<string, 0 | 1 | 2>;
  metrics: Metrics;
  events: SimEvent[];
  vehicles: VehicleTuple[];
  persons: PersonTuple[];
}

export type ControlCommand =
  | { action: "pause" }
  | { action: "resume" }
  | { action: "restart" }
  | { action: "speed"; value: number }
  | { action: "scenario"; name: string }
  | { action: "controller"; name: string }
  | { action: "caps"; caps: Caps }
  | { action: "button"; site: string; target: string }
  | { action: "block"; site: string; target: string };

export type ExperimentMetrics = Omit<Metrics, "maxVehicleWait"> & { maxVehicleWait?: number; wallSeconds?: number };

export interface ExperimentResult {
  scenario: string;
  label: string;
  duration: number;
  seed: number;
  finishedAt: string;
  results: Record<string, ExperimentMetrics>;
}

export interface ExperimentsResponse {
  running: boolean;
  startedAt: number | null;
  args: { scenarios: string[]; duration: number } | null;
  results: ExperimentResult[];
}

export interface VisionZone {
  id: string;
  kind: "approach" | "crosswalk";
  label: string;
  polygon: [number, number][];
}

export interface VisionVideo {
  name: string;
  file: string;
  zone_file: boolean;
  zones: VisionZone[];
}

export interface VisionZoneCount {
  id: string;
  kind: "approach" | "crosswalk";
  label: string;
  vehicles: number;
  queued: number;
  persons: number;
  waiting: number;
}

export interface VisionCounts {
  video: string;
  t: number;
  fps: number;
  zones: VisionZoneCount[];
}
