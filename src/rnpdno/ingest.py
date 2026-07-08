"""Fetch RNPDNO Versión Estadística data and cache raw responses.

For a single entidad x month slice this fetches:
- Totales, with mostrarFechaNula=0 and =1 (the pair feeds the SIN_FECHA
  bucket: undated records = flag-on minus flag-off),
- AreaChartSexoMeses (all statuses),
- TablaDetalle (TipoDetalle=3, municipios) once per categoría
  (idEstatusVictima=7/2/3) — the complete municipio table; the bar
  chart endpoint truncates to the top 30 municipios,
- the municipio catalog for the state.
Verbatim response bodies are written to data/raw/ before any parsing.

Usage:
    python -m rnpdno.ingest --estado 1 --mes 2024-01
"""

import argparse
import calendar
import json
import sys
import time
from datetime import datetime, timezone

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from rnpdno.catalogs import CATEGORIAS, ENTIDADES
from rnpdno.config import (
    CATALOGO_MUNICIPIOS,
    DASHBOARD_PAGE,
    DEFAULT_PAYLOAD,
    ENDPOINTS,
    RAW_DIR,
    REQUEST_DELAY_SECONDS,
    TIPO_DETALLE_MUNICIPIOS,
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def make_session() -> requests.Session:
    """Create a session primed with the dashboard's cookies and headers."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    # GET the dashboard page first so the server sets session cookies.
    # NOTE: must look like a normal page load — sending AJAX headers
    # (X-Requested-With/Referer) here makes the server return an empty
    # page without the .AspNet.ApplicationCookie, and all subsequent
    # POSTs then return empty 200s.
    resp = session.get(DASHBOARD_PAGE, timeout=30)
    resp.raise_for_status()
    if ".AspNet.ApplicationCookie" not in session.cookies:
        raise RuntimeError("dashboard GET did not set expected session cookies")
    return session


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    reraise=True,
)
def post_endpoint(session: requests.Session, url: str, payload: dict) -> requests.Response:
    resp = session.post(
        url,
        json=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Referer": DASHBOARD_PAGE,
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=60,
    )
    resp.raise_for_status()
    # The server occasionally returns an empty 200; treat as retryable.
    if not resp.content:
        raise ValueError(f"empty response body from {url}")
    resp.json()  # raises if body is not valid JSON
    return resp


def cache_response(slice_dir, name: str, resp: requests.Response, payload: dict) -> None:
    """Write the verbatim response body plus a metadata sidecar."""
    slice_dir.mkdir(parents=True, exist_ok=True)
    (slice_dir / f"{name}.json").write_bytes(resp.content)
    meta = {
        "url": resp.request.url,
        "payload": payload,
        "status_code": resp.status_code,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    (slice_dir / f"{name}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2)
    )


def fetch_slice(id_estado: str, fecha_inicio: str, fecha_fin: str) -> dict:
    """Fetch all spike endpoints for one entidad x date range; cache raw.

    Returns the parsed Totales response for quick validation.
    """
    base = dict(DEFAULT_PAYLOAD, idEstado=id_estado,
                fechaInicio=fecha_inicio, fechaFin=fecha_fin)
    # e.g. data/raw/estado=1/2024-01/
    slice_dir = RAW_DIR / f"estado={id_estado}" / fecha_inicio[:7]

    # (cache file name, url, payload)
    tasks = [
        ("Totales", ENDPOINTS["Totales"], base),
        ("Totales_fechaNula", ENDPOINTS["Totales"], dict(base, mostrarFechaNula="1")),
        ("AreaChartSexoMeses", ENDPOINTS["AreaChartSexoMeses"], base),
        ("CatalogoMunicipios", CATALOGO_MUNICIPIOS, {"idEstado": id_estado}),
    ]
    for id_estatus in CATEGORIAS.values():
        tasks.append((
            f"TablaDetalle_estatus={id_estatus}",
            ENDPOINTS["TablaDetalle"],
            dict(base, idEstatusVictima=id_estatus,
                 TipoDetalle=TIPO_DETALLE_MUNICIPIOS),
        ))

    session = make_session()
    time.sleep(REQUEST_DELAY_SECONDS)

    totales = None
    for name, url, payload in tasks:
        print(f"POST {url} -> {name}", file=sys.stderr)
        resp = post_endpoint(session, url, payload)
        cache_response(slice_dir, name, resp, payload)
        if name == "Totales":
            totales = resp.json()
        time.sleep(REQUEST_DELAY_SECONDS)

    print(f"cached to {slice_dir}", file=sys.stderr)
    return totales


def month_bounds(mes: str) -> tuple[str, str]:
    """'2024-01' -> ('2024-01-01', '2024-01-31')."""
    year, month = int(mes[:4]), int(mes[5:7])
    last = calendar.monthrange(year, month)[1]
    return f"{mes}-01", f"{mes}-{last:02d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and cache one RNPDNO entidad x month slice.")
    parser.add_argument("--estado", required=True, choices=sorted(ENTIDADES),
                        metavar="ID", help="INEGI entidad code (1-32, 33=entidad no especificada)")
    parser.add_argument("--mes", required=True, metavar="YYYY-MM",
                        help="month to fetch, e.g. 2024-01")
    args = parser.parse_args()
    try:
        datetime.strptime(args.mes, "%Y-%m")
    except ValueError:
        parser.error(f"--mes must be YYYY-MM, got {args.mes!r}")
    return args


def main() -> None:
    args = parse_args()
    fecha_inicio, fecha_fin = month_bounds(args.mes)
    totales = fetch_slice(id_estado=args.estado,
                          fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
    print(json.dumps(totales, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
