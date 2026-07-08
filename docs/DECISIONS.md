# Decision log

ADR-style record of significant pipeline decisions. Append a new entry
whenever a call of this kind is made; keep entries short.

---

## 1. Scrape the dashboard's internal JSON API, not the UI

- **Problem:** The Versión Estadística dashboard has no bulk export;
  we need machine-readable counts per filter combination.
- **Options:** (a) browser/UI automation reading rendered charts;
  (b) reproduce the dashboard's internal POST JSON endpoints.
- **Decision:** (b). We mapped the endpoints (`Totales`,
  `TablaDetalle`, catalogs, …) and the 31-field filter payload from
  the site's JS bundle, and verified API responses match the UI.
- **Why:** Stable, complete, and lighter on the server than driving a
  browser; raw responses can be cached verbatim before parsing.
  Gotcha encoded in `ingest.py`: the initial page GET must look like a
  normal load (no AJAX headers) or the session cookie is not set.

## 2. Municipio counts from TablaDetalle, with a residual-row fallback

- **Problem:** `BarChartSexoMunicipio` silently truncates to the top
  30 municipios (Edomex × 2024-01 summed 123 vs the true 164), which
  broke reconciliation for large states.
- **Options:** (a) keep the bar chart and absorb the gap in a residual
  row; (b) switch to `TablaDetalle` (`TipoDetalle=3`), the complete
  "Ver detalle completo" table, keeping the residual row only as a
  fallback.
- **Decision:** (b). If a table's sum still falls short of the Totales
  field, a single `MUNICIPIO NO DESGLOSADO` row reconciles the total
  and the fallback is logged; an excess is a hard error.
- **Why:** TablaDetalle verified complete (Edomex sums exactly
  164/331/26 = 521). The residual row preserves the invariant that
  every CSV reconciles to `TotalGlobal` even if the source degrades.

## 3. Categoría grain: 7 / 2 / 3, not desaparecida vs no localizada

- **Problem:** We want the finest categoría split available at the
  municipio × sexo grain.
- **Options:** (a) desaparecida and no localizada as separate
  categories; (b) the coarser 3-way partition
  `DESAPARECIDA_O_NO_LOCALIZADA` (7) / `LOCALIZADA_CON_VIDA` (2) /
  `LOCALIZADA_SIN_VIDA` (3).
- **Decision:** (b).
- **Why:** The public API only exposes the desaparecida/no-localizada
  split in the `Totales` aggregate, not in any detail endpoint. The
  3-way set partitions `TotalGlobal` exactly, which powers the
  reconciliation invariants.

## 4. Monthly CSVs are dated-records-only (`mostrarFechaNula=0`)

- **Problem:** The date filter acts on fecha de hechos;
  `mostrarFechaNula=1` would fold undated records into whatever month
  is queried.
- **Options:** (a) flag on — every monthly CSV silently includes the
  same undated pile, double-counting it across months; (b) flag off —
  monthly CSVs contain only records whose events fall in that month.
- **Decision:** (b), with the undated records handled separately
  (entry 5).
- **Why:** Months stay additive (summable across a range without
  double counting) and the periodo column means what it says.

## 5. SIN_FECHA bucket = Totales(flag on) − Totales(flag off)

- **Problem:** With dated-only monthly CSVs, undated records would
  vanish from the dataset entirely — unacceptable (Edomex has ~22k).
- **Options:** (a) drop them; (b) a per-state `sin-fecha.csv` computed
  per categoría as the difference between the two Totales calls.
- **Decision:** (b). The diff is date-range-independent (verified:
  identical values from the 2024-01 and 2024-02 slices), so the file
  is month-independent and refreshed on every export.
- **Why:** Preserves the full register while keeping monthly files
  clean. Limitation: the API exposes the undated diff only at the
  Totales aggregate, so no sexo/municipio breakdown; a negative diff
  raises `ReconciliationError`.

## 6. Living-register semantics: `consultado_en`, no fixed snapshot

- **Problem:** The RNPDNO is continuously updated — records are added,
  dated, re-classified, or removed — so counts for the same period
  change between consultations.
- **Options:** (a) pretend counts are stable; (b) stamp every row with
  the UTC query date and document that cross-consultation comparisons
  are not apples-to-apples.
- **Decision:** (b). `consultado_en` comes from the cached
  `.meta.json` sidecar written at fetch time.
- **Why:** Honest provenance; enables detecting register churn by
  re-consulting the same slice later.

## 7. Two-mechanism caveat for low monthly counts (not "mostly undated")

- **Problem:** Jalisco's tiny 2024 monthly counts (~20) were first
  attributed to bulk-loaded undated records, and the docs said the
  "vast majority" lacked dates.
- **Options:** (a) keep that wording; (b) probe historical months and
  restate the caveat.
- **Decision:** (b). Probe (2019/2021 × 3 months each) showed Jalisco
  dated monthly totals of ~270–450, vs only ~1,443 undated — the mass
  sits in earlier years. Edomex is the opposite (~22k undated). Docs
  now state two mechanisms — undated records OR events in other
  periods — with the share varying by state.
- **Why:** The original claim was empirically wrong for Jalisco;
  the corrected caveat tells users to cover the full date range *and*
  `sin-fecha.csv` before quoting state totals.

## 8. Estado 33 included as ENTIDAD NO ESPECIFICADA

- **Problem:** The dashboard has a "se desconoce" option
  (`idEstado=33`, not an INEGI code) for records whose entidad is
  unknown. Excluding it silently drops those records from any
  national aggregate.
- **Options:** (a) exclude — only real entidades; (b) include as its
  own entity in the run, labeled `ENTIDAD NO ESPECIFICADA`, written to
  `data/processed/33/`.
- **Decision:** (b), included in every batch alongside estados 1–32.
- **Why:** Unknown location ≠ zero — the same principle behind the
  SIN_FECHA bucket applies to the spatial dimension. `cve_entidad`
  `33` is documented as a special non-INEGI value; consumers joining
  on INEGI codes must handle or filter it explicitly.
