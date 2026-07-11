"""Panorama nacional — KPI header, tendencia nacional, ranking estatal."""

import streamlit as st

import data
import filters
import theme

st.title("Panorama nacional")
st.caption(
    "Registros del RNPDNO por fecha de hechos, 2010–2026. "
    "El registro es vivo: los conteos cambian entre consultas."
)

dated, undated = data.load_register()
f = filters.filter_rail(key_prefix="pan")
rows, sin_desglose = filters.apply(dated, f)
filters.slice_download(rows, key_prefix="pan")
if sin_desglose:
    st.caption(
        f"{theme.fmt(sin_desglose)} registros sin desglose de sexo "
        "quedan fuera de esta selección."
    )

st.markdown("*(Vistas en construcción: tendencia, KPIs, ranking.)*")
