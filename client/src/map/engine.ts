import {
  AttributionControl,
  Map as MapLibreMap,
  NavigationControl,
  type ExpressionSpecification,
  type GeoJSONSource,
  type LngLatBoundsLike,
} from "maplibre-gl";
import type { Frame, LngLat, Network, SimEvent } from "../api/types";
import { distanceMeters } from "../lib/geo";
import { bestLight, LIGHT_CODE, linkLight } from "../lib/signals";
import { palette } from "../ui/palette";
import { registerVehicleIcons, VEHICLE_ICON_BY_KIND } from "./icons";

export const BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/dark";

interface Track {
  fromLon: number;
  fromLat: number;
  fromAngle: number;
  toLon: number;
  toLat: number;
  toAngle: number;
  kind: number;
  stopped: number;
}

interface Flash {
  site: string;
  center: LngLat;
  started: number;
}

interface PointFeature {
  type: "Feature";
  id?: number;
  properties: Record<string, number | string>;
  geometry: { type: "Point"; coordinates: LngLat };
}

interface PointCollection {
  type: "FeatureCollection";
  features: PointFeature[];
}

const FLASH_MS = 2600;
const FIT_PADDING = { top: 20, right: 48, bottom: 160, left: 20 };
const TELEPORT_METERS = 40;

const lightColor = (fallback: string): ExpressionSpecification => [
  "match",
  ["coalesce", ["feature-state", "l"], 0],
  LIGHT_CODE.green,
  palette.go,
  LIGHT_CODE.amber,
  palette.amber,
  LIGHT_CODE.red,
  palette.stop,
  LIGHT_CODE.flashing,
  palette.stop,
  fallback,
];

const lerpAngle = (from: number, to: number, alpha: number) => {
  const delta = ((((to - from) % 360) + 540) % 360) - 180;
  return from + delta * alpha;
};

export class MapEngine {
  readonly map: MapLibreMap;
  private network: Network;
  private ready = false;
  private tracks = new Map<number, Track>();
  private people = new Map<number, Track>();
  private frameStarted = 0;
  private frameDuration = 200;
  private lastFrameAt = 0;
  private dirty = false;
  private raf = 0;
  private lastDraw = 0;
  private crossingCodes = new Map<string, number>();
  private headCodes = new Map<number, number>();
  private congestionCodes = new Map<string, number>();
  private flashingCrossings = new Set<string>();
  private blinkTimer: number | undefined;
  private blinkOn = true;
  private flashes: Flash[] = [];
  private headsBySite = new Map<string, { id: number; links: number[] }[]>();
  private crossingsBySite = new Map<string, { id: string; link: number }[]>();
  private reducedMotion: boolean;
  private pendingFrame: Frame | null = null;

  constructor(container: HTMLElement, network: Network, reducedMotion: boolean) {
    this.network = network;
    this.reducedMotion = reducedMotion;
    this.map = new MapLibreMap({
      container,
      style: BASEMAP_STYLE,
      bounds: network.bounds as LngLatBoundsLike,
      fitBoundsOptions: { padding: FIT_PADDING },
      attributionControl: false,
      maxPitch: 0,
      dragRotate: false,
      pitchWithRotate: false,
      fadeDuration: 0,
    });
    this.map.touchZoomRotate.disableRotation();
    this.map.addControl(
      new AttributionControl({ compact: false, customAttribution: "Simulation: Eclipse SUMO" }),
      "bottom-right",
    );
    this.map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    this.map.on("load", () => this.setup());
  }

  destroy(): void {
    cancelAnimationFrame(this.raf);
    window.clearInterval(this.blinkTimer);
    this.map.remove();
  }

  fitNetwork(): void {
    this.map.fitBounds(this.network.bounds as LngLatBoundsLike, { padding: FIT_PADDING, duration: this.reducedMotion ? 0 : 600 });
  }

  focusSite(center: LngLat): void {
    const zoom = Math.max(this.map.getZoom(), 17);
    if (this.reducedMotion) this.map.jumpTo({ center, zoom });
    else this.map.easeTo({ center, zoom, duration: 700 });
  }

  private setup(): void {
    const { map, network } = this;
    this.tuneBasemap();
    registerVehicleIcons(map);

    const heads = {
      ...network.signalHeads,
      features: network.signalHeads.features.map((feature, index) => ({ ...feature, id: index })),
    };
    heads.features.forEach((feature) => {
      const site = feature.properties.site;
      if (!site) return;
      const list = this.headsBySite.get(site) ?? [];
      list.push({ id: feature.id, links: feature.properties.links });
      this.headsBySite.set(site, list);
    });
    network.crossings.features.forEach((feature) => {
      const site = feature.properties.site;
      if (!site) return;
      const list = this.crossingsBySite.get(site) ?? [];
      list.push({ id: feature.properties.id, link: feature.properties.link });
      this.crossingsBySite.set(site, list);
    });

    map.addSource("sidewalks", { type: "geojson", data: network.sidewalks });
    map.addSource("roads", { type: "geojson", data: network.roads, promoteId: "id" });
    map.addSource("crossings", { type: "geojson", data: network.crossings, promoteId: "id" });
    map.addSource("heads", { type: "geojson", data: heads });
    map.addSource("persons", { type: "geojson", data: emptyCollection() });
    map.addSource("vehicles", { type: "geojson", data: emptyCollection() });
    map.addSource("flashes", { type: "geojson", data: emptyCollection() });

    const firstLabel = map.getStyle().layers.find((layer) => layer.type === "symbol")?.id;
    const lanes = ["get", "lanes"] as ExpressionSpecification;

    map.addLayer(
      {
        id: "sidewalks",
        type: "line",
        source: "sidewalks",
        minzoom: 15,
        paint: {
          "line-color": palette.sidewalk,
          "line-width": ["interpolate", ["linear"], ["zoom"], 15, 0.5, 18, 2],
        },
      },
      firstLabel,
    );
    map.addLayer(
      {
        id: "roads-casing",
        type: "line",
        source: "roads",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": palette.night,
          "line-width": [
            "interpolate",
            ["exponential", 2],
            ["zoom"],
            14,
            ["+", ["*", lanes, 0.7], 1.5],
            17,
            ["+", ["*", lanes, 3.6], 2],
            19,
            ["+", ["*", lanes, 14], 3],
          ],
        },
      },
      firstLabel,
    );
    map.addLayer(
      {
        id: "roads",
        type: "line",
        source: "roads",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": [
            "match",
            ["coalesce", ["feature-state", "c"], -1],
            0,
            palette.go,
            1,
            palette.amber,
            2,
            palette.stop,
            palette.idle,
          ],
          "line-opacity": [
            "match",
            ["coalesce", ["feature-state", "c"], -1],
            0,
            ["case", ["get", "main"], 0.55, 0.32],
            1,
            0.85,
            2,
            0.95,
            0.5,
          ],
          "line-width": [
            "interpolate",
            ["exponential", 2],
            ["zoom"],
            14,
            ["*", lanes, 0.7],
            17,
            ["*", lanes, 3.6],
            19,
            ["*", lanes, 14],
          ],
        },
      },
      firstLabel,
    );
    map.addLayer({
      id: "crossings",
      type: "line",
      source: "crossings",
      minzoom: 14.5,
      paint: {
        "line-color": [
          "case",
          ["==", ["get", "site"], null],
          palette.background,
          lightColor(palette.background),
        ],
        "line-opacity": ["match", ["coalesce", ["feature-state", "l"], 0], LIGHT_CODE.flashing, ["coalesce", ["feature-state", "blink"], 1], 1],
        "line-width": ["interpolate", ["exponential", 2], ["zoom"], 15, 2.5, 17, 7, 19, 24],
        "line-dasharray": [0.32, 0.26],
      },
    });
    map.addLayer({
      id: "heads",
      type: "line",
      source: "heads",
      minzoom: 15,
      layout: { "line-cap": "butt" },
      paint: {
        "line-color": ["case", ["==", ["get", "site"], null], palette.background, lightColor(palette.background)],
        "line-width": ["interpolate", ["exponential", 2], ["zoom"], 15, 1.5, 17, 3.5, 19, 7],
        "line-opacity": ["case", ["==", ["get", "site"], null], 0.6, 1],
      },
    });
    map.addLayer({
      id: "persons",
      type: "circle",
      source: "persons",
      paint: {
        "circle-color": palette.walker,
        "circle-radius": ["interpolate", ["exponential", 2], ["zoom"], 14, 1, 17, 2.2, 19, 5],
        "circle-stroke-color": palette.night,
        "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 15, 0, 17, 0.8],
      },
    });
    map.addLayer({
      id: "vehicles",
      type: "symbol",
      source: "vehicles",
      layout: {
        "icon-image": ["get", "icon"],
        "icon-rotate": ["get", "a"],
        "icon-rotation-alignment": "map",
        "icon-allow-overlap": true,
        "icon-ignore-placement": true,
        "icon-size": ["interpolate", ["exponential", 2], ["zoom"], 14, 0.45, 16, 0.7, 17, 0.9, 19, 3],
      },
      paint: {
        "icon-opacity": ["case", ["==", ["get", "s"], 1], 0.5, 1],
      },
    });
    map.addLayer({
      id: "flashes",
      type: "circle",
      source: "flashes",
      paint: {
        "circle-color": "rgba(0,0,0,0)",
        "circle-radius": ["get", "r"],
        "circle-stroke-color": palette.stop,
        "circle-stroke-width": 2.5,
        "circle-stroke-opacity": ["get", "o"],
      },
    });

    this.ready = true;
    this.blinkTimer = window.setInterval(() => this.blink(), 450);
    if (this.pendingFrame) this.applySignals(this.pendingFrame);
    this.raf = requestAnimationFrame(this.tick);
  }

  private tuneBasemap(): void {
    const { map } = this;
    for (const layer of map.getStyle().layers) {
      if (layer.type === "line" && /^(highway|road|railway)/.test(layer.id)) {
        map.setPaintProperty(layer.id, "line-opacity", 0.28);
      }
      if (layer.id === "building") {
        map.setPaintProperty(layer.id, "fill-color", "#1f2328");
        map.setPaintProperty(layer.id, "fill-outline-color", "#262b31");
      }
      if (layer.id === "background") map.setPaintProperty(layer.id, "background-color", palette.night);
    }
  }

  ingest(frame: Frame): void {
    if (!this.ready) {
      this.pendingFrame = frame;
      return;
    }
    const now = performance.now();
    if (this.lastFrameAt) {
      const interval = now - this.lastFrameAt;
      this.frameDuration = Math.min(600, Math.max(60, this.frameDuration * 0.7 + interval * 0.3));
    }
    this.lastFrameAt = now;
    const alpha = this.alpha(now);
    retarget(this.tracks, frame.vehicles, alpha, ([id, lon, lat, angle, kind, stopped]) => ({ id, lon, lat, angle, kind, stopped }));
    retarget(this.people, frame.persons, alpha, ([id, lon, lat]) => ({ id, lon, lat, angle: 0, kind: 0, stopped: 0 }));
    this.frameStarted = now;
    this.dirty = true;
    this.applySignals(frame);
    this.applyCongestion(frame);
  }

  flashOverride(event: SimEvent): void {
    if (!event.site) return;
    const site = this.network.sites.find((s) => s.id === event.site);
    if (!site) return;
    this.flashes.push({ site: site.id, center: site.center, started: performance.now() });
    this.dirty = true;
  }

  private alpha(now: number): number {
    return Math.min(1, (now - this.frameStarted) / this.frameDuration);
  }

  private applySignals(frame: Frame): void {
    const { map } = this;
    for (const site of frame.sites) {
      for (const crossing of this.crossingsBySite.get(site.id) ?? []) {
        const light = linkLight(site.state, crossing.link, site.flashing);
        const code = LIGHT_CODE[light];
        if (light === "flashing") this.flashingCrossings.add(crossing.id);
        else this.flashingCrossings.delete(crossing.id);
        if (this.crossingCodes.get(crossing.id) === code) continue;
        this.crossingCodes.set(crossing.id, code);
        map.setFeatureState({ source: "crossings", id: crossing.id }, { l: code, blink: 1 });
      }
      for (const head of this.headsBySite.get(site.id) ?? []) {
        const code = LIGHT_CODE[bestLight(site.state, head.links)];
        if (this.headCodes.get(head.id) === code) continue;
        this.headCodes.set(head.id, code);
        map.setFeatureState({ source: "heads", id: head.id }, { l: code });
      }
    }
  }

  private applyCongestion(frame: Frame): void {
    for (const [edge, level] of Object.entries(frame.congestion)) {
      if (this.congestionCodes.get(edge) === level) continue;
      this.congestionCodes.set(edge, level);
      this.map.setFeatureState({ source: "roads", id: edge }, { c: level });
    }
  }

  private blink(): void {
    if (!this.ready || this.flashingCrossings.size === 0) return;
    this.blinkOn = !this.blinkOn;
    const value = this.reducedMotion ? 0.6 : this.blinkOn ? 1 : 0.12;
    for (const id of this.flashingCrossings) this.map.setFeatureState({ source: "crossings", id }, { blink: value });
  }

  private tick = (now: number): void => {
    this.raf = requestAnimationFrame(this.tick);
    const animating = this.alpha(now) < 1 || this.flashes.length > 0;
    if (!this.dirty && !animating) return;
    if (now - this.lastDraw < 22) return;
    this.lastDraw = now;
    const alpha = this.alpha(now);
    const vehicles: PointFeature[] = [];
    for (const [id, track] of this.tracks) {
      vehicles.push({
        type: "Feature",
        id,
        properties: {
          icon: VEHICLE_ICON_BY_KIND[track.kind] ?? "vehicle-car",
          a: lerpAngle(track.fromAngle, track.toAngle, alpha),
          s: track.stopped,
        },
        geometry: {
          type: "Point",
          coordinates: [track.fromLon + (track.toLon - track.fromLon) * alpha, track.fromLat + (track.toLat - track.fromLat) * alpha] as LngLat,
        },
      });
    }
    const persons: PointFeature[] = [];
    for (const [id, track] of this.people) {
      persons.push({
        type: "Feature",
        id,
        properties: {},
        geometry: {
          type: "Point",
          coordinates: [track.fromLon + (track.toLon - track.fromLon) * alpha, track.fromLat + (track.toLat - track.fromLat) * alpha] as LngLat,
        },
      });
    }
    this.flashes = this.flashes.filter((flash) => now - flash.started < FLASH_MS);
    const flashes: PointFeature[] = this.flashes.map((flash) => {
      const progress = (now - flash.started) / FLASH_MS;
      const pulse = this.reducedMotion ? 0.5 : (progress * 2) % 1;
      return {
        type: "Feature",
        properties: { r: 14 + pulse * 46, o: this.reducedMotion ? 0.9 : (1 - pulse) * 0.95 },
        geometry: { type: "Point", coordinates: flash.center },
      };
    });
    (this.map.getSource("vehicles") as GeoJSONSource | undefined)?.setData({ type: "FeatureCollection", features: vehicles });
    (this.map.getSource("persons") as GeoJSONSource | undefined)?.setData({ type: "FeatureCollection", features: persons });
    (this.map.getSource("flashes") as GeoJSONSource | undefined)?.setData({ type: "FeatureCollection", features: flashes });
    this.dirty = alpha < 1;
  };
}

function emptyCollection(): PointCollection {
  return { type: "FeatureCollection", features: [] };
}

interface Sample {
  id: number;
  lon: number;
  lat: number;
  angle: number;
  kind: number;
  stopped: number;
}

function retarget<T>(tracks: Map<number, Track>, items: T[], alpha: number, read: (item: T) => Sample): void {
  const seen = new Set<number>();
  for (const item of items) {
    const sample = read(item);
    seen.add(sample.id);
    const existing = tracks.get(sample.id);
    if (existing) {
      const lon = existing.fromLon + (existing.toLon - existing.fromLon) * alpha;
      const lat = existing.fromLat + (existing.toLat - existing.fromLat) * alpha;
      const far = distanceMeters([lon, lat], [sample.lon, sample.lat]) > TELEPORT_METERS;
      existing.fromLon = far ? sample.lon : lon;
      existing.fromLat = far ? sample.lat : lat;
      existing.fromAngle = far ? sample.angle : lerpAngle(existing.fromAngle, existing.toAngle, alpha);
      existing.toLon = sample.lon;
      existing.toLat = sample.lat;
      existing.toAngle = sample.angle;
      existing.kind = sample.kind;
      existing.stopped = sample.stopped;
    } else {
      tracks.set(sample.id, {
        fromLon: sample.lon,
        fromLat: sample.lat,
        fromAngle: sample.angle,
        toLon: sample.lon,
        toLat: sample.lat,
        toAngle: sample.angle,
        kind: sample.kind,
        stopped: sample.stopped,
      });
    }
  }
  for (const id of tracks.keys()) if (!seen.has(id)) tracks.delete(id);
}
