from __future__ import annotations

import heapq
import json
import math
import random
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import quoteattr

import sumolib

from . import config
from .config import CORRIDOR_SPECS, SITE_SPECS, CorridorSpec, SiteSpec
from .model import load_sites, validate_sites

Edge = sumolib.net.edge.Edge
Net = sumolib.net.Net


@dataclass(frozen=True)
class Street:
    mn: str
    en: str
    cls: str = "minor"


STREETS = (
    Street("Энх тайваны өргөн чөлөө", "Peace Ave", "arterial"),
    Street("Ж.Самбуугийн гудамж", "Sambuu St", "arterial"),
    Street("Чингисийн өргөн чөлөө", "Chinggis Ave", "arterial"),
    Street("Д.Сүхбаатарын гудамж", "Sükhbaatar St", "arterial"),
    Street("Бага тойруу", "Baga Toiruu", "collector"),
    Street("Их сургуулийн гудамж", "University St", "collector"),
    Street("Олимпийн гудамж", "Olympic St", "collector"),
    Street("Жуулчны гудамж", "Juulchny St", "collector"),
    Street("Сөүлийн гудамж", "Seoul St", "collector"),
    Street("П.Гэндэнгийн гудамж", "Genden St", "collector"),
    Street("Хичээнгүй сайд Цэрэндоржийн гудамж", "Tserendorj St", "collector"),
    Street("Баруун Сэлбийн гудамж", "Baruun Selbe St"),
    Street("Ерөнхий сайд Амарын гудамж", "Amar St"),
    Street("Анкарагийн гудамж", "Ankara St"),
    Street("Бээжингийн гудамж", "Beijing St", "arterial"),
    Street("Элчингийн гудамж", "Ambassador St"),
    Street("Усны гудамж", "Usny St"),
    Street("ЮНЭСКО-н гудамж", "UNESCO St"),
    Street("Нэгдсэн үндэсний гудамж", "United Nations St"),
    Street("Парисын гудамж", "Paris St"),
    Street("Эрхүүгийн гудамж", "Irkutsk St"),
    Street("Төмөрчний гудамж", "Tömörchny St"),
    Street("Оюутны гудамж", "Students St"),
    Street("Хуульчдын гудамж", "Khuulchdyn St"),
    Street("Гал сөнөөгчдийн гудамж", "Gal Sönöögchdiin St"),
    Street("Жамъян гүний гудамж", "Jamyan Gun St"),
    Street("Чин ван Ханддоржийн гудамж", "Khanddorj St"),
    Street("Ноён хутагт Данзанравжаагийн гудамж", "Danzanravjaa St"),
    Street("Лодонгийн Түдэвийн гудамж", "Tüdev St"),
    Street("Л. Лааганы гудамж", "Laagan St"),
    Street("Г.Чагдаржавын гудамж", "Chagdarjav St"),
    Street("Б.Ренчингийн гудамж", "Renchin St"),
    Street("Б.Ширэндэвийн гудамж", "Shirendev St"),
    Street("Д.Дамбын гудамж", "Damba St"),
    Street("Д.Чойдогийн гудамж", "Choidog St"),
    Street("С.Зоригийн гудамж", "Zorig St"),
    Street("С.Данзангийн гудамж", "Danzan St"),
    Street("Ц.Жигжиджавын гудамж", "Jigjidjav St"),
)
STREET_BY_NAME = {street.mn.casefold(): street for street in STREETS}
STREET_BY_NAME["энх тайвны өргөн чөлөө"] = STREET_BY_NAME["энх тайваны өргөн чөлөө"]

UNNAMED_WAYS = {
    "863783234": "Энх тайваны өргөн чөлөө",
    "81528712": "Бага тойруу",
    "81528723": "Ж.Самбуугийн гудамж",
    "303599291": "Бээжингийн гудамж",
    "34409213": "Баруун Сэлбийн гудамж",
    "512970905": "Баруун Сэлбийн гудамж",
    "708458504": "Усны гудамж",
}

NEIGHBOUR_METRES = 700.0
BOUNDS_MARGIN_METRES = 150.0

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


# The headers hold timestamps and local paths, so every rebuild would change the network hash the results are tied to.
def strip_header(path: Path) -> None:
    path.write_text(re.sub(r"<!-- generated on .*?-->\n+", "", path.read_text(), flags=re.S))


def fetch_osm() -> None:
    if config.OSM_FILE.exists():
        return
    run(["bash", str(config.ROOT / "scripts" / "fetch_osm.sh")])


def build_network() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        base = tmp / "base.net.xml"
        netconvert("--osm-files", str(config.OSM_FILE), "-o", str(base), *NETCONVERT_OPTIONS)

        base_net = sumolib.net.readNet(str(base))
        joins = []
        for spec in SITE_SPECS:
            group = sorted({_junction_containing(base_net, spec, osm_id) for osm_id in spec.join_nodes})
            if len(group) > 1:
                joins.append(f'  <join nodes="{" ".join(group)}" reset="{str(spec.reset_connections).lower()}"/>\n')
        nodes = tmp / "join.nod.xml"
        nodes.write_text("<nodes>\n" + "".join(joins) + "</nodes>\n")
        joined = tmp / "joined.net.xml"
        netconvert("-s", str(base), "--node-files", str(nodes), "--crossings.guess", "-o", str(joined))

        net = sumolib.net.readNet(str(joined))
        crossings = tmp / "crossings.con.xml"
        crossings.write_text(
            "<connections>\n"
            + "".join(_midblock_crossing(net, spec) for spec in SITE_SPECS if spec.kind == "midblock")
            + "</connections>\n"
        )
        netconvert("-s", str(joined), "--connection-files", str(crossings), "-o", str(config.NET_FILE))
    strip_header(config.NET_FILE)


def _junction_containing(net: Net, spec: SiteSpec, osm_id: str) -> str:
    for node in net.getNodes():
        if osm_id in node.getID().split("_"):
            return node.getID()
    raise SystemExit(f"{spec.id}: OSM node {osm_id} is not in any junction")


def _midblock_crossing(net: Net, spec: SiteSpec) -> str:
    node = net.getNode(_junction_containing(net, spec, spec.join_nodes[0]))
    cx, _ = node.getCoord()

    def far_x(edge: Edge, incoming: bool) -> float:
        other = edge.getFromNode() if incoming else edge.getToNode()
        return other.getCoord()[0] - cx

    west = spec.crossing_side == "west"
    incoming = [e for e in node.getIncoming() if e.getFunction() == "" and (far_x(e, True) < 0) == west]
    outgoing = [e for e in node.getOutgoing() if e.getFunction() == "" and (far_x(e, False) < 0) == west]
    edges = " ".join(e.getID() for e in incoming + outgoing)
    return f'  <crossing node="{node.getID()}" edges="{edges}" priority="false"/>\n'


def way_id(edge: Edge) -> str:
    return re.match(r"-?(\w+)", edge.getID()).group(1)


def street_of(edge: Edge) -> Street | None:
    name = edge.getName() or UNNAMED_WAYS.get(way_id(edge), "")
    if not name:
        return None
    return STREET_BY_NAME.get(name.casefold(), Street(name, name))


def street_class(edge: Edge) -> str:
    street = street_of(edge)
    return street.cls if street else "minor"


def heading(edge: Edge) -> str:
    shape = edge.getShape()
    (x1, y1), (x2, y2) = shape[-2], shape[-1]
    bearing = (math.degrees(math.atan2(x2 - x1, y2 - y1)) + 360) % 360
    return ["northbound", "eastbound", "southbound", "westbound"][int(((bearing + 45) % 360) // 90)]


def resolve_sites(net: Net) -> list[dict]:
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
        nodes = _tls_nodes(net, tls_id)
        _check_street_names(net, spec, nodes)

        approaches: dict[str, dict] = {}
        crosswalks: dict[str, dict] = {}
        for from_lane, to_lane, _ in tl.getConnections():
            from_edge, to_edge = from_lane.getEdge(), to_lane.getEdge()
            if to_edge.getFunction() == "crossing":
                crossed = {s.en: s for e in to_edge.getCrossingEdges() if (s := street_of(e))}
                streets = [crossed[en] for en in sorted(crossed)]
                crosswalks[to_edge.getID()] = {
                    "id": to_edge.getID(),
                    "label": "Crosswalk across " + (" / ".join(s.en for s in streets) or "the road"),
                    "streets": [{"en": s.en, "mn": s.mn} for s in streets],
                    "length": round(to_edge.getLength(), 1),
                }
            elif from_edge.getFunction() == "" and from_edge.getFromNode().getID() not in nodes:
                street, direction = street_of(from_edge), heading(from_edge)
                approaches[from_edge.getID()] = {
                    "id": from_edge.getID(),
                    "street": street.mn if street else "",
                    "streetEn": street.en if street else "",
                    "direction": direction,
                    "label": f"{street.en if street else 'Side road'} {direction}",
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
                "approaches": sorted(approaches.values(), key=lambda a: (a["label"], a["id"])),
                "crosswalks": sorted(crosswalks.values(), key=lambda c: c["id"]),
            }
        )

    neighbours = _neighbours(net, sites)
    for site in sites:
        site["neighbours"] = sorted(neighbours[site["id"]])
    return sites


def _tls_nodes(net: Net, tls_id: str) -> set[str]:
    return {
        lane.getEdge().getToNode().getID()
        for lane, _, _ in net.getTLS(tls_id).getConnections()
        if lane.getEdge().getFunction() == ""
    }


def _check_street_names(net: Net, spec: SiteSpec, nodes: set[str]) -> None:
    edges = [e for n in nodes for e in (*net.getNode(n).getIncoming(), *net.getNode(n).getOutgoing()) if e.getFunction() == ""]
    missing = {e.getName() for e in edges if e.getName() and e.getName().casefold() not in STREET_BY_NAME}
    if missing:
        raise SystemExit(f"{spec.id}: no street table entry for {', '.join(sorted(missing))}")


def _neighbours(net: Net, sites: list[dict]) -> dict[str, set[str]]:
    site_at = {node: site["id"] for site in sites for node in _tls_nodes(net, site["tls"])}
    result: dict[str, set[str]] = {site["id"]: set() for site in sites}
    for site in sites:
        nodes = {node for node, sid in site_at.items() if sid == site["id"]}
        exits = [
            e for n in nodes for e in net.getNode(n).getOutgoing()
            if e.getFunction() == "" and e.allows("passenger") and e.getToNode().getID() not in nodes
        ]
        queue = [(0.0, e.getID(), True, True) for e in exits]
        heapq.heapify(queue)
        seen: set[str] = set()
        reached: set[str] = set()
        while queue:
            distance, edge_id, clear, is_exit = heapq.heappop(queue)
            if edge_id in seen or distance > NEIGHBOUR_METRES:
                continue
            seen.add(edge_id)
            edge = net.getEdge(edge_id)
            other = site_at.get(edge.getToNode().getID())
            if other and other != site["id"] and other not in reached:
                reached.add(other)
                if clear:
                    result[site["id"]].add(other)
                    result[other].add(site["id"])
            clear = clear and not other
            length = 0.0 if is_exit else edge.getLength()
            for following in edge.getOutgoing():
                if following.getFunction() == "" and following.allows("passenger"):
                    heapq.heappush(queue, (distance + length, following.getID(), clear, False))
    return result


def check_corridors(sites: list[dict], corridors: tuple[CorridorSpec, ...]) -> list[str]:
    neighbours = {site["id"]: set(site["neighbours"]) for site in sites}
    problems = [f"Corridor {c.id}: unknown site {sid}" for c in corridors for sid in c.sites if sid not in neighbours]
    return problems or [
        f"Corridor {c.id}: {a} and {b} are not Neighbours"
        for c in corridors
        for a, b in zip(c.sites, c.sites[1:])
        if b not in neighbours[a]
    ]


def lonlat_shape(net: Net, shape: list[tuple[float, float]]) -> list[list[float]]:
    return [[round(c, 7) for c in net.convertXY2LonLat(x, y)] for x, y in shape]


def perpendicular(shape: list[tuple[float, float]], half_width: float) -> list[tuple[float, float]]:
    (x1, y1), (x2, y2) = shape[-2], shape[-1]
    length = math.hypot(x2 - x1, y2 - y1) or 1.0
    nx, ny = -(y2 - y1) / length, (x2 - x1) / length
    bx, by = x2 - (x2 - x1) / length * 1.0, y2 - (y2 - y1) / length * 1.0
    return [(bx + nx * half_width, by + ny * half_width), (bx - nx * half_width, by - ny * half_width)]


def _walkway(lane: sumolib.net.lane.Lane) -> bool:
    return lane.allows("pedestrian") and not lane.allows("passenger")


def export_geometry(net: Net, sites: list[dict]) -> None:
    roads, sidewalks, crossings, heads = [], [], [], []
    site_by_tls = {site["tls"]: site["id"] for site in sites}

    for edge in net.getEdges(withInternal=False):
        if edge.getFunction() != "":
            continue
        lanes = edge.getLanes()
        drivable = [lane for lane in lanes if lane.allows("passenger") or lane.allows("bus")]
        walk = [lane for lane in lanes if _walkway(lane)]
        if drivable:
            street = street_of(edge)
            roads.append(
                {
                    "type": "Feature",
                    "properties": {
                        "id": edge.getID(),
                        "name": street.mn if street else "",
                        "nameEn": street.en if street else "",
                        "lanes": len(drivable),
                        "main": street_class(edge) == "arterial",
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

    centres = [net.convertLonLat2XY(*site["center"]) for site in sites]
    xs, ys = [x for x, _ in centres], [y for _, y in centres]
    west, south = net.convertXY2LonLat(min(xs) - BOUNDS_MARGIN_METRES, min(ys) - BOUNDS_MARGIN_METRES)
    east, north = net.convertXY2LonLat(max(xs) + BOUNDS_MARGIN_METRES, max(ys) + BOUNDS_MARGIN_METRES)
    payload = {
        "bounds": [[round(west, 6), round(south, 6)], [round(east, 6), round(north, 6)]],
        "sites": sites,
        "corridors": [
            {"id": c.id, "nameEn": c.name_en, "nameMn": c.name_mn, "axis": c.axis, "sites": list(c.sites)} for c in CORRIDOR_SPECS
        ],
        "roads": {"type": "FeatureCollection", "features": roads},
        "sidewalks": {"type": "FeatureCollection", "features": sidewalks},
        "crossings": {"type": "FeatureCollection", "features": crossings},
        "signalHeads": {"type": "FeatureCollection", "features": heads},
    }
    config.GEO_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def _volumes(northbound: int, eastbound: int, southbound: int, westbound: int) -> dict[str, int]:
    return {"northbound": northbound, "eastbound": eastbound, "southbound": southbound, "westbound": westbound}


# Arterial eastbound and westbound entries are the Peace Avenue volumes of the original five-site demo.
SCENARIOS: dict[str, dict] = {
    "morning-rush": {
        "label": "Morning rush",
        "entry": {
            "arterial": _volumes(420, 540, 420, 400),
            "collector": _volumes(220, 160, 260, 160),
            "minor": _volumes(16, 16, 16, 16),
        },
        "exit": {
            "arterial": _volumes(400, 540, 400, 400),
            "collector": _volumes(160, 120, 160, 120),
            "minor": _volumes(16, 16, 16, 16),
        },
        "ped_period": 2.6,
    },
    "midday": {
        "label": "Midday",
        "entry": {
            "arterial": _volumes(300, 400, 300, 400),
            "collector": _volumes(160, 120, 160, 120),
            "minor": _volumes(14, 14, 14, 14),
        },
        "exit": {
            "arterial": _volumes(300, 400, 300, 400),
            "collector": _volumes(130, 100, 130, 100),
            "minor": _volumes(14, 14, 14, 14),
        },
        "ped_period": 3.2,
    },
    "evening-rush": {
        "label": "Evening rush",
        "entry": {
            "arterial": _volumes(380, 400, 380, 560),
            "collector": _volumes(260, 150, 220, 150),
            "minor": _volumes(16, 16, 16, 16),
        },
        "exit": {
            "arterial": _volumes(400, 400, 400, 560),
            "collector": _volumes(160, 120, 160, 120),
            "minor": _volumes(16, 16, 16, 16),
        },
        "ped_period": 2.4,
    },
    "incident": {
        "label": "Incident: lane blocked",
        "entry": {
            "arterial": _volumes(340, 520, 340, 450),
            "collector": _volumes(190, 140, 190, 140),
            "minor": _volumes(15, 15, 15, 15),
        },
        "exit": {
            "arterial": _volumes(340, 520, 340, 450),
            "collector": _volumes(150, 110, 150, 110),
            "minor": _volumes(15, 15, 15, 15),
        },
        "ped_period": 3.2,
        "incident": {"site": "ikh-surguuli", "street": "Peace Ave", "direction": "eastbound", "start": 240, "end": 1500},
    },
    "pedestrian-surge": {
        "label": "Pedestrian surge (event at the square)",
        "entry": {
            "arterial": _volumes(300, 420, 300, 420),
            "collector": _volumes(160, 120, 160, 120),
            "minor": _volumes(14, 14, 14, 14),
        },
        "exit": {
            "arterial": _volumes(300, 420, 300, 420),
            "collector": _volumes(130, 100, 130, 100),
            "minor": _volumes(14, 14, 14, 14),
        },
        "ped_period": 0.8,
        "ped_focus": "tuv-shuudan",
    },
}
SCENARIO_DURATION = 3600
# Sidewalk length of the five-site network that the ped_period values were chosen on.
PED_PERIOD_SIDEWALK_KM = 35.69
MIN_FLOW = 1.0
# Nearer exits are the other carriageway of the entry, which would send most of its traffic into U-turns.
RETURN_TRIP_METRES = 150.0
SKIPPED_ENTRIES = {
    "90833925#0": "leads straight out of the area at its own junction",
}


def fringe_edges(net: Net) -> tuple[list[Edge], list[Edge]]:
    def drivable(edge: Edge) -> bool:
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


def resolve_incident(name: str, spec: dict, sites: list[dict]) -> dict:
    matches = [
        approach["id"]
        for site in sites
        if site["id"] == spec["site"]
        for approach in site["approaches"]
        if (approach["streetEn"], approach["direction"]) == (spec["street"], spec["direction"])
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"Scenario {name}: incident on {spec['street']} {spec['direction']} at {spec['site']} "
            f"matches {len(matches)} Approaches, expected 1"
        )
    return {"site": spec["site"], "approach": matches[0], "start": spec["start"], "end": spec["end"]}


def reachable_exits(net: Net) -> dict[Edge, list[Edge]]:
    entries, exits = fringe_edges(net)
    result: dict[Edge, list[Edge]] = {}
    for entry in sorted(entries, key=lambda e: e.getID()):
        if entry.getID() in SKIPPED_ENTRIES:
            continue
        targets = []
        for exit_ in sorted(exits, key=lambda e: e.getID()):
            if exit_.getFromNode() == entry.getToNode():
                continue
            if math.dist(entry.getFromNode().getCoord(), exit_.getToNode().getCoord()) < RETURN_TRIP_METRES:
                continue
            path, _ = net.getShortestPath(entry, exit_, vClass="passenger")
            if path and len(path) >= 3:
                targets.append(exit_)
        if not targets:
            raise SystemExit(f"entry {entry.getID()} reaches no exit; list it in SKIPPED_ENTRIES with a reason")
        result[entry] = targets
    return result


def split_volume(total: float, weights: dict[str, float]) -> dict[str, float]:
    kept = dict(weights)
    while True:
        scale = total / sum(kept.values())
        smallest = min(kept, key=lambda edge_id: (kept[edge_id], edge_id))
        if len(kept) == 1 or kept[smallest] * scale >= MIN_FLOW:
            return {edge_id: weight * scale for edge_id, weight in kept.items()}
        del kept[smallest]


def write_scenarios(net: Net, sites: list[dict]) -> None:
    config.SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    incidents = {name: resolve_incident(name, spec["incident"], sites) for name, spec in SCENARIOS.items() if "incident" in spec}
    rng = random.Random(7)
    targets = reachable_exits(net)
    sidewalk_km = sum(
        lane.getLength() for e in net.getEdges(withInternal=False) if e.getFunction() == "" for lane in e.getLanes() if _walkway(lane)
    ) / 1000

    meta = {}
    for name, spec in SCENARIOS.items():
        flows = []
        entry_volumes: dict[str, float] = {}
        for entry, exits in targets.items():
            entry_id = entry.getID()
            entry_volumes[entry_id] = spec["entry"][street_class(entry)][heading(entry)]
            weights = {e.getID(): spec["exit"][street_class(e)][heading(e)] for e in exits}
            for exit_id, rate in split_volume(entry_volumes[entry_id], weights).items():
                begin = rng.uniform(0, min(3600 / rate, SCENARIO_DURATION - 1))
                flows.append((begin,
                    f'  <flow id="f_{entry_id}_{exit_id}" type="mix" begin="{begin:.1f}" end="{SCENARIO_DURATION}" '
                    f'from="{entry_id}" to="{exit_id}" vehsPerHour="{rate:.3f}" departLane="best" departSpeed="max"/>\n'
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
        ped_period = spec["ped_period"] * PED_PERIOD_SIDEWALK_KM / sidewalk_km
        _write_pedestrians(net, name, ped_period, spec.get("ped_focus"), sites, rng.randint(1, 10_000))
        meta[name] = {k: spec[k] for k in ("label", "ped_focus") if k in spec}
        if name in incidents:
            meta[name]["incident"] = incidents[name]
        meta[name] |= {"duration": SCENARIO_DURATION, "entryVolumes": entry_volumes}
    (config.SCENARIO_DIR / "scenarios.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))


def _write_pedestrians(net: Net, name: str, period: float, focus: str | None, sites: list[dict], seed: int) -> None:
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
        "-p", f"{period:.3f}",
        "--min-distance", "150",
        "--max-distance", "900",
        "--validate",
    ]
    if focus:
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
    strip_header(out)
    for suffix in (".weights.src.xml", ".weights.dst.xml", ".ped.trips.xml"):
        (config.SCENARIO_DIR / f"{name}{suffix}").unlink(missing_ok=True)


def check_sites(net: Net, sites: list[dict]) -> None:
    _, loaded = load_sites(net)
    problems = validate_sites(loaded) + check_corridors(sites, CORRIDOR_SPECS)
    if problems:
        raise SystemExit("\n".join(problems))


def main() -> None:
    config.DATA.mkdir(exist_ok=True)
    fetch_osm()
    build_network()
    net = sumolib.net.readNet(str(config.NET_FILE), withPrograms=True, withPedestrianConnections=True)
    sites = resolve_sites(net)
    config.SITES_FILE.write_text(json.dumps(sites, indent=2, ensure_ascii=False))
    check_sites(net, sites)
    export_geometry(net, sites)
    write_scenarios(net, sites)
    for site in sites:
        print(
            f"{site['id']:24s} tls={site['tls'][:40]:40s} approaches={len(site['approaches'])} "
            f"crosswalks={len(site['crosswalks'])} neighbours={site['neighbours']}"
        )


if __name__ == "__main__":
    main()
