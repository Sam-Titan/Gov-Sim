"""Hybrid output (D-039, D-040, D-041).

level  = actual NFHS-5 value of the district (real schemes) or of the scheme a custom
         policy "starts from"
change = the level moved in logit space by the average change in z of the eligible agents
         (D-052): sigmoid(logit(level) + mean dz) - level; no baseline term
range  = level + [change_min + sampling_low, change_max + sampling_high]
"""

from dataclasses import dataclass, replace

import numpy as np

from govsim.agents.adoption import Design, logits, probabilities

DEFF = 2.0  # assumed by team: design effect of the clustered NFHS sample (D-041)
Z80 = 1.2816  # 10th-90th percentile of a normal distribution
LOW_CONFIDENCE_PP = 30.0
LEVEL_FLOOR_PP = 0.5  # a level of exactly 0 or 100 has no logit; keep it inside
SET_NAMES = ("weak", "central", "strong")


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def anchor_shift(x: Design, beta: dict[str, float], level_pp: np.ndarray) -> np.ndarray:
    """Per-row shift of z so the eligible agents' mean sign-up probability equals `level_pp`.

    No baseline term (D-052): used for custom policies, to find the target group's own level.
    """
    goal = np.clip(level_pp, 0.5, 99.5) / 100.0
    w = x.type_w.sum(axis=1)
    w = np.where(w > 0, w, 1.0)
    lo, hi = np.full(len(goal), -20.0), np.full(len(goal), 20.0)
    for _ in range(50):
        mid = (lo + hi) / 2
        mean_p = (probabilities(replace(x, shift=mid), beta) * x.type_w).sum(axis=1) / w
        low_side = mean_p < goal
        lo, hi = np.where(low_side, mid, lo), np.where(low_side, hi, mid)
    return (lo + hi) / 2


def mean_dz(real: Design, new: Design, beta: dict[str, float]) -> np.ndarray:
    """Change in z from `real` to `new`, averaged over the eligible agent types of `new`.

    The anchor shift is the same in both, so it cancels.
    """
    w = new.type_w
    total = np.where(w.sum(axis=1) > 0, w.sum(axis=1), 1.0)
    return ((logits(new, beta) - logits(real, beta)) * w).sum(axis=1) / total


def logit_level(level_pp: np.ndarray, dz: np.ndarray) -> np.ndarray:
    """New level (pp) = sigmoid(logit(level) + dz), the whole level moved in logit space (D-052)."""
    p = np.clip(level_pp, LEVEL_FLOOR_PP, 100.0 - LEVEL_FLOOR_PP) / 100.0
    return 100.0 * _sigmoid(np.log(p / (1.0 - p)) + dz)


def slider_change(
    real: Design, new: Design, beta: dict[str, float], level_pp: np.ndarray
) -> np.ndarray:
    """Change in the level (pp) from the real settings to the new settings (D-052)."""
    lv = np.clip(level_pp, LEVEL_FLOOR_PP, 100.0 - LEVEL_FLOOR_PP)
    return logit_level(lv, mean_dz(real, new, beta)) - lv


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
