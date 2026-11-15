"""Read the Census 2011 Primary Census Abstract (district level) and build base counts.

Source: ORGI Census Digital Library, table PC11_PCA-SD
(DDW_PCA0000_2011_Indiastatedist.xlsx). District codes match the map's `pc11_d_id`.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import openpyxl
import polars as pl
import xlrd  # old .xls Census tables (C-13); approved for data scripts only (D-036)

ROOT = Path(__file__).resolve().parents[2]
CENSUS_XLSX = ROOT / "data" / "raw" / "census2011" / "DDW_PCA0000_2011_Indiastatedist.xlsx"
OUT_DISTRICTS = ROOT / "data" / "processed" / "census2011_districts.parquet"
OUT_ELIGIBLE = ROOT / "data" / "processed" / "eligible_counts.parquet"
C20_DIR = ROOT / "data" / "raw" / "census2011" / "c20_disability"
C13_DIR = ROOT / "data" / "raw" / "census2011" / "c13_age"
OUT_AGE = ROOT / "data" / "processed" / "census_age.parquet"
OUT_DISABILITY = ROOT / "data" / "processed" / "census_disability.parquet"

# PCA column -> our name
KEEP = {
    "No_HH": "households",
    "TOT_P": "population",
    "TOT_M": "male",
    "TOT_F": "female",
    "P_06": "age_0_6",
    "P_SC": "sc",
    "P_ST": "st",
    "P_LIT": "literate",
    "P_ILL": "illiterate",
    "TOT_WORK_P": "workers",
}
TRU = {"Total": "total", "Rural": "rural", "Urban": "urban"}
# Children aged 0-6 are 7 single-year groups; births in the 5 years before a survey
# are roughly the 0-4 groups, so about 5/7 of the 0-6 group.
BIRTH_SHARE_OF_AGE_0_6 = 5 / 7


def read_district_rows(path: Path = CENSUS_XLSX) -> list[dict[str, object]]:
    """All DISTRICT-level rows (Total, Rural, Urban) as dicts."""
    wb = openpyxl.load_workbook(path, read_only=True)
    rows = list(wb["Sheet1"].iter_rows(values_only=True))
    header = rows[0]
    out = [dict(zip(header, r, strict=True)) for r in rows[1:]]
    return [r for r in out if r["Level"] == "DISTRICT"]


def to_wide(rows: list[dict[str, object]]) -> pl.DataFrame:
    """One row per district, columns like `households_total`, `population_rural`."""
    wide: dict[tuple[str, str], dict[str, object]] = {}
    for r in rows:
        key = (str(r["State"]), str(r["District"]))
        rec = wide.setdefault(
            key,
            {
                "pc11_s_id": key[0],
                "pc11_d_id": key[1],
                "name": str(r["Name"]).strip(),
            },
        )
        suffix = TRU[str(r["TRU"])]
        for src, dst in KEEP.items():
            rec[f"{dst}_{suffix}"] = int(str(r[src]))
    return pl.DataFrame(list(wide.values())).sort("pc11_d_id")


def eligible_counts(df: pl.DataFrame) -> pl.DataFrame:
    """Bases for the four NFHS schemes, per 2011 district (total, rural, urban).

    pmjay, pmuy: households. jsy: births in the last 5 years (estimate from age 0-6).
    sbm: population. NFHS values are shares of these bases (SPEC section 3).
    """
    cols: list[pl.Expr] = [pl.col("pc11_s_id"), pl.col("pc11_d_id"), pl.col("name")]
    for suffix in ("total", "rural", "urban"):
        hh = pl.col(f"households_{suffix}")
        cols += [
            hh.alias(f"pmjay_households_{suffix}"),
            hh.alias(f"pmuy_households_{suffix}"),
            (pl.col(f"age_0_6_{suffix}") * BIRTH_SHARE_OF_AGE_0_6)
            .round(0)
            .cast(pl.Int64)
            .alias(f"jsy_births_5y_est_{suffix}"),
            pl.col(f"population_{suffix}").alias(f"sbm_population_{suffix}"),
        ]
    return df.select(cols)


# C-20 age groups: no exact 18+ cut, so "20+" and "60+" are used.
AGES_20_PLUS = ("20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90+")
AGES_60_PLUS = ("60-69", "70-79", "80-89", "90+")


def read_c20(path: Path) -> list[tuple[str, str, str, str, int]]:
    """(state id, district id, Total/Rural/Urban, age group, disabled persons) rows."""
    wb = openpyxl.load_workbook(path, read_only=True)
    rows = list(wb[wb.sheetnames[0]].iter_rows(values_only=True))
    start = next(i for i, r in enumerate(rows) if r and r[0] == "Table Name") + 1
    out = []
    for r in rows[start:]:
        if r and r[1] and r[3] and str(r[2]) != "000":
            out.append((str(r[1]), str(r[2]), str(r[4]), str(r[5]), int(r[6])))
    return out


def disability_wide(records: Iterable[tuple[str, str, str, str, int]]) -> pl.DataFrame:
    """Per district: disabled persons, all ages / 20+ / 60+, for total, rural, urban."""
    acc: dict[tuple[str, str], dict[str, int]] = {}
    for sid, did, tru, age, n in records:
        rec = acc.setdefault((sid, did), {})
        suffix = TRU[tru]
        if age == "Total":
            rec[f"disabled_all_{suffix}"] = n
        if age in AGES_20_PLUS:
            rec[f"disabled_20plus_{suffix}"] = rec.get(f"disabled_20plus_{suffix}", 0) + n
        if age in AGES_60_PLUS:
            rec[f"disabled_60plus_{suffix}"] = rec.get(f"disabled_60plus_{suffix}", 0) + n
    rows = [{"pc11_s_id": k[0], "pc11_d_id": k[1], **v} for k, v in acc.items()]
    return pl.DataFrame(rows).sort("pc11_d_id")


def build_disability() -> pl.DataFrame:
    records: list[tuple[str, str, str, str, int]] = []
    for path in sorted(C20_DIR.glob("*.xlsx")):
        records.extend(read_c20(path))
    return disability_wide(records)


def read_c13(path: Path) -> list[dict[str, object]]:
    """Per district: all-ages persons, persons aged 60+ (ages 60-99 and '100+') and women 15-49."""
    ws = xlrd.open_workbook(str(path)).sheet_by_index(0)
    keys: dict[tuple[str, str], dict[str, int]] = {}
    for i in range(ws.nrows):
        r = ws.row_values(i)
        if not r[1] or r[2] in ("", "000") or not isinstance(r[5], float):
            continue
        acc = keys.setdefault((str(r[1]), str(r[2])), {"all": 0, "60": 0, "w": 0})
        age = r[4]
        if age == "All ages":
            acc["all"] = int(r[5])
        elif age == "100+" or (isinstance(age, float) and age >= 60):
            acc["60"] += int(r[5])
        if isinstance(age, float) and 15 <= age <= 49:
            acc["w"] += int(r[7])  # column 7 = Females, Total block
    return [
        {
            "pc11_s_id": k[0],
            "pc11_d_id": k[1],
            "age_all": v["all"],
            "age_60plus": v["60"],
            "women_15_49": v["w"],
        }
        for k, v in keys.items()
    ]


def build_age() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for path in sorted(C13_DIR.glob("*.xls")):
        rows.extend(read_c13(path))
    return pl.DataFrame(rows).sort("pc11_d_id")


def census_traits(df: pl.DataFrame, disability: pl.DataFrame, age: pl.DataFrame) -> pl.DataFrame:
    """Shares per 2011 district from the PCA and C-20 (total, rural, urban)."""
    j = df.join(disability, on=["pc11_s_id", "pc11_d_id"], how="left")
    j = j.join(age, on=["pc11_s_id", "pc11_d_id"], how="left")
    pop = pl.col("population_total")
    return j.select(
        "pc11_s_id",
        "pc11_d_id",
        "name",
        (pl.col("population_rural") / pop).alias("rural_share"),
        (pl.col("female_total") / pop).alias("female_share"),
        (pl.col("age_0_6_total") / pop).alias("child_0_6_share"),
        (pl.col("sc_total") / pop).alias("sc_share"),
        (pl.col("st_total") / pop).alias("st_share"),
        (pl.col("literate_total") / (pop - pl.col("age_0_6_total"))).alias("literacy_rate_7plus"),
        (pl.col("workers_total") / pop).alias("worker_share"),
        (pl.col("disabled_all_total") / pop).alias("disabled_share"),
        (pl.col("disabled_20plus_total") / pop).alias("disabled_20plus_share"),
        (pl.col("disabled_60plus_total") / pop).alias("disabled_60plus_share"),
        (pl.col("age_60plus") / pl.col("age_all")).alias("age_60plus_share"),
        pl.col("disabled_all_total"),
        pl.col("disabled_20plus_total"),
        pl.col("disabled_60plus_total"),
    )


def main() -> None:
    df = to_wide(read_district_rows())
    OUT_DISTRICTS.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(OUT_DISTRICTS)
    eligible_counts(df).write_parquet(OUT_ELIGIBLE)
    disability = build_disability()
    disability.write_parquet(OUT_DISABILITY)
    age = build_age()
    age.write_parquet(OUT_AGE)
    print(f"{len(age)} districts with age counts -> {OUT_AGE.name}")
    print(f"{len(df)} Census 2011 districts -> {OUT_DISTRICTS.name}, {OUT_ELIGIBLE.name}")
    print(f"{len(disability)} districts with disability counts -> {OUT_DISABILITY.name}")


if __name__ == "__main__":
    main()
