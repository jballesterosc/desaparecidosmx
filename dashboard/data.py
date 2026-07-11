"""Cached data loaders for the dashboard.

Reads the combined yearly files (data/processed/all-states/<YYYY>.csv).
Each yearly file carries every state's sin-fecha.csv exactly once
(DECISIONS.md #9), so concatenating years repeats the undated bucket —
`load_register` dedupes it back to one row per estado × categoría.
Dated and undated frames are kept separate and are never summed
(DECISIONS.md #12.3).
"""

from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
ALL_STATES_DIR = REPO_ROOT / "data" / "processed" / "all-states"
YEARS = range(2010, 2027)

STR_COLS = ["cve_entidad", "entidad", "periodo", "categoria", "sexo",
            "cve_municipio", "municipio", "consultado_en"]


@st.cache_data(show_spinner="Cargando el registro…")
def load_register() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (dated, undated) frames for 2010–2026, all 33 entidades."""
    frames = [
        pd.read_csv(ALL_STATES_DIR / f"{year}.csv", dtype={c: str for c in STR_COLS})
        for year in YEARS
    ]
    df = pd.concat(frames, ignore_index=True)
    for col in ["sexo", "cve_municipio", "municipio"]:
        df[col] = df[col].fillna("")
    df["conteo"] = df["conteo"].astype(int)

    dated = df[df["periodo"] != "SIN_FECHA"].copy()
    undated = (
        df[df["periodo"] == "SIN_FECHA"]
        .sort_values("consultado_en")
        .drop_duplicates(subset=["cve_entidad", "categoria"], keep="last")
        .copy()
    )
    return dated, undated


@st.cache_data
def consultado_en() -> str:
    dated, _ = load_register()
    return dated["consultado_en"].max()


@st.cache_data
def month_options() -> list[str]:
    dated, _ = load_register()
    return sorted(dated["periodo"].unique())


@st.cache_data
def load_population() -> pd.DataFrame:
    """CONAPO mid-year population per entidad × year, 2010–2026.

    Built by scripts/build_population_reference.py; the vintage rides
    in the `fuente` column. Estado 33 has no population by design.
    """
    return pd.read_csv(
        REPO_ROOT / "data" / "reference" / "poblacion_entidades.csv",
        dtype={"cve_entidad": str},
    )


@st.cache_data
def estado_options() -> list[tuple[str, str]]:
    """(cve_entidad, entidad) pairs, INEGI order, estado 33 last."""
    dated, _ = load_register()
    pairs = (
        dated[["cve_entidad", "entidad"]]
        .drop_duplicates()
        .sort_values("cve_entidad")
    )
    return list(pairs.itertuples(index=False, name=None))
