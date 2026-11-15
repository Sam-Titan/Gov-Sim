"""Read state-level NFHS-5 indicators from the two state fact-sheet compendium PDFs.

Used only for traits that have no district value: women with a bank account, a mobile
phone, and internet use (SPEC 5.1). Every district gets its state's value and a
`partial_data` flag (D-035). Needs the system tool `pdftotext` (data scripts only).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
COMPENDIUM_DIR = ROOT / "data" / "raw" / "nfhs" / "compendium"
OUT = ROOT / "data" / "processed" / "nfhs_state_traits.parquet"
OUT_BASELINE = ROOT / "data" / "processed" / "nfhs4_state_baseline.parquet"

HEADING_RE = re.compile(r"^\s+(.+?) - Key Indicators\s*$")
ROW_RE = re.compile(r"^\s*(\d{1,3})\.\s+(.*?)\s{2,}(.+?)\s*$")
VALUE_RE = re.compile(r"^\(?-?\d+(?:\.\d+)?\)?$")
INDICATORS: dict[str, str] = {
    "women_bank_account": "women having a bank or savings account",
    "women_mobile_phone": "women having a mobile phone",
    "women_internet": "women who have ever used the internet",
}


# NFHS-4 state value of two scheme indicators: the PM-JAY / PMUY baseline for states where
# the district sheets have no NFHS-4 column (NCT Delhi, Telangana; D-046). These are targets,
# so they are written to their own file and never join the trait table.
BASELINE_INDICATORS: dict[str, str] = {
    "health_insurance": "covered under a health insurance",
    "clean_fuel": "using clean fuel for cooking",
}


def parse_baseline(text: str) -> list[dict[str, object]]:
    """One row per state/UT: NFHS-4 total of the PM-JAY and PMUY indicators (last column)."""
    states: dict[str, dict[str, object]] = {}
    current: str | None = None
    for line in text.splitlines():
        h = HEADING_RE.match(line)
        if h:
            current = h.group(1).strip()
            states.setdefault(current, {"state": current})
            continue
        m = ROW_RE.match(line)
        if not m or current is None:
            continue
        label = m.group(2).lower()
        for key, needle in BASELINE_INDICATORS.items():
            col = f"{key}_nfhs4"
            tokens = m.group(3).split()
            if needle in label and col not in states[current] and len(tokens) >= 4:
                states[current][col] = num(tokens[3])
    return [r for r in states.values() if len(r) > 1]


def num(token: str) -> float | None:
    return float(token.strip("()")) if VALUE_RE.match(token) else None


def parse_text(text: str) -> list[dict[str, object]]:
    """One row per state/UT: NFHS-5 total (and NFHS-4 total) for each indicator."""
    states: dict[str, dict[str, object]] = {}
    current: str | None = None
    for line in text.splitlines():
        h = HEADING_RE.match(line)
        if h:
            current = h.group(1).strip()
            states.setdefault(current, {"state": current})
            continue
        m = ROW_RE.match(line)
        if not m or current is None:
            continue
        label = m.group(2).lower()
        for key, needle in INDICATORS.items():
            if needle in label and f"{key}_nfhs5" not in states[current]:
                tokens = m.group(3).split()
                if len(tokens) >= 4:
                    states[current][f"{key}_nfhs5"] = num(tokens[2])  # total column
                    states[current][f"{key}_nfhs4"] = num(tokens[3])
    return [r for r in states.values() if len(r) > 1]


def main() -> None:
    rows: list[dict[str, object]] = []
    base_rows: list[dict[str, object]] = []
    for pdf in sorted(COMPENDIUM_DIR.glob("*.pdf")):
        text = subprocess.run(
            ["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True
        ).stdout
        rows.extend(parse_text(text))
        base_rows.extend(parse_baseline(text))
    df = pl.DataFrame(rows, infer_schema_length=None).unique(subset="state", keep="first")
    df.sort("state").write_parquet(OUT)
    print(f"{len(df)} states/UTs -> {OUT.name}")
    base = pl.DataFrame(base_rows, infer_schema_length=None).unique(subset="state", keep="first")
    base.sort("state").write_parquet(OUT_BASELINE)
    print(f"{len(base)} states/UTs -> {OUT_BASELINE.name}")


if __name__ == "__main__":
    main()
