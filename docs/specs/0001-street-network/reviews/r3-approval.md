verdict: approve
risk: human
reasons:
- Checked at 8a96d8f by reading the fix diff, spec, ledger and all eight reviews, and by re-running all 15 committed runs (seed 42) and the 15 old five-site runs (base branch extracted to a scratch folder) with my own per-person check that reads SUMO directly, not the project's sensor; no server or port was used and the tree is unchanged.
- All 15 new runs reproduce the committed JSON to the digit, and the README table matches the JSON in every cell.
- "Red throughout" claim holds: the longest time anyone stood at a site Crosswalk without green being shown was 79.0 s (evening rush, RL), equal to the metric; nobody over 90 s in any of the 15 runs.
- Crowding sentences hold: people standing over 90 s in total were 3 in incident with Fixed-time (longest 125.0 s, sambuu-baga-toiruu-east), 371 in pedestrian surge with Fixed-time (301.5 s) and 110 in pedestrian surge with Max-pressure (302.5 s), all at tuv-shuudan for the surge; these sit inside the README's "3", "368 to 381" and "101 to 110", and the other 12 runs have none.
- "Earlier results" wording holds: on the old runs the same red-throughout check finds people over 90 s in 14 of 15 runs, the longest 315.0 s in morning rush with Max-pressure where the metric said 71; my count is 96 people against the README's 99 cases, a difference of detection threshold that does not change the finding.
- The definitions are now precise: "Max pedestrian wait" is defined under the table as time until green was offered, the Caps paragraph separates being offered green from getting across, and it says the average restarts its clock the same way, which the code confirms (engine.py `_track_people`, `_finish_people`).
- About strings in both languages no longer state the caps as absolutes ("works to give green before..."), keep the `{n}` placeholder, and `tsc --noEmit` is clean.
- No blocker or major is open from any review; the Safety Guard diff is two lines that swap a link lookup and change no rule.
- Small, not required: the ledger says the red-throughout longest is 78 s, my check gives 79.0 s; the Experiments page shows "Max pedestrian wait (s)" with no note that it means wait for green; the new Mongolian vehicle-cap string says "чиглэл" where the rest of the app says "Орох чиглэл".
- For the user before any push: four review files (r1-ui, r1-ux, r2-ui, r2-ux) hold scratch paths that contain the OS user name; the ledger path itself is now relative.
- Accepted minors: I agree with accepting all of them for a demo. The Operator-cap-45 vehicle breach (192 s against a 180 s Hard Cap) is the one I would fix first, since an Operator can reach it from the UI; it is disclosed in the README and the About text no longer denies it.
- Unverified and stated as such: Mongolian wording has not been read by a speaker; the 60 fps figure comes from Chrome for Testing, not system Chrome; arrow keys on the native select and the explanation text were never exercised.
- Risk stays human: the risk script's flag stands (large diff, 73 files, Safety Guard file touched) and the branch publishes safety figures.
