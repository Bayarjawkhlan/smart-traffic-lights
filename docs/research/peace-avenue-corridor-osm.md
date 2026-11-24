# Peace Avenue corridor (Ulaanbaatar): OSM signals and data quality for SUMO

This survey chose the original five sites. The current 15-site Network is in [street-network-osm.md](street-network-osm.md).

Source: Overpass API (overpass-api.de), OSM base timestamp `2026-11-23T15:25:49Z`. Raw JSON and scripts were in a temporary scratchpad, not kept
(`raw/area_highways.json` is every `highway=*` way in bbox 47.908,106.875,47.925,106.96 plus their tagged nodes).
The query `scripts/q_all.overpassql` was in that scratchpad too.

In OSM the avenue is `name=Энх тайваны өргөн чөлөө` (a few eastern ways use the variant spelling `Энх тайвны өргөн чөлөө`),
`name:en=Peace Avenue`, `highway=trunk`, `ref=A0501`, `int_ref=AH3`. The query `Энхтайван*` (no space) finds only the
Peace Bridge (way 27850188). Sükhbaatar Square is relation 15638347 (centre 47.91881, 106.91763). Peace Avenue runs along
its south side at about lat 47.9168.

## Signalised locations, west to east

Every carriageway is mapped separately (a dual carriageway of oneway ways), so each junction has 2 to 4 `highway=traffic_signals`
nodes: one where each carriageway crosses each cross-street carriageway. "Gap" is the distance between centroids, measured
along the avenue. "x from square" is the east-west offset from the square's centre.

| # | Cross street(s) (OSM `name`; English) | Centroid lat, lon | Gap | x from square | `highway=traffic_signals` nodes | Signalised ped crossings (`crossing=traffic_signals` / `crossing:signals=yes`) |
|---|---|---|---|---|---|---|
| 0a | Нарны зам (Narny Road) | 47.91403, 106.87143 | n/a | −3.4 km | 305772130, 947444072 | 9093958244/45/46 (`crossing:signals=yes` on footway 387138803) |
| 0b | Х.Чингүнжавын гудамж (N) / П.Жасрайн гудамж (S) | 47.91433, 106.87678 | 400 m | −3.0 km | 2500456403, 4205711089 | 9093958315/16, 9093958291/92 on PA; 9093958287, 8010992210 on cross streets |
| 1 | С.Амарсанаагийн гудамж (S. Amarsanaa St); node named «Дөрвөн зам» (Four Roads) | 47.91494, 106.89120 | 1077 m | −1.97 km | 1054352981, 200777167, 1054353105, 947444066 | none tagged |
| 2 | Их тойруу (Ikh Toiruu, Big Ring Rd) / Үндсэн хуулийн гудамж (Constitution St) | 47.91521, 106.89475 | 266 m | −1.71 km | 305119842, 8047231656, 1055337678, 1055337687 | none tagged |
| 3 | Mid-block ped signal ~30 m E of Сайн ноён хан Намнансүрэнгийн гудамж (Peace Tower) | 47.91581, 106.90242 | 576 m | −1.13 km | 8838211540 (eastbound only) | 1247498089 (EB), 8047231661 (WB) |
| 4 | Mid-block ped signal at the State Department Store (Улсын их дэлгүүр, way 108195310), between the two Хичээнгүй сайд Цэрэндоржийн гудамж junctions | 47.91615, 106.90635 | 295 m | −0.84 km | 8995081807 (eastbound only) | 8995081814 (WB), 8995081815 (EB) |
| 5 | Бага тойруу (Baga Toiruu, Small Ring, west arm) | 47.91666, 106.91199 | 424 m | −0.42 km | 8420678194, 57677289 | 8047231641, 1055337506 on PA; 8420678193, 2942888033 on cross street |
| 6 | Чингисийн өргөн чөлөө (Chinggis Ave, S) / Д.Сүхбаатарын гудамж (D. Sükhbaatar St, N); SW corner of the square, Central Post Office (way 154431812) | 47.91677, 106.91625 | 318 m | −0.10 km | 1270396026, 2513512815; also 1270395917 on trunk_link 111527413 | 8420678184/86, 8420520244, 1245746484 on PA; 8420678188, 8420542535 on cross streets |
| 7 | Их сургуулийн гудамж (Ikh Surguuli / University St, N) / Олимпийн гудамж (Olympic St, S) | 47.91716, 106.91980 | 268 m | +0.16 km | 1054352912, 3911981611 | 8420542689/99, 8995093057/58 on PA; 8420542692/93, 8995093054, 14002450297, 3911981614 nearby |
| 8 | Бага тойруу (Baga Toiruu, east arm) | 47.91775, 106.92394 | 315 m | +0.47 km | 1054352964, 57677290 | none; the PA crossings 8420542697/98 are tagged `crossing=marked` |
| 9 | Их тойруу (Ikh Toiruu, east arm) | 47.91897, 106.94323 | 1445 m | +1.91 km | 804743254, 804743361, 804743279, 318126753 | 1477522703/698/704/683 on PA; 10 more on links and cross streets |

Rows 0a and 0b lie outside the ±2 km window. They are listed only to show where the next signals to the west are.

### Junctions on the avenue with no signal in OSM (unverified: they may be signalised on the ground)

- С.Чоймболын гудамж / Партизаны гудамж at 106.8986 (nodes 1054352960, 305120738). The PA crossings there (4290727918–23)
  are plain `highway=crossing` with no `crossing=*`.
- Хичээнгүй сайд Цэрэндоржийн гудамж at 106.9060 and 106.9068 (nodes 4038646299, 395217440), right beside the State Department Store ped signal.
- Сайн ноён хан Намнансүрэнгийн гудамж at 106.9020 (node 305120749).
- Токиогийн гудамж / Сангийн хорооны гудамж at 106.9353 (nodes 1054352917, 3911981332), with `crossing=marked` 9134734059/60/67/68.
  The 1.4 km between rows 8 and 9 has no signal in OSM.

## Data quality for SUMO import

Coverage is measured by length over both carriageways, 106.889–106.945, 45 ways, 7.8 km in total (`scripts/quality.py`).

- `lanes`, `oneway`, `maxspeed=60`, `surface`: 100%. `lit`: 92%. Every segment is a separately mapped oneway carriageway,
  usually with 3 lanes and 4–5 at intersection approaches.
- `turn:lanes`: 13%, on the approaches to junctions 2, 5, 6 and 7 (e.g. way 1537180317 `left|left|through|through|right`).
  `bus:lanes`: 31%, with the curb lane `designated` (e.g. ways 376274881, 1537180322). `change:lanes` appears on several ways.
- Cross streets at the core junctions also carry lanes, and in places directional lanes and turn lanes: Д.Сүхбаатар 111314589
  (`lanes:forward=4`, `turn:lanes:forward`), Олимп 1537180297, Их сургууль 1537180299, Бага тойруу 441138039/1057541826/362407168/1528135708.
- Sidewalks: 96% of PA length has a `sidewalk*` tag. That is overwhelmingly `sidewalk:right=separate` + `sidewalk:left=no`
  (22 ways) or `sidewalk:both=separate` (13 ways). The sidewalks are separate footway ways: 376 footways in the strip, about
  21.8 km in total, of which 47 are `footway=crossing` and 12 `footway=sidewalk`. Most have no `footway=*` subtag.
- Crossings: 29 crossing nodes sit on PA carriageways, 17 of them `crossing=traffic_signals`. They are well tagged at junctions 5, 6
  and 7 and at both mid-block signals. Junctions 1, 2 and 8 have no signalised crossing nodes.
- Gaps and defects:
  - Way 863783234 (the westbound carriageway, 106.9020–106.9043, which carries ped crossing 8047231661) has no `name`.
  - Connector trunk 90810928 (`lanes=6`) at junction 6 and primary 90810926 at junction 7 are unnamed.
  - The mid-block signals (3, 4) have a `highway=traffic_signals` node on the eastbound carriageway only. On the westbound
    carriageway there is only a `crossing=traffic_signals` node.
  - Junction 2 (Big Ring west) has four trunk_link slip roads: 90876377, 90876386, 90876271 and 90876365.

### Implications for netconvert (from SUMO docs via Context7, `/eclipse-sumo/sumo`)

- Because sidewalks are mapped as separate footways, use `--osm.sidewalks --osm.crossings` and do **not** use `--sidewalks.guess`.
  With `sidewalk=separate` everywhere, guessing would add a second set of sidewalks next to the imported footways.
  The docs say `--osm.sidewalks` loads OSM sidewalk data and `--osm.crossings` loads `highway=crossing` into crossings.
  Unverified: how netconvert maps the separate footway ways onto PA edges. Inspect the result in netedit. You may need
  `--crossings.guess` as a fallback at junctions 1, 2 and 8, which have no crossing nodes.
- Every junction is a cluster of 2–4 signal nodes, so `--junctions.join --tls.join` (or `--tls.guess-signals`) is required to get
  one TLS per intersection. The SUMO-recommended OSM set is `--geometry.remove --ramps.guess --junctions.join --tls.guess-signals --tls.discard-simple --tls.join`.
- Unverified: whether netconvert creates a TLS from a node tagged only `crossing=traffic_signals`. That matters for the westbound side of rows 3 and 4.

## Recommended corridor

**Primary (5 signals, about 1.3 km, about 300 m spacing): rows 4 to 8.** It runs from the State Department Store ped signal to Бага тойруу east.
It takes in the State Department Store, Бага тойруу W, Chinggis Ave / Sükhbaatar St (Central Post Office, SW corner of
Sükhbaatar Square), Ikh Surguuli / Olympic St, and Бага тойруу E (Choijin Lama Temple 443874629 lies just south of junction 7).
It is the best-tagged part of the avenue: lanes, turn lanes and bus lanes are all mapped, and 4 of its 5 sites have signalised
crossings on PA.

- bbox (south, west, north, east): **47.9140, 106.9045, 47.9210, 106.9265**

**Extended (7 signals, about 2.2 km): rows 2 to 8.** It adds the Big Ring / Constitution St junction and the Peace Tower ped signal.
Both have weaker pedestrian data: no crossings at row 2, and the unnamed westbound segment at row 3.

- bbox (south, west, north, east): **47.9125, 106.8930, 47.9210, 106.9265**

The west edge of 106.8930 cuts between rows 1 and 2, about 130 m west of the Big Ring junction. To include row 1 (Four Roads,
8 signals in all), move the west edge to 106.8895.

Not checked: real-world signal timings, whether OSM signal and crossing tags match the ground today, and whether the
transliterated English street names (where `name:en` is absent) are the usual spellings.
