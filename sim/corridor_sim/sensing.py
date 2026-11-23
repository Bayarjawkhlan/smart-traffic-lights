from __future__ import annotations

from dataclasses import dataclass, field

import libsumo as traci

from .config import Thresholds
from .model import Site


@dataclass
class SiteView:
    t: float
    phase: int
    in_transition: bool
    green_elapsed: float
    lane_vehicles: dict[str, int]
    lane_halting: dict[str, int]
    lane_occupancy: dict[str, float]
    spillback_lanes: frozenset[str]
    crosswalk_waiting: dict[str, int]
    crosswalk_wait: dict[str, float]
    approach_queue: dict[str, int]
    approach_wait: dict[str, float]
    approach_spillback: dict[str, bool]
    buttons: frozenset[str] = field(default_factory=frozenset)


def measure_lanes(site: Site, thresholds: Thresholds) -> tuple[dict[str, int], dict[str, int], dict[str, float], frozenset[str]]:
    vehicles: dict[str, int] = {}
    halting: dict[str, int] = {}
    occupancy: dict[str, float] = {}
    spill: set[str] = set()
    for lane in site.lane_lengths:
        if lane.startswith(":"):
            continue
        vehicles[lane] = traci.lane.getLastStepVehicleNumber(lane)
        halting[lane] = traci.lane.getLastStepHaltingNumber(lane)
        occ = traci.lane.getLastStepOccupancy(lane)
        occupancy[lane] = occ
        if occ >= thresholds.spillback_occupancy or (halting[lane] * 7.0 >= thresholds.spillback_occupancy * site.lane_lengths[lane]):
            spill.add(lane)
    return vehicles, halting, occupancy, frozenset(spill)


def waiting_persons(site: Site) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for crosswalk in site.crosswalks:
        waiting: list[str] = []
        for walking_area in crosswalk.walking_areas:
            for person in traci.edge.getLastStepPersonIDs(walking_area):
                if traci.person.getSpeed(person) < 0.2 and traci.person.getNextEdge(person) == crosswalk.id:
                    waiting.append(person)
        result[crosswalk.id] = waiting
    return result


def edge_congestion(edges: list[tuple[str, float]], thresholds: Thresholds) -> dict[str, int]:
    levels: dict[str, int] = {}
    for edge_id, limit in edges:
        count = traci.edge.getLastStepVehicleNumber(edge_id)
        if count == 0:
            levels[edge_id] = 0
            continue
        ratio = traci.edge.getLastStepMeanSpeed(edge_id) / limit
        halting = traci.edge.getLastStepHaltingNumber(edge_id)
        long_stop = halting > 0 and traci.edge.getWaitingTime(edge_id) / halting >= thresholds.jammed_stop_seconds
        if ratio < thresholds.congestion_jammed or long_stop:
            levels[edge_id] = 2
        elif ratio < thresholds.congestion_slow:
            levels[edge_id] = 1
        else:
            levels[edge_id] = 0
    return levels
