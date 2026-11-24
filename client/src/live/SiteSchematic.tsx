import { useMemo } from "react";
import type { Frame, Network, SiteFrame, SiteInfo } from "../api/types";
import { useI18n } from "../i18n/I18n";
import { distanceMeters, localProjector } from "../lib/geo";
import { bestLight, linkLight, type Light } from "../lib/signals";

const RADIUS = 90;
const LANE_WIDTH = 3.3;
const JUNCTION_REACH = 12;
const BADGE_LIMIT = RADIUS - 6;

interface Geometry {
  junction: string | null;
  roads: { id: string; d: string; width: number; approach: number | null }[];
  sidewalks: string[];
  crossings: { id: string; d: string; link: number; own: boolean }[];
  heads: { d: string; links: number[] }[];
  badges: { n: number; x: number; y: number }[];
}

const pathOf = (points: [number, number][]) =>
  points.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join("");

function buildGeometry(network: Network, site: SiteInfo): Geometry {
  const project = localProjector(site.center);
  const near = (coords: [number, number][]) => coords.some((c) => distanceMeters(site.center, c) < RADIUS * 1.6);
  const approachIndex = new Map(site.approaches.map((a, i) => [a.id, i]));

  const roads: Geometry["roads"] = [];
  const badges: Geometry["badges"] = [];
  for (const feature of network.roads.features) {
    if (!near(feature.geometry.coordinates)) continue;
    const points = feature.geometry.coordinates.map(project);
    const approach = approachIndex.get(feature.properties.id) ?? null;
    roads.push({ id: feature.properties.id, d: pathOf(points), width: feature.properties.lanes * LANE_WIDTH, approach });
    if (approach !== null) {
      const badge = pointBack(points, 26);
      const offset = feature.properties.lanes * LANE_WIDTH * 0.5 + 6;
      badges.push({
        n: approach + 1,
        x: clampToView(badge.x + badge.nx * offset),
        y: clampToView(badge.y + badge.ny * offset),
      });
    }
  }
  const own = [...network.signalHeads.features, ...network.crossings.features]
    .filter((f) => f.properties.site === site.id)
    .flatMap((f) => f.geometry.coordinates);
  const ends = network.roads.features
    .flatMap((f) => [f.geometry.coordinates[0], f.geometry.coordinates[f.geometry.coordinates.length - 1]])
    .filter((c) => c !== undefined)
    .filter((c) => own.some((point) => distanceMeters(point, c) < JUNCTION_REACH));
  const hull = convexHull([...own, ...ends].map(project));
  return {
    junction: hull.length >= 3 ? `${pathOf(hull)}Z` : null,
    roads,
    sidewalks: network.sidewalks.features.filter((f) => near(f.geometry.coordinates)).map((f) => pathOf(f.geometry.coordinates.map(project))),
    crossings: network.crossings.features
      .filter((f) => near(f.geometry.coordinates))
      .map((f) => ({ id: f.properties.id, d: pathOf(f.geometry.coordinates.map(project)), link: f.properties.link, own: f.properties.site === site.id })),
    heads: network.signalHeads.features
      .filter((f) => f.properties.site === site.id)
      .map((f) => ({ d: pathOf(f.geometry.coordinates.map(project)), links: f.properties.links })),
    badges,
  };
}

const clampToView = (value: number) => Math.min(Math.max(value, -BADGE_LIMIT), BADGE_LIMIT);

function convexHull(points: [number, number][]): [number, number][] {
  const sorted = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (sorted.length < 3) return sorted;
  const cross = (o: [number, number], a: [number, number], b: [number, number]) =>
    (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower: [number, number][] = [];
  for (const p of sorted) {
    while (lower.length >= 2 && cross(lower[lower.length - 2]!, lower[lower.length - 1]!, p) <= 0) lower.pop();
    lower.push(p);
  }
  const upper: [number, number][] = [];
  for (const p of [...sorted].reverse()) {
    while (upper.length >= 2 && cross(upper[upper.length - 2]!, upper[upper.length - 1]!, p) <= 0) upper.pop();
    upper.push(p);
  }
  return [...lower.slice(0, -1), ...upper.slice(0, -1)];
}

function pointBack(points: [number, number][], distance: number) {
  let remaining = distance;
  for (let i = points.length - 1; i > 0; i--) {
    const [x1, y1] = points[i]!;
    const [x0, y0] = points[i - 1]!;
    const length = Math.hypot(x1 - x0, y1 - y0) || 1;
    const nx = -(y1 - y0) / length;
    const ny = (x1 - x0) / length;
    if (length >= remaining) {
      const f = remaining / length;
      return { x: x1 + (x0 - x1) * f, y: y1 + (y0 - y1) * f, nx, ny };
    }
    remaining -= length;
  }
  const [x, y] = points[0]!;
  return { x, y, nx: 0, ny: 0 };
}

const LIGHT_CLASS: Record<Light, string> = {
  green: "is-green",
  amber: "is-amber",
  red: "is-red",
  flashing: "is-flashing",
  off: "is-off",
};

interface Props {
  network: Network;
  site: SiteInfo;
  state: SiteFrame | undefined;
  frame: Frame | null;
  highlight: string | null;
}

export function SiteSchematic({ network, site, state, frame, highlight }: Props) {
  const { t } = useI18n();
  const geometry = useMemo(() => buildGeometry(network, site), [network, site]);
  const project = useMemo(() => localProjector(site.center), [site]);
  const vehicles = (frame?.vehicles ?? []).filter((v) => distanceMeters(site.center, [v[1], v[2]]) < RADIUS * 1.3);
  const persons = (frame?.persons ?? []).filter((p) => distanceMeters(site.center, [p[1], p[2]]) < RADIUS * 1.3);
  const clipId = `clip-${site.id}`;

  return (
    <figure className="schematic">
      <svg viewBox={`${-RADIUS} ${-RADIUS} ${RADIUS * 2} ${RADIUS * 2}`} role="img" aria-label={t("schematicNote")}>
        <defs>
          <clipPath id={clipId}>
            <rect x={-RADIUS} y={-RADIUS} width={RADIUS * 2} height={RADIUS * 2} rx="6" />
          </clipPath>
        </defs>
        <g clipPath={`url(#${clipId})`}>
          <rect x={-RADIUS} y={-RADIUS} width={RADIUS * 2} height={RADIUS * 2} className="schematic__ground" />
          {geometry.sidewalks.map((d, i) => (
            <path key={i} d={d} className="schematic__sidewalk" />
          ))}
          {geometry.junction && <path d={geometry.junction} className="schematic__junction" />}
          {geometry.roads.map((road) => (
            <path
              key={road.id}
              d={road.d}
              className={`schematic__road${road.approach !== null ? " is-approach" : ""}${highlight === road.id ? " is-highlight" : ""}`}
              strokeWidth={road.width}
            />
          ))}
          {geometry.crossings.map((crossing) => {
            const light = crossing.own && state ? linkLight(state.state, crossing.link, state.flashing) : "off";
            return (
              <path
                key={crossing.id}
                d={crossing.d}
                className={`schematic__crossing ${crossing.own ? LIGHT_CLASS[light] : "is-background"}${highlight === crossing.id ? " is-highlight" : ""}`}
              />
            );
          })}
          {geometry.heads.map((head, i) => (
            <path key={i} d={head.d} className={`schematic__head ${state ? LIGHT_CLASS[bestLight(state.state, head.links)] : "is-off"}`} />
          ))}
          {vehicles.map(([id, lon, lat, angle, kind, stopped]) => {
            const [x, y] = project([lon, lat]);
            const length = kind === 1 ? 12 : kind === 2 ? 8 : 4.6;
            return (
              <rect
                key={id}
                x={-0.95}
                y={-length / 2}
                width={1.9}
                height={length}
                rx={0.6}
                className={`schematic__vehicle kind-${kind}${stopped ? " is-stopped" : ""}`}
                transform={`translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${angle})`}
              />
            );
          })}
          {persons.map(([id, lon, lat]) => {
            const [x, y] = project([lon, lat]);
            return <circle key={id} cx={x} cy={y} r={0.9} className="schematic__person" />;
          })}
          {geometry.badges.map((badge) => (
            <g key={badge.n} className="schematic__badge" transform={`translate(${badge.x.toFixed(1)} ${badge.y.toFixed(1)})`}>
              <circle r="4.6" />
              <text dy="1.7">{badge.n}</text>
            </g>
          ))}
        </g>
        <g className="schematic__scale" transform={`translate(${RADIUS - 30} ${RADIUS - 8})`}>
          <path d="M0 0h20M0 -2v2M20 -2v2" />
          <text x="10" y="-3.5">20 m</text>
        </g>
        <g className="schematic__north" transform={`translate(${-RADIUS + 9} ${-RADIUS + 10})`}>
          <path d="M0 -5L3 3L0 1.5L-3 3Z" />
          <text y="10">N</text>
        </g>
      </svg>
      <figcaption>{t("schematicNote")}</figcaption>
    </figure>
  );
}
