# Client

The web app for the Peace Avenue corridor demo: a live map of the simulated Corridor, a panel for each Signal Site, Operator controls, Controller comparisons from Experiment Mode, the camera vision showcase and a plain-language explanation of the system. UI text is in English and Mongolian. Terms follow [GLOSSARY.md](../GLOSSARY.md).

React 19, Vite, TypeScript (strict) and MapLibre GL JS. The basemap is OpenFreeMap's `dark` style (no key); map data © OpenStreetMap contributors.

## Run for development

Start the services first (each in its own terminal):

```sh
cd sim && uv run python -m corridor_sim.server                 # http://localhost:8000
cd vision && uv run uvicorn app.main:app --port 8001           # optional, for the Vision page
```

Then the client:

```sh
cd client
pnpm install
pnpm dev                                                        # http://localhost:5173
```

The services allow `http://localhost:5173` by CORS out of the box. The client reconnects to the simulation by itself, so the order you start things in does not matter.

| Variable | Default | |
| --- | --- | --- |
| `VITE_SIM_URL` | `http://localhost:8000` | simulation service, HTTP and `/ws` |
| `VITE_VISION_URL` | `http://localhost:8001` | vision service; the Vision page shows an offline state without it |

Both are read at build time and must be reachable from the viewer's browser.

## Checks

```sh
pnpm exec tsc --noEmit
pnpm build
pnpm lint
```

## Docker

Multi-stage: builds with pnpm, serves the static files with nginx on port 80. The service URLs are baked in at build time:

```sh
docker build -t stl-client \
  --build-arg VITE_SIM_URL=http://localhost:8000 \
  --build-arg VITE_VISION_URL=http://localhost:8001 \
  client
docker run --rm -p 8080:80 stl-client
```

`docker compose up` at the repository root does the same for all three services; the client is then on `http://localhost:8080`.

## Using it

- **Live**: congestion on every road (free, slow, jammed), signal colours at stop lines and Crosswalks, vehicles and pedestrians. Click a Signal Site on the map or in the corridor strip at the bottom to open its panel: a live schematic, the current Phase and stage, the Controller's score for each Phase, every Approach and Crosswalk with its wait against the caps, and the site's events. The Explain button asks the simulation service for a language-model explanation (only when it has an OpenAI key).
- **Operator** switch (top right, no login): change the Controller, Scenario, speed and caps, pause, restart, press a pedestrian button on a Crosswalk or block a lane on an Approach. Viewers see the same data read-only. The setting is remembered per browser.
- **Experiments**: Controllers compared per Scenario, with the change against the Fixed-time baseline. Operators can start a run; the page polls until it finishes.
- **Vision**: the annotated camera stream and zone counts from the vision service, with each clip's licence. The simulation does not use it.

The event log only holds events that happened while the page was open; the simulation service does not replay older ones.

## Layout

```
src/
  api/        types, HTTP calls, the reconnecting live store (WebSocket)
  map/        MapLibre engine: layers, per-frame updates, vehicle interpolation, site markers, legend
  live/       Live page: metrics strip, Operator bar, corridor strip, Signal Site panel and schematic, event log
  pages/      Experiments, Vision, About
  i18n/       EN/MN dictionary and localised names
  ui/, lib/   shared pieces
  styles/     tokens and app styles
```

## Licence

AGPL-3.0, like the rest of the repository.
