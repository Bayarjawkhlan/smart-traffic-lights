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
    reset_connections: bool = False
    crossing_side: str = ""


@dataclass(frozen=True)
class CorridorSpec:
    id: str
    name_en: str
    name_mn: str
    axis: str
    sites: tuple[str, ...]


# join_nodes are OSM nodes netconvert leaves apart: the stubs between them are shorter than a car, so queues on them go unseen.
# reset_connections discards OSM turn lanes; use it only where joining left whole lanes that can do nothing but a U-turn.
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
    SiteSpec(
        "tuv-shuudan",
        "Central Post Office",
        "Төв шуудан",
        "intersection",
        47.91673,
        106.91625,
        join_nodes=(
            "1270396026",
            "2513512815",
            "1270395917",
            "1241686844",
            "8420520244",
            "1245746484",
            "8420678184",
            "8420678186",
            "8420678188",
        ),
        reset_connections=True,
    ),
    SiteSpec(
        "ikh-surguuli",
        "University St / Olympic St",
        "Их сургуулийн гудамж",
        "intersection",
        47.91723,
        106.91958,
        join_nodes=("1054352912", "2499240111", "14002450297", "14002450296"),
    ),
    SiteSpec("baga-toiruu-east", "Baga Toiruu East", "Бага тойруу (зүүн)", "intersection", 47.91775, 106.92394),
    SiteSpec(
        "juulchny-baga-toiruu",
        "Juulchny St / Baga Toiruu West",
        "Жуулчны гудамж / Бага тойруу (баруун)",
        "intersection",
        47.92003,
        106.91138,
    ),
    SiteSpec(
        "amar-ikh-surguuli",
        "Amar St / University St",
        "Амарын гудамж / Их сургуулийн гудамж",
        "intersection",
        47.91993,
        106.91888,
    ),
    SiteSpec(
        "sambuu-baga-toiruu-west",
        "Sambuu St / Baga Toiruu West",
        "Самбуугийн гудамж / Бага тойруу (баруун)",
        "intersection",
        47.92213,
        106.91095,
    ),
    SiteSpec(
        "sambuu-sukhbaatar",
        "Sambuu St / Sükhbaatar St",
        "Самбуугийн гудамж / Сүхбаатарын гудамж",
        "intersection",
        47.92208,
        106.91555,
        join_nodes=("2496907426", "2498065898", "2498065895", "9065258158"),
        reset_connections=True,
    ),
    SiteSpec(
        "sambuu-ikh-surguuli",
        "Sambuu St / University St",
        "Самбуугийн гудамж / Их сургуулийн гудамж",
        "intersection",
        47.92222,
        106.91844,
        join_nodes=("3913061711", "9065258185", "8962539123"),
        reset_connections=True,
    ),
    SiteSpec(
        "sambuu-baga-toiruu-east",
        "Sambuu St / Baga Toiruu East",
        "Самбуугийн гудамж / Бага тойруу (зүүн)",
        "intersection",
        47.92257,
        106.92291,
    ),
    SiteSpec(
        "juulchny-baruun-selbe",
        "Juulchny St / Baruun Selbe St",
        "Жуулчны гудамж / Баруун Сэлбийн гудамж",
        "intersection",
        47.91971,
        106.90641,
        join_nodes=("2869681150", "3973275898"),
        reset_connections=True,
    ),
    SiteSpec(
        "chinggis-genden",
        "Chinggis Ave / Genden St",
        "Чингисийн өргөн чөлөө / Гэндэнгийн гудамж",
        "intersection",
        47.91319,
        106.91516,
    ),
    SiteSpec(
        "olympic-genden",
        "Olympic St / Genden St",
        "Олимпийн гудамж / Гэндэнгийн гудамж",
        "intersection",
        47.91408,
        106.92183,
    ),
    SiteSpec(
        "seoul-tserendorj",
        "Seoul St / Tserendorj St",
        "Сөүлийн гудамж / Цэрэндоржийн гудамж",
        "intersection",
        47.91375,
        106.90689,
    ),
)

CORRIDOR_SPECS: tuple[CorridorSpec, ...] = (
    CorridorSpec(
        "peace",
        "Peace Avenue",
        "Энх тайваны өргөн чөлөө",
        "ew",
        ("ikh-delguur", "baga-toiruu-west", "tuv-shuudan", "ikh-surguuli", "baga-toiruu-east"),
    ),
    CorridorSpec(
        "sambuu",
        "Sambuu St",
        "Самбуугийн гудамж",
        "ew",
        ("sambuu-baga-toiruu-west", "sambuu-sukhbaatar", "sambuu-ikh-surguuli", "sambuu-baga-toiruu-east"),
    ),
    CorridorSpec("juulchny", "Juulchny St", "Жуулчны гудамж", "ew", ("juulchny-baruun-selbe", "juulchny-baga-toiruu")),
    CorridorSpec("genden", "Genden St", "Гэндэнгийн гудамж", "ew", ("chinggis-genden", "olympic-genden")),
    CorridorSpec(
        "baga-toiruu-w",
        "Baga Toiruu West",
        "Бага тойруу (баруун)",
        "ns",
        ("sambuu-baga-toiruu-west", "juulchny-baga-toiruu", "baga-toiruu-west"),
    ),
    CorridorSpec(
        "sukhbaatar-chinggis",
        "Sükhbaatar St – Chinggis Ave",
        "Сүхбаатарын гудамж – Чингисийн өргөн чөлөө",
        "ns",
        ("sambuu-sukhbaatar", "tuv-shuudan", "chinggis-genden"),
    ),
    CorridorSpec(
        "university-olympic",
        "University St – Olympic St",
        "Их сургуулийн гудамж – Олимпийн гудамж",
        "ns",
        ("sambuu-ikh-surguuli", "amar-ikh-surguuli", "ikh-surguuli", "olympic-genden"),
    ),
    CorridorSpec(
        "baga-toiruu-e",
        "Baga Toiruu East",
        "Бага тойруу (зүүн)",
        "ns",
        ("sambuu-baga-toiruu-east", "baga-toiruu-east"),
    ),
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
