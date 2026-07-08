# `rnpdno` package — module map

How a count travels from the RNPDNO dashboard to a national CSV:

```
                    RNPDNO Versión Estadística (internal JSON API)
                                      │
                                      ▼
 ingest.py ──── POST per filter permutation, cache verbatim ────► data/raw/
                                                                     │
 transform.py ◄── read cached JSON, parse, reconcile totals ─────────┘
     │
     ▼ row dicts (COLUMNS grain: entidad × month × categoría × sexo × municipio)
 export.py ──── write per-state CSVs ────► data/processed/<cve_entidad>/
                                                                     │
 combine.py ◄── concatenate per-state CSVs ──────────────────────────┘
     │
     ▼
 data/processed/all-states/<YYYY-MM>.csv and <YYYY>.csv

 run.py ── orchestrates ingest → export → combine over a scope,
           log-and-continue, pass/fail summary
```

Each stage reads only the previous stage's output: `transform`/`export`
never hit the network, `combine` never reads `data/raw/`. That makes
every stage re-runnable offline and independently testable.

## Modules

| module | role | CLI |
|---|---|---|
| `config.py` | Endpoints, the 31-field filter payload, `REQUEST_DELAY_SECONDS`, paths. No logic. | — |
| `catalogs.py` | Static maps: `ENTIDADES` (INEGI codes `1`–`32` + `33` = entidad no especificada), `CATEGORIAS` (label → `idEstatusVictima`), key helpers `cve_entidad`/`cve_municipio`. | — |
| `ingest.py` | Fetch one entidad × month slice (Totales ×2, AreaChart, municipio catalog, TablaDetalle ×3 categorías) and cache verbatim bodies + `.meta.json` sidecars to `data/raw/`. Session priming, retries, rate limiting live here — **all network access goes through this module**. `slice_cache_complete()` tells the runner what's already fetched. | `python -m rnpdno.ingest --estado 1 --mes 2024-01` |
| `transform.py` | Parse a cached slice into row dicts (`COLUMNS`), enforcing the reconciliation invariants: per-categoría sums match Totales (shortfall → `MUNICIPIO NO DESGLOSADO` residual row; excess → `ReconciliationError`), grand total == `TotalGlobal`. Also computes the per-state `SIN_FECHA` bucket. Pure: raw JSON in, rows out. | — (library only) |
| `export.py` | Call `transform` for a slice and write `data/processed/<cve>/<YYYY-MM>.csv` plus a refreshed `sin-fecha.csv`. | `python -m rnpdno.export --estado 1 --mes 2024-01` |
| `combine.py` | Concatenate per-state CSVs into `all-states/<YYYY-MM>.csv` (dated rows only) and `all-states/<YYYY>.csv` (12 months + each state's SIN_FECHA bucket once, filterable via `periodo`). Refuses to write if **any** state's input is missing (`MissingInputError`) — no partial national files. | `python -m rnpdno.combine --periodo 2024-01` or `--periodo 2024` |
| `run.py` | Orchestrator: for each estado × month in scope, ingest (skipped when the raw cache is complete; `--refetch` overrides) then export; combines run last over the full entidad set. Failures are recorded and skipped, not fatal (`log-and-continue`); the run ends with a pass/fail summary and exit 1 if anything failed. Re-running with the same arguments resumes an interrupted batch. | `python -m rnpdno.run --estados all --periodos 2024` |

## Import graph

`config` and `catalogs` are leaves. `ingest` uses both.
`transform` reads `config` (paths) + `catalogs`. `export` wraps
`transform`. `combine` reads `export` (output dir) + `transform`
(schema) + `catalogs`. `run` calls `ingest`, `export`, `combine` —
nothing imports `run`.

The single-slice CLIs are fail-fast; only `run.py` is
log-and-continue. Design rationale lives in `docs/DECISIONS.md`; the
CSV contract in `docs/data_dictionary.md`.
