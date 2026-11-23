# Vision service

Camera vision on recorded street video. It shows what a camera at a Signal Site would feed the Controller: the vehicle Queue on each Approach and the Pedestrian Demand at each Crosswalk. It is a showcase only; it never decides anything and does not drive the SUMO simulation (see `docs/adr/0001-simulation-first-on-sumo.md`).

Detection is Ultralytics YOLO (`yolo26n.pt`, the smallest current model) with its built-in ByteTrack tracker for stable track ids. It runs on the CPU, or on Apple MPS when available. Ultralytics is AGPL-3.0, which is why the whole project is (`docs/adr/0003-agpl-open-source.md`).

## Run

```sh
cd vision
uv sync
./scripts/fetch_sample_videos.sh          # two freely licensed clips, see videos/SOURCES.md
uv run uvicorn app.main:app --port 8001
```

The model weights download to `models/` on first use. Open `http://localhost:8001/api/stream.mjpg?video=tyumen-respubliki-ordzhonikidze` in a browser to watch the annotated stream.

Docker (CPU only, videos mounted from the host):

```sh
docker build -t stl-vision vision
docker run --rm -p 8001:8001 -v "$PWD/vision/videos:/app/videos:ro" stl-vision
```

### Settings

| Variable | Default | |
| --- | --- | --- |
| `VISION_VIDEOS_DIR` | `videos/` | |
| `VISION_ZONES_DIR` | `zones/` | |
| `VISION_MODEL` | `models/yolo26n.pt` | any Ultralytics detection weights |
| `VISION_DEVICE` | `mps` if available, else `cpu` | e.g. `cpu`, `cuda:0` |
| `VISION_MAX_FPS` | `10` | frames processed per second, at most |
| `VISION_FRAME_WIDTH` | `960` | frames are downscaled to this width |
| `VISION_IMGSZ` | frame width | model input size; 640 is faster but misses distant pedestrians |
| `VISION_IDLE_STOP_SECONDS` | `15` | a video's loop stops this long after its last viewer leaves |
| `VISION_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | comma-separated |

## How counting works

Each video has one shared processing loop, started by its first viewer (stream or WebSocket) and stopped once nobody is watching. It plays the video in real time, processes at most `VISION_MAX_FPS` frames per second and loops at the end, resetting the tracker.

On each processed frame it detects vehicles (car, bus, truck, motorcycle, bicycle) and persons, and for every zone counts:

- `vehicles`, `persons`: detections whose footpoint (bottom-centre of the box) is inside the zone.
- `queued`: vehicles in the zone whose box centre has stayed within 15 % of the box size for the last second.
- `waiting`: persons that are stationary in the same sense, counted only in `crosswalk` zones. `waiting > 0` is Pedestrian Demand.

A track needs about one second of history before it can count as stationary. A handheld or swaying camera makes everything look like it moves, so use footage from a fixed mount where you can.

## API

| | |
| --- | --- |
| `GET /api/health` | `{"status": "ok", "device", "model", "videos": n, "active": [video names being processed]}` |
| `GET /api/videos` | `[{"name", "file", "zone_file": bool, "zones": [{"id", "kind", "label", "polygon"}]}]` |
| `GET /api/stream.mjpg?video=<name>` | MJPEG (`multipart/x-mixed-replace`) of annotated frames: boxes with track ids (red when stationary), zone polygons tinted by load (green 0, amber 1–3, red 4+ queued vehicles or waiting persons), counts per zone. Use it as an `<img src>`. |
| `WS /ws/counts?video=<name>` | About 5 JSON messages per second, shown below. |

`<name>` is the video's file name without extension. An unknown name gives 404 on HTTP and a rejected handshake (403) on the WebSocket.

```json
{
  "video": "tyumen-respubliki-ordzhonikidze",
  "t": 8.1,
  "fps": 10.0,
  "zones": [
    {"id": "far-approach", "kind": "approach", "label": "Ordzhonikidze approach", "vehicles": 5, "queued": 0, "persons": 0, "waiting": 0},
    {"id": "near-crosswalk", "kind": "crosswalk", "label": "Near crosswalk", "vehicles": 0, "queued": 0, "persons": 1, "waiting": 1}
  ]
}
```

`t` is seconds into the video and restarts at 0 when the video loops; `fps` is the measured processing rate.

## Your own video and zones

Drop any `.mp4`, `.webm`, `.mov`, `.mkv`, `.avi` or `.m4v` into `videos/` (gitignored), for example your own footage of Peace Avenue. Without a zone file the whole frame is one `approach` zone.

To add zones, create `zones/<video-name>.json`:

```json
{
  "zones": [
    {"id": "north-approach", "kind": "approach", "label": "Northbound approach", "polygon": [[0.33, 0.49], [0.70, 0.49], [0.70, 0.585], [0.33, 0.585]]},
    {"id": "east-crosswalk", "kind": "crosswalk", "label": "East crosswalk", "polygon": [[0.24, 0.70], [0.70, 0.70], [0.74, 1.0], [0.24, 1.0]]}
  ]
}
```

Polygons are in normalised image coordinates: `[0, 0]` is the top-left corner, `[1, 1]` the bottom-right. Draw an `approach` over the road surface where vehicles stop before the stop line, and a `crosswalk` over the kerb area where pedestrians wait plus the crossing itself; membership is decided by where a road user's feet are. To find coordinates, grab a frame (`ffmpeg -ss 5 -i videos/<file> -frames:v 1 frame.png`) and read positions off it as fractions of its width and height. Zone files are read when a video's loop starts, so after editing one, stop all viewers for `VISION_IDLE_STOP_SECONDS` or restart the server.
