# RNPDNO Data Pipeline

## Goal
Scrape/ingest Mexico's RNPDNO and produce monthly CSVs per state,
disaggregated by category, sex, municipality (where available), and
other variables. Output goes to data/processed/.

## Key facts about the source
- Versión Estadística dashboard returns AGGREGATE counts per filter
  combination, no bulk export. The pipeline works by discovering the
  dashboard's internal API calls and iterating over filter permutations.
- Categoría = desaparecido / no localizado / localizado.
- 32 entidades federativas; use INEGI codes for state/municipio joins.

## Conventions
- All fetching goes through src/rnpdno/ingest.py and caches raw
  responses to data/raw/ before any parsing.
- Be gentle: respect REQUEST_DELAY_SECONDS, use tenacity for retries.
- Never commit data/raw/ (may contain sensitive detail).
- CSV schema is defined in docs/data_dictionary.md — keep it in sync.

## Brand — binding for all UI, charts, and published artifacts
Anything user-facing (dashboard, figures, social, docs) follows the
Umbral design system: docs/umbral-brand.md (identity, voice, color
modes, chart rules) and docs/umbral-engineering.md (implementation,
accessibility, interpretability standards). Color/type tokens live in
assets/tokens.json and assets/tokens.css — never hard-code a hex that
exists as a token. Logo SVGs are in assets/.

## Definition of done for the spike
One entidad × one month, fetched → normalized → written as a clean CSV
matching the schema, with totals that match the dashboard's displayed count.