# desaparecidosmx — RNPDNO data pipeline

Turns Mexico's [RNPDNO](https://versionpublicarnpdno.segob.gob.mx/Dashboard/Sociodemografico)
(Registro Nacional de Personas Desaparecidas y No Localizadas, *Versión
Estadística*) into clean, monthly, per-state CSVs disaggregated by
categoría, sexo, and municipio.

The public dashboard only shows aggregate counts per filter combination
and has no bulk export. This pipeline reproduces the dashboard's
internal JSON API calls, iterates over filter permutations, caches every
raw response, and reconciles the normalized output against the
dashboard's own totals.

## Output

For each entidad (INEGI codes `01`–`32`, plus `33` = entidad no
especificada):

- `data/processed/<cve_entidad>/<YYYY-MM>.csv` — one row per
  categoría × sexo × municipio for records whose **fecha de hechos**
  falls in that month.
- `data/processed/<cve_entidad>/sin-fecha.csv` — records with no fecha
  de hechos, per categoría (month-independent).

Plus combined national files built from the per-state CSVs:

- `data/processed/all-states/<YYYY-MM>.csv` — all states, one month
  (dated rows only).
- `data/processed/all-states/<YYYY>.csv` — all states, all 12 months,
  plus each state's SIN_FECHA bucket once (filterable via `periodo`).

Columns: `cve_entidad`, `entidad`, `periodo`, `categoria`, `sexo`,
`cve_municipio`, `municipio`, `conteo`, `consultado_en`. The full schema
and its caveats are in [`docs/data_dictionary.md`](docs/data_dictionary.md).

### Coverage

All 33 entidades are present with continuous month-by-month coverage
from **2010-01 through 2026-12** — every state has all 204 monthly CSVs
plus its month-independent `sin-fecha.csv`. Combined
`all-states/<YYYY>.csv` yearly files exist for every year **2010–2026**.
Regenerate or extend any scope with `rnpdno.run` (see Quickstart).

**Read the caveats before quoting numbers.** A month's CSV can be a
small fraction of a state's register (undated records live only in
`sin-fecha.csv`; dated events may sit in other years), and the RNPDNO is
a living register — counts change between consultations, hence the
`consultado_en` column.

## Quickstart

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional; REQUEST_DELAY_SECONDS defaults to 2.0

# run everything (ingest → export → combine) for a scope:
PYTHONPATH=src python -m rnpdno.run --estados all --periodos 2024

# or drive the steps individually:
PYTHONPATH=src python -m rnpdno.ingest --estado 1 --mes 2024-01
PYTHONPATH=src python -m rnpdno.export --estado 1 --mes 2024-01
PYTHONPATH=src python -m rnpdno.combine --periodo 2024-01

pytest
```

The runner records failures, skips them, keeps going, and prints a
pass/fail summary (nonzero exit if anything failed). Slices whose raw
cache is already complete are not re-fetched, so re-running with the
same arguments resumes an interrupted batch (`--refetch` overrides).

`ingest` only fetches and caches; `export` only reads the cache;
`combine` only reads `data/processed/` and refuses to write a national
file if any state's input is missing. The
transform enforces reconciliation invariants (every CSV must sum to the
dashboard's `TotalGlobal` for the same filter) and fails loudly if the
source and output disagree.

## Repository layout

```
src/rnpdno/
├── config.py      # endpoints, filter payload, request settings
├── ingest.py      # fetch + cache raw API responses (data/raw/)
├── catalogs.py    # entidad / municipio / categoría maps
├── transform.py   # normalize, disaggregate, reconcile
├── export.py      # write per-state monthly CSVs (data/processed/)
├── combine.py     # concatenate per-state CSVs into all-states files
└── run.py         # orchestrator: ingest → export → combine, log-and-continue
docs/
├── data_dictionary.md  # CSV schema — the contract for consumers
├── methodology.md      # how the numbers are produced, and why
└── DECISIONS.md        # ADR-style log of pipeline decisions
```

## Ground rules

- **Be gentle with the source.** All fetching goes through
  `rnpdno.ingest`, which waits `REQUEST_DELAY_SECONDS` between requests
  and retries with backoff.
- **`data/raw/` is never committed** — cached responses may contain
  sensitive detail. Only the aggregated `data/processed/` CSVs are
  shareable.
- Every fetched response is cached verbatim before any parsing, so
  transforms are reproducible and re-runnable offline.
