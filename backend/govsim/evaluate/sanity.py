"""Sanity table: change in covered share (pp) for one-step slider changes (D-040, D-041)."""

from dataclasses import replace

import numpy as np

from govsim.agents.adoption import Design, subset
from govsim.hybrid import slider_change

CHANGES = ("+1 document", "+1 burden", "+1 speed", "double benefit", "add bank requirement")


def modify(x: Design, change: str) -> Design:
    if change == "+1 document":
        return replace(x, docs=x.docs + 1 / 4)
    if change == "+1 burden":
        s = x.scalar.copy()
        s[:, 0] += 0.5  # (burden - 3) / 2
        return replace(x, scalar=s)
    if change == "+1 speed":
        s = x.scalar.copy()
        s[:, 1] += 0.5
        return replace(x, scalar=s)
    if change == "double benefit":
        f = lambda v: np.log1p(2.0 * np.expm1(v))  # noqa: E731
        return replace(x, log_ben_rural=f(x.log_ben_rural), log_ben_urban=f(x.log_ben_urban))
    if change == "add bank requirement":
        return replace(x, bank=np.ones_like(x.bank))
    raise ValueError(change)


def sanity_table(
    x: Design, schemes: np.ndarray, beta_sets: dict[str, dict[str, float]]
) -> dict[str, dict[str, dict[str, float]]]:
    """Median change over NFHS-5 districts, anchored at each district's actual NFHS value."""
    out: dict[str, dict[str, dict[str, float]]] = {}
    for sc in sorted(set(schemes)):
        m = (schemes == sc) & (x.era == 0)
        xs = subset(x, m)
        out[sc] = {
            ch: {
                name: round(float(np.median(slider_change(xs, modify(xs, ch), b, xs.target))), 3)
                for name, b in beta_sets.items()
            }
            for ch in CHANGES
        }
    return out
