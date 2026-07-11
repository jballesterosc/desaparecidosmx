"""Build data/reference/poblacion_entidades.csv from CONAPO open data.

Source: CONAPO, Conciliación Demográfica de México 1950-2019 y
Proyecciones de la Población de México y de las Entidades Federativas
2020-2070 (revisión 2023) — población a mitad de año, by single age
and sex. We aggregate to entidad × year totals for 2010-2026.

The vintage travels inside the output file (`fuente` column) so a
downloaded CSV stays self-describing; estado 33 (ENTIDAD NO
ESPECIFICADA) deliberately has no population row.

Usage:  python scripts/build_population_reference.py
"""

import io
import sys
from pathlib import Path

import pandas as pd
import requests

URL = (
    "https://conapo.segob.gob.mx/work/models/CONAPO/Datos_Abiertos/"
    "pry23/00_Pob_Mitad_1950_2070.csv"
)
FUENTE = (
    "CONAPO, Proyecciones de la Población de México y de las Entidades "
    "Federativas 2020-2070 (revisión 2023), población a mitad de año"
)
YEARS = range(2010, 2027)
OUT = Path(__file__).resolve().parents[1] / "data" / "reference" / \
    "poblacion_entidades.csv"


def main() -> None:
    print(f"Downloading {URL} …", file=sys.stderr)
    # Government TLS chain is incomplete; the data is public and the
    # aggregate is sanity-checked below.
    resp = requests.get(URL, timeout=300, verify=False)
    resp.raise_for_status()
    raw = pd.read_csv(io.BytesIO(resp.content), encoding="utf-8-sig")

    states = raw[raw["CVE_GEO"].between(1, 32) & raw["AÑO"].isin(YEARS)]
    pop = (
        states.groupby(["CVE_GEO", "ENTIDAD", "AÑO"], as_index=False)["POBLACION"]
        .sum()
        .rename(columns={
            "CVE_GEO": "cve_entidad", "ENTIDAD": "entidad",
            "AÑO": "anio", "POBLACION": "poblacion",
        })
    )
    pop["cve_entidad"] = pop["cve_entidad"].astype(int).astype(str).str.zfill(2)
    pop["fuente"] = FUENTE

    assert len(pop) == 32 * len(YEARS), f"expected {32*len(YEARS)} rows, got {len(pop)}"
    nat_2026 = pop.loc[pop["anio"] == 2026, "poblacion"].sum()
    assert 120_000_000 < nat_2026 < 145_000_000, f"implausible national total {nat_2026}"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pop.to_csv(OUT, index=False)
    print(f"Wrote {OUT} ({len(pop)} rows; national mid-2026 = {nat_2026:,.0f})",
          file=sys.stderr)


if __name__ == "__main__":
    main()
