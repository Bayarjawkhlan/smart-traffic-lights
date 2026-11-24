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
