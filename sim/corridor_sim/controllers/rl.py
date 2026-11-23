from __future__ import annotations

import argparse
import json
import random
import time

import numpy as np

from .. import config
from ..model import Site
from ..sensing import SiteView
from .base import Controller
from .max_pressure import MaxPressureController

MODEL_FILE = config.MODEL_DIR / "rl-linear.json"
DECISION_INTERVAL = 5.0
FEATURES = (
    "pressure",
    "upstream_queue",
    "spillback_exits",
    "pedestrians_waiting",
    "oldest_pedestrian",
    "oldest_vehicle",
    "is_current",
    "current_age",
    "bias",
)


def features(site: Site, view: SiteView, phase_index: int, pressure: float) -> np.ndarray:
    phase = site.phases[phase_index]
    upstream = 0
    spill = 0
    lanes_seen: set[str] = set()
    for index in phase.green:
        link = site.links[index]
        if link.pedestrian or link.from_lane in lanes_seen:
            continue
        lanes_seen.add(link.from_lane)
        upstream += view.lane_halting.get(link.from_lane, 0)
        spill += link.to_lane in view.spillback_lanes
    peds = 0
    oldest_ped = 0.0
    for crosswalk in site.crosswalks:
        if phase.green & set(crosswalk.links):
            peds += view.crosswalk_waiting.get(crosswalk.id, 0)
            oldest_ped = max(oldest_ped, view.crosswalk_wait.get(crosswalk.id, 0.0))
    oldest_vehicle = max(
        (view.approach_wait.get(a.id, 0.0) for a in site.approaches if phase.green & set(a.links)), default=0.0
    )
    current = 1.0 if phase_index == view.phase else 0.0
    return np.array(
        [
            np.clip(pressure / 20, -3, 3),
            min(upstream / 20, 3),
            min(spill / 4, 2),
            min(peds / 10, 3),
            min(oldest_ped / 90, 1.5),
            min(oldest_vehicle / 120, 1.5),
            current,
            current * min(view.green_elapsed / 60, 2),
            1.0,
        ]
    )


def reward(site: Site, view: SiteView, neighbour_views: list[SiteView]) -> float:
    own = sum(view.approach_queue.values()) + 1.5 * sum(view.crosswalk_waiting.values())
    near = sum(sum(v.approach_queue.values()) for v in neighbour_views)
    spill = sum(view.approach_spillback.values())
    return -(own + 0.5 * near) / 20 - 0.5 * spill


class RLController(Controller):
    name = "rl"
    label = "Reinforcement learning (trained in simulation)"

    def __init__(self, weights: np.ndarray | None = None, epsilon: float = 0.0, alpha: float = 0.0, gamma: float = 0.9) -> None:
        if weights is None:
            weights = np.array(json.loads(MODEL_FILE.read_text())["weights"])
        self.weights = weights
        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        self.views: dict[str, SiteView] = {}
        self._pressure = MaxPressureController()
        self._last: dict[str, tuple[float, int, np.ndarray]] = {}

    @staticmethod
    def available() -> bool:
        return MODEL_FILE.exists()

    def attach(self, views: dict[str, SiteView]) -> None:
        self.views = views

    def _scores(self, site: Site, view: SiteView) -> tuple[list[float], list[np.ndarray]]:
        pressures = self._pressure.pressures(site, view)
        feats = [features(site, view, i, pressures[i]) for i in range(len(site.phases))]
        return [float(self.weights @ f) for f in feats], feats

    def propose(self, site: Site, view: SiteView) -> int:
        last = self._last.get(site.id)
        if last and view.t - last[0] < DECISION_INTERVAL:
            return last[1]
        scores, feats = self._scores(site, view)
        if self.alpha > 0 and last is not None:
            neighbours = [self.views[n] for n in site.neighbours if n in self.views]
            target = reward(site, view, neighbours) + self.gamma * max(scores)
            _, action, f = last
            error = target - float(self.weights @ f)
            self.weights += self.alpha * np.clip(error, -5, 5) * f
        if self.epsilon and random.random() < self.epsilon:
            action = random.randrange(len(site.phases))
        else:
            action = max(range(len(scores)), key=scores.__getitem__)
        self._last[site.id] = (view.t, action, feats[action])
        return action

    def explain(self, site: Site, view: SiteView) -> dict[str, float]:
        scores, _ = self._scores(site, view)
        return {str(i): round(s, 2) for i, s in enumerate(scores)}


def train(episodes: int, duration: float, scenarios: list[str]) -> None:
    from ..engine import Simulation

    rng = np.random.default_rng(0)
    weights = np.zeros(len(FEATURES))
    weights[0] = 1.0
    weights[6] = 0.3
    sim = Simulation()
    history = []
    for episode in range(episodes):
        scenario = scenarios[episode % len(scenarios)]
        epsilon = max(0.02, 0.3 * (1 - episode / max(episodes - 1, 1)))
        controller = RLController(weights=weights, epsilon=epsilon, alpha=0.01)
        sim.start(scenario=scenario, seed=int(rng.integers(1, 10_000)))
        sim.controller = controller
        controller.attach(sim.views)
        started = time.time()
        while sim.t < duration and not sim.finished:
            sim.step()
        summary = sim.metrics.summary(sim.t)
        weights = controller.weights
        history.append({"episode": episode, "scenario": scenario, **{k: summary[k] for k in ("avgVehicleWait", "maxPedestrianWait", "vehiclesPerHour")}})
        print(
            f"episode {episode:3d} {scenario:16s} eps={epsilon:.2f} wait={summary['avgVehicleWait']:6.1f}s "
            f"ped_max={summary['maxPedestrianWait']:5.0f}s veh/h={summary['vehiclesPerHour']:5d} ({time.time() - started:.0f}s)",
            flush=True,
        )
    sim.close()
    config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_FILE.write_text(
        json.dumps({"features": FEATURES, "weights": [round(float(w), 5) for w in weights], "history": history}, indent=2)
    )
    print("weights", dict(zip(FEATURES, np.round(weights, 3))))


def main() -> None:
    parser = argparse.ArgumentParser(prog="corridor_sim.controllers.rl")
    parser.add_argument("command", choices=["train"])
    parser.add_argument("--episodes", type=int, default=24)
    parser.add_argument("--duration", type=float, default=1800)
    parser.add_argument("--scenarios", default="morning-rush,midday,evening-rush,incident,pedestrian-surge")
    args = parser.parse_args()
    train(args.episodes, args.duration, args.scenarios.split(","))


if __name__ == "__main__":
    main()
