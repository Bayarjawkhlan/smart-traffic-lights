# ux review, round 1
verdict: changes

Screenshots are in `<scratchpad>/ux/`, called `ux/` below. "Introduced" and "pre-existing" are relative to `feat/corridor-demo`.

## Findings

### F1 [major] On a phone, a selected site's name hides other pins and swallows taps on them
where: Live, 390x844, both languages, initial fitted view, tap a site on the map. Introduced.
evidence: `ux/cover-all-390.png`. With "All sites", tap "Amar St / University St": its two-line name covers the Sambuu pins at Baga Toiruu West, Sükhbaatar and University. Tapping each of those three pins (touch events at the pin centre) left `#/live/amar-ikh-surguuli` selected. With the University Corridor chosen, the same name covers "Baga Toiruu East" and the tap on it also does nothing. Checked selecting every site on the Peace, Sambuu and University Corridors and "All sites": on the three Corridors, 5 sites (Baga Toiruu East, Amar, Sambuu/Sükhbaatar, Olympic/Genden, Seoul/Tserendorj) cover 1 or 2 pins; on "All sites", 4 do, up to 3 pins. Tapping empty map does not clear the selection, and the panel's back button is below the fold. Spec: "Pins always show". No pin is covered at 1440x900. The cause is the `asked.includes(id) ? free[0]` fallback in `siteLabels.ts`, and the name is part of the button.
fix: Never place a name over another pin. If neither side is clear, drop the secondary line, then try more positions (left, right, shifted), then hide the name (the ribbon and panel already show it). At minimum add `pointer-events: none` to `.site-marker__text` and draw pins above names.

### F2 [major] The chosen Corridor cannot be told from the rest of the map when its names do not fit
where: Live, pick a Corridor, 390x844 in both languages and two Corridors at 1440x900 in Mongolian. Introduced.
evidence: Names are the only map cue for a Corridor, and colliding names hide. At 390 only 3 of 8 Corridors (English) and 2 of 8 (Mongolian) show all their names. `ux/live-390-mn-sukhbaatar-chinggis.png` shows 2 of 3 and loses the northern end; `ux/live-390-en-university-olympic.png` loses the Peace Avenue junction; Juulchny shows 1 of 2. `ux/live-1440-mn-university-olympic.png` loses the northern end of a north-south street on a desktop, and Sambuu loses one site there. The remaining pins look identical to the pins outside the Corridor, so a viewer cannot follow the street on the map. At 1440 in English it works well, and the ribbon always lists the sites in the right order.
fix: Mark every pin of the chosen Corridor, for example a solid ring or fill with the others dimmed (not colour alone, keeping 3:1). One class set from `corridor.sites` is enough. A thin line through the pins would be better still. The AC11 hiding rule can stay.

### F3 [minor] Picking a Corridor while zoomed in gives no feedback on the map
where: Live, 1440 and 390, select a site from the ribbon (the map zooms to it), then pick another Corridor. Introduced, but as specified (resolution 15).
evidence: `ux/switch-1440.png`: picker says "Sambuu St", the map still shows Olympic/Genden with no Sambuu pin in view and nothing pressed in the ribbon. The only way back is a 29 px icon button. A deep link also opens zoomed in, so a visitor from a shared link meets this first.
fix: Ask the user to revisit the decision: fit the Corridor only when none of its sites is in view. Otherwise leave as is.

### F4 [minor] The picker and ribbon come after 15 map pins for keyboard users, in an order that jumps around the map
where: Live, keyboard only. Worsened (5 pin stops before, 15 now).
evidence: The picker is Tab stop 33, or about 24 stops after the skip link. Pin order is API order, so focus goes from the Peace sites to Juulchny, Amar, the Sambuu sites, then back south-west. When the map is zoomed to a site, Tab passes pins up to 2,400 px outside the map, with no visible focus. After the panel closes, focus falls to `body` (pre-existing), so the trip starts again.
fix: Put the ribbon before the map in the DOM (position stays by CSS), or add a skip link to it. Order pins by Corridor, take off-screen pins out of the tab order, and return focus to the site's ribbon button when the panel closes.

### F5 [minor] The same street has two names in Mongolian
where: Live, Mongolian, site panel and event log against picker, ribbon and map. Mostly introduced (the prefixed form was already on the base at `tuv-shuudan`).
evidence: The picker and site names say Самбуугийн, Сүхбаатарын, Гэндэнгийн, Амарын and Цэрэндоржийн гудамж; the panel says Ж.Самбуугийн, Д.Сүхбаатарын, П.Гэндэнгийн, Ерөнхий сайд Амарын and Хичээнгүй сайд Цэрэндоржийн гудамж. Both appear in one event line: "Амарын гудамж / Их сургуулийн гудамж — Ерөнхий сайд Амарын гудамж". English has a smaller version: "Peace Avenue" against "Peace Ave", and "Baga Toiruu West" against "Baga Toiruu".
fix: Use one short Mongolian form per street from the street table, as for English. The user should choose the form.

### F6 [minor] Site names that equal street or Corridor names
where: Live, picker and ribbon. The names are fixed by the spec; the ambiguity is new with the Network.
evidence: In Mongolian the site `ikh-surguuli` is "Их сургуулийн гудамж", the name of the whole street, in a Corridor where two other sites are "… / Их сургуулийн гудамж". English says "University St / Olympic St" for it. "Baga Toiruu West" and "Baga Toiruu East" are each both a Corridor and a site.
fix: For the user: name these sites by crossing, e.g. "Peace Ave / Baga Toiruu West" and "Энх тайваны өргөн чөлөө / Их сургуулийн гудамж". Ids stay.

### F7 [minor] "All sites" in the ribbon is a long strip in no visible order
where: Live, "All sites". Introduced.
evidence: 15 sites are 2,482 px wide in English and 3,515 px in Mongolian, in a 954 px ribbon (344 px on a phone). `ux/live-1440-en-all.png` shows 6, in API order. There is no scrollbar on macOS and no edge fade, so a mouse user without horizontal scroll reaches the rest only with Tab. No names show on the map, and touch has no hover, so this is the only list. Mongolian Sambuu (1,155 px) and University (999 px) also overflow at 1440.
fix: Fade the clipped edge, and group or sort the list by name or by west to east. A two-line name would stop most overflow.

### F8 [minor] Small touch targets on the new controls
where: Live, 390x844. The pin size is pre-existing; the picker is introduced.
evidence: Pins are 18x18 (base also 18), and 15 of them are now as close as 43 px. The picker is 210x32 (188x32 in Mongolian), the fit and zoom buttons 29x29. WCAG 2.1 AA sets no minimum; 44 is the usual phone target and 24 the WCAG 2.2 AA minimum, which the pins meet only by spacing.
fix: Give `.site-marker` a 32 to 40 px hit area around the 18 px pin, and the picker `min-height: 44px` on narrow screens.

### F9 [minor] Experiments bars are not to scale (pre-existing; the new chart has it too)
where: Experiments, Charts, 1440, both languages. Pre-existing flex shrink in `.bars__bar`; the base "Max pedestrian wait" chart already drew 73 longer than 80.
evidence: `ux/page-experiments-1440-en.png`, measured widths. "Longest Approach wait": 67 is 153 px and 102 is 178 px (86% drawn, 66% real); 99 is 184 px but 106 is 177 px. "Max pedestrian wait": 63 is 193 px and 79 is 185 px, so the lowest value has the longest bar beside a red "+25%". The numbers, deltas and the table are right.
fix: Give the bar its own track (grid column) with a fixed space for value and delta, or scale to the track less the label width with `flex-shrink: 0`.

### F10 [minor] The headline cards leave out the result where Max-pressure is worse
where: Experiments, top cards. Introduced by the new metric and results.
evidence: The Max-pressure card shows three green "better" figures, while its longest Approach wait is 48 to 58% worse than fixed-time in every Scenario, shown only further down.
fix: Add "Longest Approach wait" to the cards.

### F11 [minor] Older accessibility and language issues, seen again (all pre-existing)
where: Live, Experiments, About.
evidence: axe reports `definition-list` (serious, metrics strip) and no `h1` on Live; no contrast violations on Live, Experiments or About. A closed panel drops focus to `body`. At 390 the panel opens at y=911, below the fold, with no scroll or announcement after a map tap. "Select a Signal Site on the map or below" is wrong at both sizes, since the ribbon is beside or above that text. Mongolian still shows " s" for seconds in the ribbon, panel and About caps, "Skip to content" and "Failed to fetch". Signal state in the ribbon is `aria-hidden` or on a plain span, so a screen reader hears only name, queue and wait. Crosswalks numbered "· 1", "· 2", "· 3" have no matching number on the schematic. At 390 the attribution covers the bottom 14 px of the ribbon, including its scroll bar.
fix: Separate work. The wrong "or below" text is a cheap one.

### F12 [nit] Copy
where: Experiments legend, panel, ribbon.
evidence: "queues against exit roads" (and "дарааллыг гарах замтай харьцуулна") is hard to read alone. "Longest Approach wait" sits beside "Max pedestrian wait". "Crosswalk across the road" / "Явган гарц: зам" at `seoul-tserendorj` says little (allowed by resolution 6). On a phone the picker cuts "University St – Olympi…" and "Сүхбаатарын гудамж…", so the second half of a renamed street is not visible until the list opens. "All sites" has an unlabelled `ol` inside the labelled nav.
fix: "compares queues with exit roads"; hide the word "Corridor" visually on narrow screens to give the picker room.

### F13 [nit] Mongolian for the user to check
where: all screens. I cannot judge these.
evidence: End marks "Хойд" and "Өмнөд" beside directions "хойш" and "урагш" and About's "хойд-урд"; "Орох чиглэлийн хамгийн урт хүлээлт (с)"; "Сүлжээг бүтнээр харуулах"; "Улаанбаатарын гэрлэн дохионы сүлжээ" (cut off in the phone header, as the old name was); "дүүрсэн зам руу цөөн машин оруулна"; "Гэрлэн дохионы цэгүүд, хойноос урагш". Street spellings and English pairs: Б.Ренчингийн / Renchin St, Элчингийн / Ambassador St, Усны / Usny St, Анкарагийн / Ankara St.
fix: User review.

## Checked and good
- All eight Corridors and "All sites", English and Mongolian, 1440 and 390: correct order, end marks West/East and North/South localised, no page overflow (also 320, 720, 768). No two visible names overlapped in the screenshots I looked at, and no pin is covered before a selection.
- Finding a north-south street: "Corridor" is labelled and its names are clear. At 1440 in English a viewer can find and follow University St – Olympic St without help.
- A site outside the Corridor switches the picker from map click and from keyboard Enter; `seoul-tserendorj` goes to "All sites"; "All sites" stays on selection. Deep links, an unknown site id, browser Back and leaving and returning to Live all behave.
- Every stop has a 2 px focus outline except the zoom buttons (MapLibre's own style, pre-existing). Marker names read "name — Intersection"; the picker is announced as "Corridor". Choosing with the keyboard keeps focus on the select, and Tab then goes to the first listed site.
- Headed Chromium: type-ahead changes the picker. I could not drive arrow keys through the macOS native menu from Playwright, so that part is unproven; it is a plain `select`.
- Missing and empty `corridors`: 15 sites, no picker, no errors. Offline state renders in both languages and recovers by itself, keeping the deep link's Corridor.
- Experiments shows "Longest Approach wait" in chart and table, in both languages. Document title follows the language.

Not checked: screen reader software itself, Operator actions, Explain (no key), the Vision page (its service is off), and loss of the connection in mid-session. Base comparison is from its code and committed screenshots; I did not run the base.
