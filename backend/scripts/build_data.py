"""Clean raw data and write Parquet, GeoJSON and the data report.

Runs in order: NFHS PDFs -> Census 2011 -> district join -> map -> report.
Needs the system tool `pdftotext` (data scripts only, D-029).
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from scripts import census, geo, join_districts, parse_income, parse_nfhs, parse_state
from scripts import traits as traits_mod

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REPORT = ROOT / "docs" / "DATA_REPORT.md"
INDICATORS = ("health_insurance", "clean_fuel", "institutional_births", "sanitation")
SCHEMES = {
    "health_insurance": "PM-JAY",
    "clean_fuel": "PMUY",
    "institutional_births": "JSY",
    "sanitation": "SBM",
}


def state_coverage(table: pl.DataFrame) -> pl.DataFrame:
    """Per NFHS state: sheets, mapped to a 2011 district, unmapped, missing NFHS-4."""
    return (
        table.group_by("state_code", "nfhs_state")
        .agg(
            pl.len().alias("nfhs_districts"),
            (pl.col("match_type") != "unmapped").sum().alias("mapped"),
            (pl.col("match_type") == "unmapped").sum().alias("unmapped"),
            pl.col("no_nfhs4").sum().alias("no_nfhs4"),
        )
        .sort("state_code")
    )


def md_table(df: pl.DataFrame) -> str:
    cols = df.columns
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.iter_rows():
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def leakage_screen() -> pl.DataFrame:
    """Largest |correlation| of each NFHS-5 trait with the 4 NFHS-5 targets."""
    t = pl.read_parquet(PROCESSED / "nfhs_traits.parquet")
    n = pl.read_parquet(PROCESSED / "nfhs_districts.parquet")
    d = t.join(n.select("file", *[f"{i}_nfhs5" for i in INDICATORS]), on="file")
    rows = []
    for k in sorted({c[:-6] for c in t.columns if c.endswith("_nfhs5")}):
        r = {i: d.select(pl.corr(f"{k}_nfhs5", f"{i}_nfhs5")).item() for i in INDICATORS}
        worst = max(r, key=lambda i: abs(r[i]))
        rows.append(
            {
                "trait": k,
                "districts_with_value": len(d) - d[f"{k}_nfhs5"].null_count(),
                "max_abs_r": round(abs(r[worst]), 2),
                "with_target": SCHEMES[worst],
            }
        )
    return pl.DataFrame(rows)


def traits_section() -> str:
    tr = pl.read_parquet(PROCESSED / "district_traits.parquet")
    st = pl.read_parquet(PROCESSED / "nfhs_state_traits.parquet")
    census_cols = [c for c in tr.columns if c.startswith("census_") and c.endswith("_share")]
    nt = pl.read_parquet(PROCESSED / "nfhs_traits.parquet")
    nfhs_names = ", ".join(sorted({c[:-6] for c in nt.columns if c.endswith("_nfhs5")}))
    n_disabled = int(
        pl.read_parquet(PROCESSED / "census_disability.parquet")["disabled_all_total"].sum()
    )
    layer_rows = "\n".join(
        [
            f"| NFHS-5 district sheets | {nfhs_names} | district | survey estimate |",
            f"| Census 2011 PCA, C-13, C-20 | {len(census_cols)} shares (rural, female, 0-6, "
            "SC, ST, literacy 7+, workers, age 60+, disabled all/20+/60+) "
            "| 2011 district, mapped only | counts |",
            f"| NFHS-5 state compendium | women: bank account, phone, internet "
            f"({len(st) - 3} states/UTs) | **state**, same in every district "
            "| `partial_data` |",
        ]
    )
    targets = pl.read_parquet(PROCESSED / "nfhs_districts.parquet").select(
        pl.col("file").alias("nfhs_file"),
        *[pl.col(f"{i}_nfhs5").alias(f"target_{i}") for i in INDICATORS],
    )
    dep = tr.join(targets, on="nfhs_file")
    dep_corr = ", ".join(
        f"{SCHEMES[i]} {dep.select(pl.corr('deprivation_score', f'target_{i}')).item():.2f}"
        for i in INDICATORS
    )
    n_no_income = tr.filter(
        pl.col("in_v1") & pl.col("state_per_capita_nsdp_2021_22").is_null()
    ).height
    excluded = "\n".join(f"| {k} | {v} |" for k, v in parse_nfhs.EXCLUDED.items())
    return f"""## Traits for the agent sampler (SPEC 5.1)
`district_traits.parquet`: {len(tr)} NFHS districts x {len(tr.columns)} columns; column
`in_v1` marks the {tr["in_v1"].sum()} mapped districts that V1 uses.

| Layer | Traits | Level | Quality flag |
|---|---|---|---|
{layer_rows}

**Disability:** Census C-20 has no exact 18+ cut; use 20+ and 60+. Total disabled in the
640 districts: {n_disabled:,}.

**Leakage screen (NFHS-5, 704 districts):** largest absolute correlation of each trait with
any of the 4 targets. Nothing is above 0.9, so no trait is a near-copy of a target.

{md_table(leakage_screen())}

**Excluded from traits (never used) and why**

| NFHS indicator | Reason |
|---|---|
{excluded}

**Dropped after review (D-036):** electricity (#7). It overlaps the PMUY target because
electricity counts as a clean cooking fuel.

**Deprivation score (beta7).** Mean of six sign-adjusted z-scores over all 704 districts
(higher = more deprived): women literate, women with 10+ years of schooling, female school
attendance and birth registration (low = deprived); women married before 18 and population
below 15 (high = deprived). Only non-leaking NFHS-5 district traits. Correlation with the
targets: {dep_corr}.

**Income (beta2).** State per-capita NSDP, current prices, 2021-22, from the Economic Survey
2023-24 table 1.11A (source: state Directorates of Economics & Statistics). A single common
year is used because 2022-23 and 2023-24 have gaps. Null for Ladakh and Dadra & Nagar
Haveli and Daman & Diu (not in the table; {n_no_income} districts). State-level, so it is
the same for every district of a state (`partial_data`).
No national figure was added; the {n_no_income} districts stay null (Phase 2 decides).

**Not available:**
- BPL and household income: no free district or state source found (NFHS state sheets have
  no wealth or BPL indicator). Dropped from the traits.
- Widows: Census C-02 has district tables for only 13 states (none for Rajasthan or UP).
  Dropped in V1 (D-036). Age 60+ share comes from Census C-13 (all 640 districts).
- LPG ownership: it is the PMUY target, so it cannot be a trait.
"""


def write_report(path: Path = REPORT) -> None:
    nfhs = pl.read_parquet(PROCESSED / "nfhs_districts.parquet")
    census_df = pl.read_parquet(PROCESSED / "census2011_districts.parquet")
    jt = pl.read_parquet(PROCESSED / "district_map.parquet")
    elig = pl.read_parquet(PROCESSED / "eligible_counts.parquet")
    gj = json.loads((PROCESSED / "districts.geojson").read_text(encoding="utf-8"))
    jt = jt.join(
        nfhs.select(
            pl.col("file").alias("nfhs_file"),
            pl.col("sanitation_nfhs4").is_null().alias("no_nfhs4"),
        ),
        on="nfhs_file",
    )
    n_map = len(jt.filter(pl.col("match_type") != "unmapped"))
    mapped_ids = set(jt.filter(pl.col("match_type") != "unmapped")["pc11_d_id"].to_list())
    census_without = census_df.filter(~pl.col("pc11_d_id").is_in(list(mapped_ids)))
    ind_rows = []
    for ind in INDICATORS:
        a, b = nfhs[f"{ind}_nfhs5"], nfhs[f"{ind}_nfhs4"]
        ind_rows.append(
            {
                "scheme": SCHEMES[ind],
                "nfhs5_rows": len(a) - a.null_count(),
                "nfhs5_missing": a.null_count(),
                "nfhs4_rows": len(b) - b.null_count(),
                "nfhs4_missing": b.null_count(),
                "nfhs5_min": a.min(),
                "nfhs5_max": a.max(),
            }
        )
    text = f"""# Data report — Phase 1

Generated by `backend/scripts/build_data.py`. Do not edit by hand.

## Row counts
| Table (data/processed/) | Rows |
|---|---|
| nfhs_districts.parquet | {len(nfhs)} |
| census2011_districts.parquet | {len(census_df)} |
| eligible_counts.parquet | {len(elig)} |
| district_map.parquet (NFHS district -> 2011 district) | {len(jt)} |
| districts.geojson (polygons) | {len(gj["features"])} |

## Uptake table (NFHS values, survey estimates)
{md_table(pl.DataFrame(ind_rows))}

NFHS-5 has no missing values. NFHS-4 is missing where the sheet prints `na`
(new or re-drawn districts, and all of Telangana).

## District join (NFHS -> Census 2011 / map)
- Mapped: {n_map} of {len(jt)} NFHS districts
  (exact name: {len(jt.filter(pl.col("match_type") == "exact"))},
  reviewed spelling/rename: {len(jt.filter(pl.col("match_type") == "spelling"))}).
- Unmapped: {len(jt.filter(pl.col("match_type") == "unmapped"))}. Mostly districts created
  after 2011. Their 2011 parent needs an official source; list in
  `data/interim/unmapped_districts.csv`. No parent was guessed.
- Census 2011 districts with no mapped NFHS district: {len(census_without)}
  ({", ".join(census_without["name"].to_list())}).
- Exact-name matches do not prove identical boundaries: a 2011 district that later lost
  territory to a new district keeps its name. Treat states with unmapped districts as
  "boundary changed".
- Not downloaded: Chandigarh (skipped by decision), Vidisha (MP) and Lakshadweep (no sheet
  found at the DHS address; the third-party district list lacks Vidisha).

## Missing districts (accepted, D-034)
- **Chandigarh:** skipped by decision.
- **Vidisha (Madhya Pradesh):** no NFHS-5 district sheet found (not on the district list;
  `MP_Vidisha.pdf` is 404 at DHS).
- **Lakshadweep:** no district sheet found (`LD_Lakshadweep.pdf` is 404). The state
  sheet exists but is not a district value.
- To be listed on the About page.
- **V1 uses the {n_map} mapped districts** (D-033). The 70 unmapped districts show as
  "no data" and are not on the map. Their names are in `data/interim/unmapped_districts.csv`.

## Coverage per state
{md_table(state_coverage(jt))}

{traits_section()}

## Map
- {len(gj["features"])} polygons from SHRUG v2.1 (Census 2011 districts);
  {sum(1 for f in gj["features"] if f["properties"].get("has_nfhs_data"))} have NFHS data
  (`has_nfhs_data`), the rest show as "no data". One polygon
  (`pc11_d_id` 000, Jammu & Kashmir) has no Census row or name; it is kept for the outline
  and marked `has_census_data: false`.
- Simplified to about 1 km. Licence CC BY-NC-SA 4.0 (credit on the About page).

## Eligible counts (Census 2011 bases)
PM-JAY and PMUY: households. SBM: people. JSY: births in the last 5 years, estimated as
children aged 0-6 x 5/7 (ignores child deaths and migration). Rural, urban and total.
All-India check: {elig["pmjay_households_total"].sum():,} households,
{elig["sbm_population_total"].sum():,} people.

## JSY births estimate and NFHS-4 state baseline (Phase 3, D-042, D-046)
- **JSY sample size:** births in the last 5 years are not printed on the NFHS sheets, so the
  sampling band uses an estimate: women interviewed x (Census 2011 children 0-6 x 5/7 / Census
  2011 women 15-49). `census_age.parquet` has `women_15_49` (C-13, females aged 15-49; 311,681,858
  in India); births per woman: median 0.38, range 0.19 to 0.79. 2011 ratio applied to 2019-21;
  ignores child deaths and migration. Label: estimated.
- **NFHS-4 state value for PM-JAY and PMUY:** `nfhs4_state_baseline.parquet` (37 states/UTs, no
  missing values) from the NFHS-5 state compendium, NFHS-4 total column (same two PDFs, MANIFEST
  rows 751 and 752). It is used only where no district of a state has an NFHS-4 value: NCT Delhi
  (9 mapped districts) and Telangana (9). Health insurance: Delhi 15.7, Telangana 66.4; clean fuel:
  Delhi 97.9, Telangana 67.3. Rows are flagged `partial_data`. It is a target-type value, so it is
  in its own file and never a trait. Phase 2 training does not use it (rows and numbers unchanged).
"""
    path.write_text(text, encoding="utf-8")
    print(f"report -> {path}")


def main() -> None:
    parse_nfhs.main()
    parse_state.main()
    parse_income.main()
    census.main()
    join_districts.main()
    traits_mod.main()
    geo.main()
    write_report()


if __name__ == "__main__":
    main()
