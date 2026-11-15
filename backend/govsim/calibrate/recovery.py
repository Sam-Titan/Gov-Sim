"""Beta recovery test: simulate NFHS-like targets from known betas, refit, compare."""

from dataclasses import replace

import numpy as np

from govsim.agents.adoption import FITTED, Design, covered_share
from govsim.calibrate.fit import fit


def simulate_targets(x: Design, true_beta: dict[str, float], noise_sd: float, seed: int) -> Design:
    """Replace x.target by model output + Gaussian noise (pp), clipped to 0-100."""
    rng = np.random.default_rng(seed)
    y = covered_share(x, true_beta) + rng.normal(0.0, noise_sd, x.target.shape)
    return replace(x, target=np.clip(y, 0.0, 100.0))


def recover(
    x: Design,
    true_beta: dict[str, float],
    noise_sd: float = 2.0,
    seed: int = 7,
    fixed: dict[str, float] | None = None,
) -> dict[str, dict[str, float]]:
    """Fit simulated data from a start far from the truth. Returns true, estimate, error.

    `fixed` terms are held at their value (D-039); only the free terms are reported.
    """
    sim = simulate_targets(x, true_beta, noise_sd, seed)
    est = fit(sim, start={k: 0.0 for k in FITTED}, fixed=fixed, maxiter=3000)
    free = [k for k in FITTED if k not in (fixed or {})]
    return {k: {"true": true_beta[k], "est": est[k], "err": est[k] - true_beta[k]} for k in free}
