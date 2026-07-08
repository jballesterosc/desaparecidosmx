# Methodology — how these numbers are produced

> **Read this first — two caveats that shape every number in this repo**
>
> 1. **The date filter is on *fecha de hechos*** (the date the events
>    occurred), not the date a record was registered. A record only
>    appears in a monthly CSV if the register holds a fecha de hechos
>    for it that falls inside that month. Records without a fecha de
>    hechos go to the separate per-state `sin-fecha.csv` bucket.
> 2. **A month's CSV can be a small fraction of a state's register**,
>    via two mechanisms whose share varies by state (both consulted
>    2026-07): (a) **undated records** — no fecha de hechos at all,
>    captured only in `sin-fecha.csv` (Estado de México: ~22,096
>    undated vs ~500 dated per month); (b) **events in other periods**
>    — Jalisco has only ~1,443 undated records, but its dated monthly
>    totals run ~270–450 in 2019/2021 vs ~20 in early 2024: the mass
>    sits in earlier years, not in the undated bucket. **Never** sum a
>    handful of monthly CSVs and present the result as a state total;
>    cover the full date range **and** account for `sin-fecha.csv`.

## Source

Mexico's RNPDNO (Registro Nacional de Personas Desaparecidas y No
Localizadas), via the public **Versión Estadística** dashboard at
`versionpublicarnpdno.segob.gob.mx`. The dashboard exposes only
aggregate counts per filter combination — there is no bulk export and
no per-record microdata. The pipeline reproduces the dashboard's own
internal API calls and iterates over filter permutations.

## How the pipeline queries the dashboard

1. **Session.** A plain GET of `/Dashboard/Sociodemografico` (no AJAX
   headers) obtains the `.AspNet.ApplicationCookie` session cookie.
   Data endpoints then accept JSON POSTs carrying the dashboard's
   31-field filter payload (empty string = filter not applied).
2. **Per entidad × month slice**, `ingest.py` POSTs:
   - `/Sociodemografico/Totales` twice — with `mostrarFechaNula=0`
     and `=1` (the pair feeds the SIN_FECHA computation below);
   - `/SocioDemografico/AreaChartSexoMeses` (context/cross-check);
   - `/SocioDemografico/TablaDetalle` with `TipoDetalle=3`
     (municipios), once per categoría (`idEstatusVictima` = 7, 2, 3);
   - `/Catalogo/Municipios` for the state's INEGI municipio codes.
3. Verbatim response bodies are cached to `data/raw/` (gitignored)
   with a metadata sidecar (URL, payload, timestamp) **before** any
   parsing. `transform.py` reads only from the cache and never hits
   the network.
4. Requests are throttled (`REQUEST_DELAY_SECONDS`, default 2 s) and
   retried with exponential backoff.

## Why TablaDetalle and not the bar chart

The dashboard's municipio bar chart endpoint
(`BarChartSexoMunicipio`) silently **truncates to the top 30
municipios**. Confirmed with Estado de México × 2024-01: the chart
summed 123 while the dashboard total was 164. `TablaDetalle`
(`TipoDetalle=3`, the "Ver detalle completo" table) returns the
complete municipio × sexo table — the same slice sums exactly 164.
All municipio counts in the CSVs come from TablaDetalle.

If a TablaDetalle sum still falls short of the corresponding Totales
field, the transform adds a single `MUNICIPIO NO DESGLOSADO` residual
row so totals reconcile, and logs the fallback. An excess is treated
as a hard error.

## Categoría granularity

The public API cannot split "desaparecida" from "no localizada" at the
municipio × sexo grain (that split exists only in the Totales
aggregate). The finest partition available, used throughout:

- `DESAPARECIDA_O_NO_LOCALIZADA` (`idEstatusVictima=7`)
- `LOCALIZADA_CON_VIDA` (`2`)
- `LOCALIZADA_SIN_VIDA` (`3`)

These three partition the filter total exactly.

## The SIN_FECHA bucket

The `mostrarFechaNula` flag adds records with no fecha de hechos to
whatever date range is queried. The undated bucket per categoría is
therefore:

    SIN_FECHA = Totales(mostrarFechaNula=1) − Totales(mostrarFechaNula=0)

This difference is independent of the date range used, so
`sin-fecha.csv` is month-independent and simply refreshed on every
export of that state. The API exposes the undated diff only at the
Totales aggregate, so `sin-fecha.csv` has no sexo or municipio
breakdown.

## Validation invariants

Every entidad × month slice must satisfy, or the transform fails:

1. Sum of all monthly rows == `TotalGlobal` from the cached Totales.
2. Per categoría: TablaDetalle sum == the matching Totales field
   (shortfall → logged residual row; excess → `ReconciliationError`).
3. SIN_FECHA diffs are non-negative.

Spike anchor: Aguascalientes × 2024-01 → `TotalGlobal` = 79
(browser-verified), enforced in `tests/test_transform.py`.

## Living-register semantics

The RNPDNO is continuously updated: records are added, dated,
re-classified (e.g. localizada con vida), or removed. Counts for the
same period change between consultations. Every row carries
`consultado_en` (UTC date of the API query); comparisons across CSVs
consulted on different dates are not apples-to-apples.
