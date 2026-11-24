# Factory: Signal Sites beyond Peace Avenue
spec: docs/specs/0001-street-network/index.md
branch: factory/street-network   worktree: ../smart-traffic-lights-factory-street-network (sibling of the main checkout)   base: feat/corridor-demo (local, unpushed, 9ada9d0)
ship policy: none chosen while the user was asleep; later the user asked to bring it into local main and push
stage: done (fast-forwarded into main and pushed at 93e63df; no PR)
round: 2
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
- 2026-11-24 verify round 0: 15 of 17 pass. AC10 failed at 8.5x (fixed per-step sleep overshoots), sent to the runtime builder. AC14 failed on one research-note sentence, corrected by the foreman. Verifier notes: arrow keys on the native select untested headless; explanation text not checked (no LLM key); AC16 grey signals near invisible in a screenshot. Pre-existing, unfixed: "Failed to fetch" and "Skip to content" stay English in Mongolian mode. Verifier screenshots: scratchpad/verify.
| AC | Result |
|---|---|
| AC1-AC9, AC11-AC13, AC15-AC17 | pass |
| AC10 | failed at 8.5x, fixed by deadline pacing; 9.95x over 60 s in the foreman's own timing, 9.87x in the code reviewer's; 60 fps drawn |
| AC14 | fail on one sentence, fixed |
- 2026-11-24 review round 1 (head 3adb02d): code pass, security pass, ux changes (2 majors), ui changes (4 majors). Client majors sent to the S3 builder.
- 2026-11-24 incident: the code reviewer ran `pkill -f corridor_sim.server`, which killed the other reviewers' test servers. The user's three Docker containers are stopped; they finished at 02:50 UTC, before the first agent pkill (03:05 UTC), and no agent ran a Docker stop. Left as found.
- 2026-11-24 fix round 1 (3bc3d82): client majors fixed; names take no pointer events and hide rather than cover a pin, Corridor pins numbered, schematic hull per site; builder reports 576 label states and 540 taps clean. Review round 2 started (ux, ui, code on the fix diff).
- 2026-11-24 review round 2 (3bc3d82): ux pass, ui pass, code pass (minors listed in the review files). Security pass at round 1, no change since touches it.
- 2026-11-24 approval round 1 (efd3bbe): changes. Required: README pedestrian-cap claim (3 of 15 runs had people standing over 90 s through crowding) and About cap wording. Fixed by rewording; the red-throughout check finds nobody over 90 s in all 15 new runs (longest 79 s); crowding counts given as ranges. Screenshots retaken.
- 2026-11-24 approval round 2 (8a96d8f): approve, risk human. Done as a local branch: not pushed, no PR, no merge, worktree kept.
- 2026-11-24 after: user asked to bring the work into local main (fast-forward) and then to push main; pushed at 93e63df, no PR.
- 2026-11-24 after: Operator-cap breach fixed in `guard.py` by ranking the two Hard Caps together by least time left. With the old ordering a 3-Phase site could starve an Approach at pedestrian cap 45. Search of the patched Guard (9,180 runs, 15 sites plus 2 synthetic, caps 45 to 90 and 60 to 600 s): no breach, tightest margin 0 s at cap 45. All 15 committed experiments replay identically.
