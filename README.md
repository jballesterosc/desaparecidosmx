rnpdno-pipeline/
├── README.md
├── CLAUDE.md              # project context for Claude Code (see step 5)
├── .gitignore
├── .env.example           # config template — no secrets committed
├── pyproject.toml         # or requirements.txt
├── data/
│   ├── raw/               # cached API responses (gitignored)
│   ├── interim/           # cleaned, not yet final
│   └── processed/         # the deliverable: monthly per-state CSVs
├── src/rnpdno/
│   ├── __init__.py
│   ├── config.py          # states, date ranges, base URLs
│   ├── ingest.py          # hit the source, cache raw responses
│   ├── catalogs.py        # entidad / municipio / sexo / categoría maps
│   ├── transform.py       # normalize + disaggregate
│   └── export.py          # write per-state monthly CSVs
├── notebooks/             # exploration
├── tests/
└── docs/
    ├── data_dictionary.md
    └── methodology.md