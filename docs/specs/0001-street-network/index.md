# 0001: A Network of Signal Sites beyond Peace Avenue

Date: 2026-11-24 · Status: Approved (user accepted every grill recommendation and asked to build) · Ledger: [factory.md](factory.md)

## Summary

The demo controls five Signal Sites on one street. This work replaces it with a Network of 15 Signal Sites on streets running both east-west and north-south around Sükhbaatar Square, with new demand, a retrained RL Controller, rerun experiments, and a client that can navigate more than one Corridor. Terms are in [GLOSSARY.md](../../../GLOSSARY.md).

## Decisions

1. Medium area, 15 sites (why: several streets in both directions, good OSM tagging, few junctions to hand-tune).
2. Network is the whole; Corridor is one continuous street, even where its name changes (why: the old definition no longer fits). Package and file names containing `corridor` stay.
3. The Network replaces the five-site demo (why: one set of Scenarios, results and models to maintain).
4. Demand stays generated, set by street class and direction; pedestrian density per km stays about today's (why: the name table starves unlisted streets).
5. Fix the starved Peace Avenue westbound exit and the ignored State Department Store crossing (why: both distort results).
6. Correct the Max-pressure Neighbour claim; do not add coordination (why: separate feature).
7. Retrain RL, rerun every Scenario and Controller, publish whatever wins (why: old results are invalid). Passing means Hard Caps hold, not that RL wins.
8. Chinggis/Genden and the pedestrian signal about 60 m north of it stay one site. Juulchny/Baruun Selbe is a site. Seoul/Chinggis, Sükhbaatar/Juulchny and Amar/Baga Toiruu east stay unsignalised. Other signals run fixed programs and stay grey.
9. Eight Corridors (table below). The ribbon becomes a Corridor picker plus "All sites".
10. Neighbours come from the road graph, not street names; used only in explanations.
11. The same five Scenarios; the incident stays at `ikh-surguuli` Peace Avenue eastbound, the surge at `tuv-shuudan`.
12. Record the maximum vehicle wait. A Hard Cap breach is fixed in the Safety Guard, never by relaxing a cap.
13. Performance is optimised only if AC10 misses.

## Acceptance criteria

- **AC1** Given a fresh `uv run python -m corridor_sim.build`, when `GET /api/network` is called, then it returns exactly the 15 sites below with those ids and names; the five existing ids are unchanged; every site has 1 to 3 Phases; every Approach and Crosswalk is green in at least one Phase; each site has its own TLS.
- **AC2** `GET /api/network` returns `corridors` with exactly the eight below, each with its sites in the listed order.
- **AC3** Neighbours are symmetric, never include the site itself, and every consecutive pair in a Corridor is a Neighbour pair.
- **AC4** The build exits non-zero with a message naming the site when a site has no Phase or more than 3, an Approach or Crosswalk no Phase serves, or a TLS another site already uses; and naming the Scenario when its incident does not match exactly one Approach.
- **AC5** In every Scenario's `.rou.xml`, summed flow per entry is within 2% of the volume specified for that entry (no silent loss); vehicles enter in all four directions; northbound plus southbound entries carry at least 25% of vehicle volume; the Peace Avenue westbound exit receives at least 200 vehicles/h in morning rush.
- **AC6** With the Fixed-time Controller over 3600 s, every Scenario arrives at least 85% of departed vehicles and teleports at most 2% of departed vehicles.
- **AC7** At `ikh-delguur`, waiting pedestrians on either Crosswalk raise the Max-pressure score and the RL features of the Phase serving it.
- **AC8** `data/experiments/` holds all 5 Scenarios × 3 Controllers, 3600 s, seed 42, each with `maxVehicleWait`; every run has `maxVehicleWait` ≤ 180 and `maxPedestrianWait` ≤ 90.
- **AC9** The Experiments page shows maximum vehicle wait for every Controller, in both languages; the README results table matches the JSON.
- **AC10** Morning rush at ×10 with one WebSocket client advances simulated time at ≥ 9× wall time over 60 s of wall time, and the map holds ≥ 30 fps in system Chrome at 1440×900.
- **AC11** The map shows 15 site pins. In the initial fitted view at 1440×900 and 390×844 no two visible site names overlap.
- **AC12** The ribbon has a labelled Corridor picker: the eight Corridors plus "All sites", starting on Peace Avenue. It lists the chosen Corridor west to east or north to south, with end marks to match. Choosing a site outside it on the map switches to the first Corridor containing that site, or to "All sites". Picker and sites work by keyboard.
- **AC13** No user-facing text in English or Mongolian (strings, page title and description, About, README files, API title) says the demo has five Signal Sites, is 1.3 km, or covers only Peace Avenue. Mongolian labels show Mongolian street names, English labels English ones, for every Approach and Crosswalk at all 15 sites.
- **AC14** No text claims Max-pressure coordinates with or reads its Neighbours.
- **AC15** In the incident Scenario exactly one Approach, Peace Avenue eastbound at `ikh-surguuli`, is blocked from 240 s to 1500 s and reopens.
- **AC16** Signals outside the 15 sites are drawn grey, as today.
- **AC17** If the API returns no `corridors`, the ribbon shows all sites without a picker and the page does not crash. The offline state still renders.

## Surfaces

UI: yes

| Surface | Kind | New or changed |
|---|---|---|
| `corridor_sim.build`, generated `sim/data` | CLI, data | changed |
| `GET /api/network` (`corridors`, approach `direction`) | endpoint | changed |
| `/ws` frames and `/api/experiments` (`maxVehicleWait`) | endpoint | changed |
| Live page: map, markers, ribbon | screen | changed |
| Experiments and About pages | screen | changed |

## Design

### Sites

The five existing specs keep their ids and names. Coordinates are survey centroids; tune joins in the build, not the ids.

| id | nameEn | nameMn | lat, lon |
|---|---|---|---|
| ikh-delguur, baga-toiruu-west, tuv-shuudan, ikh-surguuli, baga-toiruu-east | unchanged | unchanged | unchanged |
| juulchny-baga-toiruu | Juulchny St / Baga Toiruu West | Жуулчны гудамж / Бага тойруу (баруун) | 47.92003, 106.91138 |
| amar-ikh-surguuli | Amar St / University St | Амарын гудамж / Их сургуулийн гудамж | 47.91993, 106.91888 |
| sambuu-baga-toiruu-west | Sambuu St / Baga Toiruu West | Самбуугийн гудамж / Бага тойруу (баруун) | 47.92213, 106.91095 |
| sambuu-sukhbaatar | Sambuu St / Sükhbaatar St | Самбуугийн гудамж / Сүхбаатарын гудамж | 47.92208, 106.91555 |
| sambuu-ikh-surguuli | Sambuu St / University St | Самбуугийн гудамж / Их сургуулийн гудамж | 47.92222, 106.91844 |
| sambuu-baga-toiruu-east | Sambuu St / Baga Toiruu East | Самбуугийн гудамж / Бага тойруу (зүүн) | 47.92257, 106.92291 |
| juulchny-baruun-selbe | Juulchny St / Baruun Selbe St | Жуулчны гудамж / Баруун Сэлбийн гудамж | 47.91971, 106.90641 |
| chinggis-genden | Chinggis Ave / Genden St | Чингисийн өргөн чөлөө / Гэндэнгийн гудамж | 47.91319, 106.91516 |
| olympic-genden | Olympic St / Genden St | Олимпийн гудамж / Гэндэнгийн гудамж | 47.91408, 106.92183 |
| seoul-tserendorj | Seoul St / Tserendorj St | Сөүлийн гудамж / Цэрэндоржийн гудамж | 47.91375, 106.90689 |

All new sites are `intersection`.

### Corridors

| id | nameEn / nameMn | axis | sites in order |
|---|---|---|---|
| peace | Peace Avenue / Энх тайваны өргөн чөлөө | ew | ikh-delguur, baga-toiruu-west, tuv-shuudan, ikh-surguuli, baga-toiruu-east |
| sambuu | Sambuu St / Самбуугийн гудамж | ew | sambuu-baga-toiruu-west, sambuu-sukhbaatar, sambuu-ikh-surguuli, sambuu-baga-toiruu-east |
| juulchny | Juulchny St / Жуулчны гудамж | ew | juulchny-baruun-selbe, juulchny-baga-toiruu |
| genden | Genden St / Гэндэнгийн гудамж | ew | chinggis-genden, olympic-genden |
| baga-toiruu-w | Baga Toiruu West / Бага тойруу (баруун) | ns | sambuu-baga-toiruu-west, juulchny-baga-toiruu, baga-toiruu-west |
| sukhbaatar-chinggis | Sükhbaatar St – Chinggis Ave / Сүхбаатарын гудамж – Чингисийн өргөн чөлөө | ns | sambuu-sukhbaatar, tuv-shuudan, chinggis-genden |
| university-olympic | University St – Olympic St / Их сургуулийн гудамж – Олимпийн гудамж | ns | sambuu-ikh-surguuli, amar-ikh-surguuli, ikh-surguuli, olympic-genden |
| baga-toiruu-e | Baga Toiruu East / Бага тойруу (зүүн) | ns | sambuu-baga-toiruu-east, baga-toiruu-east |

`seoul-tserendorj` is in no Corridor.

### API contract (both sides build to this)

- `Network.corridors: { id, nameEn, nameMn, axis: "ew" | "ns", sites: string[] }[]`
- `ApproachInfo.direction: "northbound" | "eastbound" | "southbound" | "westbound"`; `label` keeps its form.
- `scenarios.json` `incident.approach` is an Approach id, resolved at build from site, street and direction.
- `Metrics.maxVehicleWait`: the longest Approach Wait Time of the run, in seconds.
- `Network.bounds` covers the site centres plus 150 m, not the whole road net.

### Build

- OSM: refetch around 47.9115,106.9030,47.9245,106.9280, widened only if a site arm would be cut shorter than 80 m. Commit the extract. Keep a cached extract rather than refetching on every build.
- Street table: one entry per named street in the net with English name and class (`arterial`, `collector`, `minor`), keyed case-insensitively. Peace, Sambuu, Chinggis and Sükhbaatar are arterial; Baga Toiruu, University, Olympic, Juulchny, Seoul, Genden and Tserendorj are collector; everything else is minor. Unnamed links that continue a named street get that street by OSM way id. English name for "Жуулчны гудамж" becomes "Juulchny St".
- Demand: each Scenario gives a volume per class and direction, for entries and for exit weights. Peace Avenue keeps today's eastbound/westbound volumes. Choose the others so AC5 and AC6 hold; record the final numbers in the build's Scenario table. Flows under 1 veh/h are redistributed to the entry's other exits.
- Pedestrians: scale `ped_period` by sidewalk length so persons per km match today's Network.
- Neighbours: for each ordered site pair, the shortest drivable path by length; they are Neighbours if it is at most 700 m in either direction and passes through no other controlled site.
- Max-pressure and RL read links by signal index; several links can share an index.
- The `MAIN_STREET` logic for Peace Avenue and `main` road flag: the flag now means class `arterial`.

### Client

- Site names are always in the DOM for assistive technology. A visible name shows for sites in the chosen Corridor; with "All sites", only for hovered, focused or selected sites. Pins always show.
- The ribbon scrolls horizontally when it does not fit instead of wrapping.
- The picker is a labelled native `select` in the ribbon; its choice is per page load.
- Language strings in EN and MN. Mongolian text is for the user to review.

## Build plan

| Slice | Does | Owns | Depends on | Done when |
|---|---|---|---|---|
| S1 Network data | area, sites, Corridors, Neighbours, demand, build checks, regenerate data | `sim/corridor_sim/build.py`, `sim/corridor_sim/config.py`, `sim/scripts/`, `sim/data/` except `experiments/` and `models/` | none | AC1, AC2, AC3, AC4, AC5 |
| S2 Runtime | link-index fix, `maxVehicleWait`, incident by Approach id, Max-pressure label, API title | `sim/corridor_sim/` except `build.py` and `config.py` | none | AC7, AC15, part of AC4, AC14 |
| S3 Client | Corridor picker, ribbon, markers, About and Experiments, strings | `client/` | S1, S2 | AC9, AC11, AC12, AC13, AC16, AC17 |
| S4 Results | train RL, run experiments, tune demand with S1's builder if AC6 fails, Guard fix with S2's if AC8 fails | `sim/data/models/`, `sim/data/experiments/` | S1, S2 | AC6, AC8 |
| S5 Docs | README files, ADR/research notes if stale, screenshots | `README.md`, `sim/README.md`, `client/README.md`, `docs/` except `docs/specs/` | S3, S4 | AC9, AC13, AC14 |

## Test plan

Test files are temporary (user rule): written to check a slice, run, then deleted before commit.

| AC | Proof |
|---|---|
| AC1 to AC5 | script over the built data and `/api/network`; deliberate bad specs for AC4 |
| AC6, AC8 | experiment JSON |
| AC7, AC15 | scripted run of the engine |
| AC10 | timed run on a spare port, plus `requestAnimationFrame` deltas in Chrome |
| AC9, AC11, AC12, AC13, AC16, AC17 | Playwright against the real client and server, screenshots at 1440×900 and 390×844 |
| AC14 | search of the repo text |

## Risk and rollback

- Results change completely, so old numbers must not be mixed with new. Rollback is a plain revert; there is no migration.
- OSM signals and names are not ground truth; Mongolian names and English strings need the user's check.
- The committed net and Scenarios grow: check the repo does not gain a file over 25 MB.
- The user's running Docker stack must not be touched.

## Out of scope

Real Max-pressure coordination, per-site RL models, vision, measured traffic data, real-world signal timings, switching between networks.

## Cross-check resolutions

The user was asleep and had asked to build, so the foreman took the recommended answer to each gap found. These are part of the spec and override anything above. **The user should read this section first.**

1. **Guard lead (safety).** `lead` depends on the site's Phase count: two switches for up to 2 Phases, three for 3. The old constant let a pedestrian reach about 99 s at a 3-Phase site. Caps are unchanged.
2. **Operator caps.** The lowest pedestrian Hard Cap an Operator can set rises from 45 s to 60 s, because 45 s is not achievable at a 3-Phase site. The `capsRange` strings say 60.
3. **Links.** `Site.links_by_index` replaces `site.links[i]` everywhere (`guard.py`, all three Controllers). `PhasePlanner` keeps every connection that shares an index.
4. **Validation.** `model.validate_sites(sites) -> list[str]` (S2) returns one message per problem: 0 or more than 3 Phases, an Approach or Crosswalk no Phase serves, a vehicle signal index no Phase makes green, a shared TLS. The planner must return at most 3 Phases or the problem is reported. S1's build calls it and exits non-zero on any message.
5. **Demand.** A volume is per entry edge, chosen by class and direction. An entry with no reachable exit fails the build unless it is listed as skipped in the build with a reason. Flows below 1 veh/h: drop the smallest exit and renormalise, repeatedly, until all flows are at least 1; keep the largest if none is. `scenarios.json` gets `entryVolumes: { [edgeId]: number }`. The 200 veh/h in AC5 is scheduled volume. AC6 also requires inserted vehicles ≥ 95% of scheduled.
6. **Names at sites.** An unnamed street may show as a localised "Side road" or "the road". `CrosswalkInfo.streets: { en, mn }[]` is added, and `ApproachInfo.streetEn`. A named street at one of the 15 sites that is missing from the street table fails the build. AC13 covers map, panel, ribbon, event log and explanation labels. "Sükhbaatar St" is used everywhere.
7. **Labels.** Marker label side alternates within the chosen Corridor. Colliding names hide by priority: selected, then Corridor order. AC11 is tested for every Corridor at both sizes, and a label outside the map area counts as not visible. The rule hiding the selected site's name goes. The secondary name line stays only on the selected site.
8. **Metric name.** The UI calls `maxVehicleWait` "Longest Approach wait", since it is an Approach's Wait Time and not one vehicle's.
9. **RL.** Trained on the final net and Guard with `train --iterations 12 --population 14 --duration 1800 --workers 6`. The model file records `network` as the sha256 of `corridor.net.xml`; experiment JSON records the same. AC8 checks both match the committed net.
10. **AC10.** S4 measures it; the fps count is drawn frames, not callbacks. S2 and S3 builders fix a miss in their own files.
11. **AC14** also covers `explain.py` (the prompt may give Neighbour state as context only, "not used in the decision"), `names.ts` and `strings.ts`. S3 owns the client parts.
12. **AC15** is proven after S1 lands.
13. **Names.** Product name: "Ulaanbaatar signal network" / "Улаанбаатарын гэрлэн дохионы сүлжээ". The API title is the English one.
14. **Neighbours.** Path length runs from the end of the site's exit edge to the start of the other site's approach edge. One direction that is clear of other controlled sites and at most 700 m is enough; the relation is then symmetric.
15. **Ribbon.** A deep-linked site switches the Corridor like a map click. "All sites" uses API order with no end marks. Picking a Corridor does not move the map. End marks are localised.
16. **Midblock.** Only `kind == "midblock"` specs get the extra crossing; `join_nodes` alone no longer implies it.
17. **Build order.** S2, then S1, then S3 with S4, then S5.
