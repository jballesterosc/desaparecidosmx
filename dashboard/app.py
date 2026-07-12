"""umbral_ · RNPDNO monitor — entry point.

Run from the repo root so .streamlit/config.toml applies:

    .venv/bin/streamlit run dashboard/app.py
"""

import os

# pyarrow 25's bundled mimalloc corrupts memory in this app (segfaults
# in Arrow-string compares and st.dataframe serialization, reproduced
# on Linux 3.13 and macOS 3.14) — force the system allocator. The env
# var must be set before pyarrow is first imported; the
# set_memory_pool call below covers the case where it already was.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import faulthandler

import pyarrow as pa
import streamlit as st

import theme

# Dump the Python stack to stderr if a native extension crashes the
# process, so hosted logs show more than "Segmentation fault".
faulthandler.enable()
pa.set_memory_pool(pa.system_memory_pool())

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
