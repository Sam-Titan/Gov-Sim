"""One traits table per NFHS district for the agent sampler (SPEC 5.1).

Three layers, each with its own quality flag:
  nfhs_*           NFHS-5/NFHS-4 district values (own district, survey estimate)
  census_*         Census 2011 shares of the mapped 2011 district (null if unmapped)
  state_*          NFHS-5 state values for women's bank account, phone, internet.
                   Same number for every district of a state: `partial_data` is true.
State per-capita income (beta2) from the Economic Survey table; null for Ladakh and
Dadra & Nagar Haveli and Daman & Diu.
No free source for BPL or household income (D-035); household income is not used.
Widows: dropped in V1 (district tables exist for only 13 states, D-036).
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from scripts import census

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
OUT = PROCESSED / "district_traits.parquet"
# women_internet has no NFHS-4 value, so it is last and skipped for NFHS-4 (STATE_KEYS[:2]).
# beta7 district deprivation score (D-036): mean z-score of these NFHS-5 district traits over
# all 704 districts, sign-flipped so that higher = more deprived. Only non-leaking traits
# (no target, no close relative). Women's schooling/literacy/attendance and birth
# registration count against deprivation; child marriage and a young population count for.
DEPRIVATION_SIGNS = {
    "female_school_attendance": -1,
    "women_literate": -1,
    "women_schooling_10plus": -1,
    "birth_registered": -1,
    "women_married_before_18": 1,
    "pop_below_15": 1,
}
STATE_KEYS = ("women_bank_account", "women_mobile_phone", "women_internet")


def deprivation_score(nt: pl.DataFrame) -> pl.Expr:
    """Mean of sign-adjusted z-scores of the NFHS-5 district traits (higher = more deprived)."""
    terms = []
    for key, sign in DEPRIVATION_SIGNS.items():
        col = pl.col(f"nfhs_{key}_nfhs5")
        terms.append(sign * (col - nt[f"nfhs_{key}_nfhs5"].mean()) / nt[f"nfhs_{key}_nfhs5"].std())
    return pl.mean_horizontal(*terms).alias("deprivation_score")


def build(
    nfhs_traits: pl.DataFrame,
    join_table: pl.DataFrame,
    census_df: pl.DataFrame,
    disability: pl.DataFrame,
    age: pl.DataFrame,
    state_traits: pl.DataFrame,
    state_income: pl.DataFrame,
) -> pl.DataFrame:
    ct = census.census_traits(census_df, disability, age).drop("name")
    ct = ct.rename({c: f"census_{c}" for c in ct.columns if c not in ("pc11_s_id", "pc11_d_id")})
    keep = [c for c in nfhs_traits.columns if c.endswith(("_nfhs5", "_nfhs4"))]
    nt = nfhs_traits.select(pl.col("file").alias("nfhs_file"), *keep)
    nt = nt.rename({c: f"nfhs_{c}" for c in keep})
    st = state_traits.select(
        pl.col("state").alias("nfhs_state"),
        *[pl.col(f"{k}_nfhs5").alias(f"state_{k}_nfhs5") for k in STATE_KEYS],
        *[pl.col(f"{k}_nfhs4").alias(f"state_{k}_nfhs4") for k in STATE_KEYS[:2]],
    )
    nt = nt.with_columns(deprivation_score(nt))
    inc = state_income.rename(
        {"state": "nfhs_state", "per_capita_nsdp_2021_22": "state_per_capita_nsdp_2021_22"}
    )
    out = join_table.join(nt, on="nfhs_file", how="left")
    out = out.join(inc, on="nfhs_state", how="left")
    out = out.join(ct, on=["pc11_s_id", "pc11_d_id"], how="left")
    out = out.join(st, on="nfhs_state", how="left")
    return out.with_columns(
        (pl.col("match_type") != "unmapped").alias("in_v1"),
        pl.lit(True).alias("state_traits_partial_data"),
    )


def main() -> None:
    out = build(
        pl.read_parquet(PROCESSED / "nfhs_traits.parquet"),
        pl.read_parquet(PROCESSED / "district_map.parquet"),
        pl.read_parquet(PROCESSED / "census2011_districts.parquet"),
        pl.read_parquet(PROCESSED / "census_disability.parquet"),
        pl.read_parquet(PROCESSED / "census_age.parquet"),
        pl.read_parquet(PROCESSED / "nfhs_state_traits.parquet"),
        pl.read_parquet(PROCESSED / "state_income.parquet"),
    )
    out.write_parquet(OUT)
    print(f"{len(out)} districts x {len(out.columns)} columns -> {OUT.name}")


if __name__ == "__main__":
    main()
