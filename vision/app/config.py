import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VIDEOS_DIR = Path(os.environ.get("VISION_VIDEOS_DIR", ROOT / "videos"))
ZONES_DIR = Path(os.environ.get("VISION_ZONES_DIR", ROOT / "zones"))
MODEL_PATH = Path(os.environ.get("VISION_MODEL", ROOT / "models" / "yolo26n.pt"))
DEVICE = os.environ.get("VISION_DEVICE", "")
MAX_FPS = float(os.environ.get("VISION_MAX_FPS", "10"))
FRAME_WIDTH = int(os.environ.get("VISION_FRAME_WIDTH", "960"))
# Above the model default of 640 so distant pedestrians on a far kerb are still detected.
IMGSZ = int(os.environ.get("VISION_IMGSZ", str(FRAME_WIDTH)))
IDLE_STOP_SECONDS = float(os.environ.get("VISION_IDLE_STOP_SECONDS", "15"))
CORS_ORIGINS = os.environ.get("VISION_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"}
