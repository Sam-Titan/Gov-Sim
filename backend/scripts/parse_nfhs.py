"""Read NFHS-5 district fact sheet PDFs and write one Parquet table.

Uses the system `pdftotext` tool (poppler). It is approved for data scripts only;
the live app never calls it (see DECISIONS D-029).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "data" / "raw" / "nfhs" / "district_pdfs"
OUT = ROOT / "data" / "processed" / "nfhs_districts.parquet"
OUT_TRAITS = ROOT / "data" / "processed" / "nfhs_traits.parquet"

# column prefix -> text the indicator label must contain. Matched on the label, not the
# number: a few sheets (e.g. Mahisagar, Wardha) number the indicators differently.
WANTED: dict[str, tuple[str, ...]] = {
    "sanitation": ("improved sanitation",),
    "clean_fuel": ("clean fuel for cooking",),
    # Mahisagar and Wardha use the older wording in the second entry.
    "health_insurance": ("health insurance/financing", "health scheme or health insurance"),
    "institutional_births": ("institutional births (%)",),
}

# Background traits for the agent sampler (SPEC 5.1). Matched on label text.
TRAITS: dict[str, tuple[str, ...]] = {
    "female_school_attendance": ("ever attended school",),
    "pop_below_15": ("population below age 15",),
    "sex_ratio": ("sex ratio of the total population",),
    "birth_registered": ("birth was registered",),
    "women_literate": ("women who are literate",),
    "women_schooling_10plus": ("women with 10 or more years of schooling",),
    "women_married_before_18": ("married before age 18",),
}

# NOT used as traits (leakage guard, D-035): the 4 targets, close relatives of each, and
# whole blocks that are health-service use or health outcomes. (Indicator numbers are
# from the Ajmer sheet; a few sheets number differently, so we match on labels.)
EXCLUDED: dict[str, str] = {
    "#9 improved sanitation facility": "TARGET (SBM)",
    "#10 clean cooking fuel": "TARGET (PMUY)",
    "#12 health insurance/financing scheme": "TARGET (PM-JAY)",
    "#42 institutional births": "TARGET (JSY)",
    "#43 institutional births in public facility": "close relative of JSY target",
    "#44-45 home births with skilled staff, births with skilled staff": "close relative of JSY",
    "#46-48 caesarean section (all, private, public)": "close relative of JSY",
    "#32-41 maternity care (ANC, MCP card, iron-folic acid, PNC, out-of-pocket)": "JSY/PM-JAY",
    "#8 improved drinking-water source": "same WASH block as the SBM target",
    "#19 hygienic protection during menstruation": "hygiene block close to SBM",
    "#20-31 family planning": "health-service use, close to JSY and PM-JAY",
    "#49-66 vaccination and treatment of childhood illness": "health-service use",
    "#4, #17, #18 sex ratio at birth, higher-order births, teenage mothers": "birth block",
    "#7 households with electricity": "overlaps the PMUY target (electricity is a clean fuel)",
    "#6 deaths registered": "no NFHS-4 value; 28 districts have few cases",
    "#13 children in pre-primary school": "no NFHS-4 value; 155 districts have few cases",
    "#67-104 nutrition, anaemia, blood sugar/pressure, cancer screening, tobacco, alcohol": (
        "health outcomes, downstream of sanitation, fuel and care"
    ),
}
LINE_RE = re.compile(r"^\s*(\d{1,3})\.\s+(.*?)\s{2,}(.+?)\s*$")
VALUE_RE = re.compile(r"^\(?-?\d+(?:,\d{3})*(?:\.\d+)?\)?$")


def pdf_text(pdf: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def parse_value(token: str) -> tuple[float | None, bool]:
    """(value, few_cases_flag). '*' and 'na' give None. '( )' marks few cases."""
    if not VALUE_RE.match(token):
        return None, False
    few = token.startswith("(")
    return float(token.strip("()").replace(",", "")), few


def parse_header(text: str) -> tuple[str, str]:
    """(district, state) from the cover page. The state name can wrap to two lines."""
    lines = [line.strip() for line in text.splitlines()]
    i = lines.index("District Fact Sheet")
    names: list[str] = []
    for line in lines[i + 1 : i + 10]:
        if line.startswith("International Institute") or LINE_RE.match(line):
            break
        if line:
            names.append(line)
    return names[0], " ".join(names[1:])


def parse_sheet(
    text: str, wanted: dict[str, tuple[str, ...]] | None = None
) -> dict[str, float | bool | str | None]:
    """One row per sheet: NFHS-5 and NFHS-4 value for every indicator in `wanted`."""
    wanted = wanted or WANTED
    district, state = parse_header(text)
    row: dict[str, float | bool | str | None] = {"district": district, "state": state}
    for line in text.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        label = m.group(2).lower()
        prefix = next((p for p, keys in wanted.items() if any(k in label for k in keys)), None)
        if prefix is None or f"{prefix}_nfhs5" in row:
            continue
        tokens = m.group(3).split()
        v5, few5 = parse_value(tokens[0])
        v4, few4 = parse_value(tokens[1]) if len(tokens) > 1 else (None, False)
        row[f"{prefix}_nfhs5"] = v5
        row[f"{prefix}_nfhs4"] = v4
        row[f"{prefix}_few_cases"] = few5 or few4
        row[f"{prefix}_ncols"] = len(tokens)
    return row


def main() -> None:
    rows = []
    trait_rows = []
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        text = pdf_text(pdf)
        code = pdf.name.split("_", 1)[0]
        row = parse_sheet(text)
        row["file"] = pdf.name
        row["state_code"] = code
        rows.append(row)
        trow = parse_sheet(text, TRAITS)
        trow["file"] = pdf.name
        trow["state_code"] = code
        trait_rows.append(trow)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = pl.DataFrame(rows, infer_schema_length=None)
    df.write_parquet(OUT)
    pl.DataFrame(trait_rows, infer_schema_length=None).write_parquet(OUT_TRAITS)
    print(f"{len(df)} districts -> {OUT.name}, {OUT_TRAITS.name}")


if __name__ == "__main__":
    main()
