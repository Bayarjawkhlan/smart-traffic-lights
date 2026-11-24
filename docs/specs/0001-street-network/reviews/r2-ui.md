# ui review, round 2

verdict: pass

Evidence root, written below as `$E`:
`/private/tmp/claude-501/-Users-bayarjavkhlan-Documents-projects-smart-traffic-lights/d77269f2-c61b-4a13-8d38-5db4e2a5003e/scratchpad/ui-r2`

Checked at 3bc3d82 in headless Chromium at 1440x900 and 390x844 (DPR 2, touch), English and Mongolian: 8 Corridors and
All sites, every site selected from every Corridor it is in, 15 schematics, Experiments, Operator mode, keyboard focus,
hover, and MN widths 320 to 1280. No console errors while the Corridors were stepped through, no page-level horizontal
overflow, and no visible name within 1 px of another site's pin in any resting or selected state.

## Round 1 majors

- F1 focus ring: fixed. All four sides draw, offset -2 px, and every focused button scrolls fully inside the row for 2 to
  5 sites in both sizes and languages (`$E/shots/focus-d-en-peace-2.png`, `$E/shots/focus-m-mn-genden-0.png`).
- F2 hover flicker: fixed. The three reported MN cases and every other selection, hovering each name and each pin in
  turn, in both languages: 8 attribute writes at most in 0.35 s, no name moves, and every hovered pin shows its name
  (`$E/b.mjs`, `$E/fl.png`).
- F3 phone names: fixed as a major. Quiet pins and numbers shared with the ribbon now carry membership, and each resting
  name is 4 px from its own pin and at least 6 px from any other. Names still missing in the fitted phone view: EN
  Peace 1 of 5, Sambuu 1 of 4, Juulchny 1 of 2; MN Sambuu 2 of 4, Juulchny 1 of 2, Baga Toiruu West 1 of 3. At 1440x900
  none is missing. Residue in F1 and F2 below (`$E/m-en-1.png` to `$E/m-mn-2.png`).
- F4 schematics: fixed. All 15 have a joined junction surface and all their Approach badges inside the view, on desktop
  and phone (`$E/sch-en.png`, `$E/sch-m.png`).

## Findings

### F1 [minor] A selected site can have no name on a phone

where: `SiteLabels.layout`, 390x844, fitted view / evidence: `$E/non.png`, `$E/d.mjs`. Tap a pin in the fitted view: MN
Sambuu St / Sükhbaatar St (Sambuu and All sites), MN Juulchny St / Baga Toiruu West (Juulchny, Baga Toiruu West, All
sites), MN Amar St / University St (All sites), EN Sambuu St / Sükhbaatar St (All sites). New in this fix: the old layout
let the selected name cover another pin, this one drops it when every position is within 6 px of one. In All sites the pin
has no number either, so only the panel and the ribbon say which site it is. The spec shows the selected site's name in
All sites and gives it first priority. Zooming in brings it back. / fix: in All sites count pins at their drawn 14 px
(`PIN_RADIUS` assumes 18), and for the selected site retry with a smaller gap, then over non-Corridor pins, before
dropping it.

### F2 [minor] Some names stand level with another Corridor pin

where: Live map names / evidence: `$E/z-genden.png` (EN phone, Genden: "Chinggis Ave / Genden St" ends 7.6 px left of
pin 2, and "Olympic St / Genden St" starts 13 px right of pin 1, so each line reads as if it belonged to the other pin),
`$E/z-sambuu.png` (MN 1440x900, Sambuu: name 4 starts 7 px right of pin 3, level with it). Own gap is 4 px and other gap
6 px, a difference the eye does not read. The names carry no number, so the pin numbers do not settle it on the map. /
fix: put the number in front of the name, as the ribbon does, or ask for about 16 px to a pin that is level with the
name, and try the other side first.

### F3 [minor] Names look like chips but no longer select the site

where: Live map, all sizes / evidence: `$E/e.mjs` (click and tap on "Central Post Office": nothing happens). Names were
inside the pin button and clickable on the base and in round 1; they now sit in a layer with `pointer-events: none`. What
remains is an 18x18 px target, under the 24 px minimum of WCAG 2.5.8, on the phone's map. The ribbon still selects
sites. / fix: give `.site-marker::before` a hit area of 24 px or more (about 32 px on coarse pointers, no more than
the spacing of neighbouring pins allows), or let a click on a shown name select its site without triggering hover.

### F4 [nit] Selected pin is larger after a tap than after a ribbon choice

where: Live map, touch / evidence: `$E/taps.png`, `$E/c.mjs` (20.7 px after a tap, 18 px from the ribbon or a link).
This is the larger pin seen at Seoul/Tserendorj: a selection state, not a defect. The accent fill and 18 px are the
selected state (others are 14 px in All sites), and `.site-marker:hover { scale(1.15) }` stays on after a tap because
touch keeps `:hover`. The hover rule is pre-existing; the 18 px base makes it more visible. In All sites the selected
pin is a plain blue disc, heavier than the rings around it. / fix: move the scale rule into the new
`@media (hover: hover)` block.

### F5 [nit] End mark touches the selected or focused site

where: ribbon / evidence: `$E/fl.png` right ("Зүүн" against the border of the last site), `$E/selm.png` second frame.
The end marks have no space beside the list. / fix: `gap: var(--space-1)` on `.ribbon__track`.

## Round 1 minors and nits

Fixed: F5 column spacing (equal when names allow; MN Sambuu 303/308/300 and University 301/228/225 px, where the row
scrolls), F6 phone picker (full width, nothing truncated), F7 edge fades and end marks in the row (`$E/fades.png`), F8
card grid (3 + 2 + 2, rows aligned in both languages, `$E/expf.png`), F9 picker position (same x and width for all
Corridors), F10 picker height (36 px, 44 px on coarse pointers). F11 left by decision.

## Pre-existing, not counted

- 390x844: map attribution covers the bottom of the ribbon and of the focused site's ring.
- The Override badge covers the neighbouring name (`$E/shots/override.png`, badge forced on by script; same badge rule as
  the base).
- MN brand name truncates on a phone; "s" for seconds in the MN ribbon; US dates on MN Experiments; zero Spillback
  draws a 1 px tick.

## Looked fine

Numbers match between ribbon and pins for 2, 3, 4 and 5 sites, and All sites drops them on both. The square mid-block
pin keeps its shape with a number. Quiet, hovered, focused and selected pins read as distinct states
(`$E/hq.png`). The selected site scrolls into view in the ribbon for every site and Corridor. Connector lines start and
end on the first and last node. Verdict cards hold four figures on one baseline in EN and MN and fold to 2x2 on a phone.
The new colours come from tokens, and the pin digit size (11 px) matches the existing map text.
