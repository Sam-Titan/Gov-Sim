import numpy as np
import polars as pl
import pytest


def make_districts(n: int = 40, seed: int = 0) -> pl.DataFrame:
    """Synthetic districts for tests only (not real data)."""
    r = np.random.default_rng(seed)
    states = ["Uttar Pradesh", "Kerala", "Bihar", "Goa"]
    cols = {
        "pc11_d_id": [str(100 + i) for i in range(n)],
        "nfhs_file": [f"f{i}" for i in range(n)],
        "nfhs_state": [states[i % 4] for i in range(n)],
        "census_rural_share": r.uniform(0.2, 0.95, n),
        "census_female_share": r.uniform(0.47, 0.5, n),
        "census_age_60plus_share": r.uniform(0.05, 0.12, n),
        "census_disabled_share": r.uniform(0.01, 0.03, n),
        "census_literacy_rate_7plus": r.uniform(0.5, 0.9, n),
        "state_women_bank_account_nfhs5": r.uniform(65, 90, n),
        "deprivation_score": r.normal(0, 0.8, n),
        "state_per_capita_nsdp_2021_22": r.uniform(5e4, 3e5, n),
        "pmjay_households_total": r.integers(1000, 9000, n),
    }
    for k, (lo, hi) in {
        "health_insurance": (5, 90),
        "clean_fuel": (20, 95),
        "institutional_births": (50, 99),
        "sanitation": (30, 99),
    }.items():
        cols[f"{k}_nfhs5"] = r.uniform(lo, hi, n)
        cols[f"{k}_nfhs4"] = [
            None if i % 7 == 0 else float(v) for i, v in enumerate(r.uniform(lo - 5, hi - 5, n))
        ]
    return pl.DataFrame(cols)


@pytest.fixture
def districts() -> pl.DataFrame:
    return make_districts()
