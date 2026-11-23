import cv2
import numpy as np

from .counting import Detection, ZoneCounts

BGR = tuple[int, int, int]

LOAD_COLOURS: tuple[BGR, BGR, BGR] = ((80, 200, 80), (0, 190, 255), (60, 60, 235))
VEHICLE_COLOUR: BGR = (255, 200, 0)
PERSON_COLOUR: BGR = (255, 90, 220)
STOPPED_COLOUR: BGR = (60, 60, 235)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def _load_colour(load: int) -> BGR:
    if load == 0:
        return LOAD_COLOURS[0]
    return LOAD_COLOURS[1] if load < 4 else LOAD_COLOURS[2]


def _text(img: np.ndarray, text: str, org: tuple[int, int], scale: float, colour: BGR = (255, 255, 255)) -> None:
    (w, h), base = cv2.getTextSize(text, FONT, scale, 1)
    x, y = org
    cv2.rectangle(img, (x - 2, y - h - 3), (x + w + 2, y + base), (20, 20, 20), -1)
    cv2.putText(img, text, (x, y), FONT, scale, colour, 1, cv2.LINE_AA)


def draw(frame: np.ndarray, counts: list[ZoneCounts], detections: list[Detection], hud: str) -> np.ndarray:
    h, w = frame.shape[:2]
    tint = frame.copy()
    outlines: list[tuple[np.ndarray, BGR]] = []
    for c in counts:
        pts = (np.array(c.zone.polygon) * [w, h]).astype(np.int32)
        colour = _load_colour(c.load)
        cv2.fillPoly(tint, [pts], colour)
        outlines.append((pts, colour))
    out = cv2.addWeighted(tint, 0.25, frame, 0.75, 0)
    for pts, colour in outlines:
        cv2.polylines(out, [pts], True, colour, 2, cv2.LINE_AA)

    for d in detections:
        x1, y1, x2, y2 = (int(v) for v in d.box)
        base = VEHICLE_COLOUR if d.category == "vehicle" else PERSON_COLOUR
        colour = STOPPED_COLOUR if d.stationary else base
        cv2.rectangle(out, (x1, y1), (x2, y2), colour, 2 if d.stationary else 1)
        tag = f"#{d.track_id} {d.label}" if d.track_id is not None else d.label
        _text(out, tag, (x1, max(12, y1 - 3)), 0.38, colour)

    for c, (pts, colour) in zip(counts, outlines):
        cx, cy = pts.mean(axis=0).astype(int)
        if c.zone.kind == "approach":
            line = f"{c.zone.label}: {c.queued}/{c.vehicles} queued"
        else:
            line = f"{c.zone.label}: {c.waiting}/{c.persons} waiting"
        (tw, _), _ = cv2.getTextSize(line, FONT, 0.5, 1)
        _text(out, line, (int(np.clip(cx - tw // 2, 4, w - tw - 4)), int(np.clip(cy, 20, h - 6))), 0.5, colour)

    _text(out, hud, (8, 22), 0.55)
    return out
