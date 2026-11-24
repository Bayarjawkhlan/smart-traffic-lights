# Is `Srikeerthiraja/Smart-Traffic-Light-Control-System` a useful base?

Research date: 2026-11-23. The repo was cloned read-only and none of its code was run (it has none, see below).

## Summary

**Verdict: don't use it as a base. Start from scratch on Eclipse SUMO (TraCI/libsumo), with your own controller, Safety Guard and vision service.** Nothing in the repo is worth taking except one idea, covered below.

- **The repository contains no code.** All 9 commits in its history add or edit only Markdown files: `README.md` plus one README each in `vehicle_detection/`, `signal_controller/` and `arduino_code/`. The "code" is short pseudocode snippets inside those READMEs. One `Vehicle_detection` file was created and deleted 26 minutes later. Its content matched the detection README. GitHub reports no detected languages, no license and no releases. The last commit was a README edit on 2026-01-13.
- The described "AI" is a single threshold formula: green = 10 s below 15 vehicles, otherwise `min(40, 10 + 2·(n−15))`. Yellow is fixed at 3 s and red at 10 s. It runs for one intersection, has no pedestrians and no coordination, and is not AI in any meaningful sense.
- The described vision approach counts contours on a binary-thresholded frame (`len(contours)`). That counts blobs, not vehicles. There is no model, no classes and no pedestrians.
- It meets **0 of your 7 wishlist items fully and only 2 partially**, and the partial ones are trivial.
- The established building blocks cover almost everything you listed:
  - **SUMO**, licensed EPL-2.0, provides:
    - TraCI control of signal states
    - crossings and walking areas that carry their own signal links
    - E2 detectors that report queue and jam length
    - person detectors and waiting-pedestrian counts
    - OSM import with `--osm.crossings` and `--tls.guess-signals`
  - **Max-pressure** (Varaiya 2013) is a decentralized controller with a proven stability guarantee. It uses downstream queues, but the original proof assumes infinite link storage. A capacity-aware variant (Gregoire et al.) is the standard fix for spillback.
  - **sumo-rl** (MIT) gives Gymnasium/PettingZoo environments for the later RL controller. It has **no pedestrian or all-red handling** and builds its own phases, so put your Safety Guard *between* the RL policy and TraCI.
  - **Ultralytics YOLO** provides region counting, which maps directly onto "count per approach / per crosswalk". It is **AGPL-3.0**: a city or commercial deployment either needs an Ultralytics Enterprise License or must comply with AGPL, including §13's network clause. Keep the vision service behind a count-only interface so the detector can be swapped out.

## 1. The repository, file by file

Cloned from `https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System`. The HEAD commit is `1005dae`. Permalinks below use that commit.

### 1.1 Facts

| Item | Finding | Source |
|---|---|---|
| Files | 4 Markdown files, nothing else (`README.md`, `vehicle_detection/README.md`, `signal_controller/README.md`, `arduino_code/README.md`) | `git ls-files`; `find` |
| History | 9 commits, 2025-11-14 to 2026-01-13, one author. Every commit touches only README files, except `fe5558d`, which added `Vehicle_detection` (47 lines), and `dbaa325`, which deleted it 26 minutes later. That file is the same text as `vehicle_detection/README.md` apart from one trailing space. | `git log --name-status`; `git show fe5558d` |
| Languages | GitHub reports `{}` (no code) and `language: null` | `gh api repos/.../languages` |
| License | **None.** `gh api .../license` returns 404, and the README says "for educational and demonstration purposes only" ([README.md:97-99](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/README.md#L97-L99)). With no license, reuse rights are not granted. | `gh api` |
| Activity | Created 2025-11-13, last push 2026-01-13, 1 star, 0 forks, 0 issues, no releases | `gh api repos/...` |
| Tests | None | file listing |
| UI | None. A dashboard appears only under "Future Enhancements" ([README.md:90-93](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/README.md#L90-L93)) | |
| Simulation | None. The README describes physical LEDs on an Arduino Uno ([README.md:36-49](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/README.md#L36-L49)) | |
| Multi-intersection | Explicitly not supported: "Only single intersection implemented" ([README.md:71-73](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/README.md#L71-L73)) | |
| Pedestrians | Not mentioned anywhere | `grep -i pedestrian` → no hits |

### 1.2 What the "AI" / decision logic does

[`signal_controller/README.md:19-34`](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/signal_controller/README.md#L19-L34) shows the whole algorithm:

```python
min_green = 10; max_green = 40; threshold = 15
green = min_green if n < threshold else min(max_green, min_green + (n - threshold) * 2)
yellow = 3; red = 10
```

- It takes one scalar count and returns one green time. There are no phases, no conflicting movements, no per-approach decision, no queue or pressure model and no learning.
- Red is a constant 10 s regardless of what the other approaches are doing. There is no all-red clearance and no pedestrian interval.
- The "23% reduction in average waiting time" ([README.md:25](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/README.md#L25), [:79-83](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/README.md#L79-L83)) cannot be reproduced. The repo has no data, scenario, script or method. **Unverified.**

### 1.3 Vision pipeline

[`vehicle_detection/README.md:26-47`](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/vehicle_detection/README.md#L26-L47) does the following:

1. Grayscale the frame.
2. Apply a Gaussian blur.
3. Apply a fixed binary threshold at 127, which the code comments call "background subtraction" although it is not.
4. Run `findContours` with `RETR_TREE`.
5. Report `vehicle_count = len(contours)`.

- **No model is used.** The prose ([:9-14](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/vehicle_detection/README.md#L9-L14)) mentions background subtraction and a counting line, but the snippet has neither.
- `RETR_TREE` on a thresholded street scene returns nested contours for lane markings, shadows, windows and so on. The number it gives is not a vehicle count.
- It doesn't distinguish classes and doesn't detect pedestrians.
- The code fence is never closed, and the "send to controller" step is a comment placeholder.

### 1.4 Arduino module

[`arduino_code/README.md:27-58`](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/arduino_code/README.md#L27-L58) has these problems:

- It reads a serial line but ignores it. Timings are hard-coded (`int g = 15; // Placeholder for parsed value`).
- It drives one signal head with blocking `delay()` calls.
- It has no conflict monitor and no fail-safe flash mode.

### 1.5 Code quality

There is nothing to assess. It is a portfolio README describing a 6-person student project ([README.md:6](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/README.md#L6), [:97-109](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/README.md#L97-L109)). The actual implementation was never published.

## 2. Wishlist against the repo

| # | Wishlist item | Repo | Notes |
|---|---|---|---|
| 1 | Simulation-first; controller doesn't care where counts come from | **Missing** | No simulator. The README describes a detection → controller → Arduino split ([README.md:45-49](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/README.md#L45-L49)) and the controller input is "via file, API, or serial" ([signal_controller/README.md:11](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/signal_controller/README.md#L11)). That is a *partial idea*, not an implementation. |
| 2 | Python vision service publishing counts per approach / per crosswalk | **Partial (idea only)** | The "count per lane (int)" output idea ([vehicle_detection/README.md:21](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/vehicle_detection/README.md#L21)) is right. The method (contour count) is unusable, and there are no pedestrians and no YOLO. |
| 3 | Max-pressure baseline, RL switchable | **Missing** | A threshold formula only |
| 4 | Safety Guard: min green, yellow, all-red, ped walk + flashing don't-walk, ped max wait 90 s, vehicle soft cap 120 s / hard cap 180 s | **Partial (trivial)** | Has `min_green=10`, `max_green=40` and `yellow=3` constants. No all-red, no pedestrian intervals, no wait caps, and no separation between the decision and the guard. |
| 5 | Pedestrian signals first-class | **Missing** | Not mentioned |
| 6 | Neighbour coordination / spillback awareness | **Missing** | Explicitly out of scope ([README.md:71-73](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/README.md#L71-L73)) |
| 7 | React + Vite UI, MapLibre/OSM corridor map, schematic detail panel | **Missing** | Listed as a future enhancement |

## 3. The alternatives, checked against primary sources

### 3.1 Eclipse SUMO

The docs below are read from `eclipse-sumo/sumo` `main` at `docs/web/docs/…` on 2026-11-23. The latest tag is `v1_28_0`.

**License.**
- SUMO is EPL-2.0 (repo `LICENSE`, header "Eclipse Public License - v 2.0", and `README.md`: "SUMO is licensed under the Eclipse Public License Version 2").
- `Libraries_Licenses.md:15-18` notes that some parts are dual-licensed or licensed GPL-2.0+.
- EPL-2.0 is weak copyleft. It is compatible with keeping your own controller and UI code under any license, as long as you don't modify SUMO itself. This is an interpretation, not legal advice.

**Controlling signals from Python (TraCI / libsumo).**
- `TraCI/Change_Traffic_Lights_State.md:20-24` lists these calls:
  - `setRedYellowGreenState` sets the full per-link state string, using the characters `rRgGyYoO`. After this call the program becomes "online" and SUMO stops advancing it.
  - `setPhase`, `setProgram` and `setPhaseDuration` change the phase, the program, or the remaining duration.
  - `setProgramLogic` installs a complete program.
- `Simulation/Traffic_Lights.md:1100-1135` describes two control patterns:
  - **Long green phases plus `setPhase`:** green phases are given long durations and the script calls `setPhase` to jump into the yellow phase. SUMO then handles yellow and all-red itself.
  - **`setRedYellowGreenState`:** "the script must handle all phases and transitions".
  - For a separate Safety Guard, the second pattern is the better fit. The guard is then the single component that writes the state string, and it owns yellow and all-red timing. This is an inference from the documented behaviour.
- `Libsumo.md:24-39` documents libsumo, which runs SUMO in-process and speeds up RL training. Its limitations:
  - sumo-gui is not supported on Windows and is experimental elsewhere.
  - libsumo can't be used to connect multiple clients.
  - `libtraci` is the API-compatible alternative that avoids these limits.
- sumo-rl's README claims roughly an 8x speed-up from libsumo (`sumo-rl/README.md:47-51`). That figure is the project's own claim and was not benchmarked here.

**Signal state characters.**
- `Simulation/Traffic_Lights.md:225-235` lists `r y g G s u o O`, where `o` means "off – blinking".
- **There is no dedicated pedestrian "flashing don't-walk" state.** Your Safety Guard and UI have to model that interval. In SUMO it would be the crossing link held at `r` while vehicles are still red, with your UI rendering it as flashing. This is an inference; no SUMO page states it.

**Pedestrians and pedestrian signals.**
- *Network elements.* Crossings are special lanes of type `crossing` and walking areas are of type `walkingarea` (`Simulation/Pedestrians.md:25-29`). A street can be crossed "at a traffic light" (`:143`). Crossings can be guessed with `--crossings.guess` (`:156-166`) or imported from OSM with `--osm.sidewalks --osm.crossings` (`:204`; `Networks/Import/OpenStreetMap.md:631-633`).
- *Signal links.* "Pedestrian crossings are always assigned at the very end" of a traffic light's link-index list (`Simulation/Traffic_Lights.md:255-257`). Crossings are therefore ordinary signal links that your controller sets in the same state string as the vehicle movements. That makes pedestrians first-class in the control model.
- *Detecting waiting pedestrians.*
  - E1, E2 and E3 detectors accept `detectPersons="walk"` (`Simulation/Pedestrians.md:453-462`).
  - The actuated-signal expression language has `p:TLSINDEX`, "the number of persons that are on a waiting area and intending to cross the pedestrian crossing with the given tls link index" (`Simulation/Traffic_Lights.md:539`). That is exactly the "pedestrians waiting per crosswalk" signal you need. It is exposed inside SUMO's custom-switching-rules language. How to read it from TraCI was **not verified**. A workaround is to read person IDs on the walking area and filter by next edge, or to use person `getWaitingTime` (`TraCI/Person_Value_Retrieval.md:45`).
- *Pedestrian models.* `striping` is the default interacting model and `jupedsim` is also available (`Simulation/Pedestrians.md:246-336`). On crossings, "the time to register as jammed is reduced to 10s" (`:333`).

**Queue detectors (E2, lane area).**
- They are "tailored for measuring queues of standing/jammed vehicles" and have `timeThreshold`, `speedThreshold` and `jamThreshold` settings (`Simulation/Output/Lanearea_Detectors_(E2).md:13-14, 82-84`).
- TraCI exposes, per step (`TraCI/Lane_Area_Detector_Value_Retrieval.md:38-40`):
  - the halting vehicles number
  - `getJamLengthVehicle`
  - `getJamLengthMeters`
- One E2 per approach (or per lane group) is the simulated equivalent of "vehicle queue per approach" from a camera. An E2 on the *outgoing* link gives the downstream queue that max-pressure and spillback checks need.

**OSM import.**
- The recommended netconvert options include `--junctions.join --tls.guess-signals --tls.discard-simple --tls.join --tls.default-type actuated` (`Networks/Import/OpenStreetMap.md:49-63`).
- `--tls.guess-signals` interprets OSM's signal nodes placed upstream of junctions. By default a junction counts as signalised only if every incoming arm has a signal within 25 m (`:310-321`).
- osmWebWizard builds a scenario from a map selection. With the "Pedestrians" box checked it adds sidewalks and crossings (`Tutorials/OSMWebWizard.md:63`) and generates random demand (`:75-93`).
- Expect manual cleanup in netedit for a real corridor. The docs have a whole "Debugging missing traffic lights" section (`Networks/Import/OpenStreetMap.md:352-389`).

**Built-in controllers you can compare against.**
- Static, `actuated` (gap-based), `delay_based` and `NEMA` (`Simulation/Traffic_Lights.md:300-808`).
- Actuated controllers support phase skipping with a pedestrian bonus: a crossing with an approaching pedestrian adds "a large amount of bonus priority" to its phase (`:470-476`).
- These are useful as a baseline ladder: fixed-time, then actuated, then max-pressure, then RL.

### 3.2 Max-pressure control (Varaiya 2013)

**Citation.** P. Varaiya, "Max pressure control of a network of signalized intersections", *Transportation Research Part C* 36 (2013) 177–195, doi:10.1016/j.trc.2013.08.014 (metadata from Crossref).

**Access.** ScienceDirect returned 403 and the Springer chapter needs a login, so **the paper's own text was not read**. The claims below come from a paper Varaiya co-authored and from a peer paper that summarises it:

- Kouvelas, Lioris, Fayazi, Varaiya, *Max-pressure Controller for Stabilizing the Queues in Signalized Arterial Networks*, TRB 2014 preprint (PDF hosted by Berkeley Connected Corridors).
- Gregoire et al., *Capacity-aware back-pressure traffic signal control*, arXiv:1309.6484v3, which was submitted to IEEE TCNS.

**What it is and what it guarantees.**
- It is a "local feedback controller … applied intersection-by-intersection and uses only the adjacent measurements of queue lengths" (Kouvelas et al., Introduction).
- It "does not require any knowledge of the mean current or future demands", it "stabilizes the network if the demand is within certain limits, thus it maximizes network throughput", but "it does require knowledge of mean turn ratios and saturation rates". An adaptive version that measures those quantities is stated to perform the same (Kouvelas et al., "Decentralized feedback control").
- Gregoire et al. describe it as "proved to be stability-optimal under infinite capacities, i.e., the queuing network is stabilized for all arrival rates that can be stably handled considering all control policies". They also say it is distributed over junctions with O(1) complexity per junction.

**Uses downstream queues.**
- A link's pressure is "the difference between the upstream and downstream queue lengths", weighted by saturation rate (Kouvelas et al., pressure definition).
- This is why max-pressure is a good fit for your spillback requirement: a full downstream link lowers the pressure of movements feeding it.

**Known limitations relevant to you.**
1. **Infinite or point-queue storage assumption.**
   - Gregoire et al.'s abstract says the stability results assume "infinite queues capacities". Under finite capacities back-pressure shows "non work-conservation and congestion propagation", and they prove that it is "not work-conserving in the general case" (Theorem 1).
   - Their fix normalises pressure by link capacity, so that full queues exert the maximum pressure.
   - Kouvelas et al. also give a storage-capacity-normalised variant (their eq. using $x_{z,\max}$).
   - **Implication:** implement capacity-normalised pressure *and* keep an explicit "downstream jammed → don't release" rule in the Safety Guard. The plain formula does not stop spillback on its own.
2. **Turn ratios and saturation flows are needed.** In simulation, read them from SUMO routes and lane capacities. With cameras they must be estimated.
3. **Phase order is not fixed.** The original formulation can choose any stage in any order. Later "cycle-based" variants add a fixed cycle because drivers expect predictable sequences. This came from a search-result summary (Anderson et al.) and is **unverified** against the source. Your Safety Guard's min green and max-wait caps bound this anyway.
4. **Pedestrians are not part of the original model.** Pedestrian service must be added, either through a pedestrian-pressure term or through the guard's hard 90 s cap. This is an inference: neither source models pedestrians.

### 3.3 RL frameworks

| Framework | License | Activity | Pedestrians | Notes |
|---|---|---|---|---|
| **sumo-rl** (LucasAlegre) | MIT (`gh api`; `pyproject.toml:11`) | Last push 2026-03-08, last release v1.4.5 (2024-05-07), about 1.1k stars | **No.** The code never reads persons, crossings or pedestrian state. | Gymnasium single-agent plus PettingZoo multi-agent (`README.md:19-24`). The observation is `[phase_one_hot, min_green, lane_density…, lane_queue…]` (`sumo_rl/environment/traffic_signal.py:29`). Its constructor already has `min_green`, `max_green`, `yellow_time` and `enforce_max_green` (`:48-83`). **It overwrites the junction's program.** It derives green phases and builds yellow transitions itself, then calls `setProgramLogic` and `setRedYellowGreenState` (`:128-161`). There is **no all-red phase**, and a crossing link going G→r gets `y`. A built-in `pressure` reward exists (`:282-286`, out-lane minus in-lane vehicle counts). |
| **RESCO** (Pi-Star-Lab) | **GPL-3.0** | v1.0 released 2025-10-28, last push 2025-12-11 | No pedestrian code found (`grep` for person/pedestrian in `*.py` returned nothing) | NeurIPS 2021 Datasets & Benchmarks track. It ships real-world SUMO scenarios (Cologne, Ingolstadt, Salt Lake City) and static baselines "Fixed Time, Max Pressure, and Max Wave" (`README.rst:20-30`; `agents/static/maxpressure.py`), plus IDQN, MPLight, FMA2C and others. Good for benchmarking. GPL-3.0 means you shouldn't copy its code into a project you might license differently. |
| **CityFlow** | Apache-2.0 | Last substantive commit 2020-12-04 (a single file was added 2025-08-19); 47 open issues | **No** (no "pedestrian" in source or docs) | A separate, faster simulator, but no pedestrians and effectively unmaintained. It **doesn't fit** your "pedestrians first-class" requirement. |

**Recommendation for RL.**
- Use sumo-rl's env as a *reference* or starting point, or write a thin Gymnasium env of your own over the same TraCI calls.
- Make the policy choose a *requested next phase*. The Safety Guard then accepts it, delays it or overrides it.
- Never let the RL env call `setRedYellowGreenState` directly. Otherwise your yellow, all-red and pedestrian clearance rules can be bypassed.
- Use RESCO's scenarios and baselines for comparison only.

### 3.4 Ultralytics YOLO

**License.** Ultralytics is AGPL-3.0, with an "Ultralytics Enterprise License" for business products, internal tools and production deployments "bypassing the open-source requirements of AGPL-3.0" (`ultralytics/README.md:276-281`; also `:33`). AGPL-3.0 §13 ("Remote Network Interaction", `LICENSE:540-548`) says that if you *modify* the program, users interacting with it over a network must be offered the Corresponding Source. In practice:
- An open-source research or student project can use it freely under AGPL.
- A city or commercial deployment should budget for the Enterprise License, or keep everything that links Ultralytics open under AGPL.
- The weights are covered too, according to Ultralytics' licensing page. That page was **not opened; unverified**.

**Mitigation.** Keep the vision service a separate process that publishes only counts, such as `{approach_id: queue, crosswalk_id: waiting}`, over MQTT, WebSocket or Redis. Then the detector (YOLO, RT-DETR under Apache-2.0, or a commercial edge device) can be swapped without touching the controller. Whether a separate process avoids AGPL obligations for the rest of the system is a legal question. **Not answered here.**

**Features that match the wishlist.**
- **`RegionCounter`** takes named polygon zones, tracks objects, and returns `region_counts` (name → count) every frame. "Counts restart every frame … current occupancy" (`docs/en/guides/region-counting.md:126-130`). That maps directly to "vehicles queued in the approach zone" and "pedestrians in the crosswalk waiting area".
- **`ObjectCounter`** counts objects crossing a line or region, with a `classes=[…]` filter (`docs/en/guides/object-counting.md:42-84`). With the COCO pretrained model, class 0 is person and class 2 is car (`:84`).
- **`QueueManager`** is also documented for queue length (`docs/en/guides/queue-management.md`).
- The current model family in the docs is YOLO26 (repo README; latest release v8.4.216, 2026-11-20).

### 3.5 OSM coverage of Peace Avenue (Ulaanbaatar)

**Not verified.** An Overpass query for `highway=traffic_signals` and `crossing=traffic_signals` within 25–40 m of ways with `name:en~"Peace Ave"` returned "502 … server is currently at capacity" from overpass-api.de on two attempts. The query against the overpass.kumi.systems mirror timed out after 120 s. Run the query below in overpass-turbo before committing to the corridor:

```
[out:json][timeout:60];
way["highway"]["name:en"~"Peace Ave",i](47.88,106.80,47.94,107.00)->.w;
node(around.w:25)["highway"="traffic_signals"];out;
node(around.w:40)["highway"="crossing"]["crossing"="traffic_signals"];out count;
```

Whatever the result, plan on hand-checking each of the 6 junctions in netedit. SUMO's own docs devote a section to missing or extra signals after OSM import (`Networks/Import/OpenStreetMap.md:352-389`).

## 4. Recommendation

**Start from scratch, on SUMO + your own Python controller stack + Ultralytics (or another detector) + React/Vite/MapLibre.** The reasons, item by item:

1. **Simulation-first with swappable counts.** Define one `CountsSource` interface, e.g. `{approach_id: queue_veh, crosswalk_id: peds_waiting, link_id: downstream_queue}`, with two implementations:
   - `SumoCounts`, built from E2 jam lengths and pedestrian waiting-area counts
   - `CameraCounts`, fed by YOLO region counts

   The controller only ever sees the interface. The repo has no such seam, and SUMO provides one side of it directly.
2. **Vision only publishes counts.** Use `RegionCounter` with named zones per approach and per crosswalk (§3.4). Don't use contour counting (§1.3).
3. **Max-pressure baseline, then RL.** Put both behind a `Controller.decide(counts, state) -> requested_phase` interface.
   - Use capacity-normalised pressure, since plain max-pressure assumes infinite storage (§3.2).
   - Write a thin Gymnasium env, or adapt sumo-rl, where the action is "requested phase" and not a raw state string (§3.3).
4. **Safety Guard is the only writer of signal state.** Own the full `setRedYellowGreenState` string and enforce:
   - min green
   - yellow
   - all-red
   - walk, then flashing don't-walk (crossing `r`, rendered as flashing in the UI)
   - ped max wait 90 s (hard)
   - vehicle soft cap 120 s, extendable when downstream is jammed, and hard cap 180 s

   SUMO has no flashing-ped state, so this logic is yours by necessity (§3.1).
5. **Pedestrians first-class.** SUMO crossings are signal links at the end of the TLS index list, with person detectors and waiting-area counts (§3.1).
6. **Neighbour coordination and spillback.**
   - Max-pressure's downstream term could give this between adjacent intersections if the downstream link were modelled with an E2 detector. As built, the Controller reads only its own exit lanes and not its Neighbours.
   - Add an explicit guard rule: no green into a link whose downstream jam exceeds X% of storage.
   - Capacity-aware pressure handles the finite-storage case (§3.2).
7. **Web client.** Nothing to reuse anywhere in this research. Build it fresh with React + Vite + MapLibre GL over OSM tiles, with junction positions taken from the SUMO net (`sumolib` gives lon/lat). MapLibre and sumolib were not researched here.

### Worth borrowing from the repo

- **One idea only:** split detection, decision and actuation into separate modules with a plain-data interface between them ([README.md:45-49](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/README.md#L45-L49)), with the vision output as a per-lane integer ([vehicle_detection/README.md:21](https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System/blob/1005dae/vehicle_detection/README.md#L21)).
- **No code.** There is none, and the repo has no license that would allow copying the snippets anyway.

## 5. Unverified items

- The repo's claimed 23% wait reduction: no data or method is published.
- Varaiya 2013's exact wording. The paper is paywalled and was not read; its claims are sourced from a co-authored TRB preprint and from Gregoire et al.
- Cycle-based max-pressure variants (Anderson et al.): known only from a search summary.
- Reading SUMO's `p:TLSINDEX` waiting-pedestrian count via TraCI.
- Ultralytics weights licensing details and whether process separation limits AGPL scope.
- OSM signal and crossing coverage on Peace Avenue (Overpass unavailable).
- sumo-rl's "~8x" libsumo speed-up is the project's own figure.

## Sources

- Repo: https://github.com/Srikeerthiraja/Smart-Traffic-Light-Control-System (commit `1005dae`; metadata via `gh api repos/Srikeerthiraja/Smart-Traffic-Light-Control-System`)
- SUMO docs (source Markdown, `main`, 2026-11-23): https://github.com/eclipse-sumo/sumo/tree/main/docs/web/docs (rendered at https://sumo.dlr.de/docs/)
  - `TraCI/Change_Traffic_Lights_State.md`
  - `Simulation/Traffic_Lights.md`
  - `Simulation/Pedestrians.md`
  - `Libsumo.md`
  - `Simulation/Output/Lanearea_Detectors_(E2).md`
  - `TraCI/Lane_Area_Detector_Value_Retrieval.md`
  - `TraCI/Person_Value_Retrieval.md`
  - `Networks/Import/OpenStreetMap.md`
  - `Tutorials/OSMWebWizard.md`
  - `Libraries_Licenses.md`
- SUMO license: https://github.com/eclipse-sumo/sumo/blob/main/LICENSE
- Varaiya 2013, TRC 36:177–195, https://doi.org/10.1016/j.trc.2013.08.014 (metadata via Crossref; full text not accessed)
- Kouvelas, Lioris, Fayazi, Varaiya, TRB 2014 preprint: https://connected-corridors.berkeley.edu/sites/default/files/Max-Pressure%20Controller%20for%20Stabilizing%20Queues%20in%20Signalized%20Arterial%20Networks.pdf
- Gregoire et al., Capacity-aware back-pressure traffic signal control: https://arxiv.org/abs/1309.6484
- sumo-rl: https://github.com/LucasAlegre/sumo-rl (`sumo_rl/environment/traffic_signal.py`, `README.md`, `pyproject.toml`)
- RESCO: https://github.com/Pi-Star-Lab/RESCO (`README.rst`, `resco_benchmark/agents/static/maxpressure.py`); paper: https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/f0935e4cd5920aa6c7c996a5ee53a70f-Abstract-round1.html
- CityFlow: https://github.com/cityflow-project/CityFlow
- Ultralytics: https://github.com/ultralytics/ultralytics (`README.md`, `LICENSE`, `docs/en/guides/region-counting.md`, `object-counting.md`, `queue-management.md`)
