from dataclasses import replace

import numpy as np

from govsim.agents.adoption import build_design, covered_share
from govsim.agents.sampler import sample_agents
from govsim.data.rows import build_rows
from govsim.evaluate.sanity import modify
from govsim.hybrid import Range, anchor_shift, combine_range, sampling_band, slider_change
from govsim.schemes import clamp_benefit

BETA = {
    "b0": 0.5,
    "b2": 0.5,
    "b3": -0.8,
    "b5": -0.6,
    "b6": 0.4,
    "b7": -0.7,
    "b8": -0.9,
    "era_shift": 0.0,
}


def _x(districts):
    rows = build_rows(districts)
    return build_design(districts, rows, sample_agents(districts, n=200))


def test_anchor_matches_level(districts) -> None:
    x = _x(districts)
    level = np.clip(x.target, 100 * x.baseline + 1, 98)
    shift = anchor_shift(x, BETA, level)
    assert np.allclose(covered_share(replace(x, shift=shift), BETA), level, atol=0.05)


def test_zero_change_is_zero_and_signs(districts) -> None:
    x = _x(districts)
    assert np.allclose(slider_change(x, x, BETA, x.target), 0.0)
    burden = slider_change(x, modify(x, "+1 burden"), BETA, x.target)
    speed = slider_change(x, modify(x, "+1 speed"), BETA, x.target)
    assert (burden <= 0).all() and (speed >= 0).all()


def test_sampling_band_shrinks_with_n_and_is_widest_at_50() -> None:
    lo, hi = sampling_band(np.array([50.0, 50.0, 10.0]), np.array([400.0, 900.0, 900.0]))
    assert hi[0] > hi[1] > hi[2] and np.allclose(lo, -hi)


def test_combine_range_end_to_end_and_low_confidence() -> None:
    r = combine_range(60.0, (-2.0, -5.0, -9.0), -3.0, 3.0)
    assert (r.low, r.point, r.high) == (48.0, 55.0, 61.0)  # 60 - 9 - 3, 60 - 5, 60 - 2 + 3
    assert not r.low_confidence
    wide = combine_range(50.0, (0.0, 0.0, 0.0), -20.0, 20.0)
    assert wide.low_confidence
    assert isinstance(combine_range(50, (0, 0, 0), -1, 1, new_policy=True), Range)
    assert combine_range(50, (0, 0, 0), -1, 1, new_policy=True).new_policy


def test_pmjay_benefit_cap() -> None:
    assert clamp_benefit("pmjay", 100_000) == 250_000
    assert clamp_benefit("pmjay", 5_000_000) == 1_000_000
    assert clamp_benefit("pmuy", 900_000) == 500_000
