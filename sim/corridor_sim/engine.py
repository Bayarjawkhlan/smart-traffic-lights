from __future__ import annotations

import json
from collections import Counter, deque
from dataclasses import asdict, dataclass, field

import libsumo as traci
import numpy as np
import sumolib

from . import config
from .config import Settings
from .controllers import CONTROLLERS, make, register_rl
from .controllers.base import Controller
from .guard import Override, SafetyGuard
from .model import Site, load_sites
from .sensing import SiteView, edge_congestion, measure_lanes, waiting_persons

register_rl()

BLOCKED_CLASSES = ["passenger", "bus", "truck", "delivery", "taxi", "motorcycle", "emergency"]


def scenarios() -> dict[str, dict]:
    return json.loads((config.SCENARIO_DIR / "scenarios.json").read_text())


@dataclass
class Metrics:
    vehicle_wait_seconds: float = 0.0
    departed: int = 0
    arrived: int = 0
    teleports: int = 0
    pedestrian_waits: list[float] = field(default_factory=list)
    pedestrian_max_wait: float = 0.0
    spillback_seconds: float = 0.0
    overrides: Counter = field(default_factory=Counter)

    def summary(self, t: float) -> dict:
        hours = max(t, 1.0) / 3600
        peds = self.pedestrian_waits
        return {
            "t": round(t, 1),
            "avgVehicleWait": round(self.vehicle_wait_seconds / max(self.departed, 1), 1),
            "vehiclesPerHour": round(self.arrived / hours),
            "avgPedestrianWait": round(sum(peds) / len(peds), 1) if peds else 0.0,
            "maxPedestrianWait": round(self.pedestrian_max_wait, 1),
            "spillbackMinutes": round(self.spillback_seconds / 60, 1),
            "overrides": dict(self.overrides),
            "overrideCount": sum(self.overrides.values()),
            "teleports": self.teleports,
            "departed": self.departed,
            "arrived": self.arrived,
        }


class Simulation:
    def __init__(self, net: sumolib.net.Net | None = None, sites: list[Site] | None = None) -> None:
        if net is None or sites is None:
            net, sites = load_sites()
        self.net = net
        self.sites = sites
        self.site_by_id = {site.id: site for site in sites}
        self.settings = Settings()
        self.guard = SafetyGuard(sites, self.settings)
        self.controller: Controller = make("max-pressure")
        self.scenario = "morning-rush"
        self.running = False
        self.t = 0.0
        self.metrics = Metrics()
        self.events: deque[dict] = deque(maxlen=200)
        self.pending_events: list[dict] = []
        self.approach_since: dict[tuple[str, str], float | None] = {}
        self.crosswalk_since: dict[tuple[str, str], float | None] = {}
        self.buttons: dict[str, set[str]] = {site.id: set() for site in sites}
        self.waiting_people: dict[str, float] = {}
        self.blocked_lanes: dict[str, list[str]] = {}
        self.views: dict[str, SiteView] = {}
        self.congestion: dict[str, int] = {}
        self._road_edges = [
            (edge.getID(), edge.getSpeed())
            for edge in net.getEdges(withInternal=False)
            if edge.getFunction() == "" and edge.allows("passenger")
        ]
        self._affine = self._fit_affine()
        self._next_control = 0.0
        self._next_congestion = 0.0
        self._seen_waiting: set[str] = set()
        self._scenario_meta: dict = {}
        self._short_ids: dict[str, int] = {}

    def _fit_affine(self) -> np.ndarray:
        xmin, ymin, xmax, ymax = self.net.getBoundary()
        points = [(xmin, ymin), (xmax, ymin), (xmin, ymax), (xmax, ymax), ((xmin + xmax) / 2, (ymin + ymax) / 2)]
        src = np.array([[x, y, 1.0] for x, y in points])
        dst = np.array([self.net.convertXY2LonLat(x, y) for x, y in points])
        coeffs, *_ = np.linalg.lstsq(src, dst, rcond=None)
        return coeffs

    def to_lonlat(self, xy: np.ndarray) -> np.ndarray:
        if len(xy) == 0:
            return xy
        return np.hstack([xy, np.ones((len(xy), 1))]) @ self._affine

    def start(self, scenario: str | None = None, controller: str | None = None, seed: int = 42) -> None:
        if self.running:
            traci.close()
        if scenario:
            self.scenario = scenario
        if controller:
            self.controller = make(controller)
        self.controller.attach(self.views)
        routes = f"{config.SCENARIO_DIR / (self.scenario + '.rou.xml')},{config.SCENARIO_DIR / (self.scenario + '.ped.rou.xml')}"
        traci.start(
            [
                str(config.SUMO_BIN / "sumo"),
                "-n", str(config.NET_FILE),
                "-r", routes,
                "--step-length", str(config.STEP_LENGTH),
                "--time-to-teleport", "300",
                "--ignore-route-errors",
                "--no-step-log",
                "--no-warnings",
                "--seed", str(seed),
                "--end", str(scenarios()[self.scenario]["duration"]),
            ]
        )
        self.running = True
        self._scenario_meta = scenarios()[self.scenario]
        self._seen_waiting = set()
        self._short_ids = {}
        self.t = 0.0
        self.metrics = Metrics()
        self.events.clear()
        self.pending_events.clear()
        self.approach_since.clear()
        self.crosswalk_since.clear()
        self.waiting_people.clear()
        self.blocked_lanes.clear()
        self.views.clear()
        self.congestion.clear()
        for buttons in self.buttons.values():
            buttons.clear()
        self.guard = SafetyGuard(self.sites, self.settings)
        self._next_control = 0.0
        self._next_congestion = 0.0
        for site in self.sites:
            traci.trafficlight.setRedYellowGreenState(site.tls, self.guard.signals[site.id].state)

    def close(self) -> None:
        if self.running:
            traci.close()
            self.running = False

    @property
    def finished(self) -> bool:
        return self.running and traci.simulation.getMinExpectedNumber() == 0 and self.t > 10

    def set_controller(self, name: str) -> None:
        self.controller = make(name)
        self.controller.attach(self.views)
        self._event("controller", f"Controller switched to {self.controller.label}")

    def press_button(self, site_id: str, crosswalk_id: str) -> None:
        site = self.site_by_id[site_id]
        crosswalk = next(c for c in site.crosswalks if c.id == crosswalk_id)
        self.buttons[site_id].add(crosswalk_id)
        self._event("button", f"Pedestrian button pressed: {crosswalk.label} at {site.name_en}", site=site_id)

    def toggle_block(self, site_id: str, approach_id: str) -> bool:
        site = self.site_by_id[site_id]
        approach = next(a for a in site.approaches if a.id == approach_id)
        if approach_id in self.blocked_lanes:
            for lane in self.blocked_lanes.pop(approach_id):
                traci.lane.setAllowed(lane, [])
                traci.lane.setDisallowed(lane, ["pedestrian"])
            self._event("incident", f"Lane reopened: {approach.label} at {site.name_en}", site=site_id)
            return False
        lanes = list(approach.lanes)
        blocked = lanes[len(lanes) // 2 : len(lanes) // 2 + max(1, len(lanes) // 2)]
        for lane in blocked:
            traci.lane.setDisallowed(lane, BLOCKED_CLASSES + ["pedestrian"])
        self.blocked_lanes[approach_id] = blocked
        self._event("incident", f"{len(blocked)} lane(s) blocked: {approach.label} at {site.name_en}", site=site_id)
        return True

    def _event(self, kind: str, text: str, **extra: object) -> None:
        event = {"t": round(self.t, 1), "kind": kind, "text": text, **extra}
        self.events.append(event)
        self.pending_events.append(event)

    def step(self) -> None:
        traci.simulationStep()
        self.t = traci.simulation.getTime()
        dt = config.STEP_LENGTH
        self.metrics.departed += traci.simulation.getDepartedNumber()
        self.metrics.arrived += traci.simulation.getArrivedNumber()
        self.metrics.teleports += traci.simulation.getStartingTeleportNumber()
        self.metrics.vehicle_wait_seconds += dt * sum(
            traci.edge.getLastStepHaltingNumber(edge_id) for edge_id, _ in self._road_edges
        )
        self._scripted_incident()

        for site in self.sites:
            self.guard.advance(site, self.t)
        if self.t + 1e-6 >= self._next_control:
            self._next_control = self.t + config.CONTROL_INTERVAL
            self._control()
        for site in self.sites:
            state = self.guard.signals[site.id].state
            if traci.trafficlight.getRedYellowGreenState(site.tls) != state:
                traci.trafficlight.setRedYellowGreenState(site.tls, state)
        if self.t + 1e-6 >= self._next_congestion:
            self._next_congestion = self.t + 2.0
            self.congestion = edge_congestion(self._road_edges, self.settings.thresholds)

    def _scripted_incident(self) -> None:
        incident = self._scenario_meta.get("incident")
        if not incident or self.t % 5 != 0:
            return
        site = self.site_by_id[incident["site"]]
        approach = next(a for a in site.approaches if a.label == incident["approach"])
        blocked = approach.id in self.blocked_lanes
        if incident["start"] <= self.t < incident["end"] and not blocked:
            self.toggle_block(site.id, approach.id)
        elif self.t >= incident["end"] and blocked:
            self.toggle_block(site.id, approach.id)

    def _control(self) -> None:
        thresholds = self.settings.thresholds
        spill_total = 0
        for site in self.sites:
            vehicles, halting, occupancy, spill = measure_lanes(site, thresholds)
            waiting = waiting_persons(site)
            signals = self.guard.signals[site.id]
            green_now = site.phases[signals.phase].green if signals.stage == "green" else frozenset()

            approach_queue: dict[str, int] = {}
            approach_wait: dict[str, float] = {}
            approach_spill: dict[str, bool] = {}
            for approach in site.approaches:
                queue = sum(halting.get(lane, 0) for lane in approach.lanes)
                approach_queue[approach.id] = queue
                key = (site.id, approach.id)
                served = bool(green_now & set(approach.links))
                if served or queue == 0:
                    self.approach_since[key] = None
                elif self.approach_since.get(key) is None:
                    self.approach_since[key] = self.t
                since = self.approach_since.get(key)
                approach_wait[approach.id] = self.t - since if since is not None else 0.0
                exits = [lane for lane in approach.exit_lanes if not lane.startswith(":")]
                approach_spill[approach.id] = bool(exits) and sum(lane in spill for lane in exits) * 2 > len(exits)
                spill_total += sum(lane in spill for lane in exits)

            crosswalk_waiting: dict[str, int] = {}
            crosswalk_wait: dict[str, float] = {}
            for crosswalk in site.crosswalks:
                people = waiting[crosswalk.id]
                crosswalk_waiting[crosswalk.id] = len(people)
                key = (site.id, crosswalk.id)
                served = bool(green_now & set(crosswalk.links))
                demand = bool(people) or crosswalk.id in self.buttons[site.id]
                if served:
                    self.buttons[site.id].discard(crosswalk.id)
                if served or not demand:
                    self.crosswalk_since[key] = None
                elif self.crosswalk_since.get(key) is None:
                    self.crosswalk_since[key] = self.t
                since = self.crosswalk_since.get(key)
                crosswalk_wait[crosswalk.id] = self.t - since if since is not None else 0.0
                if not served:
                    self._track_people(people)

            view = SiteView(
                t=self.t,
                phase=signals.phase,
                in_transition=signals.transition is not None,
                green_elapsed=self.t - signals.green_started,
                lane_vehicles=vehicles,
                lane_halting=halting,
                lane_occupancy=occupancy,
                spillback_lanes=spill,
                crosswalk_waiting=crosswalk_waiting,
                crosswalk_wait=crosswalk_wait,
                approach_queue=approach_queue,
                approach_wait=approach_wait,
                approach_spillback=approach_spill,
                buttons=frozenset(self.buttons[site.id]),
            )
            self.views[site.id] = view
            proposal = self.controller.propose(site, view) if signals.transition is None else signals.phase
            override = self.guard.decide(site, view, proposal)
            if override:
                self._record_override(site, override)
        self.metrics.spillback_seconds += spill_total * config.CONTROL_INTERVAL
        self._finish_people()

    def _track_people(self, people: list[str]) -> None:
        for person in people:
            self.waiting_people.setdefault(person, self.t)
            self._seen_waiting.add(person)

    def _finish_people(self) -> None:
        for person, since in list(self.waiting_people.items()):
            if person not in self._seen_waiting:
                wait = self.t - since
                self.metrics.pedestrian_waits.append(wait)
                self.metrics.pedestrian_max_wait = max(self.metrics.pedestrian_max_wait, wait)
                del self.waiting_people[person]
        for since in self.waiting_people.values():
            self.metrics.pedestrian_max_wait = max(self.metrics.pedestrian_max_wait, self.t - since)
        self._seen_waiting = set()

    def _record_override(self, site: Site, override: Override) -> None:
        self.metrics.overrides[override.rule] += 1
        rule_text = {
            "pedestrian-hard-cap": "pedestrian hard cap",
            "vehicle-hard-cap": "vehicle hard cap",
            "vehicle-soft-cap": "vehicle soft cap",
        }[override.rule]
        self._event(
            "override",
            f"Forced: {rule_text} at {site.name_en} — {override.subject} waited {override.wait:.0f} s",
            site=site.id,
            override=asdict(override),
        )

    def _short_id(self, sumo_id: str) -> int:
        short = self._short_ids.get(sumo_id)
        if short is None:
            short = self._short_ids[sumo_id] = len(self._short_ids) + 1
        return short

    def vehicles(self) -> list[list[float]]:
        ids = traci.vehicle.getIDList()
        if not ids:
            return []
        lonlat = self.to_lonlat(np.array([traci.vehicle.getPosition(v) for v in ids]))
        result = []
        for (lon, lat), vid in zip(lonlat, ids):
            kind = traci.vehicle.getVehicleClass(vid)
            result.append([
                self._short_id(vid),
                round(lon, 6),
                round(lat, 6),
                round(traci.vehicle.getAngle(vid)),
                1 if kind == "bus" else 2 if kind == "truck" else 0,
                1 if traci.vehicle.getSpeed(vid) < 0.3 else 0,
            ])
        return result

    def persons(self) -> list[list[float]]:
        ids = traci.person.getIDList()
        if not ids:
            return []
        lonlat = self.to_lonlat(np.array([traci.person.getPosition(p) for p in ids]))
        return [[self._short_id(pid), round(lon, 6), round(lat, 6)] for (lon, lat), pid in zip(lonlat, ids)]

    def site_states(self) -> list[dict]:
        caps = self.settings.caps
        result = []
        for site in self.sites:
            signals = self.guard.signals[site.id]
            view = self.views.get(site.id)
            transition = signals.transition
            result.append(
                {
                    "id": site.id,
                    "state": signals.state,
                    "phase": signals.phase,
                    "target": transition.target if transition else None,
                    "stage": signals.stage,
                    "flashing": sorted(signals.flashing),
                    "greenFor": round(self.t - signals.green_started, 1) if transition is None else 0,
                    "approaches": [
                        {
                            "id": a.id,
                            "queue": view.approach_queue.get(a.id, 0) if view else 0,
                            "wait": round(view.approach_wait.get(a.id, 0.0), 1) if view else 0,
                            "spillback": view.approach_spillback.get(a.id, False) if view else False,
                            "blocked": a.id in self.blocked_lanes,
                        }
                        for a in site.approaches
                    ],
                    "crosswalks": [
                        {
                            "id": c.id,
                            "waiting": view.crosswalk_waiting.get(c.id, 0) if view else 0,
                            "wait": round(view.crosswalk_wait.get(c.id, 0.0), 1) if view else 0,
                            "button": c.id in self.buttons[site.id],
                        }
                        for c in site.crosswalks
                    ],
                    "pressures": self.controller.explain(site, view) if view else {},
                    "caps": {"pedestrianHard": caps.pedestrian_hard, "vehicleSoft": caps.vehicle_soft, "vehicleHard": caps.vehicle_hard},
                }
            )
        return result

    def frame(self, include_positions: bool = True) -> dict:
        events, self.pending_events = self.pending_events, []
        frame = {
            "type": "frame",
            "t": round(self.t, 1),
            "scenario": self.scenario,
            "controller": self.controller.name,
            "sites": self.site_states(),
            "congestion": self.congestion,
            "metrics": self.metrics.summary(self.t),
            "events": events,
        }
        if include_positions:
            frame["vehicles"] = self.vehicles()
            frame["persons"] = self.persons()
        return frame

    def describe(self) -> dict:
        return {
            "sites": [
                {
                    "id": site.id,
                    "phases": [
                        {
                            "index": p.index,
                            "state": p.state,
                            "approaches": [a.id for a in site.approaches if p.green & set(a.links)],
                            "crosswalks": [c.id for c in site.crosswalks if p.green & set(c.links)],
                        }
                        for p in site.phases
                    ],
                }
                for site in self.sites
            ],
            "controllers": [{"name": c.name, "label": c.label} for c in CONTROLLERS.values()],
            "scenarios": scenarios(),
        }
