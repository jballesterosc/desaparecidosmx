# Data dictionary — processed CSVs

> **Read this first — two caveats that shape every number in these files**
>
> 1. **The date filter is on *fecha de hechos*** (date of the events),
>    not the date a record entered the register. Records without a
>    fecha de hechos are **excluded from every monthly CSV** and land
>    in the separate `sin-fecha.csv` bucket instead.
> 2. **A month's CSV can be a small fraction of a state's register**,
>    via two mechanisms whose share varies by state (both consulted
>    2026-07): (a) **undated records** — no fecha de hechos at all;
>    these live only in `sin-fecha.csv` (Estado de México: ~22,096
>    undated vs ~500 dated per month); (b) **events in other periods**
>    — Jalisco has only ~1,443 undated records, but its dated monthly
>    totals run ~270–450 in 2019/2021 vs ~20 in early 2024, so the
>    mass sits in earlier years, not in the undated bucket. Never sum
>    a handful of monthly CSVs and call it a state total; cover the
>    full date range **and** `sin-fecha.csv`. See docs/methodology.md.

## Deliverables

Per entidad:

- `data/processed/<cve_entidad>/<YYYY-MM>.csv` — records whose fecha de
  hechos falls in that month (e.g. `data/processed/01/2024-01.csv`).
- `data/processed/<cve_entidad>/sin-fecha.csv` — records with **no**
  fecha de hechos, per categoría. Month-independent; refreshed on every
  export of that state.

## Row grain

**One row per entidad × month × categoría × sexo × municipio**, with a
count column. Cells with a count of zero are omitted; absence of a row
means zero. Two special row types:

- `municipio = MUNICIPIO NO DESGLOSADO` — residual fallback row added
  only if the source table does not carry the full count (sexo and
  cve_municipio empty). The transform logs when this happens.
- `sin-fecha.csv` rows — `periodo = SIN_FECHA`, sexo and municipio
  empty (the undated bucket is only available per categoría).

## Columns

| column          | type   | example          | source |
|-----------------|--------|------------------|--------|
| `cve_entidad`   | str(2) | `01`             | INEGI entidad code; equals the dashboard's `idEstado` filter value, zero-padded. Special value `33` = `ENTIDAD NO ESPECIFICADA` (the dashboard's "se desconoce" bucket, not an INEGI code): records whose entidad is unknown, kept as their own entity — unknown location ≠ zero, same principle as SIN_FECHA. |
| `entidad`       | str    | `AGUASCALIENTES` | Static map in `src/rnpdno/catalogs.py`, taken from the dashboard's estado dropdown. |
| `periodo`       | str    | `2024-01`        | The `fechaInicio`/`fechaFin` month filter sent to the API (first to last day of the month, `mostrarFechaNula=0`), or `SIN_FECHA` in `sin-fecha.csv`. |
| `categoria`     | str    | `DESAPARECIDA_O_NO_LOCALIZADA` | `idEstatusVictima` filter used for the query. See "Categoría" below. |
| `sexo`          | str    | `MUJER`          | Column header in the `TablaDetalle` response (`Hombres`/`Mujeres`/`Indeterminado`, normalized to singular uppercase). Empty on residual and SIN_FECHA rows. |
| `cve_municipio` | str(5) | `01005`          | `cve_entidad` + 3-digit municipio code from `POST /Catalogo/Municipios` (`Value` field), joined to the table's municipio name. Empty when the name cannot be joined or on residual/SIN_FECHA rows. |
| `municipio`     | str    | `JESÚS MARÍA`    | Row label in the `TablaDetalle` response, verbatim; `MUNICIPIO NO DESGLOSADO` for residual rows; empty in `sin-fecha.csv`. |
| `conteo`        | int    | `12`             | Cell value in the `TablaDetalle` HTML table (commas stripped). |
| `consultado_en` | str    | `2026-07-08`     | UTC date the API was queried (from the cached `.meta.json`). The RNPDNO is a living register: counts for the same period change over time. |

## Categoría

`categoria` maps to the dashboard's `idEstatusVictima` filter. The
public API **cannot** separate "desaparecida" from "no localizada" at
the municipio × sexo grain (that split only exists in the `Totales`
aggregate), so the finest partition available is:

| `categoria`                    | `idEstatusVictima` |
|--------------------------------|--------------------|
| `DESAPARECIDA_O_NO_LOCALIZADA` | `7`                |
| `LOCALIZADA_CON_VIDA`          | `2`                |
| `LOCALIZADA_SIN_VIDA`          | `3`                |

These three categories partition the filter total: their sum must equal
`TotalGlobal` from `POST /Sociodemografico/Totales` for the same
entidad/month filter.

## Municipio source: TablaDetalle, not the bar chart

Municipio × sexo counts come from `POST /SocioDemografico/TablaDetalle`
(payload plus `TipoDetalle: 3`), which returns the **complete**
municipio table. The `BarChartSexoMunicipio` endpoint truncates to the
top 30 municipios and must not be used (confirmed: Estado de México ×
2024-01 chart summed 123 vs the true 164; TablaDetalle sums 164).

## Validation invariants

For every entidad × month slice, `transform.py` enforces:

1. `sum(conteo)` across all monthly rows == `TotalGlobal` from the
   cached `Totales` response.
2. Per categoría: TablaDetalle sum == the corresponding `Totales` field
   (`TotalDesaparecidos`, `TotalLocalizadosCV`, `TotalLocalizadosSV`).
   A shortfall triggers the logged `MUNICIPIO NO DESGLOSADO` residual;
   an excess raises `ReconciliationError`.
3. SIN_FECHA diffs must be non-negative.

Spike reference value: Aguascalientes × 2024-01 → `TotalGlobal` = 79.

## Known caveats

- The two headline caveats at the top of this file (fecha de hechos
  basis; undated records).
- Counts reflect the register at `consultado_en`, not a fixed
  historical snapshot.
- `sin-fecha.csv` has no sexo or municipio breakdown (only the Totales
  aggregate exposes the undated diff).
