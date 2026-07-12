"""umbral_ · RNPDNO monitor — entry point.

Run from the repo root so .streamlit/config.toml applies:

    .venv/bin/streamlit run dashboard/app.py
"""

import streamlit as st

import theme

st.set_page_config(
    page_title="umbral_ · RNPDNO",
    page_icon=str(theme.REPO_ROOT / "assets" / "umbral-favicon.svg"),
    layout="wide",
    initial_sidebar_state="expanded",
)
theme.inject_css()
# size="large": the lockup bakes in its clear space (one bar-height,
# umbral-brand.md §5), so the default 24px render leaves the wordmark
# too small to read.
st.logo(
    str(theme.REPO_ROOT / "assets" / "umbral-lockup-dark.svg"),
    icon_image=str(theme.REPO_ROOT / "assets" / "umbral-isotype-dark.svg"),
    size="large",
)

st.navigation(
    [
        st.Page("views/panorama.py", title="Panorama nacional", default=True),
        st.Page("views/estado.py", title="Detalle por estado"),
        st.Page("views/datos.py", title="Datos y método"),
    ]
).run()
