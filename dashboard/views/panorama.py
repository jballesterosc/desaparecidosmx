"""Panorama nacional — KPI header, tendencia nacional, ranking estatal."""

import pandas as pd
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
st.divider()

# ── View 2 · Ranking estatal ────────────────────────────────────────
por_estado = (
    rows.groupby(["cve_entidad", "entidad"], as_index=False)["conteo"].sum()
)
por_estado["entidad_label"] = por_estado["entidad"].map(theme.title_es)
sf_estado = (
    undated[undated["categoria"].isin(f.categorias)]
    .groupby("cve_entidad")["conteo"].sum()
)
por_estado["sin_fecha"] = (
    por_estado["cve_entidad"].map(sf_estado).fillna(0).astype(int)
)

# Denominator: mean CONAPO mid-year population over the selected years.
y0, y1 = int(f.periodo_ini[:4]), min(int(f.periodo_fin[:4]), 2026)
pop = data.load_population()
pop_periodo = (
    pop[pop["anio"].between(y0, y1)]
    .groupby("cve_entidad")["poblacion"].mean()
)
por_estado["poblacion_promedio"] = por_estado["cve_entidad"].map(pop_periodo)
por_estado["tasa_100k"] = (
    por_estado["conteo"] / por_estado["poblacion_promedio"] * 100_000
).round(1)

en_tasa = st.toggle(
    "Por cada 100 mil habitantes", key="pan-rank-tasa",
    help="Población promedio a mitad de año del periodo seleccionado "
         "(CONAPO, proyecciones revisión 2023).",
)
rank = por_estado.copy()
if en_tasa:
    rank = rank.dropna(subset=["poblacion_promedio"])
    value_col = "tasa_100k"
    rank_sorted = rank.sort_values(value_col, ascending=False)
    top = rank_sorted.iloc[0]
    title = (
        f"{top['entidad_label']} registra la tasa más alta: "
        f"{top['tasa_100k']:,.1f} registros por 100 mil habitantes "
        f"({f.periodo_label})"
    )
    subtitle = (
        f"Tasa = registros con hechos en el periodo / población promedio "
        f"a mitad de año {y0}–{y1} × 100,000 · Entidad no especificada "
        "se excluye de las tasas (sin población)"
    )
    text = [f"{v:,.1f}" for v in rank_sorted.sort_values(value_col)[value_col]]
else:
    value_col = "conteo"
    rank_sorted = rank.sort_values(value_col, ascending=False)
    top = rank_sorted.iloc[0]
    pct_top = top["conteo"] / max(int(rank["conteo"].sum()), 1) * 100
    title = (
        f"{top['entidad_label']} concentra el {pct_top:,.1f}% de los "
        f"registros con hechos en {f.periodo_label}"
    )
    subtitle = (
        "Conteos absolutos, sin ajustar por población — active la tasa "
        "para comparar entidades de distinto tamaño"
    )
    text = [
        f"{int(v):,} · +{int(sf):,} s/f"
        for v, sf in zip(
            rank.sort_values(value_col)["conteo"],
            rank.sort_values(value_col)["sin_fecha"],
        )
    ]

destacado = st.selectbox(
    "Destacar entidad",
    options=list(rank_sorted["cve_entidad"]),
    format_func=lambda c: rank_sorted.set_index("cve_entidad")
    .loc[c, "entidad_label"],
    key="pan-rank-destacar",
)
hover = [
    f"{int(v):,} registros · +{int(sf):,} sin fecha"
    + (f" · {t:,.1f} por 100k" if pd.notna(t) else "")
    for v, sf, t in zip(
        rank.sort_values(value_col)["conteo"],
        rank.sort_values(value_col)["sin_fecha"],
        rank.sort_values(value_col)["tasa_100k"],
    )
]
theme.chart_frame(
    title=title,
    subtitle=subtitle,
    source=theme.source_line(
        consultado,
        extra="población CONAPO (rev. 2023)" if en_tasa else "",
    ),
    fig=charts.ranking_fig(
        rank, value_col=value_col, text=text, hover=hover,
        highlight_key=destacado,
    ),
    data=rank_sorted.drop(columns=["entidad_label"]),
    download_name=(
        f"umbral_rnpdno_ranking_estatal_{f.periodo_ini}_{f.periodo_fin}"
        f"_c{consultado}.csv"
    ),
    key="pan-rank",
)
st.caption(
    "«+N s/f» = registros de esa entidad sin fecha de hechos, no "
    "sumados a la barra. Entidad no especificada agrupa registros cuya "
    "entidad se desconoce — ubicación desconocida no es cero."
)
