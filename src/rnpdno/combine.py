"""Concatenate per-state processed CSVs into all-states files.

Reads only from data/processed/ — never hits the network or data/raw/.

- data/processed/all-states/<YYYY-MM>.csv — every state's monthly CSV
  for that month, concatenated. Dated rows only, so monthly files stay
  additive across a range (DECISIONS.md #4).
- data/processed/all-states/<YYYY>.csv — every state's 12 monthly CSVs
  for that year plus its sin-fecha.csv exactly once. SIN_FECHA rows are
  present and filterable via the periodo column.

A combined file always spans the full entidad set (1-32 + 33): if any
input CSV is missing, MissingInputError is raised and nothing is
written, so a partial national file can never overwrite a complete one.

Usage:
    python -m rnpdno.combine --periodo 2024-01   # monthly file
    python -m rnpdno.combine --periodo 2024      # yearly file
"""

import argparse
import csv
import sys
from pathlib import Path

from rnpdno.catalogs import ENTIDADES, cve_entidad
from rnpdno.export import PROCESSED_DIR
from rnpdno.transform import COLUMNS

ALL_STATES_DIR_NAME = "all-states"


class MissingInputError(Exception):
    """A per-state input CSV expected by the combine is absent."""


def _read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            raise ValueError(
                f"{path}: header {reader.fieldnames} != expected {COLUMNS}")
        return list(reader)


def _gather(inputs: list[Path]) -> list[dict]:
    """Read all input CSVs, failing up front if any is missing."""
    missing = [str(p) for p in inputs if not p.is_file()]
    if missing:
        raise MissingInputError(
            f"{len(missing)} input CSV(s) missing, not combining: "
            + ", ".join(missing))
    rows = []
    for path in inputs:
        rows.extend(_read_rows(path))
    return rows


def _write_combined(out_name: str, inputs: list[Path]) -> Path:
    rows = _gather(inputs)
    out_dir = PROCESSED_DIR / ALL_STATES_DIR_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{out_name}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    total = sum(int(r["conteo"]) for r in rows)
    print(f"combined {len(inputs)} files -> {len(rows)} rows "
          f"(total conteo {total}) at {out_path}", file=sys.stderr)
    return out_path


def combine_month(periodo: str, entidades: list[str] | None = None) -> Path:
    """All states' <periodo>.csv -> all-states/<periodo>.csv (dated rows only)."""
    ids = entidades if entidades is not None else sorted(ENTIDADES, key=int)
    inputs = [PROCESSED_DIR / cve_entidad(i) / f"{periodo}.csv" for i in ids]
    return _write_combined(periodo, inputs)


def combine_year(year: str, entidades: list[str] | None = None) -> Path:
    """All states x 12 months + each state's sin-fecha.csv once
    -> all-states/<year>.csv. SIN_FECHA rows filterable via periodo."""
    ids = entidades if entidades is not None else sorted(ENTIDADES, key=int)
    inputs = []
    for i in ids:
        state_dir = PROCESSED_DIR / cve_entidad(i)
        inputs.extend(state_dir / f"{year}-{m:02d}.csv" for m in range(1, 13))
        inputs.append(state_dir / "sin-fecha.csv")
    return _write_combined(year, inputs)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Concatenate per-state processed CSVs into an "
                    "all-states file.")
    parser.add_argument("--periodo", required=True, metavar="YYYY[-MM]",
                        help="month (YYYY-MM) or full year (YYYY) to combine")
    args = parser.parse_args()
    if len(args.periodo) == 4 and args.periodo.isdigit():
        combine_year(args.periodo)
    elif len(args.periodo) == 7 and args.periodo[4] == "-":
        combine_month(args.periodo)
    else:
        parser.error(f"--periodo must be YYYY or YYYY-MM, got {args.periodo!r}")


if __name__ == "__main__":
    main()
