from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

from . import config
from .controllers import CONTROLLERS
from .engine import Simulation, scenarios


def run(scenario: str, controllers: list[str], duration: float, seed: int) -> dict:
    sim = Simulation()
    results = {}
    for name in controllers:
        started = time.time()
        sim.start(scenario=scenario, controller=name, seed=seed)
        while sim.t < duration and not sim.finished:
            sim.step()
        results[name] = sim.metrics.summary(sim.t) | {"wallSeconds": round(time.time() - started, 1)}
        print(f"{scenario:18s} {name:14s} {results[name]}", flush=True)
    sim.close()
    report = {
        "scenario": scenario,
        "label": scenarios()[scenario]["label"],
        "duration": duration,
        "seed": seed,
        "finishedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "results": results,
    }
    config.EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    (config.EXPERIMENT_DIR / f"{scenario}.json").write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(prog="corridor_sim.experiment")
    parser.add_argument("--scenarios", default=",".join(scenarios()))
    parser.add_argument("--controllers", default=",".join(CONTROLLERS))
    parser.add_argument("--duration", type=float, default=3600)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    for scenario in args.scenarios.split(","):
        run(scenario, args.controllers.split(","), args.duration, args.seed)


if __name__ == "__main__":
    main()
