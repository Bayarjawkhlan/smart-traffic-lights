import logging
import threading
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np
import torch
from ultralytics import YOLO

from . import config
from .annotate import draw
from .counting import PERSON_CLASS, TRACKED_CLASSES, VEHICLE_CLASSES, Detection, MotionHistory, count_zones
from .zones import Zone

log = logging.getLogger("vision")


def pick_device() -> str:
    if config.DEVICE:
        return config.DEVICE
    return "mps" if torch.backends.mps.is_available() else "cpu"


class VideoWorker:
    def __init__(self, pool: "WorkerPool", name: str, path: Path, zones: tuple[Zone, ...]) -> None:
        self.pool = pool
        self.name = name
        self.path = path
        self.zones = zones
        self.viewers = 0
        self.idle_since = time.monotonic()
        self.seq = 0
        self.jpeg: bytes | None = None
        self.counts: dict[str, object] | None = None
        self.error: str | None = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"vision-{name}", daemon=True)

    @property
    def alive(self) -> bool:
        return self._thread.is_alive() and not self._stop.is_set()

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        try:
            self._loop()
        except Exception as exc:
            log.exception("worker %s crashed", self.name)
            self.error = str(exc)
        finally:
            self._stop.set()
            self.pool.forget(self)

    def _loop(self) -> None:
        device = pick_device()
        config.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        model = YOLO(str(config.MODEL_PATH))
        motion = MotionHistory()
        cap = cv2.VideoCapture(str(self.path))
        if not cap.isOpened():
            raise RuntimeError(f"cannot open {self.path.name}")
        src_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        step = max(1, round(src_fps / config.MAX_FPS))
        frame_idx = -1
        t0 = time.monotonic()
        done_at: deque[float] = deque(maxlen=20)
        log.info("worker %s started on %s (%.1f fps source, every %d frame)", self.name, device, src_fps, step)

        while not self._stop.is_set():
            if self.pool.retire_if_idle(self):
                break
            tick = time.monotonic()
            target = max(frame_idx + step, int((time.monotonic() - t0) * src_fps))
            ok = True
            while ok and frame_idx < target:
                ok = cap.grab()
                frame_idx += 1
            if not ok and frame_idx == 0:
                raise RuntimeError(f"no frames in {self.path.name}")
            if not ok:
                # Reopening is more reliable than seeking to 0, which some webm/VP8 builds ignore.
                cap.release()
                cap = cv2.VideoCapture(str(self.path))
                frame_idx = -1
                t0 = time.monotonic()
                motion.clear()
                if model.predictor is not None and getattr(model.predictor, "trackers", None):
                    model.predictor.trackers[0].reset()
                continue
            ok, frame = cap.retrieve()
            if not ok:
                continue

            t = frame_idx / src_fps
            frame = self._resize(frame)
            detections = self._detect(model, frame, device, motion, t)
            counts = count_zones(self.zones, detections, frame.shape[1], frame.shape[0])

            done_at.append(time.monotonic())
            fps = (len(done_at) - 1) / (done_at[-1] - done_at[0]) if len(done_at) > 1 else 0.0
            annotated = draw(frame, counts, detections, f"{self.name}  t={t:5.1f}s  {fps:4.1f} fps  {device}")
            ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
            self.jpeg = buf.tobytes() if ok else self.jpeg
            self.counts = {
                "video": self.name,
                "t": round(t, 2),
                "fps": round(fps, 1),
                "zones": [c.to_json() for c in counts],
            }
            self.seq += 1

            now = time.monotonic()
            wait = max(t0 + frame_idx / src_fps - now, tick + 1 / config.MAX_FPS - now)
            if wait > 0:
                self._stop.wait(wait)
        cap.release()

    @staticmethod
    def _resize(frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        if w <= config.FRAME_WIDTH:
            return frame
        return cv2.resize(frame, (config.FRAME_WIDTH, round(h * config.FRAME_WIDTH / w)), interpolation=cv2.INTER_AREA)

    @staticmethod
    def _detect(model: YOLO, frame: np.ndarray, device: str, motion: MotionHistory, t: float) -> list[Detection]:
        result = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            classes=TRACKED_CLASSES,
            imgsz=config.IMGSZ,
            device=device,
            verbose=False,
        )[0]
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            motion.forget_stale(t)
            return []
        xyxy = boxes.xyxy.cpu().numpy()
        classes = boxes.cls.cpu().numpy().astype(int)
        ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else [None] * len(classes)
        detections: list[Detection] = []
        for box, cls, tid in zip(xyxy, classes, ids):
            b = (float(box[0]), float(box[1]), float(box[2]), float(box[3]))
            stationary = motion.observe(t, int(tid), b) if tid is not None else False
            if cls == PERSON_CLASS:
                detections.append(Detection(tid, "person", "person", b, stationary))
            elif cls in VEHICLE_CLASSES:
                detections.append(Detection(tid, "vehicle", VEHICLE_CLASSES[cls], b, stationary))
        motion.forget_stale(t)
        return detections


class WorkerPool:
    def __init__(self) -> None:
        self._workers: dict[str, VideoWorker] = {}
        self._lock = threading.Lock()

    def acquire(self, name: str, path: Path, zones: tuple[Zone, ...]) -> VideoWorker:
        with self._lock:
            worker = self._workers.get(name)
            if worker is None or not worker.alive:
                worker = VideoWorker(self, name, path, zones)
                self._workers[name] = worker
                worker.start()
            worker.viewers += 1
            return worker

    def release(self, worker: VideoWorker) -> None:
        with self._lock:
            worker.viewers -= 1
            if worker.viewers == 0:
                worker.idle_since = time.monotonic()

    def retire_if_idle(self, worker: VideoWorker) -> bool:
        with self._lock:
            if worker.viewers > 0 or time.monotonic() - worker.idle_since < config.IDLE_STOP_SECONDS:
                return False
            worker.stop()
            if self._workers.get(worker.name) is worker:
                del self._workers[worker.name]
            log.info("worker %s stopped: no viewers", worker.name)
            return True

    def forget(self, worker: VideoWorker) -> None:
        with self._lock:
            if self._workers.get(worker.name) is worker:
                del self._workers[worker.name]

    def active(self) -> list[str]:
        with self._lock:
            return sorted(self._workers)

    def stop_all(self) -> None:
        with self._lock:
            for worker in self._workers.values():
                worker.stop()
            self._workers.clear()
