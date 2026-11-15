"""Seeded agent sampler. Same seed + district = same agents (common random numbers)."""

from dataclasses import dataclass

import numpy as np
import polars as pl

N_AGENTS = 500
SEED = 42
N_TRAITS = 6  # rural, female, age60, disabled, literate, banked


@dataclass(frozen=True)
class Agents:
    """Boolean arrays of shape (districts, agents)."""

    rural: np.ndarray
    female: np.ndarray
    age60: np.ndarray
    disabled: np.ndarray
    literate: np.ndarray
    banked: np.ndarray  # state-level share, partial_data


def uniform_draws(district_ids: list[str], n: int = N_AGENTS, seed: int = SEED) -> np.ndarray:
    """Fixed uniform draws per district: shape (districts, n, N_TRAITS)."""
    out = np.empty((len(district_ids), n, N_TRAITS))
    for k, did in enumerate(district_ids):
        rng = np.random.default_rng(np.random.SeedSequence([seed, int(did)]))
        out[k] = rng.random((n, N_TRAITS))
    return out


def sample_agents(d: pl.DataFrame, n: int = N_AGENTS, seed: int = SEED) -> Agents:
    """Sample agents for every district in `d` (one row per district)."""
    u = uniform_draws(d["pc11_d_id"].to_list(), n, seed)
    share = lambda col, scale=1.0: d[col].to_numpy()[:, None] / scale  # noqa: E731
    return Agents(
        rural=u[:, :, 0] < share("census_rural_share"),
        female=u[:, :, 1] < share("census_female_share"),
        age60=u[:, :, 2] < share("census_age_60plus_share"),
        disabled=u[:, :, 3] < share("census_disabled_share"),
        literate=u[:, :, 4] < share("census_literacy_rate_7plus"),
        banked=u[:, :, 5] < share("state_women_bank_account_nfhs5", 100.0),
    )
