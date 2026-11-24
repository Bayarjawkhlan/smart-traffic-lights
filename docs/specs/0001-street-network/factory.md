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
