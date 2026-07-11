"""Datos y método — descargas, diccionario de datos, metodología, cita."""

import streamlit as st

import data
import theme

REPO_URL = "https://github.com/jballesterosc/desaparecidosmx"

st.title("Datos y método")
consultado = data.consultado_en()
st.caption(
    f"Todos los números provienen del RNPDNO consultado el {consultado} "
    f"(snapshot rnpdno-{consultado[:7]}). Pipeline, datos y documentación "
    f"completa: [{REPO_URL}]({REPO_URL})."
)

# ── Descargas ───────────────────────────────────────────────────────
st.markdown("### Descargas")
st.markdown(
    "Archivos anuales combinados (las 33 entidades × 12 meses, más el "
    "bloque sin fecha de cada estado exactamente una vez, distinguible "
    "por `periodo = SIN_FECHA`). Son los mismos artefactos que produce "
    "el pipeline, byte por byte."
)
cols = st.columns(6)
for i, year in enumerate(data.YEARS):
    path = data.ALL_STATES_DIR / f"{year}.csv"
    cols[i % 6].download_button(
        str(year),
        path.read_bytes(),
        file_name=f"umbral_rnpdno_all-states_{year}_c{consultado}.csv",
        mime="text/csv",
        key=f"dl-{year}",
    )
st.download_button(
    "Población por entidad 2010–2026 (CONAPO, rev. 2023)",
    (data.REPO_ROOT / "data" / "reference" / "poblacion_entidades.csv")
    .read_bytes(),
    file_name="umbral_poblacion_entidades_conapo_rev2023.csv",
    mime="text/csv",
    key="dl-pob",
)
st.divider()

# ── Lo que hay que saber antes de citar ─────────────────────────────
st.markdown("### Antes de citar estos números")
st.markdown(
    """
1. **El filtro de fecha es sobre la *fecha de hechos*** (cuándo ocurrió),
   no la fecha de registro. Un mes reciente se sigue llenando durante
   meses o años: por eso las series marcan la cola como *provisional*.
2. **Un mes puede ser una fracción pequeña del registro de un estado.**
   Dos mecanismos: registros **sin fecha de hechos** (Estado de México:
   ~22 mil sin fecha contra ~500 fechados por mes) y hechos en otros
   periodos. Nunca sume unos cuantos meses y lo llame total estatal.
3. **El registro es vivo.** Los conteos del mismo periodo cambian entre
   consultas (altas, fechado tardío, reclasificación); cada fila lleva
   `consultado_en`. Comparaciones entre consultas distintas no son
   equivalentes.
4. **Entidad 33 = «Entidad no especificada»** (no es clave INEGI):
   registros cuya entidad se desconoce. Ubicación desconocida no es
   cero.
5. **Los conteos se reconcilian**: cada corte entidad × mes debe sumar
   exactamente el total que muestra el propio dashboard del RNPDNO; las
   tres categorías particionan ese total.
"""
)
st.divider()

# ── Diccionario de datos ────────────────────────────────────────────
st.markdown("### Diccionario de datos")
st.markdown(
    "Una fila por **entidad × mes × categoría × sexo × municipio**; la "
    "ausencia de fila significa cero. Esquema completo en "
    f"[docs/data_dictionary.md]({REPO_URL}/blob/main/docs/data_dictionary.md)."
)
st.markdown(
    """
| columna | ejemplo | nota |
|---|---|---|
| `cve_entidad` | `01` | clave INEGI; `33` = entidad no especificada |
| `entidad` | `AGUASCALIENTES` | nombre según el dashboard |
| `periodo` | `2024-01` | mes de la fecha de hechos, o `SIN_FECHA` |
| `categoria` | `DESAPARECIDA_O_NO_LOCALIZADA` | también `LOCALIZADA_CON_VIDA`, `LOCALIZADA_SIN_VIDA` |
| `sexo` | `MUJER` | vacío en filas residuales y `SIN_FECHA` |
| `cve_municipio` | `01005` | clave INEGI de 5 dígitos |
| `municipio` | `JESÚS MARÍA` | o `MUNICIPIO NO DESGLOSADO` (residual) |
| `conteo` | `12` | registros en esa combinación |
| `consultado_en` | `2026-07-08` | fecha UTC de consulta al API |
"""
)
st.caption(
    "La fuente no permite separar «desaparecida» de «no localizada» al "
    "grano municipio × sexo, ni desglosar el bloque sin fecha por sexo o "
    "municipio."
)
st.divider()

# ── Método ──────────────────────────────────────────────────────────
st.markdown("### Método, en corto")
st.markdown(
    f"""
El RNPDNO solo publica agregados por combinación de filtros — no hay
export masivo ni microdatos. El pipeline reproduce las llamadas
internas del dashboard **Versión Estadística**, guarda cada respuesta
cruda antes de procesarla, itera con pausas de cortesía, y valida que
cada corte reconcilie con los totales del propio dashboard (si no,
falla). El detalle — endpoints, el bloque sin fecha como diferencia de
totales, invariantes — está en
[docs/methodology.md]({REPO_URL}/blob/main/docs/methodology.md); las
decisiones y sus porqués, en
[docs/DECISIONS.md]({REPO_URL}/blob/main/docs/DECISIONS.md).
"""
)
st.divider()

# ── Cómo citar ──────────────────────────────────────────────────────
st.markdown("### Cómo citar")
st.code(
    "Umbral (2026). Registros del RNPDNO por entidad, mes, categoría, "
    f"sexo y municipio (snapshot rnpdno-{consultado[:7]}, consultado "
    f"{consultado}). Datos fuente: RNPDNO, Comisión Nacional de "
    f"Búsqueda / SEGOB. {REPO_URL} · Datos CC BY 4.0, código MIT.",
    language=None,
    wrap_lines=True,
)
st.caption(
    "Los datos procesados se publican bajo CC BY 4.0 y el código bajo "
    "MIT. La fuente original es pública; al citar, nombre siempre al "
    "RNPDNO y la fecha de consulta."
)
