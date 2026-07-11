"""Detalle por estado — tendencia, categoría × sexo, municipios, sin fecha."""

import streamlit as st

import data
import filters
import theme

st.title("Detalle por estado")

dated, undated = data.load_register()
estados = data.estado_options()
cve, entidad = st.selectbox(
    "Estado",
    options=estados,
    format_func=lambda pair: theme.title_es(pair[1]),
    key="est-entidad",
)
f = filters.filter_rail(key_prefix="est")
rows, sin_desglose = filters.apply(dated[dated["cve_entidad"] == cve], f)
filters.slice_download(rows, key_prefix="est")

st.markdown("*(Vistas en construcción: tendencia estatal, categoría × sexo, "
            "municipios, panel sin fecha.)*")
