"""Sidebar filter rail shared by the dashboard pages.

There is deliberately no "include SIN_FECHA" toggle: undated records
render as permanent separate elements and are never mixed into dated
series (DECISIONS.md #12.3).
"""

from dataclasses import dataclass, field

import pandas as pd
import streamlit as st

import data
import theme


@dataclass
class Filters:
    periodo_ini: str
    periodo_fin: str
    categorias: list[str] = field(default_factory=list)
    sexos: list[str] = field(default_factory=list)

    @property
    def periodo_label(self) -> str:
        if self.periodo_ini == self.periodo_fin:
            return self.periodo_ini
        return f"{self.periodo_ini} a {self.periodo_fin}"


_CAT_BY_LABEL = {v: k for k, v in theme.CATEGORIA_LABELS.items()}
_SEXO_BY_LABEL = {v: k for k, v in theme.SEXO_LABELS.items()}


def filter_rail(*, key_prefix: str) -> Filters:
    months = data.month_options()
    with st.sidebar:
        st.caption("Filtros · por fecha de hechos")
        ini, fin = st.select_slider(
            "Periodo",
            options=months,
            value=(months[0], months[-1]),
            key=f"{key_prefix}-periodo",
        )
        cat_labels = st.multiselect(
            "Categoría",
            options=list(_CAT_BY_LABEL),
            default=list(_CAT_BY_LABEL),
            key=f"{key_prefix}-categoria",
        )
        sexo_labels = st.multiselect(
            "Sexo",
            options=list(_SEXO_BY_LABEL),
            default=list(_SEXO_BY_LABEL),
            key=f"{key_prefix}-sexo",
        )
    return Filters(
        periodo_ini=ini,
        periodo_fin=fin,
        categorias=[_CAT_BY_LABEL[l] for l in cat_labels] or list(theme.CATEGORIA_LABELS),
        sexos=[_SEXO_BY_LABEL[l] for l in sexo_labels] or list(theme.SEXO_LABELS),
    )


def apply(dated: pd.DataFrame, f: Filters) -> tuple[pd.DataFrame, int]:
    """Filter the dated frame; return (rows, n_sin_desglose_excluded).

    Rows with empty sexo (the MUNICIPIO NO DESGLOSADO residuals) are
    kept while every sexo is selected — so totals reconcile with the
    register — and excluded (but counted) once the user narrows sexo,
    since they cannot be attributed to one.
    """
    mask = (
        dated["periodo"].between(f.periodo_ini, f.periodo_fin)
        & dated["categoria"].isin(f.categorias)
    )
    all_sexos = set(f.sexos) == set(theme.SEXO_LABELS)
    if all_sexos:
        return dated[mask], 0
    residual = int(dated.loc[mask & (dated["sexo"] == ""), "conteo"].sum())
    return dated[mask & dated["sexo"].isin(f.sexos)], residual


def slice_download(rows: pd.DataFrame, *, key_prefix: str) -> None:
    """Sidebar download of the current full-grain filtered slice."""
    with st.sidebar:
        st.download_button(
            "Descargar selección (CSV)",
            rows.to_csv(index=False).encode("utf-8"),
            file_name=f"umbral_rnpdno_seleccion_c{data.consultado_en()}.csv",
            mime="text/csv",
            key=f"{key_prefix}-slice-csv",
            help="Todas las filas (grano completo) que coinciden con los "
                 "filtros actuales; solo registros con fecha de hechos.",
        )
