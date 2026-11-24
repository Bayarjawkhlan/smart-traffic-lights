# ux review, round 2
verdict: pass

Reviewed 3bc3d82. No blockers or majors. Screenshots are in `<scratchpad>/ux2/`, called `ux2/` below.

## Round 1 majors

- **R1 F1, names over pins: fixed.** At 390x844, 1,080 real touch taps over English and Mongolian, all eight Corridors and "All sites". From each, I tapped all 15 pins, then with that site selected the three nearest pins; every tap selected its site (taps 560 ms apart; two fast taps zoom the map, which is the MapLibre default). Five points on every other pin were also hit-tested in each selected state. At 1440x900, 540 real clicks (all 15 pins, then the nearest one). No name box touched any pin, another name, the legend, the controls, the ribbon or the attribution in any of the 576 measured states. The same held for covers and name overlaps at 320, 360, 768, 1024 and 1280 wide with every site selected, when hovering every pin, and at five zoom steps per Corridor at 1440.
- **R1 F2, Corridor not identifiable: fixed.** Corridor pins are larger, filled and numbered; the others shrink to grey rings. Size, fill and number all differ, so it does not rest on colour. Numbers match the Corridor order and the ribbon in all 36 views, and "All sites" has none. At 1440 every Corridor now shows all its names in both languages (Mongolian Sambuu and University did not in round 1). At 390, 5 of 8 Corridors show all names in each language (was 3 and 2); the rest can be followed by number.

## Findings

### F1 [minor] On a phone a name can sit under another numbered pin and read as that pin's name
where: Live, 390x844, initial fitted view, including the default Corridor. Introduced: a name can now shift, and the pin it belongs to may lie at its edge.
evidence: English Peace Avenue, the first thing a phone visitor sees: "Central Post Office" (site 3) is centred 3 px from pin 4 and 54 px from pin 3, and pin 4 has no name (`ux2/probe.png`). Mongolian Juulchny: the only visible name belongs to 1 but is centred 19 px from pin 2 and 90 px from pin 1 (`ux2/390-mn-juulchny.png`). In 16 Corridor views a name spans another numbered pin 11 times; in 8 of them it is centred nearer that other pin. Own gap 4 px, other pin's gap 8 to 14 px. The ribbon numbers resolve it, so nobody is stuck. The code reasons that a 4 px gap against 6 px shows ownership, but the eye also uses centring.
fix: Put the number in the name tag ("3 Central Post Office"), or prefer a wrapped form that stays centred on its own pin before a full shift, or reject a place where another numbered pin is nearer the name's centre.

### F2 [minor] The selected site's name hides on a phone for a few sites
where: Live, 390x844, fitted view. Introduced; accepted by round 1's suggested fix, but it differs from resolution 7 (selected has priority).
evidence: No name on the map for `juulchny-baga-toiruu` and `sambuu-sukhbaatar` in Mongolian in nearly every Corridor, `amar-ikh-surguuli` in Mongolian "All sites", and `sambuu-sukhbaatar` in English "All sites". `ux2/flow-mn-sambuu-sukhbaatar.png`: pin 2 is selected and unnamed while 1 and 4 keep names. The filled pin, the highlighted ribbon item (scrolled into view) and the panel still name it.
fix: None required. The user should know that "pins never covered" wins over "selected name first". Trying a wrapped name above and beside with a smaller gap would recover some.

### F3 [minor] Screen readers get no Corridor cue from map pins
where: Live, map pins. The visible cue is new and has no spoken counterpart.
evidence: The pin number is `aria-hidden` and the pin's accessible name is unchanged ("Central Post Office — Intersection"), so membership and order are only in the ribbon list. The ribbon's own number is hidden too, which is right, since the ordered list gives the position. Not worse than before.
fix: Add the position to the pin's accessible name when it is in the chosen Corridor, for example "Central Post Office, 3 of 5 on Peace Avenue — Intersection".

### F4 [nit] The far end mark is off screen on a phone
where: Ribbon, 390x844, all eight Corridors in both languages; Mongolian Sambuu and University at 1440. Introduced (both marks were always visible in round 1).
evidence: "West" or "North" shows at first, "East" or "South" only after scrolling, and neither when the ribbon scrolls to a site in the middle. "Зүүн" is half faded in `ux2/kb-390-mn.png`. The near mark plus the numbers make the direction clear, and AC12 is met in the DOM.
fix: None needed. If wanted, put the axis beside the picker ("West to East").

### F5 [nit] Smaller things
where: Live.
evidence: A tap on a name no longer selects its site, which follows from names taking no pointer events; the pin stays an 18 px target. An open legend at 1440 covers the edge of one name and one pin, and on a phone most of the map; names are not re-laid out when it opens (covering is pre-existing, `ux2/legend-1440-en.png`). An override badge can cover a neighbouring pin's name or run off the right edge for 4 s (pre-existing, `ux2/badge-390-en.png`; simulated except in the flow screenshot).
fix: Re-measure when the legend toggles.

## Open from round 1, deliberately not fixed

- R1 F3 (picking a Corridor while zoomed in), R1 F4 (picker after the pins in Tab order; still stop 33), R1 F5 and F6 (names), R1 F9 (bars not to scale, pre-existing), R1 F11 (older issues, including the attribution over the ribbon's bottom edge at 390), R1 F13 (Mongolian for the user).
- R1 F7: partly done. Clipped edges fade and there is a thin scroll bar; "All sites" is still 2,482 px (English) and 3,515 px (Mongolian) in API order.
- R1 F8: partly done. The picker is 44 px high on a phone; pins are still 18 px targets.
- R1 F10 and F12: done where checked. "Longest Approach wait" is in the Experiments text three times per language, cards included in the code; "compares queues with exit roads" and the hidden "Corridor" word on a phone are in, and picker text is no longer cut.
- Seen again: 7 px of page overflow at 320 wide in English, on About too, so it comes from the header, not the fix.

## Checked and good

- Selected-site flow with taps at 390 in both languages: pin, panel, picker switch, "All sites" for `seoul-tserendorj`, ribbon item highlighted and scrolled into view; fit and close return to the numbered view.
- Keyboard at both sizes and languages: 2 px focus outline on every pin and ribbon stop, a focused quiet pin grows and shows its name, Enter selects and keeps focus, select type-ahead changes the Corridor, Tab goes on to site 1. Focusing a ribbon item scrolls it clear of the fade where it fits.
- Ribbon height is constant (138 px at 1440, 146 px at 390) over all Corridors. The picker is announced as "Corridor", the list as "Signal Sites, west to east".
- Map noise and readability: 11 px bold numbers on a filled 18 px pin read well at 1440 and 390, including the square mid-block pin and the selected pin (dark on accent). Quiet rings are visible but clearly secondary. Hovering does not move names already shown.
- No console or page errors.

Not checked: screen reader software, real phone hardware, arrow keys in the macOS native menu, Operator actions, Explain, a base comparison by running the old client, and the schematic's drawing (UI reviewer).
