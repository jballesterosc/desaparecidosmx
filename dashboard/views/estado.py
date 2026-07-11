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
