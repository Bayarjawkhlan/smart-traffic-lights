# security review, round 1

verdict: pass

Scope: `feat/corridor-demo...HEAD`, read statically. No service was started and no port was touched. No blocker or
major is introduced by this diff. Four small items are introduced or worsened (F1-F4); five are pre-existing and
listed for the record (F5-F9).

## Findings

### F1 [minor] Committed ledger holds an absolute home path with the OS user name (introduced)

where: `docs/specs/0001-street-network/factory.md:3`

evidence: the line reads `worktree: /Users/<user>/Documents/projects/smart-traffic-lights-factory-street-network`.
It is the only personal path left in `HEAD` under `sim`, `client`, `docs` and `README.md`. On the base branch the
SUMO headers in `corridor.net.xml` and the five `*.ped.rou.xml` files also held local paths; `strip_header` in
`build.py` removes those, so this diff is a net improvement apart from this one line.

fix: write the worktree as a repo-relative or placeholder path in the ledger before the branch is pushed.

### F2 [minor] Untrusted OSM street names now reach the LLM prompt on more fields (worsened, low exposure)

where: `sim/corridor_sim/build.py:190-194` (`street_of`), `sim/corridor_sim/server.py:266-277` (`_labels`),
`sim/corridor_sim/explain.py:38-45`

evidence: `street_of` falls back to `Street(name, name)` for any OSM `name` not in the `STREETS` table, so a raw OSM
tag becomes `street`, `streetEn`, the approach label and the crosswalk `streets[]`. `_labels` puts those strings in
the JSON sent as `input` to the model. The base already sent approach street names; the diff adds crosswalk street
names. OSM is publicly editable, so the text is attacker-influenced in principle. Exposure is low: the data is
fetched only when `corridor.osm.xml` is missing, the committed snapshot has 18 street names and all are plain
street names (checked in `sim/data/sites.json`), the call has no tools, and the output is rendered as text. Site
and neighbour names come from `SITE_SPECS`, not OSM.

fix: at build time reject or strip names that are not short letter/space/punctuation strings (for example a length
cap of 60 and no control or markup characters), so a re-fetch cannot carry instructions into `sites.json`.

### F3 [nit] ScenarioError text is returned to the client in a 500 body (introduced)

where: `sim/corridor_sim/server.py:243-247` (`_start`), `sim/corridor_sim/engine.py:167-178`

evidence: `raise HTTPException(500, str(error))` returns the scenario name, site id and approach id from
`scenarios.json`. All of it is already public through `/api/network`, so nothing sensitive leaks today.

fix: none needed for the demo; return a fixed message and keep the detail in the log if the service is ever exposed.

### F4 [nit] Each switch to the RL Controller re-reads and hashes the 3.1 MB network file on the simulation thread (introduced)

where: `sim/corridor_sim/controllers/rl.py:69-74` (`load_weights` -> `network_hash`), reached from
`POST /api/control {"action":"controller","name":"rl"}`

evidence: `network_hash()` reads `corridor.net.xml` (3,155,721 bytes) and computes SHA-256 on every `RLController()`
construction, inside `runner.call`. A client that loops this request adds a short stall per call, and one warning
log line per call when the hash differs. Small next to the restart cost in F7. Not measured, read from the code.

fix: cache the hash at module level (the file does not change while the service runs).

### F5 [minor] /api/explain does not validate `site` (pre-existing)

where: `sim/corridor_sim/server.py:296` (`sim.site_by_id[request.site]`)

evidence: an unknown id raises `KeyError` inside `runner.call` and surfaces as an unhandled 500. Same line on the
base branch. The refactor to `_labels` adds two more unguarded lookups on the Mongolian path
(`DIRECTIONS_MN[direction]`, `next(...)` over `sites.json`); with the committed data every approach has a valid
`direction` and every crosswalk has `streets`, so they do not fire.

fix: return 404 when `request.site not in runner.sim.site_by_id`, as `_require` does for `/api/control`.

### F6 [minor] Unauthenticated, unthrottled endpoint spends the OpenAI key (pre-existing)

where: `sim/corridor_sim/server.py:288-321`, `sim/corridor_sim/explain.py:38-45`

evidence: any client that can reach the service can call `/api/explain` in a loop; each call is one paid model
request and one synchronous worker thread. Unchanged by this diff. Acceptable for a service bound to localhost.

fix: a small per-process rate limit or an in-flight guard before the service is exposed beyond localhost.

### F7 [minor] Any client can restart, pause or re-run the simulation (pre-existing, cost grows with the Network)

where: `sim/corridor_sim/server.py:197-241` (`/api/control`), `:346-363` (`POST /api/experiments`)

evidence: no auth by design. `scenario` and `restart` close and relaunch SUMO; with 15 sites and a 3.1 MB network
each restart is heavier than on the base, and `runner.call` blocks a request thread for up to 30 s.
`POST /api/experiments` starts an hour-long subprocess (one at a time, guarded by the 409). Inputs are validated:
`action` is a `Literal`, `speed` must be in `SPEEDS`, scenario and controller names are checked against the known
sets, caps are range-checked (NaN fails the comparison chain and is rejected), `site`/`target` go through
`_require`. No user string reaches a path, a shell or a subprocess argument unchecked; experiment scenario names
are checked against `scenarios()` and passed as an argv list.

fix: none for the local demo; bind to 127.0.0.1 and keep the CORS allow-list as is.

### F8 [nit] Build writes XML from network ids with f-strings, not `quoteattr` (pre-existing)

where: `sim/corridor_sim/build.py:146` (`<join nodes=...>`), `:183` (`<crossing ...>`), `:599-602` (`<flow ...>`)

evidence: node and edge ids come from netconvert output over OSM numeric ids, so they cannot contain quotes in
practice. The diff only adds a boolean `reset=` attribute to the join line. The pedestrian weight file already uses
`quoteattr`.

fix: use `quoteattr` on the three lines for consistency.

### F9 [nit] Overpass download has no integrity check (pre-existing)

where: `sim/scripts/fetch_osm.sh`, `sim/corridor_sim/build.py:130-133`

evidence: the diff changes only the bounding box and removes a comment. The script uses a fixed HTTPS URL, quoted
variables, `set -euo pipefail` and `curl --fail`; nothing in it is caller-controlled. The result is parsed by
netconvert and by `sumolib` (Python SAX, external entities off by default). The committed `corridor.osm.xml` has
no DOCTYPE or ENTITY and no mapper `user`/`uid` attributes. The fetch runs only when the file is absent.

fix: none needed while the snapshot is committed.

## Checked and clean

- Subprocess use: `subprocess.run` and `Popen` take argv lists, no `shell=True`; arguments are config paths, fixed
  flags, numbers and names validated against known sets. No command injection path added.
- Path handling: no request field is used to build a file path. Experiment results are read by a fixed glob of
  `EXPERIMENT_DIR/*.json`; the model file path is a constant.
- Model and result JSON: `rl-linear.json` and the experiment files gain a `network` SHA-256 string; loaded with
  `json.loads`, no pickle or eval. A hash mismatch only logs a warning.
- XSS: the only `innerHTML` in the client (`client/src/map/LiveMap.tsx:59`) is a constant string. Site names go in
  through `textContent` and `setAttribute("aria-label")`; the ribbon, corridor picker, event feed and site panel
  render names as React text. The new `SITE_EVENT` regex in `EventFeed.tsx` has no nested quantifiers.
- Secrets: no key, token or `.env` file added; only `sim/.env.example` is tracked. No secret-shaped string in the
  added lines.
- Dependencies: no change to `pyproject`, lock files or `package.json` in this range.
- CORS: unchanged allow-list (`localhost:5173`, `127.0.0.1:5173`, or `CORS_ORIGINS`).
- WebSocket: unchanged; per-client queue stays bounded at 4.
- `guard.py`: Safety Guard link lookup only, no security relevance.
