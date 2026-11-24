from __future__ import annotations

import asyncio
import json
import logging
import os
import queue
import subprocess
import sys
import threading
import time
from concurrent.futures import Future
from contextlib import asynccontextmanager
from typing import Any, Callable, Literal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import config, explain
from .controllers import CONTROLLERS
from .engine import ScenarioError, Simulation, scenarios
from .model import Site

logger = logging.getLogger(__name__)

FRAME_INTERVAL = 0.1
SPEEDS = (0.5, 1, 2, 5, 10)


class Runner:
    def __init__(self) -> None:
        self.sim = Simulation()
        self.speed = 1.0
        self.paused = False
        self.commands: queue.Queue[tuple[Callable[[], Any], Future]] = queue.Queue()
        self.clients: set[asyncio.Queue[str]] = set()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, name="simulation", daemon=True)
        self.last_frame: dict | None = None

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.thread.start()

    def call(self, fn: Callable[[], Any]) -> Any:
        future: Future = Future()
        self.commands.put((fn, future))
        return future.result(timeout=30)

    def state(self) -> dict:
        caps = self.sim.settings.caps
        return {
            "type": "state",
            "scenario": self.sim.scenario,
            "controller": self.sim.controller.name,
            "speed": self.speed,
            "paused": self.paused,
            "caps": {"pedestrianHard": caps.pedestrian_hard, "vehicleSoft": caps.vehicle_soft, "vehicleHard": caps.vehicle_hard},
            "explainAvailable": explain.available(),
        }

    def _drain_commands(self) -> None:
        while True:
            try:
                fn, future = self.commands.get_nowait()
            except queue.Empty:
                return
            try:
                future.set_result(fn())
            except Exception as error:
                future.set_exception(error)

    def _run(self) -> None:
        self.sim.start()
        next_frame = 0.0
        while not self.stop.is_set():
            self._drain_commands()
            if self.paused:
                if time.monotonic() >= next_frame:
                    next_frame = time.monotonic() + 0.5
                    self._publish(self.sim.frame())
                time.sleep(0.02)
                continue
            started = time.monotonic()
            if self.sim.finished or self.sim.t >= scenarios()[self.sim.scenario]["duration"]:
                try:
                    self.sim.start()
                except ScenarioError:
                    logger.exception("cannot restart the Scenario, simulation paused")
                    self.paused = True
                self._broadcast(json.dumps(self.state()))
                if self.paused:
                    continue
            self.sim.step()
            if time.monotonic() >= next_frame:
                next_frame = time.monotonic() + FRAME_INTERVAL
                self._publish(self.sim.frame())
            budget = config.STEP_LENGTH / self.speed - (time.monotonic() - started)
            if budget > 0:
                time.sleep(budget)
        self.sim.close()

    def _publish(self, frame: dict) -> None:
        self.last_frame = frame
        self._broadcast(json.dumps(frame, separators=(",", ":"), ensure_ascii=False))

    def _broadcast(self, message: str) -> None:
        if self.loop is None:
            return
        for client in list(self.clients):
            self.loop.call_soon_threadsafe(_offer, client, message)


def _offer(client: asyncio.Queue[str], message: str) -> None:
    if client.full():
        try:
            client.get_nowait()
        except asyncio.QueueEmpty:
            pass
    client.put_nowait(message)


runner = Runner()
experiment_job: dict[str, Any] = {"process": None, "startedAt": None, "args": None}


@asynccontextmanager
async def lifespan(_: FastAPI):
    runner.start(asyncio.get_running_loop())
    yield
    runner.stop.set()
    runner.thread.join(timeout=5)


app = FastAPI(title="Ulaanbaatar signal network", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "t": runner.sim.t}


_network_cache: dict | None = None


@app.get("/api/network")
def network() -> dict:
    global _network_cache
    if _network_cache is None:
        payload = json.loads(config.GEO_FILE.read_text())
        described = runner.sim.describe()
        phases = {site["id"]: site["phases"] for site in described["sites"]}
        for site in payload["sites"]:
            site["phases"] = phases[site["id"]]
        payload["scenarios"] = described["scenarios"]
        _network_cache = payload
    return _network_cache | {"controllers": [{"name": c.name, "label": c.label} for c in CONTROLLERS.values()]}


@app.get("/api/state")
def state() -> dict:
    return runner.state()


class Control(BaseModel):
    action: Literal["pause", "resume", "speed", "scenario", "restart", "controller", "caps", "button", "block"]
    value: float | None = None
    name: str | None = None
    site: str | None = None
    target: str | None = None
    caps: dict[str, float] | None = None


@app.post("/api/control")
def control(command: Control) -> dict:
    sim = runner.sim
    match command.action:
        case "pause":
            runner.paused = True
        case "resume":
            runner.paused = False
        case "speed":
            if command.value not in SPEEDS:
                raise HTTPException(400, f"speed must be one of {SPEEDS}")
            runner.speed = float(command.value)
        case "scenario":
            if command.name not in scenarios():
                raise HTTPException(404, "unknown scenario")
            _start(command.name)
        case "restart":
            _start(sim.scenario)
        case "controller":
            if command.name not in CONTROLLERS:
                raise HTTPException(404, "unknown controller")
            runner.call(lambda: sim.set_controller(command.name))
        case "caps":
            values = command.caps or {}
            caps = sim.settings.caps
            ped = values.get("pedestrianHard", caps.pedestrian_hard)
            soft = values.get("vehicleSoft", caps.vehicle_soft)
            hard = values.get("vehicleHard", caps.vehicle_hard)
            if not (45 <= ped <= 300 and 60 <= soft <= hard <= 600):
                raise HTTPException(400, "caps out of range: pedestrian 45-300 s, 60 <= soft <= hard <= 600 s")
            runner.call(lambda: _set_caps(ped, soft, hard))
        case "button":
            _require(command.site, command.target, "crosswalks")
            runner.call(lambda: sim.press_button(command.site, command.target))
        case "block":
            _require(command.site, command.target, "approaches")
            runner.call(lambda: sim.toggle_block(command.site, command.target))
    state = runner.state()
    runner._broadcast(json.dumps(state))
    return state


def _start(scenario: str) -> None:
    try:
        runner.call(lambda: runner.sim.start(scenario=scenario))
    except ScenarioError as error:
        raise HTTPException(500, str(error)) from error


def _set_caps(ped: float, soft: float, hard: float) -> None:
    caps = runner.sim.settings.caps
    caps.pedestrian_hard, caps.vehicle_soft, caps.vehicle_hard = ped, soft, hard
    runner.sim._event("caps", f"Caps changed: pedestrians {ped:.0f} s, vehicles soft {soft:.0f} s / hard {hard:.0f} s")


def _require(site: str | None, target: str | None, kind: str) -> None:
    if not site or site not in runner.sim.site_by_id or not target:
        raise HTTPException(400, "site and target are required")
    if target not in {item.id for item in getattr(runner.sim.site_by_id[site], kind)}:
        raise HTTPException(404, f"unknown {kind[:-1]} at {site}")


DIRECTIONS_MN = {"northbound": "хойш", "southbound": "урагш", "eastbound": "зүүн тийш", "westbound": "баруун тийш"}


def _labels(site: Site, language: str) -> dict[str, str]:
    labels = {item.id: item.label for item in (*site.approaches, *site.crosswalks)}
    if language != "mn":
        return labels
    info = next(s for s in json.loads(config.SITES_FILE.read_text()) if s["id"] == site.id)
    for approach in info["approaches"]:
        direction = approach.get("direction") or approach["label"].rsplit(" ", 1)[-1]
        labels[approach["id"]] = f"{approach['street'] or 'Туслах зам'}, {DIRECTIONS_MN[direction]}"
    for crosswalk in info["crosswalks"]:
        if "streets" in crosswalk:
            labels[crosswalk["id"]] = "Явган гарц: " + (" / ".join(s["mn"] for s in crosswalk["streets"]) or "зам")
    return labels


def _site_name(site: Site, language: str) -> str:
    return site.name_mn if language == "mn" else site.name_en


class ExplainRequest(BaseModel):
    site: str
    language: Literal["en", "mn"] = "en"


@app.post("/api/explain")
def explain_site(request: ExplainRequest) -> dict:
    if not explain.available():
        raise HTTPException(503, "OPENAI_API_KEY is not set for the simulation service")

    def snapshot() -> dict:
        sim = runner.sim
        site = sim.site_by_id[request.site]
        states = {s["id"]: s for s in sim.site_states()}
        current = states[site.id]
        labels = _labels(site, request.language)
        phases = sim.describe()["sites"]
        phase_info = next(p for p in phases if p["id"] == site.id)["phases"]
        return {
            "site": _site_name(site, request.language),
            "controller": sim.controller.label,
            "time": round(sim.t, 1),
            "stage": current["stage"],
            "greenPhase": [labels[x] for x in phase_info[current["phase"]]["approaches"] + phase_info[current["phase"]]["crosswalks"]],
            "greenForSeconds": current["greenFor"],
            "approaches": [{"name": labels[a["id"]], "queue": a["queue"], "waitSeconds": a["wait"], "exitSpillback": a["spillback"], "laneBlocked": a["blocked"]} for a in current["approaches"]],
            "crosswalks": [{"name": labels[c["id"]], "peopleWaiting": c["waiting"], "waitSeconds": c["wait"], "buttonPressed": c["button"]} for c in current["crosswalks"] if c["waiting"] or c["wait"] or c["button"]],
            "controllerScores": current["pressures"],
            "caps": current["caps"],
            "recentEvents": [e["text"] for e in sim.events if e.get("site") == site.id][-5:],
            "neighbours": [
                {"site": _site_name(sim.site_by_id[n], request.language), "queuedVehicles": sum(a["queue"] for a in states[n]["approaches"]), "spillbackApproaches": sum(a["spillback"] for a in states[n]["approaches"])}
                for n in site.neighbours
            ],
        }

    context = runner.call(snapshot)
    try:
        text = explain.explain(context, request.language)
    except Exception as error:
        raise HTTPException(502, f"explanation failed: {type(error).__name__}") from error
    return {"text": text, "t": context["time"]}


@app.get("/api/experiments")
def experiments() -> dict:
    results = []
    if config.EXPERIMENT_DIR.exists():
        for path in sorted(config.EXPERIMENT_DIR.glob("*.json")):
            results.append(json.loads(path.read_text()))
    process: subprocess.Popen | None = experiment_job["process"]
    running = process is not None and process.poll() is None
    return {"running": running, "startedAt": experiment_job["startedAt"], "args": experiment_job["args"], "results": results}


class ExperimentRequest(BaseModel):
    scenarios: list[str] = Field(default_factory=lambda: list(scenarios()))
    # Runs overwrite the stored hour-long result per Scenario, so shorter runs would not be comparable.
    duration: float = Field(default=3600, ge=3600, le=3600)


@app.post("/api/experiments")
def run_experiments(request: ExperimentRequest) -> dict:
    process: subprocess.Popen | None = experiment_job["process"]
    if process is not None and process.poll() is None:
        raise HTTPException(409, "an experiment is already running")
    unknown = set(request.scenarios) - set(scenarios())
    if unknown:
        raise HTTPException(404, f"unknown scenarios: {sorted(unknown)}")
    args = ["--scenarios", ",".join(request.scenarios), "--duration", str(request.duration)]
    experiment_job["process"] = subprocess.Popen(
        [sys.executable, "-m", "corridor_sim.experiment", *args],
        cwd=config.ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    experiment_job["startedAt"] = time.time()
    experiment_job["args"] = request.model_dump()
    return {"running": True}


@app.websocket("/ws")
async def frames(socket: WebSocket) -> None:
    await socket.accept()
    inbox: asyncio.Queue[str] = asyncio.Queue(maxsize=4)
    runner.clients.add(inbox)
    try:
        await socket.send_text(json.dumps(runner.state()))
        if runner.last_frame:
            history = runner.last_frame | {"events": list(runner.sim.events)}
            await socket.send_text(json.dumps(history, ensure_ascii=False))
        while True:
            await socket.send_text(await inbox.get())
    except WebSocketDisconnect:
        pass
    finally:
        runner.clients.discard(inbox)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()
