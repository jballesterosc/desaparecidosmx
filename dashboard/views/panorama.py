"""Panorama nacional — KPI header, tendencia nacional, ranking estatal."""

import streamlit as st

import charts
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

consultado = data.consultado_en()

# ── View 1 · Tendencia nacional ─────────────────────────────────────
months = charts.month_span(f.periodo_ini, f.periodo_fin)
por_categoria = st.toggle("Ver por categoría", key="pan-trend-cat")

if por_categoria:
    series = {
        theme.CATEGORIA_LABELS[cat]: (
            charts.monthly_series(rows[rows["categoria"] == cat], months),
            theme.CATEGORIA_COLORS[cat],
        )
        for cat in theme.CATEGORIA_LABELS
        if cat in f.categorias
    }
    trend_data = (
        rows.pivot_table(
            index="periodo", columns="categoria", values="conteo",
            aggfunc="sum", fill_value=0,
        )
        .reindex(months, fill_value=0)
        .reset_index()
    )
else:
    serie = charts.monthly_series(rows, months)
    series = {"Total": (serie, theme.MODE["signal"])}
    trend_data = serie.rename("conteo").rename_axis("periodo").reset_index()

total_periodo = int(sum(s.sum() for s, _ in series.values()))
theme.chart_frame(
    title=(
        f"El RNPDNO acumula {theme.fmt(total_periodo)} registros con "
        f"hechos entre {months[0]} y {months[-1]}"
    ),
    subtitle=(
        "México · registros por mes de la fecha de hechos · "
        "el registro se actualiza retroactivamente"
    ),
    source=theme.source_line(consultado),
    fig=charts.trend_fig(series),
    data=trend_data,
    download_name=(
        f"umbral_rnpdno_tendencia_nacional_{months[0]}_{months[-1]}"
        f"_c{consultado}.csv"
    ),
    key="pan-trend",
)
undated_sel = int(undated[undated["categoria"].isin(f.categorias)]["conteo"].sum())
st.caption(
    f"{theme.fmt(undated_sel)} registros sin fecha de hechos no aparecen "
    "en esta serie; se detallan en Datos y método."
)
if f.periodo_fin > charts.consult_month():
    st.caption(
        f"Meses posteriores a la consulta ({charts.consult_month()}) "
        "no se dibujan: aún no pueden contener hechos registrados."
    )
