"""Read state per-capita NSDP (current prices) from the Economic Survey 2023-24 table 1.11A.

Used for beta2 (benefit value relative to income). Source: state Directorate of Economics
& Statistics via the Economic Survey statistical appendix. One common year (2021-22) is
used for every state because 2022-23 and 2023-24 have gaps. Ladakh, Lakshadweep and
Dadra & Nagar Haveli and Daman & Diu are not in the table: their value stays null.
Needs `pdftotext` (data scripts only, D-029).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "data" / "raw" / "income" / "tab111a.pdf"
OUT = ROOT / "data" / "processed" / "state_income.parquet"
YEAR_COL = 7  # 2021-22 is the 7th of 9 year columns (2015-16 .. 2023-24); list index 6
RENAME = {
    "Delhi": "NCT Delhi",
    "Jammu & Kashmir-UT*": "Jammu & Kashmir",
    "Andaman & Nicobar": "Andaman & Nicobar Islands",
}
ROW_RE = re.compile(r"^\s*([A-Za-z][A-Za-z &*\-]+?)\s{2,}((?:(?:\d+|NA)\s+){8}(?:\d+|NA))\s*$")


def parse_text(text: str) -> list[dict[str, object]]:
    rows = []
    for line in text.splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        vals = m.group(2).split()
        v = vals[YEAR_COL - 1]
        rows.append(
            {
                "state": RENAME.get(m.group(1).strip(), m.group(1).strip()),
                "per_capita_nsdp_2021_22": None if v == "NA" else int(v),
            }
        )
    return rows


def main() -> None:
    text = subprocess.run(
        ["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True, check=True
    ).stdout
    df = pl.DataFrame(
        parse_text(text), schema={"state": pl.String, "per_capita_nsdp_2021_22": pl.Int64}
    )
    df.write_parquet(OUT)
    print(f"{len(df)} states/UTs -> {OUT.name}")


if __name__ == "__main__":
    main()
