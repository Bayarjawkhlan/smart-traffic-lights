from __future__ import annotations

import json
import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

import sumolib

from . import config
from .config import SITE_SPECS, SiteSpec

STREET_NAMES_EN = {
    "Энх тайваны өргөн чөлөө": "Peace Ave",
    "Энх тайвны өргөн чөлөө": "Peace Ave",
    "Бага тойруу": "Baga Toiruu",
    "Бага Тойруу": "Baga Toiruu",
    "Чингисийн өргөн чөлөө": "Chinggis Ave",
    "Д.Сүхбаатарын гудамж": "D. Sükhbaatar St",
    "Их сургуулийн гудамж": "University St",
    "Олимпийн гудамж": "Olympic St",
    "Хичээнгүй сайд Цэрэндоржийн гудамж": "Tserendorj St",
    "Сөүлийн гудамж": "Seoul St",
    "Жуулчны гудамж": "Tourist St",
}
MAIN_STREET = "Peace Ave"

NETCONVERT_OPTIONS = [
    "--geometry.remove",
    "--ramps.guess",
    "--junctions.join",
    # 25 m merges each dual-carriageway crossing into one junction; the 10 m default leaves median links that deadlock.
    "--junctions.join-dist", "25",
    "--tls.guess-signals",
    "--tls.join",
    "--tls.join-dist", "70",
    "--tls.default-type", "static",
    "--sidewalks.guess",
    # Peace Avenue is tagged maxspeed=60; the default 13.89 m/s limit would leave it without sidewalks.
    "--sidewalks.guess.max-speed", "20",
    "--crossings.guess",
    "--osm.crossings",
    # OSM maps sidewalks as separate footways; importing them next to guessed sidewalks duplicates every sidewalk.
    "--remove-edges.by-type",
    "highway.footway,highway.path,highway.steps,highway.pedestrian,highway.crossing,highway.service",
    "--keep-edges.components", "1",
    "--remove-edges.isolated",
    "--output.street-names",
    "--osm.turn-lanes",
    "--osm.bike-access", "false",
]


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd[:3])} ...")


def netconvert(*args: str) -> None:
    run([str(config.SUMO_BIN / "netconvert"), "--no-warnings", *args])


def fetch_osm() -> None:
    if config.OSM_FILE.exists():
        return
    run(["bash", str(config.ROOT / "scripts" / "fetch_osm.sh")])


def build_network() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        base = tmp / "base.net.xml"
        netconvert("--osm-files", str(config.OSM_FILE), "-o", str(base), *NETCONVERT_OPTIONS)

        joins = [spec for spec in SITE_SPECS if spec.join_nodes]
        base_net = sumolib.net.readNet(str(base))
        groups = [sorted({_junction_containing(base_net, osm_id) for osm_id in spec.join_nodes}) for spec in joins]
        for spec in SITE_SPECS:
            if spec.join_radius:
                centre = base_net.convertLonLat2XY(spec.lon, spec.lat)
                groups.append(sorted(
                    n.getID() for n in base_net.getNodes()
                    if n.getType() == "traffic_light" and math.dist(centre, n.getCoord()) <= spec.join_radius
                ))
        nodes = tmp / "join.nod.xml"
        nodes.write_text(
            "<nodes>\n"
            + "".join(f'  <join nodes="{" ".join(group)}"/>\n' for group in groups if len(group) > 1)
            + "</nodes>\n"
        )
        joined = tmp / "joined.net.xml"
        netconvert("-s", str(base), "--node-files", str(nodes), "--crossings.guess", "-o", str(joined))

        net = sumolib.net.readNet(str(joined))
        crossings = tmp / "crossings.con.xml"
        crossings.write_text(
            "<connections>\n"
            + "".join(_midblock_crossing(net, spec) for spec in joins)
            + "</connections>\n"
        )
        netconvert("-s", str(joined), "--connection-files", str(crossings), "-o", str(config.NET_FILE))


def _junction_containing(net: sumolib.net.Net, osm_id: str) -> str:
    for node in net.getNodes():
        if node.getID() == osm_id or osm_id in node.getID().split("_"):
            return node.getID()
    raise SystemExit(f"OSM node {osm_id} is not in any junction")


def _midblock_crossing(net: sumolib.net.Net, spec: SiteSpec) -> str:
    node = net.getNode(_junction_containing(net, spec.join_nodes[0]))
    cx, _ = node.getCoord()

    def far_x(edge: sumolib.net.edge.Edge, incoming: bool) -> float:
        other = edge.getFromNode() if incoming else edge.getToNode()
        return other.getCoord()[0] - cx

    west = spec.crossing_side == "west"
    incoming = [e for e in node.getIncoming() if e.getFunction() == "" and (far_x(e, True) < 0) == west]
    outgoing = [e for e in node.getOutgoing() if e.getFunction() == "" and (far_x(e, False) < 0) == west]
    edges = " ".join(e.getID() for e in incoming + outgoing)
    return f'  <crossing node="{node.getID()}" edges="{edges}" priority="false"/>\n'


def english(name: str) -> str:
    return STREET_NAMES_EN.get(name, name)


def heading(edge: sumolib.net.edge.Edge) -> str:
    shape = edge.getShape()
    (x1, y1), (x2, y2) = shape[-2], shape[-1]
    bearing = (math.degrees(math.atan2(x2 - x1, y2 - y1)) + 360) % 360
    return ["northbound", "eastbound", "southbound", "westbound"][int(((bearing + 45) % 360) // 90)]


def resolve_sites(net: sumolib.net.Net) -> list[dict]:
    tls_centres: dict[str, tuple[float, float]] = {}
    for tl in net.getTrafficLights():
        points = [lane.getShape()[-1] for lane, _, _ in tl.getConnections() if lane.getEdge().getFunction() == ""]
        if not points:
            continue
        tls_centres[tl.getID()] = (
            sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points),
        )

    sites = []
    for spec in SITE_SPECS:
        sx, sy = net.convertLonLat2XY(spec.lon, spec.lat)
        tls_id, distance = min(
            ((tid, math.dist((sx, sy), c)) for tid, c in tls_centres.items()), key=lambda item: item[1]
        )
        if distance > 60:
            raise SystemExit(f"no traffic light within 60 m of site {spec.id} (closest {tls_id} at {distance:.0f} m)")
        tl = net.getTLS(tls_id)
        tls_nodes = {lane.getEdge().getToNode().getID() for lane, _, _ in tl.getConnections() if lane.getEdge().getFunction() == ""}

        approaches: dict[str, dict] = {}
        crosswalks: dict[str, dict] = {}
        for from_lane, to_lane, _ in tl.getConnections():
            from_edge, to_edge = from_lane.getEdge(), to_lane.getEdge()
            if to_edge.getFunction() == "crossing":
                crossed = sorted({english(e.getName()) for e in to_edge.getCrossingEdges() if e.getName()})
                crosswalks[to_edge.getID()] = {
                    "id": to_edge.getID(),
                    "label": "Crosswalk across " + (" / ".join(crossed) or "the road"),
                    "length": round(to_edge.getLength(), 1),
                }
            elif from_edge.getFunction() == "" and from_edge.getFromNode().getID() not in tls_nodes:
                approaches[from_edge.getID()] = {
                    "id": from_edge.getID(),
                    "street": from_edge.getName(),
                    "label": f"{english(from_edge.getName()) or 'Side road'} {heading(from_edge)}",
                }
        lon, lat = net.convertXY2LonLat(*tls_centres[tls_id])
        sites.append(
            {
                "id": spec.id,
                "nameEn": spec.name_en,
                "nameMn": spec.name_mn,
                "kind": spec.kind,
                "tls": tls_id,
                "center": [round(lon, 6), round(lat, 6)],
                "approaches": sorted(approaches.values(), key=lambda a: a["label"]),
                "crosswalks": sorted(crosswalks.values(), key=lambda c: c["id"]),
            }
        )

    by_tls = {site["tls"]: site["id"] for site in sites}
    for site in sites:
        tl = net.getTLS(site["tls"])
        neighbours: set[str] = set()
        for _, to_lane, _ in tl.getConnections():
            edge = to_lane.getEdge()
            for _ in range(6):
                node = edge.getToNode()
                found = [t for t, sid in by_tls.items() if sid != site["id"] and node.getID() in _tls_node_ids(net, t)]
                if found:
                    neighbours.add(by_tls[found[0]])
                    break
                nxt = [e for e in edge.getOutgoing() if e.getFunction() == "" and e.getName() == edge.getName()]
                if not nxt:
                    break
                edge = nxt[0]
        site["neighbours"] = sorted(neighbours)
    return sites


_TLS_NODES: dict[str, set[str]] = {}


def _tls_node_ids(net: sumolib.net.Net, tls_id: str) -> set[str]:
    if tls_id not in _TLS_NODES:
        _TLS_NODES[tls_id] = {
            lane.getEdge().getToNode().getID()
            for lane, _, _ in net.getTLS(tls_id).getConnections()
            if lane.getEdge().getFunction() == ""
        }
    return _TLS_NODES[tls_id]


def lonlat_shape(net: sumolib.net.Net, shape: list[tuple[float, float]]) -> list[list[float]]:
    return [[round(c, 7) for c in net.convertXY2LonLat(x, y)] for x, y in shape]


def perpendicular(shape: list[tuple[float, float]], half_width: float) -> list[tuple[float, float]]:
    (x1, y1), (x2, y2) = shape[-2], shape[-1]
    length = math.hypot(x2 - x1, y2 - y1) or 1.0
    nx, ny = -(y2 - y1) / length, (x2 - x1) / length
    bx, by = x2 - (x2 - x1) / length * 1.0, y2 - (y2 - y1) / length * 1.0
    return [(bx + nx * half_width, by + ny * half_width), (bx - nx * half_width, by - ny * half_width)]


def export_geometry(net: sumolib.net.Net, sites: list[dict]) -> None:
    roads, sidewalks, crossings, heads = [], [], [], []
    site_by_tls = {site["tls"]: site["id"] for site in sites}

    for edge in net.getEdges(withInternal=False):
        if edge.getFunction() != "":
            continue
        lanes = edge.getLanes()
        drivable = [lane for lane in lanes if lane.allows("passenger") or lane.allows("bus")]
        walk = [lane for lane in lanes if lane.allows("pedestrian") and not lane.allows("passenger")]
        if drivable:
            roads.append(
                {
                    "type": "Feature",
                    "properties": {
                        "id": edge.getID(),
                        "name": edge.getName(),
                        "nameEn": english(edge.getName()),
                        "lanes": len(drivable),
                        "main": english(edge.getName()) == MAIN_STREET,
                        "speed": round(edge.getSpeed(), 2),
                    },
                    "geometry": {"type": "LineString", "coordinates": lonlat_shape(net, edge.getShape())},
                }
            )
        for lane in walk:
            sidewalks.append(
                {
                    "type": "Feature",
                    "properties": {"id": lane.getID()},
                    "geometry": {"type": "LineString", "coordinates": lonlat_shape(net, lane.getShape())},
                }
            )

    for tl in net.getTrafficLights():
        site_id = site_by_tls.get(tl.getID())
        lane_links: dict[str, list[int]] = {}
        for from_lane, to_lane, index in tl.getConnections():
            to_edge = to_lane.getEdge()
            if to_edge.getFunction() == "crossing":
                crossings.append(
                    {
                        "type": "Feature",
                        "properties": {"id": to_edge.getID(), "site": site_id, "tls": tl.getID(), "link": index},
                        "geometry": {"type": "LineString", "coordinates": lonlat_shape(net, to_lane.getShape())},
                    }
                )
            elif from_lane.getEdge().getFunction() == "":
                lane_links.setdefault(from_lane.getID(), []).append(index)
        for lane_id, indices in lane_links.items():
            lane = net.getLane(lane_id)
            heads.append(
                {
                    "type": "Feature",
                    "properties": {"site": site_id, "tls": tl.getID(), "links": sorted(set(indices)), "lane": lane_id},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": lonlat_shape(net, perpendicular(lane.getShape(), lane.getWidth() / 2 - 0.2)),
                    },
                }
            )

    xmin, ymin, xmax, ymax = net.getBoundary()
    west, south = net.convertXY2LonLat(xmin, ymin)
    east, north = net.convertXY2LonLat(xmax, ymax)
    payload = {
        "bounds": [[round(west, 6), round(south, 6)], [round(east, 6), round(north, 6)]],
        "sites": sites,
        "roads": {"type": "FeatureCollection", "features": roads},
        "sidewalks": {"type": "FeatureCollection", "features": sidewalks},
        "crossings": {"type": "FeatureCollection", "features": crossings},
        "signalHeads": {"type": "FeatureCollection", "features": heads},
    }
    config.GEO_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


SCENARIOS: dict[str, dict] = {
    "morning-rush": {"label": "Morning rush", "main": {"eastbound": 540, "westbound": 400}, "side": 115, "ped_period": 2.6},
    "midday": {"label": "Midday", "main": {"eastbound": 400, "westbound": 400}, "side": 90, "ped_period": 3.2},
    "evening-rush": {"label": "Evening rush", "main": {"eastbound": 400, "westbound": 560}, "side": 120, "ped_period": 2.4},
    "incident": {
        "label": "Incident: lane blocked",
        "main": {"eastbound": 520, "westbound": 450},
        "side": 110,
        "ped_period": 3.2,
        "incident": {"site": "ikh-surguuli", "approach": "Peace Ave eastbound", "start": 240, "end": 1500},
    },
    "pedestrian-surge": {
        "label": "Pedestrian surge (event at the square)",
        "main": {"eastbound": 420, "westbound": 420},
        "side": 90,
        "ped_period": 0.8,
        "ped_focus": "tuv-shuudan",
    },
}
SCENARIO_DURATION = 3600
MINOR_ENTRY_SHARE = 0.12


def _street_weight(name: str, main: float, major: float, minor: float) -> float:
    if english(name) == MAIN_STREET:
        return main
    return major if name in STREET_NAMES_EN else minor


def fringe_edges(net: sumolib.net.Net) -> tuple[list[sumolib.net.edge.Edge], list[sumolib.net.edge.Edge]]:
    def drivable(edge: sumolib.net.edge.Edge) -> bool:
        return edge.getFunction() == "" and edge.allows("passenger")

    entries = [
        e for e in net.getEdges(withInternal=False)
        if drivable(e) and not [i for i in e.getFromNode().getIncoming() if drivable(i) and i.getFromNode() != e.getToNode()]
    ]
    exits = [
        e for e in net.getEdges(withInternal=False)
        if drivable(e) and not [o for o in e.getToNode().getOutgoing() if drivable(o) and o.getToNode() != e.getFromNode()]
    ]
    return entries, exits


def write_scenarios(net: sumolib.net.Net, sites: list[dict]) -> None:
    config.SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    entries, exits = fringe_edges(net)
    rng = random.Random(7)

    pairs: list[tuple[sumolib.net.edge.Edge, sumolib.net.edge.Edge, float]] = []
    for entry in entries:
        for exit_ in exits:
            if exit_.getFromNode() == entry.getToNode() or exit_.getToNode() == entry.getFromNode():
                continue
            path, _ = net.getShortestPath(entry, exit_, vClass="passenger")
            if not path or len(path) < 3:
                continue
            pairs.append((entry, exit_, _street_weight(exit_.getName(), main=6.0, major=2.0, minor=0.3)))

    for name, spec in SCENARIOS.items():
        flows = []
        by_entry: dict[str, list[tuple[sumolib.net.edge.Edge, float]]] = {}
        for entry, exit_, weight in pairs:
            by_entry.setdefault(entry.getID(), []).append((exit_, weight))
        for entry_id, targets in sorted(by_entry.items()):
            entry = net.getEdge(entry_id)
            if english(entry.getName()) == MAIN_STREET:
                total = spec["main"][heading(entry) if heading(entry) in spec["main"] else "eastbound"]
            elif entry.getName() in STREET_NAMES_EN:
                total = spec["side"]
            else:
                total = spec["side"] * MINOR_ENTRY_SHARE
            weight_sum = sum(w for _, w in targets)
            for exit_, weight in targets:
                rate = total * weight / weight_sum
                if rate < 1:
                    continue
                begin = rng.uniform(0, min(3600 / rate, SCENARIO_DURATION - 1))
                flows.append((begin,
                    f'  <flow id="f_{entry_id}_{exit_.getID()}" type="mix" begin="{begin:.1f}" end="{SCENARIO_DURATION}" '
                    f'from="{entry_id}" to="{exit_.getID()}" vehsPerHour="{rate:.1f}" departLane="best" departSpeed="max"/>\n'
                ))
        routes = config.SCENARIO_DIR / f"{name}.rou.xml"
        routes.write_text(
            "<routes>\n"
            '  <vType id="car" vClass="passenger" sigma="0.5" length="4.6" minGap="2.2" maxSpeed="16.7" guiShape="passenger"/>\n'
            '  <vType id="bus" vClass="bus" length="12" minGap="2.5" maxSpeed="15" guiShape="bus"/>\n'
            '  <vType id="truck" vClass="truck" length="8" minGap="2.5" maxSpeed="15" guiShape="truck"/>\n'
            '  <vTypeDistribution id="mix" vTypes="car bus truck" probabilities="0.9 0.05 0.05"/>\n'
            # SUMO silently drops flows that are not sorted by begin time.
            + "".join(line for _, line in sorted(flows))
            + "</routes>\n"
        )
        _write_pedestrians(net, name, spec, sites, rng.randint(1, 10_000))

    meta = {
        name: {k: v for k, v in spec.items() if k in ("label", "incident", "ped_focus")} | {"duration": SCENARIO_DURATION}
        for name, spec in SCENARIOS.items()
    }
    (config.SCENARIO_DIR / "scenarios.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))


def _write_pedestrians(net: sumolib.net.Net, name: str, spec: dict, sites: list[dict], seed: int) -> None:
    out = config.SCENARIO_DIR / f"{name}.ped.rou.xml"
    cmd = [
        sys.executable,
        str(config.SUMO_TOOLS / "randomTrips.py"),
        "-n", str(config.NET_FILE),
        "-o", str(config.SCENARIO_DIR / f"{name}.ped.trips.xml"),
        "-r", str(out),
        "--pedestrians",
        "--prefix", "p",
        "--seed", str(seed),
        "-b", "0",
        "-e", str(SCENARIO_DURATION),
        "-p", str(spec["ped_period"]),
        "--min-distance", "150",
        "--max-distance", "900",
        "--validate",
    ]
    if focus := spec.get("ped_focus"):
        site = next(s for s in sites if s["id"] == focus)
        fx, fy = net.convertLonLat2XY(*site["center"])
        prefix = config.SCENARIO_DIR / f"{name}.weights"
        lines = []
        for edge in net.getEdges(withInternal=False):
            if edge.getFunction() == "" and edge.allows("pedestrian"):
                d = math.dist((fx, fy), edge.getShape()[len(edge.getShape()) // 2])
                lines.append(f'    <edge id={quoteattr(edge.getID())} value="{30.0 if d < 220 else 1.0}"/>\n')
        body = '<edgedata>\n  <interval begin="0" end="{}">\n{}  </interval>\n</edgedata>\n'.format(SCENARIO_DURATION, "".join(lines))
        Path(f"{prefix}.src.xml").write_text(body)
        Path(f"{prefix}.dst.xml").write_text(body)
        cmd += ["--weights-prefix", str(prefix)]
    run(cmd)
    for suffix in (".weights.src.xml", ".weights.dst.xml", ".ped.trips.xml"):
        (config.SCENARIO_DIR / f"{name}{suffix}").unlink(missing_ok=True)


def main() -> None:
    config.DATA.mkdir(exist_ok=True)
    fetch_osm()
    build_network()
    net = sumolib.net.readNet(str(config.NET_FILE), withPrograms=True, withPedestrianConnections=True)
    sites = resolve_sites(net)
    config.SITES_FILE.write_text(json.dumps(sites, indent=2, ensure_ascii=False))
    export_geometry(net, sites)
    write_scenarios(net, sites)
    for site in sites:
        print(
            f"{site['id']:18s} tls={site['tls'][:40]:40s} approaches={len(site['approaches'])} "
            f"crosswalks={len(site['crosswalks'])} neighbours={site['neighbours']}"
        )


if __name__ == "__main__":
    main()
