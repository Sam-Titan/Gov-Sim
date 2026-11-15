"""Nelder-Mead calibration of the beta terms to NFHS values (loss: MAE in pp + ridge)."""

import numpy as np
from scipy.optimize import minimize

from govsim.agents.adoption import FITTED, PRIOR_SD, PRIORS, RIDGE, Design, covered_share

LAMBDA = 0.5  # ridge weight, in pp per unit of squared (beta / prior sd)


def to_beta(v: np.ndarray, fixed: dict[str, float] | None = None) -> dict[str, float]:
    out = dict(zip(FITTED, v, strict=True))
    out.update(fixed or {})
    return out


def loss(
    v: np.ndarray, x: Design, fixed: dict[str, float] | None = None, prior: str = "neutral"
) -> float:
    beta = to_beta(v, fixed)
    mae = float(np.abs(covered_share(x, beta) - x.target).mean())
    pen = sum(((beta[k] - PRIORS[prior][k]) / PRIOR_SD) ** 2 for k in RIDGE)
    return mae + LAMBDA * pen


def mae(x: Design, beta: dict[str, float]) -> float:
    return float(np.abs(covered_share(x, beta) - x.target).mean())


def fit(
    x: Design,
    start: dict[str, float] | None = None,
    fixed: dict[str, float] | None = None,
    maxiter: int = 4000,
    prior: str = "neutral",
) -> dict[str, float]:
    """Fit all FITTED terms except those in `fixed` (held at the given value, e.g. b8 = 0)."""
    s = {k: 0.0 for k in FITTED} | (start or {})
    free = [k for k in FITTED if k not in (fixed or {})]

    def f(w: np.ndarray) -> float:
        return loss(
            np.array([dict(zip(free, w, strict=True)).get(k, s[k]) for k in FITTED]),
            x,
            fixed,
            prior,
        )

    w = np.array([s[k] for k in free])
    for _ in range(2):  # restart once: Nelder-Mead can stall early
        w = minimize(
            f,
            w,
            method="Nelder-Mead",
            options={"maxiter": maxiter, "xatol": 1e-3, "fatol": 1e-4, "adaptive": True},
        ).x
    return to_beta(np.array([dict(zip(free, w, strict=True)).get(k, s[k]) for k in FITTED]), fixed)
