"""Build the district table and the (district, scheme, time) rows used by every model."""

from pathlib import Path

import numpy as np
import polars as pl

from govsim.schemes import CODES, SCHEMES, jsy_benefit, jsy_documents

PROCESSED = Path(__file__).resolve().parents[3] / "data" / "processed"
INCOME = "state_per_capita_nsdp_2021_22"

# Trait columns the GBM may use (SPEC 5.1). Never the 4 NFHS targets or their relatives.
GBM_TRAITS = [
    "census_rural_share",
    "census_female_share",
    "census_child_0_6_share",
    "census_sc_share",
    "census_st_share",
    "census_literacy_rate_7plus",
    "census_worker_share",
    "census_disabled_share",
    "census_age_60plus_share",
    "deprivation_score",
    "nfhs_female_school_attendance_nfhs5",
    "nfhs_pop_below_15_nfhs5",
    "nfhs_sex_ratio_nfhs5",
    "nfhs_birth_registered_nfhs5",
    "nfhs_women_literate_nfhs5",
    "nfhs_women_schooling_10plus_nfhs5",
    "nfhs_women_married_before_18_nfhs5",
    "state_women_bank_account_nfhs5",
    "state_women_mobile_phone_nfhs5",
    "state_women_internet_nfhs5",
    INCOME,
]


def load_districts(processed: Path = PROCESSED) -> pl.DataFrame:
    """V1 districts (mapped, with state income), joined to their NFHS targets."""
    traits = pl.read_parquet(processed / "district_traits.parquet")
    nfhs = pl.read_parquet(processed / "nfhs_districts.parquet").drop(["state", "state_code"])
    hh = pl.read_parquet(processed / "eligible_counts.parquet").select(
        "pc11_s_id", "pc11_d_id", "pmjay_households_total"
    )
    return (
        traits.filter(pl.col("in_v1") & pl.col(INCOME).is_not_null())
        .join(nfhs, left_on="nfhs_file", right_on="file", how="left")
        .join(hh, on=["pc11_s_id", "pc11_d_id"], how="left")
        .sort("nfhs_file")
    )


def _state_means(d: pl.DataFrame, col: str) -> dict[str, float]:
    """Household-weighted state mean of an NFHS-4 column (districts that have it)."""
    ok = d.filter(pl.col(col).is_not_null())
    g = ok.group_by("nfhs_state").agg(
        (
            (pl.col(col) * pl.col("pmjay_households_total")).sum()
            / pl.col("pmjay_households_total").sum()
        ).alias("m")
    )
    return dict(zip(g["nfhs_state"], g["m"], strict=True))


def _scheme_row_values(code: str, state: str, rural_share: float) -> dict[str, float]:
    """Scheme feature values for one district (JSY depends on state and area, D-037)."""
    s = SCHEMES[code].inputs
    if code == "jsy":
        ben_r, ben_u = jsy_benefit(state, True), jsy_benefit(state, False)
        docs = jsy_documents(state)
    else:
        ben_r = ben_u = s.cash_benefit_inr
        docs = s.document_count
    return {
        "benefit_rural": ben_r,
        "benefit_urban": ben_u,
        "benefit_mean": rural_share * ben_r + (1 - rural_share) * ben_u,
        "documents": float(docs),
        "bank_required": float(s.requires_bank_account),
        "burden": float(s.application_burden),
        "immediacy": float(s.benefit_immediacy),
    }


def build_rows(d: pl.DataFrame) -> pl.DataFrame:
    """One row per (district, scheme, era). era 0 = NFHS-5; era 1 = NFHS-4 (JSY, SBM only).

    Baseline b (D-038): PM-JAY / PMUY = NFHS-4 value (state mean if missing, flagged);
    JSY / SBM = 0. Districts with no usable baseline are dropped for PM-JAY / PMUY.
    """
    out: list[dict] = []
    for code in CODES:
        sch = SCHEMES[code]
        c5, c4 = f"{sch.nfhs_column}_nfhs5", f"{sch.nfhs_column}_nfhs4"
        smean = _state_means(d, c4) if sch.nfhs4_is_baseline else {}
        for i, r in enumerate(d.iter_rows(named=True)):
            base_ok, partial, b = True, False, 0.0
            if sch.nfhs4_is_baseline:
                v = r[c4]
                if v is None:
                    v = smean.get(r["nfhs_state"])
                    partial = True
                base_ok = v is not None
                b = (v or 0.0) / 100.0
            if not base_ok:
                continue
            vals = _scheme_row_values(code, r["nfhs_state"], r["census_rural_share"])
            common = {
                "district": i,
                "scheme": code,
                "baseline": b,
                "baseline_partial": partial,
                **vals,
            }
            out.append({**common, "era": 0, "target": r[c5]})
            if not sch.nfhs4_is_baseline and r[c4] is not None:
                out.append({**common, "era": 1, "target": r[c4]})
    return pl.DataFrame(out).with_columns(pl.col("district").cast(pl.Int64))


def share_to_array(d: pl.DataFrame, col: str, scale: float = 1.0) -> np.ndarray:
    return d[col].to_numpy().astype(np.float64) / scale
