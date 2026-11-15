import numpy as np

from govsim.agents.eligibility import TargetGroup, eligible_mask
from govsim.agents.sampler import sample_agents, uniform_draws


def test_draws_are_deterministic_and_district_specific() -> None:
    a = uniform_draws(["1", "2"], 50)
    assert np.array_equal(a, uniform_draws(["1", "2"], 50))
    assert not np.array_equal(a[0], a[1])
    assert np.array_equal(a[0], uniform_draws(["1"], 50)[0])  # order does not matter


def test_sampled_shares_match_traits(districts) -> None:
    ag = sample_agents(districts, n=4000)
    assert np.allclose(ag.rural.mean(axis=1), districts["census_rural_share"], atol=0.05)
    assert np.allclose(ag.literate.mean(axis=1), districts["census_literacy_rate_7plus"], atol=0.05)
    bank = districts["state_women_bank_account_nfhs5"].to_numpy() / 100
    assert np.allclose(ag.banked.mean(axis=1), bank, atol=0.05)


def test_eligibility_filters(districts) -> None:
    ag = sample_agents(districts, n=200)
    assert eligible_mask(ag).all()
    m = eligible_mask(ag, TargetGroup(rural=True, age_60_plus=True))
    assert np.array_equal(m, ag.rural & ag.age60)
    assert np.array_equal(eligible_mask(ag, TargetGroup(unbanked=True)), ~ag.banked)
