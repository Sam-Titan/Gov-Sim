"""Who can sign up. Real schemes: everyone (D-038). Custom policies: a target group."""

import numpy as np
from pydantic import BaseModel

from govsim.agents.sampler import Agents


class TargetGroup(BaseModel):
    """Custom-policy target group (SPEC 7.2). None means no filter on that trait."""

    age_60_plus: bool | None = None
    female: bool | None = None
    disabled: bool | None = None
    rural: bool | None = None
    unbanked: bool | None = None  # state-level trait, partial_data


def eligible_mask(agents: Agents, target: TargetGroup | None = None) -> np.ndarray:
    """Boolean (districts, agents) mask. No target group = everyone is eligible."""
    mask = np.ones(agents.rural.shape, dtype=bool)
    if target is None:
        return mask
    for field, arr in (
        ("age_60_plus", agents.age60),
        ("female", agents.female),
        ("disabled", agents.disabled),
        ("rural", agents.rural),
        ("unbanked", ~agents.banked),
    ):
        want = getattr(target, field)
        if want is not None:
            mask &= arr == want
    return mask
