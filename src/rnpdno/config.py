"""Configuration for the RNPDNO Versión Estadística pipeline.

Endpoint and payload structure discovered by inspecting the dashboard's
internal XHR calls (see docs/methodology.md). All data endpoints are
POST + JSON under the same host; no auth, but we mimic the browser by
establishing a session cookie and sending a Referer.
"""

import os
from pathlib import Path

BASE_URL = "https://versionpublicarnpdno.segob.gob.mx"

# GET this first to pick up session cookies; also used as Referer.
DASHBOARD_PAGE = f"{BASE_URL}/Dashboard/Sociodemografico"

# Data endpoints (all POST, JSON body, same payload schema).
# NOTE: casing is inconsistent on the server ("Sociodemografico" vs
# "SocioDemografico") — these paths are verbatim from the page's JS bundle.
ENDPOINTS = {
    "Totales": f"{BASE_URL}/Sociodemografico/Totales",
    "AreaChartSexoMeses": f"{BASE_URL}/SocioDemografico/AreaChartSexoMeses",
    # Full detail table behind "Ver detalle completo". Same payload plus
    # TipoDetalle (3 = municipios). Returns {"Title", "Html"} where Html
    # is a complete table (NOT truncated to top 30 like the bar charts).
    "TablaDetalle": f"{BASE_URL}/SocioDemografico/TablaDetalle",
}

# TipoDetalle values for TablaDetalle (from the page's MostrarTablaDetalle).
TIPO_DETALLE_MUNICIPIOS = 3

# Catalog endpoint; POST {"idEstado": "<n>"} -> [{"Value": int, "Text": str}].
# Value is the INEGI municipio code within the state.
CATALOGO_MUNICIPIOS = f"{BASE_URL}/Catalogo/Municipios"

REQUEST_DELAY_SECONDS = float(os.environ.get("REQUEST_DELAY_SECONDS", "2.0"))

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"

# Every field is sent as a string; empty string means "no filter".
# idEstatusVictima: 0=todas, 7=desaparecidas+no localizadas, 6=localizadas,
#                   2=localizadas con vida, 3=localizadas sin vida.
# idEstado: INEGI entidad code (1..32), 0=todos, 33=se desconoce.
# Dates: ISO yyyy-mm-dd (dd/mm/yyyy also accepted by the server).
DEFAULT_PAYLOAD = {
    "titulo": "",
    "subtitulo": "",
    "idEstatusVictima": "0",
    "fechaInicio": "",
    "fechaFin": "",
    "idEstado": "0",
    "idMunicipio": "0",
    "mostrarFechaNula": "0",
    "idColonia": "0",
    "idNacionalidad": "0",
    "edadInicio": "",
    "edadFin": "",
    "mostrarEdadNula": "0",
    "idHipotesis": "",
    "idMedioConocimiento": "",
    "idCircunstancia": "",
    "tieneDiscapacidad": "",
    "idTipoDiscapacidad": "",
    "idEtnia": "",
    "idLengua": "",
    "idReligion": "",
    "esMigrante": "",
    "idEstatusMigratorio": "",
    "esLgbttti": "",
    "esServidorPublico": "",
    "esDefensorDH": "",
    "esPeriodista": "",
    "esSindicalista": "",
    "esONG": "",
    "idHipotesisNoLocalizacion": "",
    "idDelito": "",
}
