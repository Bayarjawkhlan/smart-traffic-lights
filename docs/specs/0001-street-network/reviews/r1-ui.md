# ui review, round 1

verdict: changes

Evidence root, written below as `$E`:
`/private/tmp/claude-501/-Users-bayarjavkhlan-Documents-projects-smart-traffic-lights/d77269f2-c61b-4a13-8d38-5db4e2a5003e/scratchpad/ui-r1`

Checked in headless Chromium at 1440x900 and 390x844 (DPR 2, touch), dark only (the app has no light theme), English
and Mongolian: 8 Corridors, All sites, three selected sites, all 15 schematics (English), Experiments, About, legend
open, Operator mode, keyboard focus, hover, pan and zoom. No page-level horizontal overflow in any state, and no two
visible names overlap.

The committed base screenshots predate the base branch's current stylesheet, so regressions were judged from them and
from the CSS diff; differences in palette or type face were ignored. The base app was not run.

## Findings

### F1 [major] Ribbon focus ring is clipped to two side brackets

where: Live, ribbon, keyboard focus (1440x900, EN and MN; same rule on phones) / evidence: `$E/shots/x-en-focus3.png`
(middle site: only left and right strokes), `$E/shots/x-en-focus2.png` (first site: only the right stroke, between two
sites). `.ribbon__sites` now has `overflow-x: auto` at every width, which also clips vertically, and the global
`:focus-visible` outline sits 2 px outside each button. On the base, the desktop list had no overflow. / fix:
`.ribbon__site:focus-visible { outline-offset: -2px; }`, or 4 px of padding with a matching negative margin on
`.ribbon__sites`.

### F2 [major] Hovering a label can make names jump back and forth every frame

where: Live map, 1440x900, MN, `SiteLabels.layout` / evidence: `$E/four.mjs` (repro). In `$E/shots/y-flicker-0.png` the
West label is on its "hovered" side, above its pin; `$E/shots/d-mn-site-sambuu-ikh-surguuli.png` shows its resting
side, below. Click a pin, then hover another label in the same Corridor: the hovered site takes priority, its name
moves to its preferred side and out from under the pointer, the hover ends, it moves back, and repeats. Measured 114
and 76 `data-side` writes in 0.6 s (a steady 93 toggles per name in 1.5 s), moving two or three names each time.
Reached by ordinary clicks in three MN cases: Sambuu (select University, hover Baga Toiruu West) and Genden (select
either site, hover the other). It also ignores reduced motion. / fix: place the active site at its current side if that
side is still free (order `sides` by the side it already has), or give `.site-marker__text` `pointer-events: none` so
only the pin triggers hover.

### F3 [major] On a phone, names are dropped and the remaining ones read as belonging to other pins

where: Live map, 390x844, EN and MN, including the opening Peace Avenue view / evidence: `$E/shots/m-en-c-peace.png`,
`$E/shots/m-en-c-juulchny.png`, `$E/shots/m-mn-c-sambuu.png`, sheets `$E/m-en.png`, `$E/m-mn.png`, distances from
`$E/near.py`. All 15 pins look alike, so the name is the only sign that a site is in the chosen Corridor. Names missing
in the fitted view: EN Peace 2 of 5, Sambuu 2 of 4, Juulchny 1 of 2, Baga Toiruu West 1 of 3, University 1 of 4; MN
those plus Sükhbaatar 1 of 3; MN also drops 1 of 4 on Sambuu and University at 1440x900
(`$E/shots/d-mn-c-sambuu.png`). Every label sits 15 px from its own pin, and many sit closer to a different, unnamed
pin: "Baga Toiruu East" is 10 px from Amar St, "State Department Store" 14 px from Seoul St, "Sambuu St / University
St" 11 px from Sükhbaatar. A selected Seoul St label also sits over the State Department Store pin in the fitted phone
view (distance 0; spec: "Pins always show"). The spec says a visible name shows for sites in the chosen Corridor. /
fix: make pins outside the chosen Corridor quieter (for example 10 px with an `--ink-3` border) so membership never
depends on a name; bring the label nearer its pin (it starts 15 px from the pin centre); add left- and
right-shifted candidates before dropping a name; consider wrapping names at " / " on two lines on narrow maps, which
roughly halves their width.

### F4 [major] Junction surface is missing or half drawn in site schematics

where: site panel schematic, all widths / evidence: `$E/sch.png`, `$E/shots/sch-ikh-surguuli.png`,
`$E/shots/sch-seoul-tserendorj.png`, `$E/shots/m-en-site-seoul-tserendorj.png`. `SiteSchematic` builds the junction
from road ends within a fixed 40 m, and the new wider joins put stop lines at 40 to 70 m (`$E/hull.py`). New sites
`seoul-tserendorj` and `sambuu-sukhbaatar` show a lone triangle with detached arms. `tuv-shuudan` dropped from 16 road
ends inside the radius to 5 and lost its east exit. `ikh-surguuli` has none (already broken on the base, with 2, so
pre-existing). On `chinggis-genden` the number 2 Approach badge falls outside the drawing, while the list below still
refers to 2. / fix: build the hull from the site's own Approach stop-line ends and Crosswalk ends instead of a radius,
and clamp badges to the view.

### F5 [minor] Ribbon nodes are no longer evenly spaced

where: ribbon, 1440x900 / evidence: `$E/ribbons.png`, `$E/shots/d-en-c-baga-toiruu-w.png`. `flex: 1 0 auto` sizes columns
by name, so Peace gaps are 191/176/203/196 px (the base had equal columns), MN Sükhbaatar columns are 383/178/393, and a
two-site connector is off centre. Order is the only thing the line claims, so the uneven gaps look like distance. / fix:
`flex: 1 1 0; min-width: max-content` on the items and the 120 px floor on the button, so columns are equal when the
list fits.

### F6 [minor] Picker truncates on a phone, including the opening Corridor in Mongolian

where: ribbon head, 390x844 / evidence: `$E/shots/x-m-mn-ribbon-center.png` ("Энх тайваны өргөн ч..."), `$E/m-en.png`
("Sükhbaatar St – Ching..."). End marks and the label take about 150 of 344 px. The base street title was not
truncated there. / fix: below 760 px put the end marks on the list row, or drop the visible label to its own line,
so the select takes the full width.

### F7 [minor] No cue that the ribbon scrolls

where: ribbon, MN Sambuu and University at 1440x900, All sites at 1440x900, most Corridors at 390x844 / evidence:
`$E/shots/d-mn-c-sambuu.png`, `$E/ribbons.png`, `$E/shots/m-mn-c-sambuu.png`. Text is cut at the inner edge with no fade,
and with overlay scrollbars nothing else marks it. The fixed "East" / "Зүүн" mark then stands next to a middle site,
not the last one. MN phones show about one site at a time. / fix: an edge fade (`mask-image`) while there is more to
scroll, and end marks inside the scrolled row. Two-line site names (split at " / ") would remove scrolling in the MN
desktop cases.

### F8 [minor] Experiments grid ends with one orphan card

where: Experiments, 1440x900 / evidence: `$E/pages.png` against
`git show feat/corridor-demo:docs/screenshots/experiments.png`. Seven metrics in three columns leave two empty cells under
a formerly even 3x2 grid. The MN title "Орох чиглэлийн хамгийн урт хүлээлт (с)" wraps, so that card's bars sit about
22 px lower than its row neighbours. / fix: show the two waits that have a Hard Cap in one row and let the last card
span, or use a four-column grid at this width; give card heads a fixed two-line height or let the grid align rows with
`subgrid`.

### F9 [nit] Picker shifts sideways when the Corridor changes

where: ribbon head / evidence: `$E/ribbons.png`. The select moves 2.5 px (EN) or 12 px (MN) between east-west and
north-south Corridors, and on phones changes width between 188 and 284 px, because it is centred between end marks of
different widths. It is also not centred over the row below. / fix: `grid-template-columns: 1fr auto 1fr` for the head.

### F10 [nit] Picker height differs from the other selects

where: ribbon head / evidence: `$E/shots/x-en-operator.png` (Scenario select 36 px, Corridor select 32 px on one screen).
32 px is also small for touch, where it is the main navigation. / fix: keep the shared 36 px, and 44 px on coarse
pointers.

### F11 [nit] Street named two ways in Mongolian

where: MN site panel / evidence: `$E/shots/x-mn-panel2.png`. The title says "Самбуугийн гудамж" and the Approaches
"Ж.Самбуугийн гудамж". / fix: use one form, for the user to choose.

## Pre-existing, not counted

- 390x844: the two-line map attribution covers the bottom 14 px of the ribbon and of the selected site's border
  (`$E/shots/x-m-seoul-map.png`). Neither rule changed on this branch.
- The MN brand name truncates on a phone although the row has room (`.brand__name` at 50vw); the old name was longer.
- Seconds stay "s" in the MN ribbon and site panel while the metrics strip uses "с".
- The MN Experiments page shows dates in US format; a zero Spillback value still draws a 1 px tick.

## Looked fine

Connector line starts and ends at the first and last node and is on the node centre for 2, 3, 4 and 5 sites, and
disappears for All sites. Selected-site border, radii and tokens match neighbouring components. Site titles wrap
cleanly in both languages. Selected site scrolls into view in the ribbon. About and the results table hold their
layout. Labels stay steady while panning (3 changes over 240 px).
