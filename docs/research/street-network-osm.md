# Street network (Ulaanbaatar): OSM signals and data quality for the 15-site Network

Sources: the committed extract `sim/data/corridor.osm.xml` (Overpass, OSM base timestamp `2026-11-24T03:09:47Z`, fetched by
`sim/scripts/fetch_osm.sh`), the Signal Site definitions in `sim/corridor_sim/config.py` and the built `sim/data/sites.json`.
Facts marked "survey" come from a wider Overpass query (bbox 47.905,106.895,47.930,106.935, base `2026-11-24T02:28:56Z`),
kept only in a temporary scratchpad. The earlier survey of Peace Avenue is [peace-avenue-corridor-osm.md](peace-avenue-corridor-osm.md).

- bbox (south, west, north, east): **47.9115, 106.9030, 47.9245, 106.9280**
- The extract holds 4,288 nodes and 907 ways. Ways are kept whole, so some reach outside the bbox. 33 nodes are
  `highway=traffic_signals`; 49 are signalised crossings (`crossing=traffic_signals` or `crossing:signals=yes`).
- The built network has 23 traffic lights: 15 belong to the Signal Sites, 8 run fixed programs.

## The 15 sites

"Signal nodes" and "signalised crossings" are nodes within 60 m of the coordinates in `config.py`. Crossings count only when
they lie on a road. Approaches and Crosswalks are what the build resolved; `netconvert` guesses Crosswalks where OSM has none.

| id | lat, lon (`config.py`) | Signal nodes | Signalised crossings | Approaches | Crosswalks |
|---|---|---|---|---|---|
| ikh-delguur (Mid-block Crossing) | 47.91618, 106.90638 | 8995081807 | 2 | 2 | 2 |
| baga-toiruu-west | 47.91666, 106.91193 | 57677289, 8420678194 | 4 | 3 | 4 |
| tuv-shuudan | 47.91673, 106.91625 | 1270395917, 1270396026, 2513512815 | 6 | 4 | 5 |
| ikh-surguuli | 47.91723, 106.91958 | 1054352912, 3911981611 | 8 | 4 | 4 |
| baga-toiruu-east | 47.91775, 106.92394 | 57677290, 1054352964 | 0 | 3 | 3 |
| juulchny-baga-toiruu | 47.92003, 106.91138 | 305119956 | 0 | 4 | 4 |
| amar-ikh-surguuli | 47.91993, 106.91888 | 280742669 | 1 | 3 | 3 |
| sambuu-baga-toiruu-west | 47.92213, 106.91095 | 6236425319 | 1 | 4 | 3 |
| sambuu-sukhbaatar | 47.92208, 106.91555 | 2496907426 | 1 | 4 | 4 |
| sambuu-ikh-surguuli | 47.92222, 106.91844 | 3913061711 | 0 | 4 | 4 |
| sambuu-baga-toiruu-east | 47.92257, 106.92291 | 280742383 | 5 | 4 | 3 |
| juulchny-baruun-selbe | 47.91971, 106.90641 | none | 2 | 4 | 4 |
| chinggis-genden | 47.91319, 106.91516 | 480748221, 8995108307 | 1 | 4 | 5 |
| olympic-genden | 47.91408, 106.92183 | 281051608 | 3 | 4 | 4 |
| seoul-tserendorj | 47.91375, 106.90689 | 281052570, 395232771 | 4 | 4 | 6 |

- `juulchny-baruun-selbe` has no signal node, only signalised crossings (9763736527, 14026600889) about 11 m either side of
  the junction. It is controlled on that evidence.
- `chinggis-genden` includes the pedestrian signal 8995108307 (`traffic_signals=pedestrian_crossing`), about 51 m north of its
  junction. The two junctions share one traffic light.
- Three junctions have no signal node and stay unsignalised: Seoul / Chinggis (node 1241687100, nearest signal 94 m),
  Sükhbaatar / Juulchny (641468227, 205 m) and Amar / Baga Toiruu east (3892885154, 255 m).

## Junctions that need joins

At six sites `netconvert` leaves nodes of one junction apart, with stubs shorter than a car between them, so the build joins
the OSM nodes listed as `join_nodes`:

| Site | Nodes | OSM turn lanes |
|---|---|---|
| ikh-delguur | 3 | kept |
| tuv-shuudan | 9 | discarded |
| ikh-surguuli | 4 | kept |
| sambuu-sukhbaatar | 4 | discarded |
| sambuu-ikh-surguuli | 3 | discarded |
| juulchny-baruun-selbe | 2 | discarded |

Turn lanes are discarded where joining left whole lanes that can do nothing but a U-turn.

## Data quality for SUMO import

Shares are by length of ways inside the bbox, from the committed extract (a way segment counts if its midpoint is inside).
"Major" is trunk to tertiary with links, 20.4 km; "minor" is unclassified, residential and living street, 17.1 km.

| | Major | Minor |
|---|---|---|
| `lanes` | 100% | 59% |
| `maxspeed` | 90% | 3% |
| `turn:lanes*` | 12% | 0% |
| any `sidewalk*` | 60% | 9% |
| `name` | 93% | 18% |

- **Direction split.** 61% of major road length is two-way with two or more lanes. For 38% (about six tenths of it) there is
  no `lanes:forward` or `lanes:backward`, so the split between directions is a guess. That includes all of Juulchny, Genden,
  Amar and Usny streets, 80% of Chinggis Ave, 72% of Seoul St and 64% of Olympic St. Two ways have an odd total with no
  split: 241658524 (Ambassador St, 3 lanes) and 1537784426 (Seoul St, 5 lanes).
- **Speed.** Tserendorj St and Usny St have no `maxspeed`.
- **Sidewalks.** OSM maps most sidewalks as separate footways. The build leaves those out and guesses sidewalks on the roads.
- **Turn restrictions.** The survey found 45 turn restriction relations with a via node in the bbox (25 `no_left_turn`,
  15 `no_u_turn`, 3 `no_right_turn`, 2 `no_straight_on`). `fetch_osm.sh` asks for ways only, so the extract holds no
  relations and the network does not know these restrictions.
- **Names.** Spellings differ by case or letter for one street (`Бага Тойруу` / `Бага тойруу`, `Баруун сэлбийн` /
  `Баруун Сэлбийн`, `Энх тайвны` / `Энх тайваны`). The build matches names without case and has one alias.
- **Unnamed continuations.** 24 major ways have no name. Seven ways that continue a named street get its name by way id in
  `build.py`: 863783234 (Peace Ave), 81528712 (Baga Toiruu), 81528723 (Sambuu St), 303599291 (Beijing St), 34409213 and
  512970905 (Baruun Selbe St), 708458504 (Usny St).

## Not verified

- Whether OSM signals and crossings match the ground, including the sites and the unsignalised junctions above.
- Real signal timings and Phases. The Phases are derived from the road geometry.
- Crosswalks guessed where OSM has no signalised crossing: all of them at `baga-toiruu-east`, `juulchny-baga-toiruu` and
  `sambuu-ikh-surguuli`.
- Lane splits on the two-way streets listed above, and lane use where turn lanes were discarded.
- Mongolian site names and the English transliterations.
- Demand. Volumes are generated from street class and direction, not measured.
