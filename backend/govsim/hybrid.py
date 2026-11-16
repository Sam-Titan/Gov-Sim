"""Hybrid output (D-039, D-040, D-041).

level  = actual NFHS-5 value of the district (real schemes) or of the scheme a custom
         policy "starts from"
change = agent model at the user's settings minus agent model at the real settings, with the
         district's z shifted (anchored in logit space) so the model starts at `level`
range  = level + [change_min + sampling_low, change_max + sampling_high]
"""

from dataclasses import dataclass, replace

import numpy as np

from govsim.agents.adoption import Design, covered_share

DEFF = 2.0  # assumed by team: design effect of the clustered NFHS sample (D-041)
Z80 = 1.2816  # 10th-90th percentile of a normal distribution
LOW_CONFIDENCE_PP = 30.0
SET_NAMES = ("weak", "central", "strong")


def anchor_shift(x: Design, beta: dict[str, float], level_pp: np.ndarray) -> np.ndarray:
    """Per-row shift of z (logit space) so covered_share(x) equals `level_pp`."""
    lo_pp = 100.0 * x.baseline + 0.5  # the model cannot go below the baseline
    goal = np.clip(level_pp, lo_pp, 99.5)
    lo, hi = np.full(len(goal), -20.0), np.full(len(goal), 20.0)
    for _ in range(50):
        mid = (lo + hi) / 2
        low_side = covered_share(replace(x, shift=mid), beta) < goal
        lo, hi = np.where(low_side, mid, lo), np.where(low_side, hi, mid)
    return (lo + hi) / 2


def slider_change(
    real: Design, new: Design, beta: dict[str, float], level_pp: np.ndarray
) -> np.ndarray:
    """Change in covered share (pp) from the real settings to the new settings, anchored."""
    shift = anchor_shift(real, beta, level_pp)
    return covered_share(replace(new, shift=shift), beta) - covered_share(
        replace(real, shift=shift), beta
    )


def sampling_band(
    level_pp: np.ndarray, n: np.ndarray, deff: float = DEFF
) -> tuple[np.ndarray, np.ndarray]:
    """10th and 90th percentile offsets (pp) of the NFHS sampling error.

    SE = sqrt(deff * p * (1 - p) / n), n = households (PM-JAY, PMUY, SBM) or estimated
    births (JSY, D-042). Symmetric, so the offsets are -Z80*SE and +Z80*SE.
    """
    p = np.clip(level_pp / 100.0, 0.0, 1.0)
    half = 100.0 * Z80 * np.sqrt(deff * p * (1.0 - p) / n)
    return -half, half


@dataclass(frozen=True)
class Range:
    low: float
    point: float
    high: float
    low_confidence: bool
    new_policy: bool


def combine_range(
    level: float,
    changes: tuple[float, float, float],
    err_low: float,
    err_high: float,
    new_policy: bool = False,
) -> Range:
    """End-to-end sum (not root-of-squares): worst case, both errors line up (D-040).

    `changes` = (weak, central, strong) slider change. Custom policies are always
    labelled `new_policy`.
    """
    low = max(0.0, level + min(changes) + err_low)
    high = min(100.0, level + max(changes) + err_high)
    point = min(100.0, max(0.0, level + changes[1]))
    return Range(low, point, high, (high - low) > LOW_CONFIDENCE_PP, new_policy)
