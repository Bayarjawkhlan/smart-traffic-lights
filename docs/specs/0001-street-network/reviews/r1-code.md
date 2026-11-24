# code review, round 1
verdict: pass

Checked by reading the diff `feat/corridor-demo...HEAD` and by running the code read-only: site validation and Neighbour symmetry over the built data, flow sums per entry, README table against the experiment JSON (every cell and every percentage matches), network hash in model and results (all `02b3baea`), a scratch server on port 8130 (pacing, 72 concurrent control commands, bad input), one full independent pedestrian-wait run, `tsc --noEmit` (clean) and `oxlint` (the three known warnings). No test files are committed. No blockers and no majors.

## Findings

### F1 [minor] The ledger still records AC10 as failed
where: AC10, docs/specs/0001-street-network/factory.md verify table; fix in sim/corridor_sim/server.py:81-89
evidence: The table says "AC10 fail at 8.5x". Commit 3adb02d (running deadline) came after it and no re-measurement is logged. Measured in this review on port 8130, morning rush, one WebSocket client, 60.1 s wall: 593.5 s simulated = 9.87x. Also 1.02x at x1, 4.89x at x5, no catch-up burst after pause/resume. The deadline logic cannot oversleep (`ahead` is at most one step) and resets on pause, restart, speed change and lag over 0.5 s.
fix: Re-run the AC10 check in verify and record the result in the ledger; no code change needed.

### F2 [minor] About page still says the caps are never exceeded
where: client/src/i18n/strings.ts:196, 198, 418, 420 (AC13 neighbour; ledger "Open text questions")
evidence: "Pedestrians never wait longer than {n} s" and "Vehicles: Hard Cap {n} s, never exceeded for any reason." The ledger records a measured 192 s vehicle wait with the Operator pedestrian cap at 45 s, which the Operator bar allows. The README was reworded to "caps the Safety Guard works to" with the caveat; the About page was not, so the two disagree.
fix: Reword both strings in EN and MN to match the README (for example "Hard Cap {n} s: the Safety Guard forces a switch before it is reached"), or close the breach in the Guard. This is the user's call, as the ledger says.

### F3 [minor] A failed build leaves sim/data half-written
where: sim/corridor_sim/build.py:669-678
evidence: `main()` overwrites `corridor.net.xml` and `sites.json` before `check_sites`, and `network.json` before `write_scenarios` resolves the incident. Every AC4 failure therefore exits non-zero with a new net and site list next to old Scenarios, experiments and RL model (hash mismatch). The order exists because `load_sites` reads the site specs from the file.
fix: Build into a temporary directory and move the files into `sim/data` only after every check has passed; or let `load_sites` take the resolved site list as an argument so validation and incident resolution run before anything is written.

### F4 [minor] The simulation thread dies silently on any error except ScenarioError
where: sim/corridor_sim/server.py:91-122 (line 105 in particular); sim/corridor_sim/engine.py:119-144
evidence: The loop calls `scenarios()` (a file read and JSON parse, 53 µs measured) on every step. `build.py` rewrites `scenarios.json` with a plain `write_text`, so a rebuild while the server runs can hand the loop a half-written file: `JSONDecodeError`, the daemon thread ends, `/api/health` keeps answering `ok`, frames stop and every later control call blocks 30 s. The same happens if `traci.start` fails after `traci.close()` in `Simulation.start` (`running` stays true). The new handler covers only a bad incident. The per-step read predates this branch; the narrow handler is new.
fix: Read the Scenario duration once in `Simulation.start` and keep it on the simulation (`self.duration`), so the loop never touches the file. Wrap the loop body so an unexpected exception is logged, sets `paused`, and is reported by `/api/health`.

### F5 [minor] The new phase packer is not used by any site
where: sim/corridor_sim/phases.py:62-66, 107-130; sim/corridor_sim/model.py:101-106
evidence: All 15 sites have 2 or 3 candidate Phases from SUMO's own program, so `PhasePlanner.plan` is never called on the committed network, and `_pack` runs only when the greedy plan exceeds 3 groups, which happens at no site (greedy gives 2 or 3 everywhere). The backtracking search is 25 lines with no run behind it. Resolution 4 only asks that more than 3 Phases be reported, which `validate_sites` already does.
fix: Delete `_pack` and the `plan` wrapper and let validation report the site. Add a packer when a site actually needs one, with that site as its evidence.

### F6 [minor] The runtime never validates what it loads
where: sim/corridor_sim/model.py:145-213; sim/corridor_sim/guard.py:42; sim/corridor_sim/engine.py:72-79
evidence: `validate_sites` runs only in the build. The server, experiments and training call `load_sites` directly, so a hand-edited or stale `sites.json` reaches `SafetyGuard.__init__` (`site.phases[0]`, IndexError on a site with no Phase) or runs with an unserved Approach. A mismatched RL model is only a log warning. Illegal sites are representable at the place where they matter most.
fix: Call `validate_sites` at the end of `load_sites` and raise with the joined messages; the build then catches that one error instead of calling the validator itself.

### F7 [nit] Event localisation parses English sentences
where: client/src/live/EventFeed.tsx:21-58; sim/corridor_sim/engine.py:198, 207, 214
evidence: The client matches `"N lane(s) blocked: <label> at <nameEn>"` with a regular expression and then looks the label up by its English text. Any rewording on the server silently falls back to English. Controller and caps events are still English in Mongolian mode (as before this branch).
fix: Put `target` (Approach or Crosswalk id) and, for blocks, `lanes` on the event, as overrides already carry structured fields, and build the sentence from ids on the client.

### F8 [nit] Mongolian label logic exists twice, with a dead fallback
where: sim/corridor_sim/server.py:263-277; client/src/i18n/names.ts:39-53
evidence: `_labels` repeats the client's direction words, "Туслах зам" and "Явган гарц" for the explain prompt, and rereads `sites.json` on each call. `approach.get("direction") or approach["label"].rsplit(" ", 1)[-1]` can never take its second branch: the build always writes `direction`. `if "streets" in crosswalk` is the same kind of guard.
fix: Drop both fallbacks (index the fields directly). Keep the server copy only because the prompt needs it; a shared JSON of terms would remove the duplication if it grows.

### F9 [nit] Small build details
where: sim/corridor_sim/build.py:298-318, 515-517, 555, 585, 644
evidence: (a) Heap entries are `(distance, edge_id, clear, is_exit)`, so on an exact distance tie the path through another site wins over the clear one. (b) An id in `SKIPPED_ENTRIES` that is no longer an entry after a refetch is ignored without a word. (c) One `random.Random(7)` is shared by all Scenarios, so adding a Scenario changes the begin times of the ones after it. (d) An unknown `ped_focus` site raises a bare `StopIteration`.
fix: (a) push `not clear` so clear paths sort first; (b) fail the build when a skipped id is not an entry; (c) seed per Scenario name; (d) raise `SystemExit` naming the Scenario, as the incident check does.

### F10 [nit] `selectOnMap` and the render-time reveal overlap
where: client/src/live/LivePage.tsx:29-32; client/src/live/useCorridor.ts:24-31
evidence: `useCorridor` already reveals whenever `selectedSite` changes; the explicit `corridor.reveal(id)` on a map click matters only when the clicked site is already selected and the picker shows another Corridor. Correct, but two paths set the same state and the reason is not visible.
fix: Keep one path: let the hook take a "reveal now" nonce from map clicks, or leave it and say why in one line.

## Acceptance criteria: evidence seen

- AC1, AC2, AC3: reproduced. 15 sites, 15 distinct TLS, 2 or 3 Phases each, `validate_sites` returns no problem, eight Corridors in order, Neighbours symmetric with no self and no Corridor gap (27 pairs, longest real path 645 m).
- AC4: reproduced in memory for no Phase, 4 Phases, unserved Crosswalk, shared TLS; each message names the site. Incident mismatch read in code (build.py:535-548, engine.py:167-178).
- AC5: reproduced. Every entry within 2%, lowest flow 1.0 veh/h, north plus south 32.5% of volume, Peace Avenue westbound exit 542 veh/h in morning rush.
- AC6, AC8: from the JSON. Arrived 90.6 to 93.9%, teleports at most 0.58%, longest waits 79 s and 106 s, seed 42, 3600 s, hash matches the committed net. Evening rush with RL re-run here gives the same 79 s and 56 s. An independent per-person check of that run (SUMO's own waiting time, any edge) found nobody over 90 s and nobody waiting outside the sensed walking areas.
- AC7: reproduced. Five people on either Crosswalk at `ikh-delguur` raise the Max-pressure score of Phase 1 from 0 to 1.08 and the RL pedestrian features from 0 to 0.5 and 0.22.
- AC9, AC11, AC12, AC13, AC16, AC17: code read and ledger; not re-run in a browser in this review.
- AC10: see F1.
- AC14: no text in code, strings or README files claims coordination; the explain prompt says Neighbour state is not used.
- AC15: incident resolves to one Approach (`1537180313#0`), 240 to 1500 s.

README: every number in the results table and every percentage, throughput and teleport figure matches the JSON. Nothing overclaims; the caps paragraph and the Spillback paragraph state their limits. Comments added in the diff all carry a reason and are one or two lines; no docstrings.
