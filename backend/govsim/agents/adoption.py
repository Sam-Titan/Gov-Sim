"""Adoption model: p = sigmoid(z); covered = b + (1 - b) * mean(eligible * p) (D-038).

z = b0 + b1*trust + b2*log(1+benefit/monthly_income) + b3*docs*illiterate + b5*burden
    + b6*speed + b7*deprivation + b8*bank_required*unbanked (+ era_shift on NFHS-4 rows).
b1 is fixed (trust has no data, D-038); era_shift is a nuisance shift, not a beta.
"""

from dataclasses import dataclass

import numpy as np
import polars as pl

from govsim.agents.eligibility import TargetGroup, eligible_mask
from govsim.agents.sampler import Agents
from govsim.data.rows import INCOME

BETA1 = 1.0  # assumed, not fitted
TRUST = 0.0  # assumed prior mean of the district trust latent
FITTED = ("b0", "b2", "b3", "b5", "b6", "b7", "b8", "era_shift")
PRIOR_SD = 1.0  # ridge prior on all fitted terms except b0 and era_shift
# Prior means. "neutral": 0 for all (signs come from data). "signed": expected signs, size 0.5.
PRIORS = {
    "neutral": dict.fromkeys(("b2", "b3", "b5", "b6", "b7", "b8"), 0.0),
    "signed": {"b2": 0.5, "b3": -0.5, "b5": -0.5, "b6": 0.5, "b7": -0.5, "b8": -0.5},
}
RIDGE = ("b2", "b3", "b5", "b6", "b7", "b8")
DOCS_SCALE = 4.0
MONTHS = 12.0


# Agents differ in z only by (rural, illiterate, unbanked): 8 types. Grouping agents by type
# gives the same expected uptake as looping over every agent, about 60x faster.
TYPE_RURAL = np.array([(t >> 2) & 1 for t in range(8)], dtype=bool)
TYPE_ILL = np.array([(t >> 1) & 1 for t in range(8)], dtype=float)
TYPE_UNB = np.array([t & 1 for t in range(8)], dtype=float)


@dataclass(frozen=True)
class Design:
    """Everything the model needs for R rows. Agents are fixed (common random numbers)."""

    scalar: np.ndarray  # (R, 4): burden_c, speed_c, deprivation, era
    log_ben_rural: np.ndarray  # (R,)  log(1 + benefit_rural / monthly income)
    log_ben_urban: np.ndarray  # (R,)
    docs: np.ndarray  # (R,) documents / 4
    bank: np.ndarray  # (R,) bank account required (0/1)
    type_w: np.ndarray  # (R, 8) share of the district's agents that are eligible, by type
    baseline: np.ndarray  # (R,)
    target: np.ndarray  # (R,) in pp
    era: np.ndarray  # (R,)
    shift: np.ndarray  # (R,) logit anchor shift (D-041); 0 = not anchored


def build_design(
    d: pl.DataFrame,
    rows: pl.DataFrame,
    agents: Agents,
    target_group: TargetGroup | None = None,
) -> Design:
    j = rows["district"].to_numpy()
    income = d[INCOME].to_numpy()[j] / MONTHS  # monthly income (D-040)
    kind = (agents.rural[j] * 4 + (~agents.literate[j]) * 2 + (~agents.banked[j])).astype(int)
    elig = eligible_mask(agents, target_group)[j]
    type_w = np.stack([((kind == t) & elig).mean(axis=1) for t in range(8)], axis=1)
    scalar = np.column_stack(
        [
            (rows["burden"].to_numpy() - 3.0) / 2.0,
            (rows["immediacy"].to_numpy() - 3.0) / 2.0,
            d["deprivation_score"].to_numpy()[j],
            rows["era"].to_numpy().astype(float),
        ]
    )
    return Design(
        scalar=scalar,
        log_ben_rural=np.log1p(rows["benefit_rural"].to_numpy() / income),
        log_ben_urban=np.log1p(rows["benefit_urban"].to_numpy() / income),
        docs=rows["documents"].to_numpy() / DOCS_SCALE,
        bank=rows["bank_required"].to_numpy(),
        type_w=type_w,
        baseline=rows["baseline"].to_numpy(),
        target=rows["target"].to_numpy(),
        era=rows["era"].to_numpy(),
        shift=np.zeros(len(j)),
    )


def logits(x: Design, beta: dict[str, float]) -> np.ndarray:
    """z for every (row, agent type): shape (R, 8)."""
    const = (
        beta["b0"]
        + BETA1 * TRUST
        + beta["b5"] * x.scalar[:, 0]
        + beta["b6"] * x.scalar[:, 1]
        + beta["b7"] * x.scalar[:, 2]
        + beta["era_shift"] * x.scalar[:, 3]
        + x.shift
    )
    log_ben = np.where(TYPE_RURAL[None, :], x.log_ben_rural[:, None], x.log_ben_urban[:, None])
    return (
        const[:, None]
        + beta["b2"] * log_ben
        + beta["b3"] * x.docs[:, None] * TYPE_ILL[None, :]
        + beta["b8"] * x.bank[:, None] * TYPE_UNB[None, :]
    )


def probabilities(x: Design, beta: dict[str, float]) -> np.ndarray:
    """Sign-up probability for every (row, agent type): shape (R, 8)."""
    return 1.0 / (1.0 + np.exp(-logits(x, beta)))


def uptake_terms(x: Design, beta: dict[str, float]) -> np.ndarray:
    """Mean of eligible * p over all agents, per row (share of non-covered who sign up)."""
    return (probabilities(x, beta) * x.type_w).sum(axis=1)


def covered_share(x: Design, beta: dict[str, float]) -> np.ndarray:
    """Predicted covered share in percentage points, one value per row."""
    return 100.0 * (x.baseline + (1.0 - x.baseline) * uptake_terms(x, beta))


def subset(x: Design, mask: np.ndarray) -> Design:
    return Design(*(getattr(x, f)[mask] for f in x.__dataclass_fields__))
