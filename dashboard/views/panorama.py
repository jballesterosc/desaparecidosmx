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

# ── KPI header ──────────────────────────────────────────────────────
# Neutral figures, no delta arrows: a month-over-month drop is usually
# reporting lag, and valenced deltas fail the dignity rule
# (DECISIONS.md #12.4).
por_categoria_kpi = (
    rows.groupby("categoria")["conteo"].sum()
    .reindex(list(theme.CATEGORIA_LABELS), fill_value=0)
)
undated_kpi = int(
    undated[undated["categoria"].isin(f.categorias)]["conteo"].sum()
)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros en el periodo", theme.fmt(int(por_categoria_kpi.sum())))
c2.metric(
    "Desaparecidas o no localizadas",
    theme.fmt(int(por_categoria_kpi["DESAPARECIDA_O_NO_LOCALIZADA"])),
)
c3.metric(
    "Localizadas (con y sin vida)",
    theme.fmt(
        int(por_categoria_kpi["LOCALIZADA_CON_VIDA"]
            + por_categoria_kpi["LOCALIZADA_SIN_VIDA"])
    ),
)
c4.metric("Sin fecha de hechos", theme.fmt(undated_kpi))
c4.caption("No incluidos en las demás cifras ni en las series.")
st.caption(
    f"Periodo {f.periodo_label} · las tres categorías particionan el "
    "total; cifras según el registro consultado el "
    f"{consultado}."
)
kpi_data = por_categoria_kpi.rename("conteo").rename_axis("categoria").reset_index()
kpi_data.loc[len(kpi_data)] = ["SIN_FECHA", undated_kpi]
st.download_button(
    "Descargar CSV de estas cifras",
    kpi_data.to_csv(index=False).encode("utf-8"),
    file_name=f"umbral_rnpdno_kpi_nacional_{f.periodo_ini}_{f.periodo_fin}"
              f"_c{consultado}.csv",
    mime="text/csv",
    key="pan-kpi-csv",
)
st.divider()

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
