import type { LngLat } from "../api/types";

const M_PER_DEG_LAT = 110_574;

export function localProjector(origin: LngLat) {
  const mPerDegLon = 111_320 * Math.cos((origin[1] * Math.PI) / 180);
  return ([lon, lat]: LngLat): [number, number] => [(lon - origin[0]) * mPerDegLon, -(lat - origin[1]) * M_PER_DEG_LAT];
}

export function distanceMeters(a: LngLat, b: LngLat): number {
  const mPerDegLon = 111_320 * Math.cos((a[1] * Math.PI) / 180);
  return Math.hypot((a[0] - b[0]) * mPerDegLon, (a[1] - b[1]) * M_PER_DEG_LAT);
}
