# code review, round 2
verdict: pass

Scope: `git diff 3adb02d...3bc3d82 -- client`. Read in full and run in a browser against a scratch server (sim on 8138, client on 5288, both stopped by PID afterwards). `pnpm exec tsc --noEmit` is clean; `pnpm lint` gives the same three known warnings, none in the changed files. No test files in the diff. No blockers and no majors. Round-1 findings F2 to F10 are not repeated.

Browser: system Chrome is not installed on this machine, so the runs used Playwright's Chrome for Testing, headless, 1440×900, GPU on (ANGLE Metal, Apple M2 Pro). The fps figures are `requestAnimationFrame` deltas, so they count callbacks, not drawn frames.

## Findings

### F1 [minor] Names ignore the legend once it is opened or closed
where: client/src/map/siteLabels.ts:115-120, 205-209; client/src/map/LiveMap.tsx:50-53
evidence: `obstacleBoxes` is read only in `measure()`, which runs on `show`, `setNames`, map resize and font load. The legend is a `<details>`; opening it changes its box without any of those. Measured: Peace Avenue chosen, legend opened, pointer on the Sambuu St / Baga Toiruu West pin: its name is drawn across the open legend (`name sambuu-baga-toiruu-west x map-legend`). The other way round: with the legend open and Sambuu Street chosen the name sits at x=303; after closing the legend it stays at 303 and only returns to 260 after the next Corridor or selection change.
fix: Refresh the obstacle boxes when an obstacle changes size: observe the obstacle elements with one `ResizeObserver` in `SiteLabels` (disconnect it in `destroy`) and call `measure` from it. This also covers the ribbon growing when its content changes.

### F2 [minor] A click on the faded edge of a ribbon site selects nothing
where: client/src/live/CorridorRibbon.tsx:106 (with 12-18)
evidence: `onFocus` scrolls the row. Chrome focuses the button on mouse down, the row scrolls under the pointer, and mouse up lands on another element, so no click reaches the button. Measured at 700 px wide, All sites: a click 8 px inside the right edge on "Baga Toiruu East" moved the row 61 px, the element under the pointer became "Juulchny St / Baga Toiruu West", and no site was selected. The same click 30 px inside the edge selected the site. The strip is the 16 px fade on either side.
fix: Scroll on focus only for keyboard focus: `event.currentTarget.matches(":focus-visible") && scrollToShow(...)`. A pointer selection is already scrolled into view by the `selectedSite` effect.

### F3 [nit] A keyboard-focused pin loses its name when the pointer passes another pin
where: client/src/map/siteLabels.ts:78-83
evidence: There is one `active` id for both hover and focus. `pointerenter` on pin B replaces focused pin A; `pointerleave` on B sets `active` to null. Measured: a quiet pin focused with Tab shows 6 names; after the pointer crosses another pin and leaves, 5 names, while the first pin still has visible focus (and its enlarged size from CSS).
fix: Keep `hovered` and `focused` apart and use `hovered ?? focused` in `layout`.

### F4 [nit] The wrap-first retry is skipped when the selected site is outside the Corridor
where: client/src/map/siteLabels.ts:164-166
evidence: `single.size < this.order.length` counts the selected name too. With a selected site that is not in `order`, `single` can hold `order.length` names while one Corridor name was dropped, so `arrange(["wrap", "line"])` never runs. Not seen on the committed network: all eight Corridors show every name in both languages at 1440×900 and at 700 px wide.
fix: Compare against the number of ids asked for (the size of the set built in `arrange`), or count only ids in `order`.

### F5 [nit] The "must not move" comment does not hold for quiet pins
where: client/src/map/siteLabels.ts:132-139, 173
evidence: `arrange` runs after `pinBoxes` is built, and a hovered quiet pin is given the 9 px radius there. A name that fitted next to the 5 px pin can be placed elsewhere while the pointer is on that pin, which is the jump the comment says cannot happen. Not reproduced: 135 hovers (15 pins in each of 9 picker choices) at fit zoom moved or removed no shown name.
fix: Give quiet pins the hover radius in `pinBoxes` always (the name then never needs the freed space), or arrange with the resting radii and use the larger one only when placing the active name.

## Checked and found sound

- Placement: in every Corridor, in English and Mongolian, at five zoom levels and at 700 px wide, no shown name overlapped another name, any pin, the legend (closed), the zoom buttons, the fit button or the ribbon, and none left the map. Shown names equal the ribbon items for all eight Corridors; All sites shows none until hover or selection, and every one of the 15 pins shows its name on hover there. The selected site gets the two-language form.
- Cost. Per frame the labels do nothing: `live.onFrame` reaches only `engine.ingest`. Per map move, `layout` cost 62 ms in total across a 14 s profile of continuous dragging and wheel zoom (about 1,200 frames, a dev build); `measure` 3 ms; `CorridorRibbon` renders 136 ms. Morning rush at ×10: 60.0 fps idle, 59.8 fps while dragging, 60.1 fps while zooming, p95 16.8 ms, no frame over 33.4 ms. `layout` reads `clientWidth` per candidate, but nothing writes to the DOM before those reads, so there is no forced reflow per move.
- Cleanup: `SiteLabels.destroy` removes both map listeners, the font listener and the layer. Pin listeners die with the pin elements, which the effect removes. The ribbon effects remove the font listener, the scroll listener and the `ResizeObserver`; the row is remounted by `key` on Corridor change and the effect with `[corridor]` re-attaches to the new element (`corridor` is a stable object from `network.corridors`).
- Hook dependencies are complete; `onSelectSite` and `lang` reach the long-lived effect through refs on purpose.
- Ribbon: list keys are site and Phase ids. Scroll state: `data-more-after` at the start, `data-more-before` at the end, scroll back to 0 after a Corridor switch, the selected site scrolled into view without scrolling the page.
- `convexHull`: fewer than three points, all points equal and all points on one line each return two points or fewer, so `junction` is null and no path is drawn.
- Comments: four added, each one line with a reason (F5 is about one being inaccurate). No docstrings.
- Dead code: no reference to the old `.site-marker__text`, `__name`, `__alt`, `is-named`, `data-side` or `--shift` remains in TS or CSS.
- No console errors or page errors in any run.
