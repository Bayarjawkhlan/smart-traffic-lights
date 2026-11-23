from __future__ import annotations

import argparse
import json
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


class RLController(Controller):
    name = "rl"
    label = "Reinforcement learning (trained in simulation)"

    def __init__(self, weights: np.ndarray | None = None) -> None:
        if weights is None:
            weights = np.array(json.loads(MODEL_FILE.read_text())["weights"])
        self.weights = weights
        self._pressure = MaxPressureController()
        self._last: dict[str, tuple[float, int]] = {}

    @staticmethod
    def available() -> bool:
        return MODEL_FILE.exists()

    def _scores(self, site: Site, view: SiteView) -> tuple[list[float], list[np.ndarray]]:
        pressures = self._pressure.pressures(site, view)
        feats = [features(site, view, i, pressures[i]) for i in range(len(site.phases))]
        return [float(self.weights @ f) for f in feats], feats

    def propose(self, site: Site, view: SiteView) -> int:
        last = self._last.get(site.id)
        if last and view.t - last[0] < DECISION_INTERVAL:
            return last[1]
        scores, _ = self._scores(site, view)
        action = max(range(len(scores)), key=scores.__getitem__)
        self._last[site.id] = (view.t, action)
        return action

    def explain(self, site: Site, view: SiteView) -> dict[str, float]:
        scores, _ = self._scores(site, view)
        return {str(i): round(s, 2) for i, s in enumerate(scores)}


def objective(summary: dict) -> float:
    return summary["avgVehicleWait"] + 0.5 * summary["avgPedestrianWait"] + 0.5 * summary["teleports"]


def evaluate(job: tuple[list[float], str, int, float]) -> float:
    import libsumo as traci

    from ..engine import Simulation

    weights, scenario, seed, duration = job
    sim = Simulation()
    sim.start(scenario=scenario, seed=seed)
    sim.controller = RLController(weights=np.array(weights))
    backlog = 0
    while sim.t < duration and not sim.finished:
        sim.step()
        if sim.t % 60 == 0:
            backlog += len(traci.simulation.getPendingVehicles())
    score = objective(sim.metrics.summary(sim.t)) + backlog / max(duration / 60, 1)
    sim.close()
    return score


def train(iterations: int, population: int, duration: float, scenarios: list[str], workers: int) -> None:
    from multiprocessing import get_context

    rng = np.random.default_rng(0)
    mean = np.zeros(len(FEATURES))
    mean[FEATURES.index("pressure")] = 1.0
    mean[FEATURES.index("is_current")] = 0.3
    std = np.full(len(FEATURES), 0.6)
    std[FEATURES.index("bias")] = 0.0
    elite_count = max(2, population // 4)
    history = []
    best: tuple[float, np.ndarray] = (float("inf"), mean.copy())
    with get_context("spawn").Pool(workers) as pool:
        for iteration in range(iterations):
            started = time.time()
            candidates = [mean.copy()] + [mean + std * rng.standard_normal(len(FEATURES)) for _ in range(population - 1)]
            picked = [scenarios[(iteration * 2 + k) % len(scenarios)] for k in range(2)]
            seeds = [int(rng.integers(1, 10_000)) for _ in picked]
            jobs = [(list(c), sc, sd, duration) for c in candidates for sc, sd in zip(picked, seeds)]
            raw = pool.map(evaluate, jobs)
            scores = [float(np.mean(raw[i * len(picked):(i + 1) * len(picked)])) for i in range(len(candidates))]
            order = np.argsort(scores)
            elites = np.array([candidates[i] for i in order[:elite_count]])
            mean = elites.mean(axis=0)
            std = np.maximum(elites.std(axis=0), 0.05)
            std[FEATURES.index("bias")] = 0.0
            if scores[order[0]] < best[0]:
                best = (scores[order[0]], candidates[order[0]].copy())
            history.append({"iteration": iteration, "scenarios": picked, "best": round(scores[order[0]], 1), "meanScore": round(float(np.mean(scores)), 1), "incumbent": round(scores[0], 1)})
            print(f"iter {iteration:2d} {picked} best={scores[order[0]]:6.1f} mean={np.mean(scores):6.1f} incumbent={scores[0]:6.1f} ({time.time() - started:.0f}s)", flush=True)
    config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_FILE.write_text(
        json.dumps({"method": "cross-entropy policy search", "features": FEATURES, "weights": [round(float(w), 4) for w in mean], "history": history}, indent=2)
    )
    print("weights", dict(zip(FEATURES, np.round(mean, 3))))


def main() -> None:
    parser = argparse.ArgumentParser(prog="corridor_sim.controllers.rl")
    parser.add_argument("command", choices=["train"])
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--population", type=int, default=12)
    parser.add_argument("--duration", type=float, default=1200)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--scenarios", default="morning-rush,midday,evening-rush,incident,pedestrian-surge")
    args = parser.parse_args()
    train(args.iterations, args.population, args.duration, args.scenarios.split(","), args.workers)


if __name__ == "__main__":
    main()
