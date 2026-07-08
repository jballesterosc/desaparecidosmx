"""Write per-state monthly CSVs from normalized rows.

Usage:
    python -m rnpdno.export --estado 1 --mes 2024-01
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

from rnpdno.catalogs import ENTIDADES, cve_entidad
from rnpdno.config import REPO_ROOT
from rnpdno.transform import COLUMNS, sin_fecha_rows, transform_slice

PROCESSED_DIR = REPO_ROOT / "data" / "processed"


def _write_csv(out_path: Path, rows: list[dict]) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    total = sum(r["conteo"] for r in rows)
    print(f"wrote {len(rows)} rows (total conteo {total}) to {out_path}",
          file=sys.stderr)


def export_slice(id_estado: str, periodo: str) -> Path:
    """Transform a cached slice and write its CSVs. Returns the monthly path.

    Writes the dated-records monthly CSV plus the per-state sin-fecha.csv
    (undated records; month-independent, refreshed on every export).
    """
    rows = transform_slice(id_estado, periodo)
    out_dir = PROCESSED_DIR / cve_entidad(id_estado)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{periodo}.csv"
    _write_csv(out_path, rows)
    _write_csv(out_dir / "sin-fecha.csv", sin_fecha_rows(id_estado, periodo))
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transform a cached slice and write its per-state monthly CSV.")
    parser.add_argument("--estado", required=True, choices=sorted(ENTIDADES),
                        metavar="ID", help="INEGI entidad code (1-32, 33=entidad no especificada)")
    parser.add_argument("--mes", required=True, metavar="YYYY-MM",
                        help="month to export, e.g. 2024-01")
    args = parser.parse_args()
    try:
        datetime.strptime(args.mes, "%Y-%m")
    except ValueError:
        parser.error(f"--mes must be YYYY-MM, got {args.mes!r}")
    export_slice(id_estado=args.estado, periodo=args.mes)


if __name__ == "__main__":
    main()
