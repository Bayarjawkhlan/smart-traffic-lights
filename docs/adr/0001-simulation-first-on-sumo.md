# Simulation-first on SUMO, built from scratch

The project is a simulated demo of a Peace Avenue corridor in Ulaanbaatar, not a pilot on real signals. Traffic, signals and pedestrians run in Eclipse SUMO on road geometry imported from OpenStreetMap; camera vision is shown separately on recorded video and does not drive the simulation. We did not build on `Srikeerthiraja/Smart-Traffic-Light-Control-System`: it holds only README pseudocode and has no license (see `docs/research/smart-traffic-light-repo-evaluation.md`).

Note, 2026-11-24: the simulated area is now a 15-site Network (`docs/specs/0001-street-network/index.md`). The decision is unchanged.

## Consequences

- Real signal hardware, NTCIP and city approval are out of scope.
- Traffic demand is generated from Scenarios, tuned to look plausible rather than measured, so results compare Controllers against each other, not against reality.
