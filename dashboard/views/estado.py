"""Detalle por estado — tendencia, categoría × sexo, municipios, sin fecha."""

import streamlit as st

import charts
import data
import filters
import theme

st.title("Detalle por estado")

dated, undated = data.load_register()
estados = dict(data.estado_options())
cve = st.selectbox(
    "Estado",
    options=list(estados),
    format_func=lambda c: theme.title_es(estados[c]),
    key="est-entidad",
)
entidad_label = theme.title_es(estados[cve])
f = filters.filter_rail(key_prefix="est")
rows, sin_desglose = filters.apply(dated[dated["cve_entidad"] == cve], f)
filters.slice_download(rows, key_prefix="est")

consultado = data.consultado_en()
undated_estado = undated[
    (undated["cve_entidad"] == cve)
    & (undated["categoria"].isin(f.categorias))
]
undated_total = int(undated_estado["conteo"].sum())

# ── Tendencia estatal ───────────────────────────────────────────────
months = charts.month_span(f.periodo_ini, f.periodo_fin)
por_categoria = st.toggle("Ver por categoría", key="est-trend-cat")

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
        f"{entidad_label} acumula {theme.fmt(total_periodo)} registros "
        f"con hechos entre {months[0]} y {months[-1]}"
    ),
    subtitle=(
        f"{entidad_label} · registros por mes de la fecha de hechos · "
        "el registro se actualiza retroactivamente"
    ),
    source=theme.source_line(consultado),
    fig=charts.trend_fig(series),
    data=trend_data,
    download_name=(
        f"umbral_rnpdno_tendencia_{cve}_{months[0]}_{months[-1]}"
        f"_c{consultado}.csv"
    ),
    key="est-trend",
)
st.caption(
    f"{theme.fmt(undated_total)} registros de {entidad_label} sin fecha "
    "de hechos no aparecen en esta serie; se detallan al final de la "
    "página."
)
st.divider()

# ── Categoría × sexo ────────────────────────────────────────────────
SEXO_ORDER = {"HOMBRE": 0, "MUJER": 1, "INDETERMINADO": 2, "": 3}
bd = (
    rows.groupby(["categoria", "sexo"], as_index=False)["conteo"].sum()
)
bd["sexo_label"] = bd["sexo"].map(
    lambda s: theme.SEXO_LABELS.get(s, "Sin desglose")
)
bd = bd.sort_values(
    ["categoria", "sexo"],
    key=lambda col: col.map(SEXO_ORDER) if col.name == "sexo" else col.map(
        {c: i for i, c in enumerate(theme.CATEGORIA_LABELS)}
    ),
)

desap = bd[bd["categoria"] == "DESAPARECIDA_O_NO_LOCALIZADA"]
if not desap.empty and desap["conteo"].sum() > 0:
    lead = desap.loc[desap["conteo"].idxmax()]
    pct = lead["conteo"] / desap["conteo"].sum() * 100
    title = (
        f"El {pct:,.0f}% de los registros de personas desaparecidas o no "
        f"localizadas en {entidad_label} corresponde a "
        f"{lead['sexo_label'].lower()}"
    )
else:
    title = (
        f"Registros de {entidad_label} por categoría y sexo, "
        f"{f.periodo_label}"
    )
theme.chart_frame(
    title=title,
    subtitle=(
        f"{entidad_label} · {f.periodo_label} · solo registros con fecha "
        "de hechos"
    ),
    source=theme.source_line(consultado),
    fig=charts.cat_sexo_fig(bd),
    data=bd[["categoria", "sexo_label", "conteo"]],
    download_name=(
        f"umbral_rnpdno_categoria_sexo_{cve}_{f.periodo_ini}"
        f"_{f.periodo_fin}_c{consultado}.csv"
    ),
    key="est-catsexo",
)
notas = [
    f"Los {theme.fmt(undated_total)} registros sin fecha de hechos no "
    "tienen desglose de sexo y quedan fuera de esta gráfica."
]
residual_aqui = int(rows.loc[rows["sexo"] == "", "conteo"].sum())
if residual_aqui:
    notas.append(
        f"«Sin desglose» agrupa {theme.fmt(residual_aqui)} registros que "
        "la fuente no reparte por municipio ni sexo."
    )
st.caption(" ".join(notas))
st.divider()

# ── Municipios ──────────────────────────────────────────────────────
if cve == "33":
    with st.container(border=True):
        st.markdown("### Sin desglose municipal")
        st.markdown(
            "Estos registros corresponden a personas cuya entidad se "
            "desconoce; su único «municipio» en la fuente es "
            "**Se desconoce**, por lo que aquí no hay desglose municipal. "
            "Ubicación desconocida no es cero: por eso esta entidad se "
            "reporta como una más."
        )
else:
    mun = (
        rows.groupby(["cve_municipio", "municipio"], as_index=False)["conteo"]
        .sum()
        .sort_values("conteo", ascending=False)
    )
    mun["municipio_label"] = mun["municipio"].map(theme.title_es)
    total_estado = max(int(mun["conteo"].sum()), 1)
    mun["porcentaje"] = (mun["conteo"] / total_estado * 100).round(1)
    top = mun.iloc[0]
    top15 = mun.head(15)
    theme.chart_frame(
        title=(
            f"{top['municipio_label']} concentra el {top['porcentaje']:,.1f}% "
            f"de los registros de {entidad_label} en {f.periodo_label}"
        ),
        subtitle=(
            f"Los 15 municipios con más registros de {len(mun)} con "
            "registros en el periodo · la tabla y el CSV incluyen todos"
        ),
        source=theme.source_line(consultado),
        fig=charts.ranking_fig(
            top15,
            value_col="conteo",
            text=[f"{int(v):,}" for v in top15.sort_values("conteo")["conteo"]],
            hover=[
                f"{int(v):,} registros · {p:,.1f}% del estado"
                for v, p in zip(
                    top15.sort_values("conteo")["conteo"],
                    top15.sort_values("conteo")["porcentaje"],
                )
            ],
            highlight_key=top["cve_municipio"],
            key_col="cve_municipio",
            label_col="municipio_label",
        ),
        data=mun[["cve_municipio", "municipio", "conteo", "porcentaje"]],
        download_name=(
            f"umbral_rnpdno_municipios_{cve}_{f.periodo_ini}"
            f"_{f.periodo_fin}_c{consultado}.csv"
        ),
        key="est-mun",
    )
    if (mun["municipio"] == "MUNICIPIO NO DESGLOSADO").any():
        nd = int(
            mun.loc[mun["municipio"] == "MUNICIPIO NO DESGLOSADO", "conteo"]
            .sum()
        )
        st.caption(
            f"«Municipio no desglosado» agrupa {theme.fmt(nd)} registros "
            "que la fuente no reparte por municipio."
        )
    st.caption(
        "Conteos agregados por municipio (clave INEGI en el CSV); el "
        "registro público no contiene ni permite ubicar casos "
        "individuales."
    )
st.divider()

# ── Registros sin fecha de hechos ───────────────────────────────────
# Un hecho del estado completo: independiente de los filtros de
# periodo/categoría/sexo (el hueco es del registro, no de la selección).
dated_estado_full = int(
    dated.loc[dated["cve_entidad"] == cve, "conteo"].sum()
)
undated_full = undated[undated["cve_entidad"] == cve]
undated_full_total = int(undated_full["conteo"].sum())
registro_total = dated_estado_full + undated_full_total
pct_sf = undated_full_total / max(registro_total, 1) * 100

with st.container(border=True):
    st.markdown(
        f"### El {pct_sf:,.1f}% del registro de {entidad_label} "
        "no tiene fecha de hechos"
    )
    st.caption(
        f"{theme.fmt(undated_full_total)} de {theme.fmt(registro_total)} "
        "registros carecen de fecha de hechos: no aparecen en ninguna "
        "serie mensual ni en el desglose municipal o por sexo (la fuente "
        "solo expone este bloque por categoría). Todo el registro del "
        "estado, sin filtros."
    )
    cols = st.columns(3)
    for col, cat in zip(cols, theme.CATEGORIA_LABELS):
        val = int(
            undated_full.loc[undated_full["categoria"] == cat, "conteo"].sum()
        )
        col.metric(theme.CATEGORIA_LABELS[cat], theme.fmt(val))
    st.markdown(
        f'<p class="u-source">{theme.source_line(consultado)}</p>',
        unsafe_allow_html=True,
    )
    st.download_button(
        "Descargar CSV sin fecha",
        undated_full.to_csv(index=False).encode("utf-8"),
        file_name=f"umbral_rnpdno_sin_fecha_{cve}_c{consultado}.csv",
        mime="text/csv",
        key="est-sf-csv",
    )
