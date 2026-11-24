from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from functools import cached_property

import sumolib

from . import config
from .phases import MAX_PHASES, PhasePlanner

PLANNED_PHASE_SECONDS = 35.0

GREEN = frozenset("Gg")


@dataclass(frozen=True)
class Link:
    index: int
    from_lane: str
    to_lane: str
    pedestrian: bool
    approach: str | None
    crosswalk: str | None


@dataclass(frozen=True)
class Phase:
    index: int
    state: str
    default_duration: float

    @property
    def green(self) -> frozenset[int]:
        return frozenset(i for i, c in enumerate(self.state) if c in GREEN)


@dataclass
class Approach:
    id: str
    label: str
    lanes: tuple[str, ...]
    exit_lanes: tuple[str, ...]
    links: tuple[int, ...]


@dataclass
class Crosswalk:
    id: str
    label: str
    links: tuple[int, ...]
    walking_areas: tuple[str, ...]


@dataclass
class Site:
    id: str
    name_en: str
    name_mn: str
    kind: str
    tls: str
    neighbours: tuple[str, ...]
    links: tuple[Link, ...]
    phases: tuple[Phase, ...]
    approaches: tuple[Approach, ...]
    crosswalks: tuple[Crosswalk, ...]
    lane_lengths: dict[str, float] = field(default_factory=dict)

    @cached_property
    def links_by_index(self) -> dict[int, tuple[Link, ...]]:
        result: dict[int, tuple[Link, ...]] = {}
        for link in self.links:
            result[link.index] = (*result.get(link.index, ()), link)
        return result

    def green_links(self, phase: Phase) -> list[Link]:
        return [link for index in sorted(phase.green) for link in self.links_by_index.get(index, ())]

    def phases_serving_approach(self, approach: Approach) -> list[Phase]:
        return [p for p in self.phases if p.green & set(approach.links)]

    def phases_serving_crosswalk(self, crosswalk: Crosswalk) -> list[Phase]:
        return [p for p in self.phases if p.green & set(crosswalk.links)]


def _candidate_phases(program_phases: list) -> list[Phase]:
    raw = [
        (p.state, float(p.duration))
        for p in program_phases
        if "y" not in p.state.lower() and set(p.state) & GREEN and float(p.duration) >= 5
    ]
    unique: dict[str, float] = {}
    for state, duration in raw:
        unique.setdefault(state, duration)
    greens = {s: frozenset(i for i, c in enumerate(s) if c in GREEN) for s in unique}
    kept = [s for s in unique if not any(greens[s] < greens[o] for o in unique if o != s)]
    return [Phase(i, s, unique[s]) for i, s in enumerate(kept)]


def _phases(net: sumolib.net.Net, tls_id: str, program, approaches: list[Approach], crosswalks: list[Crosswalk]) -> list[Phase]:
    phases = _candidate_phases(program.getPhases())
    if len(phases) <= MAX_PHASES:
        return phases
    states = PhasePlanner(net, tls_id).plan([set(a.links) for a in approaches], [set(c.links) for c in crosswalks])
    return [Phase(i, state, PLANNED_PHASE_SECONDS) for i, state in enumerate(states)]


def validate_sites(sites: list[Site]) -> list[str]:
    problems: list[str] = []
    tls_sites: dict[str, str] = {}
    for site in sites:
        if site.tls in tls_sites:
            problems.append(f"{site.id}: traffic light {site.tls} is already used by {tls_sites[site.tls]}")
        tls_sites.setdefault(site.tls, site.id)
        if not site.phases:
            problems.append(f"{site.id}: no Phase")
            continue
        if len(site.phases) > MAX_PHASES:
            problems.append(f"{site.id}: {len(site.phases)} Phases, at most {MAX_PHASES} allowed")
        for approach in site.approaches:
            if not site.phases_serving_approach(approach):
                problems.append(f"{site.id}: no Phase serves Approach {approach.label} ({approach.id})")
        for crosswalk in site.crosswalks:
            if not site.phases_serving_crosswalk(crosswalk):
                problems.append(f"{site.id}: no Phase serves {crosswalk.label} ({crosswalk.id})")
        green = frozenset().union(*(phase.green for phase in site.phases))
        for index, links in site.links_by_index.items():
            if index not in green and not all(link.pedestrian for link in links):
                problems.append(f"{site.id}: no Phase makes vehicle signal {index} green ({links[0].from_lane} to {links[0].to_lane})")
    return problems


def network_hash() -> str:
    return hashlib.sha256(config.NET_FILE.read_bytes()).hexdigest()


def _walking_areas(net: sumolib.net.Net, crossing_links: list[Link]) -> set[str]:
    # SUMO signals a crossing from one kerb only, but people wait at both.
    near = {net.getLane(link.from_lane).getEdge().getID() for link in crossing_links}
    far = {conn.getToLane().getEdge().getID() for link in crossing_links for conn in net.getLane(link.to_lane).getOutgoing()}
    return near | far


def load_sites(net: sumolib.net.Net | None = None) -> tuple[sumolib.net.Net, list[Site]]:
    net = net or sumolib.net.readNet(str(config.NET_FILE), withPrograms=True, withPedestrianConnections=True)
    specs = json.loads(config.SITES_FILE.read_text())
    sites: list[Site] = []
    for spec in specs:
        tl = net.getTLS(spec["tls"])
        approach_ids = {a["id"]: a for a in spec["approaches"]}
        crosswalk_ids = {c["id"]: c for c in spec["crosswalks"]}
        links: list[Link] = []
        for from_lane, to_lane, index in tl.getConnections():
            from_edge, to_edge = from_lane.getEdge(), to_lane.getEdge()
            pedestrian = to_edge.getFunction() == "crossing"
            links.append(
                Link(
                    index=index,
                    from_lane=from_lane.getID(),
                    to_lane=to_lane.getID(),
                    pedestrian=pedestrian,
                    approach=from_edge.getID() if from_edge.getID() in approach_ids else None,
                    crosswalk=to_edge.getID() if pedestrian and to_edge.getID() in crosswalk_ids else None,
                )
            )
        links.sort(key=lambda link: link.index)

        approaches = []
        for approach_id, info in approach_ids.items():
            own = [link for link in links if link.approach == approach_id]
            approaches.append(
                Approach(
                    id=approach_id,
                    label=info["label"],
                    lanes=tuple(sorted({link.from_lane for link in own})),
                    exit_lanes=tuple(sorted({link.to_lane for link in own})),
                    links=tuple(link.index for link in own),
                )
            )
        crosswalks = []
        for crosswalk_id, info in crosswalk_ids.items():
            own = [link for link in links if link.crosswalk == crosswalk_id]
            crosswalks.append(
                Crosswalk(
                    id=crosswalk_id,
                    label=info["label"],
                    links=tuple(link.index for link in own),
                    walking_areas=tuple(sorted(_walking_areas(net, own))),
                )
            )

        program = list(tl.getPrograms().values())[0]
        lane_lengths: dict[str, float] = {}
        for link in links:
            for lane_id in (link.from_lane, link.to_lane):
                lane_lengths.setdefault(lane_id, net.getLane(lane_id).getLength())
        sites.append(
            Site(
                id=spec["id"],
                name_en=spec["nameEn"],
                name_mn=spec["nameMn"],
                kind=spec["kind"],
                tls=spec["tls"],
                neighbours=tuple(spec["neighbours"]),
                links=tuple(links),
                phases=tuple(_phases(net, spec["tls"], program, approaches, crosswalks)),
                approaches=tuple(approaches),
                crosswalks=tuple(crosswalks),
                lane_lengths=lane_lengths,
            )
        )
    return net, sites
