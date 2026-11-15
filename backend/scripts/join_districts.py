"""Join NFHS-5 districts to Census 2011 districts (the map's `pc11_d_id`).

Only two kinds of match are accepted:
  exact    - same name (letters only, case-insensitive) in the same 2011 state
  spelling - a short reviewed list of spelling or renamed-district variants
Everything else is left `unmapped` (mostly districts created after 2011). We do not
guess parents: they need an official source (see PROGRESS.md).
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
NFHS = ROOT / "data" / "processed" / "nfhs_districts.parquet"
CENSUS = ROOT / "data" / "processed" / "census2011_districts.parquet"
OUT = ROOT / "data" / "processed" / "district_map.parquet"
UNMAPPED_CSV = ROOT / "data" / "interim" / "unmapped_districts.csv"

# NFHS state code -> Census 2011 state ids it covers. TG was part of Andhra Pradesh (28),
# LH part of Jammu & Kashmir (01), DD covers Daman & Diu (25) and Dadra & Nagar Haveli (26).
STATE_IDS: dict[str, list[str]] = {
    "AN": ["35"], "AP": ["28"], "AR": ["12"], "AS": ["18"], "BR": ["10"], "CT": ["22"],
    "DD": ["25", "26"], "DL": ["07"], "GA": ["30"], "GJ": ["24"], "HP": ["02"],
    "HR": ["06"], "JH": ["20"], "JK": ["01"], "KA": ["29"], "KL": ["32"], "LH": ["01"],
    "MH": ["27"], "ML": ["17"], "MN": ["14"], "MP": ["23"], "MZ": ["15"], "NL": ["13"],
    "OR": ["21"], "PB": ["03"], "PY": ["34"], "RJ": ["08"], "SK": ["11"], "TG": ["28"],
    "TN": ["33"], "TR": ["16"], "UP": ["09"], "UT": ["05"], "WB": ["19"],
}  # fmt: skip

# (NFHS state code, NFHS name) -> Census 2011 name. Same district, different spelling
# or name. Reviewed by hand; each target is checked to exist.
SPELLING: dict[tuple[str, str], str] = {
    ("AN", "Nicobar"): "Nicobars",
    ("GJ", "Ahmedabad"): "Ahmadabad",
    ("GJ", "Panchmahal"): "Panch Mahals",
    ("MH", "Ahmednagar"): "Ahmadnagar",
    ("MP", "Narsinghpur"): "Narsimhapur",
    ("PB", "Gurudaspur"): "Gurdaspur",
    ("TG", "Mahabubnagar"): "Mahbubnagar",
    ("UP", "Maharajganj"): "Mahrajganj",
    ("UP", "Sant Kabeer Nagar"): "Sant Kabir Nagar",
    ("UP", "Shravasti"): "Shrawasti",
    ("UT", "Haridwar"): "Hardwar",
    ("UT", "Udam Singh Nagar"): "Udham Singh Nagar",
    ("UT", "Pauri Garhwal"): "Garhwal",
    ("WB", "Darjeeling"): "Darjiling",
    ("CT", "Dantewada"): "Dakshin Bastar Dantewada",
    ("GJ", "Dahod"): "Dohad",
    ("UP", "Prayagraj"): "Allahabad",
}


def norm(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def match_district(
    state_code: str, nfhs_name: str, census: dict[tuple[str, str], str]
) -> tuple[str | None, str | None, str]:
    """(pc11_s_id, pc11_d_id, match_type). `census` maps (state id, norm name) -> d_id."""
    target = SPELLING.get((state_code, nfhs_name))
    key_name = norm(target) if target else norm(nfhs_name)
    for sid in STATE_IDS[state_code]:
        did = census.get((sid, key_name))
        if did is not None:
            return sid, did, "spelling" if target else "exact"
    return None, None, "unmapped"


def build(nfhs: pl.DataFrame, census_df: pl.DataFrame, check_spelling: bool = True) -> pl.DataFrame:
    census = {(r["pc11_s_id"], norm(r["name"])): r["pc11_d_id"] for r in census_df.to_dicts()}
    if check_spelling:
        names = {k[1] for k in census}
        missing = [k for k, v in SPELLING.items() if norm(v) not in names]
        if missing:
            raise ValueError(f"Spelling targets not in Census: {missing}")
    rows = []
    for r in nfhs.to_dicts():
        sid, did, kind = match_district(r["state_code"], r["district"], census)
        rows.append(
            {
                "state_code": r["state_code"],
                "nfhs_state": r["state"],
                "nfhs_district": r["district"],
                "nfhs_file": r["file"],
                "pc11_s_id": sid,
                "pc11_d_id": did,
                "match_type": kind,
            }
        )
    return pl.DataFrame(rows)


def main() -> None:
    table = build(pl.read_parquet(NFHS), pl.read_parquet(CENSUS))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    table.write_parquet(OUT)
    UNMAPPED_CSV.parent.mkdir(parents=True, exist_ok=True)
    table.filter(pl.col("match_type") == "unmapped").select(
        "state_code", "nfhs_state", "nfhs_district"
    ).write_csv(UNMAPPED_CSV)
    print(table.group_by("match_type").len().sort("match_type"))


if __name__ == "__main__":
    main()
