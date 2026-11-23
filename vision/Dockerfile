FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

# OpenCV's wheel links against these even when nothing is shown on screen.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    YOLO_CONFIG_DIR=/tmp/ultralytics \
    YOLO_AUTOINSTALL=false

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-install-project

COPY app ./app
COPY zones ./zones
COPY scripts ./scripts
RUN uv run --no-sync python -c "from ultralytics import YOLO; YOLO('models/yolo26n.pt')"

VOLUME /app/videos
EXPOSE 8001
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
