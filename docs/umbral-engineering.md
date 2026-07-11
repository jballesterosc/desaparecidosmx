# umbral-engineering.md — implementation & interpretability handoff

> Companion to `CLAUDE.md`. That file defines the brand; **this file tells an engineer (or an engineer working with an AI) how to build it in real code** and how to keep the *analysis itself* honest and interpretable. Where the two ever disagree, the human decides. Tokens are the source of truth: `assets/tokens.css` (web) and `assets/tokens.json` (everything else). Never hard-code a hex that exists as a token.

---

## 1. Setup

Load tokens once, globally. Light mode is the default; add `data-mode="instrumento"` to any subtree that must render dark (a dashboard shell, a social card).

```html
<link rel="stylesheet" href="/assets/tokens.css">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
```

```css
body { background: var(--u-base); color: var(--u-ink); font-family: var(--u-font-body); }
h1,h2,h3 { font-family: var(--u-font-display); font-weight: var(--u-weight-display); letter-spacing: var(--u-tracking-display); }
.mono, [data-numeric] { font-family: var(--u-font-mono); font-variant-numeric: tabular-nums; }
```

Self-host the three fonts for production (don't ship a Google Fonts dependency on a data product that must work offline / in government networks). Subset to Latin + `latin-ext` (Spanish diacritics).

## 2. Charts — library choices

**Web, interactive:** [Observable Plot](https://observablehq.com/plot/) for standard charts, drop to D3 only when Plot can't express it. A reusable theme:

```js
import * as Plot from "@observablehq/plot";
import tokens from "/assets/tokens.json" assert { type: "json" };

export function umbralPlot(mode = "laboratorio") {
  const t = tokens.mode[mode];
  return {
    style: { background: "transparent", color: t.ink,
             fontFamily: "IBM Plex Sans, sans-serif", fontSize: "13px" },
    marginLeft: 52, marginBottom: 34,
    x: { tickFormat: "d", grid: false },
    y: { grid: true, ticks: 5, tickFormat: "~s", // 12k, 3.7M
         line: false },
    color: { range: [t.signal, t.model, t.caption, t.alert] },
    // gridlines: override the default grid stroke to --u-gridline via CSS:
    // .plot [aria-label='y-grid'] line { stroke: var(--u-gridline); }
  };
}
```

Rules the code must enforce, not just the designer:
- Horizontal gridlines only (`x.grid = false`, `y.grid = true`); baseline drawn separately in `--u-baseline`.
- Direct series labels via `Plot.text` at the last datum — **do not** render a legend box.
- One series in `signal`; everything else steps down to `model`/`caption`. If a chart needs >5 series, it's two charts.
- Tick + source text in `--u-font-mono`. Number format: `d3.format("~s")` for axes, `,` group separator for callouts.
- Every chart component takes required `title`, `subtitle`, `source` props and renders the title/subtitle/source frame around the plot. A chart with no `source` should throw in dev.

**Uncertainty helpers (brand signature — build these once, reuse everywhere):**
- `Plot.areaY` at 15% opacity of the series color for confidence bands.
- Dashed stroke (`strokeDasharray: "7 5"`) for any segment past the present.
- A `Plot.ruleX([today])` dashed in `--u-caption`, annotated `hoy`.

**Python (desaparecidosmx, observatorio-delictivo-mx):** ship a matplotlib style file so every notebook/export matches the web. Save as `umbral.mplstyle`:

```ini
figure.facecolor: none
axes.facecolor: none
axes.edgecolor: C4C9C4
axes.linewidth: 1
axes.grid: True
axes.grid.axis: y
grid.color: E6E8E4
grid.linewidth: 1
axes.spines.top: False
axes.spines.right: False
axes.spines.left: False
font.family: IBM Plex Sans
font.size: 12
axes.titlesize: 16
axes.titleweight: medium
axes.titlelocation: left
xtick.color: 9AA19B
ytick.color: 9AA19B
text.color: 16191C
axes.prop_cycle: cycler('color', ['128273','5A63D8','9AA19B','C8503F'])
```

```python
import matplotlib.pyplot as plt
plt.style.use("umbral.mplstyle")
# title = the finding; always annotate the source:
ax.set_title("Los registros crecen 9% anual desde 2015", loc="left")
fig.text(0.01, -0.02, "Fuente: RNPDNO · umbral.mx · CC BY 4.0",
         family="IBM Plex Mono", size=9, color="#9AA19B")
```

For projections in Python, plot the CI band with `ax.fill_between(..., alpha=0.15)` and a dashed median past the last observed point. Prefer `matplotlib`/`plotnine`; avoid seaborn defaults (they fight the style).

## 3. Component specs (web app / dashboard)

All flat — no shadow, radius ≤ 2px, 1px borders in `--u-border`.

- **Button (primary):** bg `--u-ink`, text `--u-base`, `13px 26px` padding, Space Grotesk 500; hover → bg `--u-signal`. **Secondary:** transparent, 1px `--u-baseline` border, `--u-ink` text; hover → border+text `--u-signal`. No border-radius beyond 2px.
- **Card / panel:** bg `--u-panel`, 1px `--u-border`, 24–32px padding, no shadow.
- **Stat / KPI:** label in mono `--u-caption` uppercase; value in Space Grotesk 500, large; delta colored `signal` (good) / `alert` (bad) — decide direction per metric, never by sign alone.
- **Table:** 2px `--u-ink` top rule, 1px `--u-border` row rules, mono tabular figures right-aligned, highlighted row = `--u-panel` fill + 4px left `--u-signal` border.
- **Nav / filters:** flat bordered controls, no pills. Active state = `--u-signal` text or 2px underline.

## 4. Accessibility (non-negotiable for a public-interest lab)

- **Contrast:** body text on `base`/`panel` meets WCAG AA (both modes are designed to). If you introduce a new color, verify ≥ 4.5:1 for text, ≥ 3:1 for UI/graph strokes.
- **Never encode meaning by color alone.** Series need direct text labels; up/down deltas need an arrow or word, not just red/green. This also covers color-blind readers (signal-teal vs alert-red is *not* safe for deuteranopia on its own).
- Charts: provide a `<title>`/`aria-label` summarizing the finding, and a `<figcaption>` or adjacent data table (`<details>`) so screen readers and scrapers get the numbers. Ship the underlying CSV next to every chart.
- Respect `prefers-reduced-motion`; keep focus-visible outlines (in `--u-signal`); target size ≥ 44px on touch.
- Language: set `lang="es"` (or the right subtree lang) so screen readers pronounce Spanish correctly.

## 5. Data & repo conventions

- **Structure:** `data/raw/` (immutable, as-downloaded, dated), `data/processed/` (build output, git-ignored or via DVC), `src/` pipeline, `notebooks/` exploration, `output/` figures. A `Makefile` or single `make all` rebuilds every figure from raw.
- **Provenance:** every dataset gets a `SOURCE.md` — origin URL, accessor, download date, license, known caveats. Every published number must trace to a scripted transform, not a manual edit. *If you can't reproduce the figure, don't publish it.*
- **Versioning:** tag data snapshots (`rnpdno-2026-07`); charts state which snapshot they use. Public data is returned to the public, improved — publish the cleaned CSV under CC BY 4.0, code under MIT.
- **Naming:** files and columns `snake_case`, Spanish or English but consistent within a repo; ISO dates; entities keyed by INEGI/CVEGEO codes, never by free-text names.

## 6. Interpretability & honesty standards (how outputs stay trustworthy)

This is the lab's credibility. Enforce in review, not just design:

- **Title = claim, and the claim must be defensible from the chart shown.** No headline the data doesn't support.
- **Causal vs descriptive language is deliberate.** Say "asociado con" / "correlaciona" for descriptive work; reserve "efecto", "reduce", "causa" for designs with an identification strategy (RCT, diff-in-diff, RD, IV). State the design and its key assumption near the estimate.
- **Uncertainty is always visible:** intervals on projections, CIs on estimates, n and denominator on rates. A point estimate with no interval is incomplete.
- **Denominators & normalization:** counts vs rates-per-100k stated explicitly; never compare raw counts across differently-sized populations.
- **Axes are honest:** y-axis starts at 0 for bars; any truncation on line charts is annotated. No dual axes.
- **Show the gaps:** missing/underreported data (e.g. records lacking a verifiable date) is disclosed, not silently dropped or imputed without a note.
- **Sensitive topics** (desapariciones, violence) are handled with human dignity: people are counted, never spectacle; no gratuitous mapping to identifiable individuals.

## 7. Definition of done

Builds from raw with one command · matches tokens in both modes · every chart has finding-title + subtitle + source + downloadable CSV · uncertainty shown · AA contrast + non-color encoding + keyboard/reader access · causal language matches method · code MIT, data CC BY 4.0 on GitHub.
