# Factory: Signal Sites beyond Peace Avenue
spec: docs/specs/0001-street-network/index.md
branch: factory/street-network   worktree: /Users/bayarjavkhlan/Documents/projects/smart-traffic-lights-factory-street-network   base: feat/corridor-demo (local, unpushed, 9ada9d0)
ship policy: none chosen (user asleep): no push, no PR, no merge; stop at a finished local branch
stage: build
round: 0
pr:
## Log
- 2026-11-24 preflight: origin/main holds only README.md, so the user chose to stack on local feat/corridor-demo; gh is authenticated; no repo rule files. The base branch must be pushed before a PR can target it.
- 2026-11-24 grill: user chose "beyond Peace Avenue" as the meaning of "scale the lights"; facts being gathered.
- 2026-11-24 grill: code and OSM surveys done (OSM data 2026-11-24T02:28:56Z). User added: cover north-south streets as well as east-west ones. Round 1 asked.
- 2026-11-24 grill round 1 (6 decisions): Medium area (15 sites); Network/Corridor terms (GLOSSARY.md updated); the Network replaces the 5-site demo; generated demand by street importance and direction; fix the westbound exit and ignored crossing, and correct the Max-pressure Neighbour text; retrain RL, rerun all experiments, pass = safety caps hold.
- 2026-11-24 grill round 2 (10 decisions): user accepted every recommendation, said they were going to sleep and asked to write the spec and start building. Frontier empty.
- 2026-11-24 spec: written; Plan agent cross-check found 23 gaps. The user was asleep, so the foreman resolved them with the recommended answers (spec, "Cross-check resolutions"); the station 2 approval dialog was skipped on the user's instruction. Build order S2, S1, S3+S4, S5. Test files are temporary (user rule). Review diff base is feat/corridor-demo.
- 2026-11-24 build S2: runtime done; foreman withdrew resolutions 1 and 2 after S2's adversarial search contradicted them (longer lead broke the vehicle Hard Cap at low Operator caps). S2 also found that SUMO links each crossing to its signal from one kerb, so pedestrians at the other kerb were not sensed; fixed, follow-up requested.
- 2026-11-24 build S2 done: lead reverted; randomised search found no breach at default caps 90/120/180. Pre-existing, unfixed: at Operator pedestrian cap 45, 3-Phase sites breach the vehicle Hard Cap (192 s, or starvation where a Phase has no Crosswalk). Finding for the user: before this branch, far-kerb pedestrians were unsensed; 99 person-runs over 90 s across 14 of 15 committed runs (longest 315 s vs metric 71), so the README 90 s claim was false.
- 2026-11-24 build S1 built: AC1 to AC5 and AC15 evidenced; AC6 89.8 to 94.3% arrived, teleports at most 0.62%. Foreman amended: Beijing St is arterial (Sambuu's eastern continuation).
- 2026-11-24 build S1 and S3 committed. AC6 with Beijing arterial: 90.6 to 93.9% arrived, at most 0.58% teleports. Build and lint clean (three pre-existing lint warnings). S3 also fixed a marker bug: pins were drawn 18 px lower per index.
- 2026-11-24 build S4: RL retrained and 15 experiment runs done; all 15 within caps (worst pedestrian 79 s, worst Approach 106 s); model and results carry the committed net hash 02b3baea. RL has the lowest average vehicle and pedestrian wait in all five Scenarios.
- 2026-11-24 finding: Spillback is 0.0 in every run. In commit 9ada9d0 (evening-rush, Max-pressure, one run traced) all 45.4 lane-minutes came from 0.2 to 7.1 m stub exit lanes, which the new joins removed; the shortest exit lane is now 16.6 m. The sensor only reads the first exit edge. Not changed; for the user.
- 2026-11-24 finding (pre-existing): fetch_osm.sh fetches no relations, so 45 OSM turn restrictions in the area are missing from the net. Not changed; for the user.
- 2026-11-24 build S5 done: README files, research note, screenshots. Open text questions: About says the caps are never exceeded (not true at Operator cap 45), the event-log empty text, vision.png branding.
