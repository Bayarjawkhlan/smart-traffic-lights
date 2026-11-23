import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import config
from .worker import VideoWorker, WorkerPool, pick_device
from .zones import load_zones, zone_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

pool = WorkerPool()
POLL_S = 0.5 / config.MAX_FPS
COUNTS_PERIOD_S = 0.2
BOUNDARY = "frame"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    pool.stop_all()


app = FastAPI(title="Smart Traffic Signals – vision", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["GET"], allow_headers=["*"])


def list_videos() -> dict[str, Path]:
    if not config.VIDEOS_DIR.is_dir():
        return {}
    files = sorted(p for p in config.VIDEOS_DIR.iterdir() if p.suffix.lower() in config.VIDEO_SUFFIXES)
    videos: dict[str, Path] = {}
    for path in files:
        videos.setdefault(path.stem, path)
    return videos


def resolve_video(name: str) -> Path:
    path = list_videos().get(name)
    if path is None:
        raise HTTPException(404, f"unknown video {name!r}")
    return path


def acquire(name: str, path: Path) -> VideoWorker:
    return pool.acquire(name, path, load_zones(config.ZONES_DIR, name))


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "device": pick_device(),
        "model": config.MODEL_PATH.name,
        "videos": len(list_videos()),
        "active": pool.active(),
    }


@app.get("/api/videos")
def videos() -> list[dict[str, object]]:
    return [
        {
            "name": name,
            "file": path.name,
            "zone_file": zone_file(config.ZONES_DIR, name).is_file(),
            "zones": [z.to_json() for z in load_zones(config.ZONES_DIR, name)],
        }
        for name, path in list_videos().items()
    ]


@app.get("/api/stream.mjpg")
async def stream(video: str = Query(...)) -> StreamingResponse:
    worker = acquire(video, resolve_video(video))

    async def frames() -> AsyncIterator[bytes]:
        seen = -1
        try:
            while worker.error is None:
                if worker.seq != seen and worker.jpeg is not None:
                    seen = worker.seq
                    jpeg = worker.jpeg
                    yield (
                        f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\nContent-Length: {len(jpeg)}\r\n\r\n".encode()
                        + jpeg
                        + b"\r\n"
                    )
                await asyncio.sleep(POLL_S)
        finally:
            pool.release(worker)

    return StreamingResponse(
        frames(),
        media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY}",
        headers={"Cache-Control": "no-store"},
    )


@app.websocket("/ws/counts")
async def counts(ws: WebSocket, video: str = Query(...)) -> None:
    path = list_videos().get(video)
    if path is None:
        await ws.close(code=1008, reason=f"unknown video {video!r}")
        return
    await ws.accept()
    worker = acquire(video, path)
    loop = asyncio.get_running_loop()
    next_send = loop.time()
    try:
        while worker.error is None:
            if worker.counts is not None:
                await ws.send_json(worker.counts)
            next_send += COUNTS_PERIOD_S
            await asyncio.sleep(max(0.0, next_send - loop.time()))
        await ws.close(code=1011, reason=worker.error)
    except WebSocketDisconnect:
        pass
    finally:
        pool.release(worker)
