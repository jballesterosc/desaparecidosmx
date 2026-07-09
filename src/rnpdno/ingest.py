"""Fetch RNPDNO Versión Estadística data and cache raw responses.

Per entidad x month slice this fetches the reconciliation set:
- Totales (mostrarFechaNula=0),
- TablaDetalle (TipoDetalle=3, municipios) once per categoría
  (idEstatusVictima=7/2/3) — the complete municipio table; the bar
  chart endpoint truncates to the top 30 municipios.

Month-invariant files are cached once per state in
data/raw/estado=<id>/ by ensure_state_cache — seeded by copying from
old-layout slices (which cached them per month) before any fetching:
- the municipio catalog,
- the Totales mostrarFechaNula=1/=0 pair behind the SIN_FECHA bucket
  (the diff is the same for any date range, so one pair per state).

One HTTP session (Fetcher) is shared across a batch run and re-primed
if it expires. Verbatim response bodies are written to data/raw/
before any parsing.

Usage:
    python -m rnpdno.ingest --estado 1 --mes 2024-01
"""

import argparse
import calendar
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

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

EXTS = (".json", ".meta.json")

# Per-month cache file names fetch_slice writes for one slice (each with
# a .meta.json sidecar). fetch_slice asserts its task list matches.
# Old-layout slices cached a superset (catalog, fechaNula, AreaChart per
# month), so they satisfy slice_cache_complete as-is and never refetch.
SLICE_CACHE_NAMES = [
    "Totales",
] + [f"TablaDetalle_estatus={v}" for v in CATEGORIAS.values()]

# Month-invariant files cached once per state in data/raw/estado=<id>/.
# Totales_fechaNula_base is the mostrarFechaNula=0 twin fetched over the
# same date range as Totales_fechaNula; sin_fecha_rows subtracts them.
STATE_CACHE_NAMES = [
    "CatalogoMunicipios", "Totales_fechaNula", "Totales_fechaNula_base",
]


def state_dir(id_estado: str) -> Path:
    return RAW_DIR / f"estado={id_estado}"


def slice_cache_complete(id_estado: str, mes: str) -> bool:
    """True if every per-month raw file for the slice is already cached."""
    slice_dir = state_dir(id_estado) / mes
    return all((slice_dir / f"{name}{ext}").is_file()
               for name in SLICE_CACHE_NAMES
               for ext in EXTS)


def state_cache_complete(id_estado: str) -> bool:
    """True if the state's month-invariant raw files are already cached."""
    d = state_dir(id_estado)
    return all((d / f"{name}{ext}").is_file()
               for name in STATE_CACHE_NAMES
               for ext in EXTS)


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


class Fetcher:
    """One HTTP session shared across a batch run.

    Primed lazily (session-cookie GET + polite delay) on first use.
    If a POST still fails after post_endpoint's retries, the session is
    re-primed once and the POST retried — the cookie may have expired
    mid-run. Every POST is followed by REQUEST_DELAY_SECONDS.
    """

    def __init__(self) -> None:
        self._session: requests.Session | None = None

    def _live_session(self) -> requests.Session:
        if self._session is None:
            self._session = make_session()
            time.sleep(REQUEST_DELAY_SECONDS)
        return self._session

    def post(self, url: str, payload: dict) -> requests.Response:
        try:
            resp = post_endpoint(self._live_session(), url, payload)
        except (requests.RequestException, ValueError):
            self._session = None
            resp = post_endpoint(self._live_session(), url, payload)
        time.sleep(REQUEST_DELAY_SECONDS)
        return resp


def cache_response(out_dir: Path, name: str, resp: requests.Response, payload: dict) -> None:
    """Write the verbatim response body plus a metadata sidecar."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_bytes(resp.content)
    meta = {
        "url": resp.request.url,
        "payload": payload,
        "status_code": resp.status_code,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / f"{name}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2)
    )


def _newest_source(month_dirs: list[Path], names: list[str]) -> Path | None:
    """Latest-fetched month dir containing every named file (+ sidecar)."""
    best, best_ts = None, ""
    for m in month_dirs:
        if not all((m / f"{n}{ext}").is_file() for n in names for ext in EXTS):
            continue
        meta = json.loads((m / f"{names[0]}.meta.json").read_text())
        ts = meta.get("fetched_at", "")
        if ts >= best_ts:
            best, best_ts = m, ts
    return best


def _seed_state_cache_from_slices(id_estado: str) -> None:
    """Copy month-invariant files from old-layout slices into the state dir.

    Old-layout slices cached the municipio catalog and the fechaNula
    pair per month; any copy will do (catalog responses are identical
    across months, the fechaNula diff is range-invariant), so the most
    recently fetched one is used. The fechaNula pair is copied from a
    single slice so both sides cover the same date range. No network.
    """
    d = state_dir(id_estado)
    if not d.is_dir():
        return
    month_dirs = sorted(p for p in d.glob("*-*") if p.is_dir())

    def copy(src_dir: Path, src: str, dst: str) -> None:
        for ext in EXTS:
            shutil.copy2(src_dir / f"{src}{ext}", d / f"{dst}{ext}")

    if not all((d / f"CatalogoMunicipios{ext}").is_file() for ext in EXTS):
        src = _newest_source(month_dirs, ["CatalogoMunicipios"])
        if src:
            copy(src, "CatalogoMunicipios", "CatalogoMunicipios")
            print(f"seeded CatalogoMunicipios for estado={id_estado} "
                  f"from cached slice {src.name}", file=sys.stderr)

    pair = ("Totales_fechaNula", "Totales_fechaNula_base")
    if not all((d / f"{n}{ext}").is_file() for n in pair for ext in EXTS):
        src = _newest_source(month_dirs, ["Totales_fechaNula", "Totales"])
        if src:
            copy(src, "Totales_fechaNula", "Totales_fechaNula")
            copy(src, "Totales", "Totales_fechaNula_base")
            print(f"seeded fechaNula pair for estado={id_estado} "
                  f"from cached slice {src.name}", file=sys.stderr)


def ensure_state_cache(id_estado: str, mes: str,
                       fetcher: Fetcher | None = None,
                       refetch: bool = False) -> None:
    """Make the state's month-invariant raw files available.

    Seeds from already-cached old-layout slices first; fetches only
    what is still missing. `mes` supplies the date range for a fresh
    fechaNula pair — the SIN_FECHA diff is the same for any range
    (see transform.sin_fecha_rows), so any month works.
    """
    if not refetch:
        if state_cache_complete(id_estado):
            return
        _seed_state_cache_from_slices(id_estado)
        if state_cache_complete(id_estado):
            return

    fecha_inicio, fecha_fin = month_bounds(mes)
    base = dict(DEFAULT_PAYLOAD, idEstado=id_estado,
                fechaInicio=fecha_inicio, fechaFin=fecha_fin)
    tasks = [
        ("CatalogoMunicipios", CATALOGO_MUNICIPIOS, {"idEstado": id_estado}),
        ("Totales_fechaNula", ENDPOINTS["Totales"], dict(base, mostrarFechaNula="1")),
        ("Totales_fechaNula_base", ENDPOINTS["Totales"], base),
    ]
    assert [name for name, _, _ in tasks] == STATE_CACHE_NAMES

    fetcher = fetcher or Fetcher()
    d = state_dir(id_estado)
    for name, url, payload in tasks:
        if not refetch and all((d / f"{name}{ext}").is_file() for ext in EXTS):
            continue  # partially seeded; fetch only the gaps
        print(f"POST {url} -> {name}", file=sys.stderr)
        resp = fetcher.post(url, payload)
        cache_response(d, name, resp, payload)


def fetch_slice(id_estado: str, fecha_inicio: str, fecha_fin: str,
                fetcher: Fetcher | None = None) -> dict:
    """Fetch the per-month endpoints for one entidad x date range; cache raw.

    Month-invariant state-level files (municipio catalog, fechaNula
    pair) are handled separately by ensure_state_cache.
    Returns the parsed Totales response for quick validation.
    """
    base = dict(DEFAULT_PAYLOAD, idEstado=id_estado,
                fechaInicio=fecha_inicio, fechaFin=fecha_fin)
    # e.g. data/raw/estado=1/2024-01/
    slice_dir = state_dir(id_estado) / fecha_inicio[:7]

    # (cache file name, url, payload)
    tasks = [
        ("Totales", ENDPOINTS["Totales"], base),
    ]
    for id_estatus in CATEGORIAS.values():
        tasks.append((
            f"TablaDetalle_estatus={id_estatus}",
            ENDPOINTS["TablaDetalle"],
            dict(base, idEstatusVictima=id_estatus,
                 TipoDetalle=TIPO_DETALLE_MUNICIPIOS),
        ))

    assert [name for name, _, _ in tasks] == SLICE_CACHE_NAMES

    fetcher = fetcher or Fetcher()
    totales = None
    for name, url, payload in tasks:
        print(f"POST {url} -> {name}", file=sys.stderr)
        resp = fetcher.post(url, payload)
        cache_response(slice_dir, name, resp, payload)
        if name == "Totales":
            totales = resp.json()

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
    fetcher = Fetcher()
    ensure_state_cache(args.estado, args.mes, fetcher)
    fecha_inicio, fecha_fin = month_bounds(args.mes)
    totales = fetch_slice(id_estado=args.estado, fecha_inicio=fecha_inicio,
                          fecha_fin=fecha_fin, fetcher=fetcher)
    print(json.dumps(totales, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
