"""Orchestrator: ingest -> export -> combine for a set of slices.

Log-and-continue: a failing slice is recorded and skipped, the batch
keeps going, and a pass/fail summary is printed at the end (exit code 1
if anything failed). Ingest is skipped for slices whose raw cache is
already complete (pass --refetch to force), so an interrupted batch can
be re-run with the same arguments and resume where it stopped.

Combines run last, over the *full* entidad set regardless of --estados:
the all-states artifact means all states, and combine refuses to write
a partial national file (see combine.py). Yearly files are only built
for periodos given as a bare year.

Usage:
    python -m rnpdno.run --estados all --periodos 2024
    python -m rnpdno.run --estados 1,15,33 --periodos 2024-01,2024-02
"""

import argparse
import sys
from datetime import datetime

from rnpdno.catalogs import ENTIDADES
from rnpdno.combine import combine_month, combine_year
from rnpdno.export import export_slice
from rnpdno.ingest import fetch_slice, month_bounds, slice_cache_complete


def parse_estados(value: str) -> list[str]:
    if value == "all":
        return sorted(ENTIDADES, key=int)
    ids = [tok.strip() for tok in value.split(",") if tok.strip()]
    unknown = [i for i in ids if i not in ENTIDADES]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown estado id(s) {unknown}; valid: 1-32, 33, or 'all'")
    return ids


def parse_periodos(value: str) -> tuple[list[str], list[str]]:
    """'2024,2025-01' -> (months, full years). YYYY expands to 12 months."""
    months, years = [], []
    for tok in (t.strip() for t in value.split(",") if t.strip()):
        if len(tok) == 4 and tok.isdigit():
            years.append(tok)
            months.extend(f"{tok}-{m:02d}" for m in range(1, 13))
            continue
        try:
            datetime.strptime(tok, "%Y-%m")
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"periodo must be YYYY or YYYY-MM, got {tok!r}")
        months.append(tok)
    return sorted(set(months)), sorted(set(years))


class Runner:
    """Tracks per-step outcomes for the end-of-run summary."""

    def __init__(self) -> None:
        self.ok: dict[str, int] = {}
        self.failures: list[tuple[str, str, str]] = []  # (step, scope, error)
        self.skipped: list[tuple[str, str, str]] = []   # (step, scope, reason)

    def attempt(self, step: str, scope: str, fn) -> bool:
        try:
            fn()
        except Exception as exc:  # log-and-continue by design
            self.failures.append((step, scope, f"{type(exc).__name__}: {exc}"))
            print(f"FAILED {step} {scope}: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            return False
        self.ok[step] = self.ok.get(step, 0) + 1
        return True

    def skip(self, step: str, scope: str, reason: str) -> None:
        self.skipped.append((step, scope, reason))

    def summary(self) -> str:
        lines = ["", "== run summary =="]
        for step in ("ingest", "export", "combine"):
            n_ok = self.ok.get(step, 0)
            n_fail = sum(1 for s, _, _ in self.failures if s == step)
            n_skip = sum(1 for s, _, _ in self.skipped if s == step)
            parts = [f"{n_ok} ok"]
            if n_skip:
                parts.append(f"{n_skip} skipped")
            if n_fail:
                parts.append(f"{n_fail} FAILED")
            lines.append(f"{step:7s}: {', '.join(parts)}")
        if self.failures:
            lines.append("failures:")
            lines.extend(f"  {step:7s} {scope}: {err}"
                         for step, scope, err in self.failures)
        else:
            lines.append("all steps passed")
        return "\n".join(lines)


def run(estados: list[str], months: list[str], years: list[str],
        refetch: bool = False) -> Runner:
    runner = Runner()
    for mes in months:
        for id_estado in estados:
            scope = f"estado={id_estado} {mes}"
            if not refetch and slice_cache_complete(id_estado, mes):
                runner.skip("ingest", scope, "already cached")
                ingested = True
            else:
                fecha_inicio, fecha_fin = month_bounds(mes)
                ingested = runner.attempt(
                    "ingest", scope,
                    lambda: fetch_slice(id_estado, fecha_inicio, fecha_fin))
            if ingested:
                runner.attempt("export", scope,
                               lambda: export_slice(id_estado, mes))
            else:
                runner.skip("export", scope, "ingest failed")

    for mes in months:
        runner.attempt("combine", mes, lambda: combine_month(mes))
    for year in years:
        runner.attempt("combine", year, lambda: combine_year(year))
    return runner


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run ingest -> export -> combine for a set of "
                    "estados x periodos, log-and-continue.")
    parser.add_argument("--estados", required=True, type=parse_estados,
                        metavar="all|ID,ID,...",
                        help="'all' or comma-separated estado ids (1-32, 33)")
    parser.add_argument("--periodos", required=True, type=parse_periodos,
                        metavar="YYYY[-MM],...",
                        help="comma-separated months (YYYY-MM) and/or full "
                             "years (YYYY)")
    parser.add_argument("--refetch", action="store_true",
                        help="fetch even if the raw cache is complete")
    args = parser.parse_args()
    months, years = args.periodos

    try:
        runner = run(args.estados, months, years, refetch=args.refetch)
    except KeyboardInterrupt:
        print("\ninterrupted — raw cache is intact; re-run with the same "
              "arguments to resume", file=sys.stderr)
        sys.exit(130)
    print(runner.summary())
    sys.exit(1 if runner.failures else 0)


if __name__ == "__main__":
    main()
