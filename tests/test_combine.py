"""Combine tests against synthetic per-state CSVs in a tmp dir.

No network, no data/raw/: combine reads only data/processed/, so these
build a fake processed tree and monkeypatch PROCESSED_DIR.
"""

import csv

import pytest

from rnpdno import combine
from rnpdno.combine import MissingInputError, combine_month, combine_year
from rnpdno.transform import COLUMNS


def _row(cve, entidad, periodo, conteo, **overrides):
    row = {
        "cve_entidad": cve, "entidad": entidad, "periodo": periodo,
        "categoria": "DESAPARECIDA_O_NO_LOCALIZADA", "sexo": "MUJER",
        "cve_municipio": f"{cve}001", "municipio": "CENTRO",
        "conteo": str(conteo), "consultado_en": "2026-07-08",
    }
    row.update(overrides)
    return row


def _write(path, rows, columns=COLUMNS):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def processed(tmp_path, monkeypatch):
    monkeypatch.setattr(combine, "PROCESSED_DIR", tmp_path)
    _write(tmp_path / "01" / "2024-01.csv",
           [_row("01", "AGUASCALIENTES", "2024-01", 4)])
    _write(tmp_path / "02" / "2024-01.csv",
           [_row("02", "BAJA CALIFORNIA", "2024-01", 7),
            _row("02", "BAJA CALIFORNIA", "2024-01", 2, sexo="HOMBRE")])
    for cve, entidad in (("01", "AGUASCALIENTES"), ("02", "BAJA CALIFORNIA")):
        for m in range(2, 13):
            _write(tmp_path / cve / f"2024-{m:02d}.csv",
                   [_row(cve, entidad, f"2024-{m:02d}", 1)])
        _write(tmp_path / cve / "sin-fecha.csv",
               [_row(cve, entidad, "SIN_FECHA", 100,
                     sexo="", cve_municipio="", municipio="")])
    return tmp_path


def _read(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_combine_month(processed):
    out = combine_month("2024-01", entidades=["1", "2"])
    rows = _read(out)
    assert out == processed / "all-states" / "2024-01.csv"
    # Every input row carried through, nothing added or dropped.
    assert len(rows) == 3
    assert sum(int(r["conteo"]) for r in rows) == 13
    assert [r["cve_entidad"] for r in rows] == ["01", "02", "02"]
    # Monthly combined files are dated-only.
    assert all(r["periodo"] == "2024-01" for r in rows)


def test_combine_year_includes_sin_fecha_once(processed):
    rows = _read(combine_year("2024", entidades=["1", "2"]))
    sin_fecha = [r for r in rows if r["periodo"] == "SIN_FECHA"]
    assert [r["cve_entidad"] for r in sin_fecha] == ["01", "02"]
    # 3 rows for 2024-01 + 2 states x 11 months + 2 sin-fecha rows.
    assert len(rows) == 3 + 22 + 2
    assert sum(int(r["conteo"]) for r in rows) == 13 + 22 + 200


def test_missing_input_refuses_to_write(processed):
    (processed / "02" / "2024-01.csv").unlink()
    with pytest.raises(MissingInputError, match="02/2024-01.csv"):
        combine_month("2024-01", entidades=["1", "2"])
    assert not (processed / "all-states" / "2024-01.csv").exists()


def test_header_mismatch_rejected(processed):
    _write(processed / "02" / "2024-01.csv",
           [{"foo": "1"}], columns=["foo"])
    with pytest.raises(ValueError, match="header"):
        combine_month("2024-01", entidades=["1", "2"])
