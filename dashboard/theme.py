"""Umbral theme for the Streamlit dashboard (modo instrumento).

Tokens come from assets/tokens.json — the source of truth; never
hard-code a hex that exists there. `chart_frame` enforces the brand
rule that no chart ships without title-as-finding + subtitle + source
+ downloadable CSV (docs/umbral-brand.md §6, umbral-engineering.md §2).
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]

with open(REPO_ROOT / "assets" / "tokens.json", encoding="utf-8") as _f:
    TOKENS = json.load(_f)

# Dashboards live in modo instrumento (umbral-brand.md §3/§8).
MODE = TOKENS["mode"]["instrumento"]

CATEGORIA_LABELS = {
    "DESAPARECIDA_O_NO_LOCALIZADA": "Desaparecidas o no localizadas",
    "LOCALIZADA_CON_VIDA": "Localizadas con vida",
    "LOCALIZADA_SIN_VIDA": "Localizadas sin vida",
}
SEXO_LABELS = {
    "HOMBRE": "Hombres",
    "MUJER": "Mujeres",
    "INDETERMINADO": "Indeterminado",
}

# Series colors: one element per view in signal, the rest step down to
# model / muted (never alert for "localizada sin vida" — dignity rule,
# DECISIONS.md #12). Trio validated for CVD separation and >=3:1
# contrast against panel.
CATEGORIA_COLORS = {
    "DESAPARECIDA_O_NO_LOCALIZADA": MODE["signal"],
    "LOCALIZADA_CON_VIDA": MODE["model"],
    "LOCALIZADA_SIN_VIDA": MODE["muted"],
}

_CSS = f"""
<style>
/* TODO(deploy): self-host fonts, latin + latin-ext subset
   (umbral-engineering.md §1) — the Google import is dev-only. */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] * {{
    font-family: 'IBM Plex Sans', sans-serif;
}}
h1, h2, h3 {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: -0.02em;
}}
[data-testid="stMetricValue"] {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500;
}}
[data-testid="stMetricLabel"] p {{
    font-family: 'IBM Plex Mono', monospace !important;
    text-transform: uppercase;
    font-size: 12px;
    color: {MODE["muted"]};
}}
code, pre, [data-testid="stCaptionContainer"] {{
    font-family: 'IBM Plex Mono', monospace;
}}
.u-source {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: {MODE["caption"]};
    margin: 0 0 0.25rem 0;
}}
.u-badge {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    color: {MODE["muted"]};
    border: 1px solid {MODE["border"]};
    padding: 2px 8px;
    border-radius: 2px;
}}
.stButton > button, .stDownloadButton > button {{
    border-radius: 2px !important;
    border: 1px solid {MODE["baseline"]} !important;
    box-shadow: none !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    border-color: {MODE["signal"]} !important;
    color: {MODE["signal"]} !important;
}}
*:focus-visible {{ outline: 2px solid {MODE["signal"]} !important; }}
[data-testid="stExpander"] details {{ border-radius: 2px; }}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def plotly_layout() -> dict:
    """Base Plotly layout with the instrumento tokens.

    Horizontal gridlines only, mono ticks, no legend box (series are
    labeled directly, umbral-engineering.md §2).
    """
    mono = dict(family="IBM Plex Mono", size=12, color=MODE["caption"])
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans", size=13, color=MODE["ink"]),
        colorway=[MODE["signal"], MODE["model"], MODE["muted"], MODE["alert"]],
        showlegend=False,
        margin=dict(l=8, r=8, t=8, b=8),
        xaxis=dict(showgrid=False, tickfont=mono, zeroline=False),
        yaxis=dict(
            gridcolor=MODE["gridline"],
            zerolinecolor=MODE["baseline"],
            tickfont=mono,
            rangemode="tozero",
            showline=False,
        ),
        hoverlabel=dict(
            bgcolor=MODE["panel"],
            bordercolor=MODE["border"],
            font=dict(family="IBM Plex Mono", size=12, color=MODE["ink"]),
        ),
    )


def source_line(consultado: str, extra: str = "") -> str:
    snapshot = f"rnpdno-{consultado[:7]}"
    parts = [
        "Fuente: RNPDNO (CNB/SEGOB)",
        f"consultado {consultado}",
        snapshot,
    ]
    if extra:
        parts.append(extra)
    parts += ["umbral.mx", "datos CC BY 4.0"]
    return " · ".join(parts)


def fmt(n: int | float) -> str:
    """Tabular figure with comma thousands separator."""
    return f"{n:,.0f}"


def chart_frame(
    *,
    title: str,
    subtitle: str,
    source: str,
    fig,
    data: pd.DataFrame,
    download_name: str,
    key: str,
) -> None:
    """Mandatory Umbral chart frame — every argument is required.

    Renders finding-title, subtitle, chart, source line, CSV download,
    and an adjacent data table (the accessibility fallback so the
    numbers are reachable without the plot).
    """
    missing = [
        name
        for name, value in [
            ("title", title), ("subtitle", subtitle), ("source", source),
            ("download_name", download_name),
        ]
        if not value
    ]
    if missing:
        raise ValueError(f"chart_frame is missing required {missing} — "
                         "a chart never ships without its frame")
    st.markdown(f"### {title}")
    st.caption(subtitle)
    st.plotly_chart(
        fig, width="stretch", key=key, config={"displayModeBar": False}
    )
    st.markdown(f'<p class="u-source">{source}</p>', unsafe_allow_html=True)
    left, right = st.columns([1, 2])
    with left:
        st.download_button(
            "Descargar CSV",
            data.to_csv(index=False).encode("utf-8"),
            file_name=download_name,
            mime="text/csv",
            key=f"{key}-csv",
        )
    with right:
        with st.expander("Ver los datos de esta gráfica"):
            st.dataframe(data, hide_index=True, width="stretch")
