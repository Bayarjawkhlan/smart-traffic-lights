from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import sumo

SUMO_HOME = Path(sumo.SUMO_HOME)
SUMO_BIN = SUMO_HOME / "bin"
SUMO_TOOLS = SUMO_HOME / "tools"

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OSM_FILE = DATA / "corridor.osm.xml"
NET_FILE = DATA / "corridor.net.xml"
SITES_FILE = DATA / "sites.json"
GEO_FILE = DATA / "network.json"
SCENARIO_DIR = DATA / "scenarios"
EXPERIMENT_DIR = DATA / "experiments"
MODEL_DIR = DATA / "models"

STEP_LENGTH = 0.5
CONTROL_INTERVAL = 1.0


@dataclass(frozen=True)
class SiteSpec:
    id: str
    name_en: str
    name_mn: str
    kind: str
    lat: float
    lon: float
    join_nodes: tuple[str, ...] = ()
    crossing_side: str = ""
    join_radius: float = 0.0


SITE_SPECS: tuple[SiteSpec, ...] = (
    SiteSpec(
        "ikh-delguur",
        "State Department Store",
        "Их дэлгүүр",
        "midblock",
        47.91618,
        106.90638,
        join_nodes=("8995081807", "8995081814", "8995081815"),
        crossing_side="west",
    ),
    SiteSpec("baga-toiruu-west", "Baga Toiruu West", "Бага тойруу (баруун)", "intersection", 47.91666, 106.91193),
    # OSM maps this junction as 8 signalised nodes joined by 12-60 m stubs; vehicles stop at several stop lines in a row unless merged.
    SiteSpec("tuv-shuudan", "Central Post Office", "Төв шуудан", "intersection", 47.91673, 106.91625, join_radius=50.0),
    SiteSpec("ikh-surguuli", "University St / Olympic St", "Их сургуулийн гудамж", "intersection", 47.91723, 106.91958),
    SiteSpec("baga-toiruu-east", "Baga Toiruu East", "Бага тойруу (зүүн)", "intersection", 47.91775, 106.92394),
)


@dataclass
class Caps:
    pedestrian_hard: float = 90.0
    vehicle_soft: float = 120.0
    vehicle_hard: float = 180.0


@dataclass
class Timings:
    min_green: float = 7.0
    pedestrian_walk: float = 7.0
    pedestrian_clearance: float = 6.0
    yellow: float = 3.0
    all_red: float = 2.0


@dataclass
class Thresholds:
    spillback_occupancy: float = 0.75
    congestion_slow: float = 0.7
    congestion_jammed: float = 0.4
    jammed_stop_seconds: float = 30.0


@dataclass
class Settings:
    caps: Caps = field(default_factory=Caps)
    timings: Timings = field(default_factory=Timings)
    thresholds: Thresholds = field(default_factory=Thresholds)
