from __future__ import annotations

from ..model import Site
from ..sensing import SiteView
from .base import Controller

PEDESTRIAN_WEIGHT = 0.15
PEDESTRIAN_AGE_WEIGHT = 1.0 / 60.0
SPILLBACK_PENALTY = 1.0
SWITCH_MARGIN = 0.3
VEHICLE_SPACE = 7.5
# Every switch costs ~11 s of clearance; switching on every small pressure lead starves throughput at rush hour.
MIN_PHASE_SECONDS = 15.0


def _capacity(site: Site, lane: str) -> float:
    return max(site.lane_lengths.get(lane, 50.0) / VEHICLE_SPACE, 2.0)


class MaxPressureController(Controller):
    name = "max-pressure"
    label = "Max-pressure (coordinates with neighbours)"

    def pressures(self, site: Site, view: SiteView) -> list[float]:
        result = []
        for phase in site.phases:
            pressure = 0.0
            seen: set[tuple[str, str]] = set()
            for index in phase.green:
                link = site.links[index]
                if link.pedestrian:
                    if link.crosswalk:
                        waiting = view.crosswalk_waiting.get(link.crosswalk, 0)
                        age = view.crosswalk_wait.get(link.crosswalk, 0.0)
                        if waiting or link.crosswalk in view.buttons:
                            pressure += PEDESTRIAN_WEIGHT * max(waiting, 1) + PEDESTRIAN_AGE_WEIGHT * age
                    continue
                key = (link.from_lane, link.to_lane)
                if key in seen or link.from_lane.startswith(":"):
                    continue
                seen.add(key)
                upstream = view.lane_halting.get(link.from_lane, 0) / _capacity(site, link.from_lane)
                downstream = view.lane_vehicles.get(link.to_lane, 0) / _capacity(site, link.to_lane)
                weight = upstream - downstream
                if link.to_lane in view.spillback_lanes:
                    weight = min(weight, 0.0) - SPILLBACK_PENALTY * (upstream > 0)
                pressure += weight
            result.append(pressure)
        return result

    def propose(self, site: Site, view: SiteView) -> int:
        if view.green_elapsed < MIN_PHASE_SECONDS:
            return view.phase
        pressures = self.pressures(site, view)
        best = max(range(len(pressures)), key=pressures.__getitem__)
        if best != view.phase and pressures[best] > pressures[view.phase] + SWITCH_MARGIN:
            return best
        return view.phase

    def explain(self, site: Site, view: SiteView) -> dict[str, float]:
        return {str(i): round(p, 2) for i, p in enumerate(self.pressures(site, view))}
