import numpy as np

from govsim.agents.adoption import FITTED, build_design, covered_share, probabilities, subset
from govsim.agents.sampler import sample_agents
from govsim.calibrate.fit import fit, mae
from govsim.calibrate.recovery import recover
from govsim.data.rows import build_rows

BETA = {
    "b0": 0.3,
    "b2": 0.4,
    "b3": -0.8,
    "b5": -0.5,
    "b6": 0.4,
    "b7": -0.3,
    "b8": -0.6,
    "era_shift": -0.2,
}


def _design(districts):
    rows = build_rows(districts)
    return rows, build_design(districts, rows, sample_agents(districts, n=200))


def test_rows_baseline_rules(districts) -> None:
    rows = build_rows(districts)
    assert set(rows["scheme"]) == {"pmjay", "pmuy", "jsy", "sbm"}
    pm = rows.filter(rows["scheme"] == "pmjay")
    assert (pm["era"] == 0).all()  # NFHS-4 is never a PM-JAY / PMUY target
    assert (pm["baseline"] > 0).all()
    assert pm["baseline_partial"].any()  # districts with no NFHS-4 use the state mean
    jsy = rows.filter(rows["scheme"] == "jsy")
    assert (jsy["baseline"] == 0).all()
    assert set(jsy["era"]) == {0, 1}


def test_covered_share_not_below_baseline_and_in_range(districts) -> None:
    rows, x = _design(districts)
    cov = covered_share(x, BETA)
    assert (cov >= 100 * x.baseline - 1e-9).all()
    assert (cov <= 100).all()


def test_type_grouping_equals_agent_loop(districts) -> None:
    rows, x = _design(districts)
    ag = sample_agents(districts, n=200)
    r = 5
    j = rows["district"][r]
    p_type = probabilities(x, BETA)[r]
    kind = (ag.rural[j] * 4 + (~ag.literate[j]) * 2 + (~ag.banked[j])).astype(int)
    assert np.isclose((p_type[kind]).mean(), (p_type * x.type_w[r]).sum())


def test_more_documents_lower_uptake_for_illiterate(districts) -> None:
    rows, x = _design(districts)
    fewer = covered_share(x, BETA)
    more = covered_share(type(x)(**{**x.__dict__, "docs": x.docs + 1.0}), BETA)
    assert (more <= fewer + 1e-9).all()


def test_fit_is_deterministic_and_improves(districts) -> None:
    rows, x = _design(districts)
    b1, b2 = fit(x, maxiter=300), fit(x, maxiter=300)
    assert b1 == b2
    assert mae(x, b1) < mae(x, {k: 0.0 for k in FITTED})


def test_recovery_on_clean_synthetic_data(districts) -> None:
    rows, x = _design(districts)
    out = recover(x, BETA, noise_sd=0.0)
    # No noise: the fitted model must reproduce the data (betas themselves may trade off).
    sim_target = covered_share(x, BETA)
    from dataclasses import replace

    est = {k: v["est"] for k, v in out.items()}
    assert np.abs(covered_share(replace(x, target=sim_target), est) - sim_target).mean() < 1.5


def test_subset_keeps_alignment(districts) -> None:
    rows, x = _design(districts)
    m = rows["scheme"].to_numpy() == "jsy"
    s = subset(x, m)
    assert len(s.target) == m.sum() and s.type_w.shape[0] == m.sum()
