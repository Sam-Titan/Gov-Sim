"""Read the NFHS sample sizes printed on each district sheet.

Sentence on the sheet: "In Patna, information was gathered from 897 households, 942 women,
and 143 men." Writes data/processed/nfhs_sample_sizes.parquet (file, n_households, n_women, n_men).
"""

import re

import polars as pl

from scripts.parse_nfhs import PDF_DIR, ROOT, pdf_text

OUT = ROOT / "data" / "processed" / "nfhs_sample_sizes.parquet"
SENTENCE = re.compile(
    r"information\s+was\s+gathered\s+from\s+([\d,]+)\s+households,\s+([\d,]+)\s+women,?\s+and\s+([\d,]+)\s+men",
    re.S,
)


def parse_sample(text: str) -> tuple[int, int, int] | None:
    m = SENTENCE.search(text)
    if not m:
        return None
    h, w, men = (int(g.replace(",", "")) for g in m.groups())
    return h, w, men


def main() -> None:
    rows, missing = [], []
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        got = parse_sample(pdf_text(pdf))
        if got is None:
            missing.append(pdf.name)
            continue
        rows.append({"file": pdf.name, "n_households": got[0], "n_women": got[1], "n_men": got[2]})
    pl.DataFrame(rows).write_parquet(OUT)
    print(f"{len(rows)} sheets -> {OUT.name}; no sentence in {len(missing)}: {missing[:10]}")


if __name__ == "__main__":
    main()
