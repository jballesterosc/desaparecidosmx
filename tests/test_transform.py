"""Transform tests against the cached AGS x 2024-01 raw slice.

These run against data/raw/ (gitignored, never committed), so they are
skipped when the cache is absent. Populate it with:
    python -m rnpdno.ingest --estado 1 --mes 2024-01
"""

import pytest

from rnpdno.config import RAW_DIR
from rnpdno.transform import COLUMNS, sin_fecha_rows, transform_slice

AGS_SLICE = RAW_DIR / "estado=1" / "2024-01"

pytestmark = pytest.mark.skipif(
    not (AGS_SLICE / "TablaDetalle_estatus=7.json").is_file(),
    reason="AGS 2024-01 raw cache missing; run ingest first",
)


@pytest.fixture(scope="module")
def rows():
    # transform_slice raises ReconciliationError if row sums do not
    # match the cached Totales, so merely returning is itself a check.
    return transform_slice("1", "2024-01")


def test_total_matches_dashboard(rows):
    # Browser-verified TotalGlobal for Aguascalientes x January 2024.
    assert sum(r["conteo"] for r in rows) == 79


def test_row_shape(rows):
    assert rows, "expected at least one row"
    for r in rows:
        assert list(r.keys()) == COLUMNS
        assert r["cve_entidad"] == "01"
        assert r["entidad"] == "AGUASCALIENTES"
        assert r["periodo"] == "2024-01"
        # sexo is empty only on MUNICIPIO NO DESGLOSADO residual rows.
        if r["municipio"] == "MUNICIPIO NO DESGLOSADO":
            assert r["sexo"] == "" and r["cve_municipio"] == ""
        else:
            assert r["sexo"] in {"HOMBRE", "MUJER", "INDETERMINADO"}
        assert isinstance(r["conteo"], int) and r["conteo"] > 0


def test_municipio_codes_joined(rows):
    # Every AGS municipio name in this slice joins to an INEGI code
    # (residual rows, if any, are exempt).
    for r in rows:
        if r["municipio"] != "MUNICIPIO NO DESGLOSADO":
            assert r["cve_municipio"].startswith("01"), r["municipio"]


def test_categoria_partition(rows):
    per_cat = {}
    for r in rows:
        per_cat[r["categoria"]] = per_cat.get(r["categoria"], 0) + r["conteo"]
    # Known split for this slice: 4 desaparecidas/no localizadas,
    # 75 localizadas con vida, 0 sin vida (no rows).
    assert per_cat == {
        "DESAPARECIDA_O_NO_LOCALIZADA": 4,
        "LOCALIZADA_CON_VIDA": 75,
    }


def test_sin_fecha_bucket():
    rows = sin_fecha_rows("1", "2024-01")
    for r in rows:
        assert r["periodo"] == "SIN_FECHA"
        assert r["municipio"] == "" and r["sexo"] == ""
        assert r["conteo"] > 0
