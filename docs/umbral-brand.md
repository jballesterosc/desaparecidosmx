# CLAUDE.md — Umbral brand & build instructions

> **How to use this file.** Drop it at the root of any Umbral repo (site, dashboard, notebook, deck, social kit). Any AI model or collaborator working in that repo must read it first and follow it unless the human explicitly overrides. It defines *what Umbral is* and *how anything Umbral-branded must look and read*. Implementation-level rules (chart libraries, component specs, accessibility, data conventions) live in `umbral-engineering.md`. Machine-readable tokens live in `assets/tokens.json` and `assets/tokens.css` — use those as the source of truth for color; the hexes below are for reference.

---

## 1. What Umbral is

Umbral (`umbral_`) is an independent, open-source data lab. It builds data products, causal analysis, and monitoring tools for the public interest — Spanish-first, bilingual-friendly, everything reproducible.

- **Meaning:** *umbral* = threshold. The point where evidence becomes significant, where a trend crosses into another reality.
- **Taglines:** «Cruzar el umbral con datos» / "Where evidence crosses over."
- **References for taste:** Isomorphic Labs (air, restraint, medium type weights), Our World in Data (chart discipline), AI Futures (uncertainty visualization).

## 2. Voice

Precise, sober, civic-scientific. Numbers carry the argument.

- **Do:** state findings as full sentences; always name the data source and its license; show uncertainty; write Spanish first, add English for international artifacts.
- **Don't:** hype words ("revolucionario", "game-changing"), exclamation marks, emoji, rhetorical questions as headlines, adjectives where a number works.
- Chart titles are sentences that state the finding ("Los registros crecen 9% anual desde 2015"), not topics ("Registros por año").

## 3. Dual-mode system

Same type, layout, logo, and semantics in both modes — **only color tokens change.**

- **modo laboratorio (light) — DEFAULT.** Website, reports, decks, press, documents.
- **modo instrumento (dark).** Live dashboards, social posts, monitoring screens, deck section-dividers and big-stat slides.

Switch by setting `data-mode="instrumento"` (or class `.u-dark`) on a container; tokens cascade. Never mix both modes inside one panel.

Color tokens (see `assets/tokens.json` for both modes):

| Token | Light | Dark | Use |
|---|---|---|---|
| ink | `#16191C` | `#EDF1F4` | text, axes, primary marks |
| base | `#F2F3F1` | `#101418` | page background |
| panel | `#FAFAF8` | `#171C22` | cards, chart panels |
| border | `#DDE0DC` | `#2A3138` | 1px rules |
| gridline | `#E6E8E4` | `#232A31` | chart gridlines |
| baseline | `#C4C9C4` | `#3A434C` | chart baseline |
| muted | `#6E756F` | `#8B95A0` | secondary text |
| caption | `#9AA19B` | `#5C6670` | axis labels, sources |
| **signal** | `#128273` | `#5FD4C4` | THE highlight — one element per view |
| model | `#5A63D8` | `#8B93F8` | second data series |
| alert | `#C8503F` | `#E26A5A` | warning / third series |

Rules: **signal is reserved for the single most important element per view** — never decorative. Never pure white/black. No gradients. Need more categorical colors? Derive with `oklch()` matching signal/model/alert chroma+lightness, vary hue only.

## 4. Typography

- **Space Grotesk** — wordmark, headlines, chart titles, big statistics. **Weight 500 by default** (600 only for small bold labels). **Never 700 for display** — medium weight is the signature. Tight tracking on display sizes (−0.02em to −0.03em).
- **IBM Plex Sans** — long body text, UI, legends. 400–600.
- **IBM Plex Mono** — axis ticks, source lines, code, tabular figures. 400–500.

Scale — web: h1 40–64px/500 · chart title 22–26px/500 · body 16–17px, line-height 1.55–1.6 · labels 13–14px · axis/source 12px mono. Slides (1920×1080): title ≥ 56px, body ≥ 28px, nothing under 24px. **Never substitute Inter, Roboto, or Arial.**

## 5. Logo

Real files in `assets/`: `umbral-isotype-{light,dark}.svg`, `umbral-lockup-{light,dark}.svg`, `umbral-favicon.svg`.

- **Wordmark:** `umbral_` — Space Grotesk 500, lowercase, underscore in signal color.
- **Isotype:** a vertical signal bar crossing a horizontal dashed line (the significance threshold): dashed line in caption gray (2px), bar ~5:44 ratio, crossing left of center.
- Clear space = one bar-height on all sides. Don't distort, outline, add effects, or recolor outside tokens.

## 6. Charts — the heart of the brand

1. Title (Space Grotesk 500, states the finding) · subtitle (Plex Sans: geography, period, unit) · source line (Plex Mono: `Fuente: … · umbral.mx · CC BY 4.0`) above a 1px rule.
2. Horizontal gridlines only; darker baseline. No vertical gridlines, chart borders, or fills.
3. Label series directly at line ends — no legend boxes.
4. Max 4–5 series. One in signal; others in model / muted gray; alert only for warnings.
5. Axis ticks in Plex Mono; abbreviate (`12k`, `3.7M`); comma thousands separator.
6. Bars: solid fills, track one step darker than panel, value labels in mono.
7. **Uncertainty is a brand signature:** projection bands at 15% opacity of series color; dashed lines past "hoy"; a dashed vertical rule labeled `hoy`.
8. Never: pie, 3D, dual axes, truncated y-axis without a note.

## 7. Layout

Generous margins, max text measure ~65ch, 8px spacing scale — more whitespace than feels necessary. Flat: 1px rules do the structural work. No shadowed cards, no rounded-pill buttons, no left-accent-border boxes, no rounded corners > 2px. Header: base bg, isotype + wordmark left, nav right (Proyectos · Datos · Metodología · ES/EN), 1px bottom rule.

## 8. Applications

- **Website / reports:** light mode. Hero = Space Grotesk 500 headline ≤ 2 lines, one signal accent, one supporting sentence.
- **Dashboards:** dark mode. Panels on `panel` with 1px borders; live figures in mono.
- **Social 1080×1080:** dark mode. Isotype top-left, ONE giant statistic, one-line explanation, `umbral_` in mono bottom.
- **Decks 1920×1080:** light mode; dark only for section dividers + big-stat slides. Footer mono: project + slide number. (Template: `Umbral Deck Template.dc.html`.)
- **Documents:** Letter, 0.75in margins, Space Grotesk headings, Plex Sans body 11–12pt, mono footnotes/sources.

## 9. Never (quick reject list)

Emoji · gradients · stock icons · drop shadows · pill buttons · pure black/white · decorative SVG illustration · hype copy · bold (700) display type · signal on more than one element per view · a chart without its source.

## 10. Pre-ship checklist

- [ ] Correct mode for the medium (light default; dark only where §8 says)
- [ ] Colors pulled from tokens, not hand-typed
- [ ] Display type is Space Grotesk 500, not bold; body is Plex Sans; data is Plex Mono
- [ ] Every chart has title-as-finding + subtitle + source line
- [ ] Uncertainty shown wherever a projection or estimate appears
- [ ] Exactly one signal-colored element per view
- [ ] Spanish first; source + license named; nothing on the Never list
