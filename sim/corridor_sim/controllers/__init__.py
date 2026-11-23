from __future__ import annotations

from .base import Controller
from .fixed_time import FixedTimeController
from .max_pressure import MaxPressureController

CONTROLLERS: dict[str, type[Controller]] = {
    FixedTimeController.name: FixedTimeController,
    MaxPressureController.name: MaxPressureController,
}


def register_rl() -> None:
    from .rl import RLController

    if RLController.available():
        CONTROLLERS[RLController.name] = RLController


def make(name: str) -> Controller:
    return CONTROLLERS[name]()
