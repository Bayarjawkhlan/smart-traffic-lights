from __future__ import annotations

from dataclasses import dataclass, field

from .config import Settings
from .model import Phase, Site
from .sensing import SiteView


@dataclass(frozen=True)
class Override:
    t: float
    site: str
    rule: str
    subject: str
    wait: float
    proposed: int
    applied: int


@dataclass
class Transition:
    target: int
    stages: list[tuple[str, str, float]]
    started: float


@dataclass
class SiteSignals:
    phase: int = 0
    green_started: float = 0.0
    transition: Transition | None = None
    state: str = ""
    stage: str = "green"
    flashing: frozenset[int] = field(default_factory=frozenset)


class SafetyGuard:
    def __init__(self, sites: list[Site], settings: Settings) -> None:
        self.settings = settings
        self.sites = {site.id: site for site in sites}
        self.signals = {site.id: SiteSignals(state=site.phases[0].state) for site in sites}

    def transition_length(self) -> float:
        t = self.settings.timings
        return t.pedestrian_clearance + t.yellow + t.all_red

    def lead(self) -> float:
        t = self.settings.timings
        # Two switches: another urgent item may need serving first, each switch costing min green plus a full transition.
        return 2 * (self.transition_length() + max(t.min_green, t.pedestrian_walk)) + 2

    def min_green(self, phase: Phase, site: Site) -> float:
        t = self.settings.timings
        has_crosswalk = any(site.links[i].pedestrian for i in phase.green)
        return max(t.min_green, t.pedestrian_walk) if has_crosswalk else t.min_green

    def decide(self, site: Site, view: SiteView, proposal: int) -> Override | None:
        signals = self.signals[site.id]
        if signals.transition is not None:
            return None
        current = site.phases[signals.phase]
        if view.t - signals.green_started < self.min_green(current, site):
            return None

        urgent = self._urgent(site, view)
        if urgent:
            rule, subject, wait, candidates = urgent[0]
            if signals.phase in candidates:
                return None
            if proposal in candidates:
                self._begin(site, proposal, view.t)
                return None
            target = max(candidates, key=lambda p: sum(p in c for *_, c in urgent))
            self._begin(site, target, view.t)
            return Override(view.t, site.id, rule, subject, round(wait, 1), proposal, target)

        if proposal != signals.phase:
            self._begin(site, proposal, view.t)
        return None

    def _urgent(self, site: Site, view: SiteView) -> list[tuple[str, str, float, set[int]]]:
        caps = self.settings.caps
        lead = self.lead()
        items: list[tuple[tuple[int, float], str, str, float, set[int]]] = []
        for crosswalk in site.crosswalks:
            wait = view.crosswalk_wait.get(crosswalk.id, 0.0)
            if wait > 0 and wait + lead >= caps.pedestrian_hard:
                items.append(((3, wait - caps.pedestrian_hard), "pedestrian-hard-cap", crosswalk.label, wait,
                              {p.index for p in site.phases_serving_crosswalk(crosswalk)}))
        for approach in site.approaches:
            wait = view.approach_wait.get(approach.id, 0.0)
            if wait <= 0:
                continue
            serving = {p.index for p in site.phases_serving_approach(approach)}
            if wait + lead >= caps.vehicle_hard:
                items.append(((2, wait - caps.vehicle_hard), "vehicle-hard-cap", approach.label, wait, serving))
            elif wait + lead >= caps.vehicle_soft and not view.approach_spillback.get(approach.id, False):
                items.append(((1, wait - caps.vehicle_soft), "vehicle-soft-cap", approach.label, wait, serving))
        items = [item for item in items if item[4]]
        items.sort(key=lambda item: item[0], reverse=True)
        return [(rule, subject, wait, phases) for _, rule, subject, wait, phases in items]

    def _begin(self, site: Site, target: int, t: float) -> None:
        signals = self.signals[site.id]
        timings = self.settings.timings
        old = site.phases[signals.phase]
        new = site.phases[target]
        leaving = old.green - new.green
        leaving_peds = {i for i in leaving if site.links[i].pedestrian}
        leaving_cars = leaving - leaving_peds

        state = list(old.state)
        stages: list[tuple[str, str, float]] = []
        if leaving_peds:
            for i in leaving_peds:
                state[i] = "r"
            stages.append(("clearance", "".join(state), timings.pedestrian_clearance))
        if leaving_cars:
            for i in leaving_cars:
                state[i] = "y"
            stages.append(("yellow", "".join(state), timings.yellow))
        if leaving:
            for i in leaving:
                state[i] = "r"
            stages.append(("all-red", "".join(state), timings.all_red))
        signals.transition = Transition(target, stages, t)
        signals.flashing = frozenset(leaving_peds)
        if not stages:
            self._finish(site, t)
        else:
            signals.stage, signals.state = stages[0][0], stages[0][1]

    def _finish(self, site: Site, t: float) -> None:
        signals = self.signals[site.id]
        assert signals.transition is not None
        signals.phase = signals.transition.target
        signals.transition = None
        signals.green_started = t
        signals.state = site.phases[signals.phase].state
        signals.stage = "green"
        signals.flashing = frozenset()

    def advance(self, site: Site, t: float) -> None:
        signals = self.signals[site.id]
        transition = signals.transition
        if transition is None:
            return
        elapsed = t - transition.started
        for name, state, duration in transition.stages:
            if elapsed < duration:
                signals.stage, signals.state = name, state
                if name != "clearance":
                    signals.flashing = frozenset()
                return
            elapsed -= duration
        self._finish(site, t)
