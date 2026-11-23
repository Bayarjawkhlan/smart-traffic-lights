from collections import deque
from dataclasses import dataclass
from typing import Literal

from .zones import Zone

# COCO class ids as used by the pretrained YOLO detection models.
VEHICLE_CLASSES: dict[int, str] = {1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
PERSON_CLASS = 0
TRACKED_CLASSES = [PERSON_CLASS, *VEHICLE_CLASSES]

Category = Literal["vehicle", "person"]


@dataclass(frozen=True)
class Detection:
    track_id: int | None
    category: Category
    label: str
    box: tuple[float, float, float, float]
    stationary: bool

    @property
    def footpoint(self) -> tuple[float, float]:
        x1, _, x2, y2 = self.box
        return (x1 + x2) / 2, y2


@dataclass
class ZoneCounts:
    zone: Zone
    vehicles: int = 0
    queued: int = 0
    persons: int = 0
    waiting: int = 0

    @property
    def load(self) -> int:
        return self.queued if self.zone.kind == "approach" else self.waiting

    def to_json(self) -> dict[str, object]:
        z = self.zone
        return {
            "id": z.id,
            "kind": z.kind,
            "label": z.label,
            "vehicles": self.vehicles,
            "queued": self.queued,
            "persons": self.persons,
            "waiting": self.waiting,
        }


class MotionHistory:
    def __init__(self, window_s: float = 1.0, stationary_fraction: float = 0.15, forget_s: float = 2.0) -> None:
        self.window_s = window_s
        self.stationary_fraction = stationary_fraction
        self.forget_s = forget_s
        self._tracks: dict[int, deque[tuple[float, float, float]]] = {}

    def observe(self, t: float, track_id: int, box: tuple[float, float, float, float]) -> bool:
        x1, y1, x2, y2 = box
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        history = self._tracks.setdefault(track_id, deque())
        history.append((t, cx, cy))
        while history and history[0][0] < t - self.window_s:
            history.popleft()
        # Too short a history cannot tell a stopped vehicle from one that just entered the frame.
        if t - history[0][0] < 0.8 * self.window_s:
            return False
        threshold = self.stationary_fraction * max(x2 - x1, y2 - y1)
        return all((cx - hx) ** 2 + (cy - hy) ** 2 < threshold**2 for _, hx, hy in history)

    def forget_stale(self, t: float) -> None:
        stale = [tid for tid, h in self._tracks.items() if not h or h[-1][0] < t - self.forget_s]
        for tid in stale:
            del self._tracks[tid]

    def clear(self) -> None:
        self._tracks.clear()


def count_zones(zones: tuple[Zone, ...], detections: list[Detection], width: int, height: int) -> list[ZoneCounts]:
    counts = [ZoneCounts(z) for z in zones]
    for det in detections:
        fx, fy = det.footpoint
        nx, ny = fx / width, fy / height
        for c in counts:
            if not c.zone.contains(nx, ny):
                continue
            if det.category == "vehicle":
                c.vehicles += 1
                c.queued += det.stationary
            else:
                c.persons += 1
                c.waiting += det.stationary and c.zone.kind == "crosswalk"
    return counts
