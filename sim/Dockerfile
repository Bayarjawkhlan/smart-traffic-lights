FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

# libsumo's wheel links X11/GL even though the simulation runs headless.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libx11-6 libxext6 libxrender1 libgl1 libglu1-mesa libxcursor1 libxft2 libxinerama1 libfontconfig1 libatomic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    HOST=0.0.0.0 \
    PORT=8000

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-install-project

COPY corridor_sim ./corridor_sim
COPY scripts ./scripts
COPY data ./data

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "python", "-m", "corridor_sim.server"]
