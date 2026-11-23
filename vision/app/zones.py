import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2
import numpy as np

ZoneKind = Literal["approach", "crosswalk"]


@dataclass(frozen=True)
class Zone:
    id: str
    kind: ZoneKind
    label: str
    polygon: tuple[tuple[float, float], ...]

    def contains(self, x: float, y: float) -> bool:
        contour = np.array(self.polygon, dtype=np.float32)
        return cv2.pointPolygonTest(contour, (x, y), False) >= 0

    def to_json(self) -> dict[str, object]:
        return {"id": self.id, "kind": self.kind, "label": self.label, "polygon": [list(p) for p in self.polygon]}


DEFAULT_ZONES = (Zone("frame", "approach", "Full frame", ((0, 0), (1, 0), (1, 1), (0, 1))),)


def _parse_zone(raw: dict[str, object]) -> Zone:
    kind = raw["kind"]
    if kind not in ("approach", "crosswalk"):
        raise ValueError(f"zone {raw.get('id')!r}: kind must be 'approach' or 'crosswalk', got {kind!r}")
    points = tuple((float(x), float(y)) for x, y in raw["polygon"])  # type: ignore[union-attr]
    if len(points) < 3 or not all(0 <= v <= 1 for p in points for v in p):
        raise ValueError(f"zone {raw.get('id')!r}: polygon needs 3+ points in normalised 0-1 coordinates")
    return Zone(str(raw["id"]), kind, str(raw.get("label", raw["id"])), points)


def zone_file(zones_dir: Path, video_stem: str) -> Path:
    return zones_dir / f"{video_stem}.json"


def load_zones(zones_dir: Path, video_stem: str) -> tuple[Zone, ...]:
    path = zone_file(zones_dir, video_stem)
    if not path.is_file():
        return DEFAULT_ZONES
    data = json.loads(path.read_text())
    return tuple(_parse_zone(z) for z in data["zones"])
