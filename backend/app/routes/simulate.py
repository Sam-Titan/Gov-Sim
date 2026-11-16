from typing import Annotated, Any

import numpy as np
from fastapi import APIRouter, Depends

from app.deps import get_service
from app.errors import UnknownState
from app.schemas.errors import ErrorBody
from app.schemas.simulate import (
    Changes,
    CompareRequest,
    CompareResponse,
    Difference,
    Inputs,
    Reach,
    Reason,
    Result,
    Setting,
    SimulateRequest,
    SimulateResponse,
    StateRow,
    StateSimulateRequest,
    StateSimulateResponse,
    WarningCode,
)
from govsim.schemes import METRIC_BASE, SchemeInputs
from govsim.service import SETS, NoData, Outcome, Service

router = APIRouter()
Svc = Annotated[Service, Depends(get_service)]
ERRORS: dict[int | str, dict[str, Any]] = {404: {"model": ErrorBody}, 422: {"model": ErrorBody}}
STATE_LEVEL_TRAITS = ["per_capita_income", "bank_account"]  # same value for a whole state


def _inputs(i: Inputs | None) -> SchemeInputs | None:
    return None if i is None else SchemeInputs(**i.model_dump())


def _reach(svc: Service, out: Outcome, i: int, row: int) -> Reach | None:
    if out.elig_share is None:
        return None
    r = out.ranges[i]
    base = float(svc.base[str(svc.scheme[row])][svc.dist[row]])
    group = base * float(out.elig_share[i])
    return Reach(
        base_count=round(base),
        group_share_pct=round(100.0 * float(out.elig_share[i]), 2),
        group_count=round(group),
        reached_point=round(group * r.point / 100.0),
        reached_low=round(group * r.low / 100.0),
        reached_high=round(group * r.high / 100.0),
    )


def _result(svc: Service, out: Outcome, i: int, row: int) -> Result:
    r = out.ranges[i]
    return Result(
        basis="all" if out.elig_share is None else "target_group",
        level=round(float(out.level[i]), 2),
        point=round(r.point, 2),
        low=round(r.low, 2),
        high=round(r.high, 2),
        low_confidence=r.low_confidence,
        changes=Changes(**{n: round(float(out.changes[i, k]), 3) for k, n in enumerate(SETS)}),
        sampling_half_width_pp=round(float(out.half_width[i]), 2),
        reach=_reach(svc, out, i, row),
    )


def _warnings(svc: Service, setting: Setting, out: Outcome, i: int, row: int) -> list[WarningCode]:
    w = [WarningCode.survey_estimate]
    if out.ranges[i].low_confidence:
        w.append(WarningCode.low_confidence)
    if setting.target_group is not None:
        w.append(WarningCode.new_policy)
    if svc.out_of_range(_inputs(setting.inputs)):
        w.append(WarningCode.out_of_range)
    unbanked = setting.target_group is not None and setting.target_group.unbanked is not None
    if svc.partial[row] or unbanked:
        w.append(WarningCode.partial_data)
    return w


def simulate_one(svc: Service, district_id: str, setting: Setting) -> SimulateResponse:
    inputs = _inputs(setting.inputs)
    svc.check_inputs(setting.scheme, inputs)
    row = svc.row_for(district_id, setting.scheme)
    out = svc.run(np.array([row]), inputs, setting.target_group)
    if out.too_small is not None and out.too_small[0]:
        raise NoData("group_too_small")
    real = svc.real_inputs(row)
    reasons = [
        Reason(term=t, effect_pp=round(e, 3), direction="up" if e > 0 else "down")
        for t, e in svc.reasons(row, inputs, setting.target_group)
    ]
    place = svc.place_by_id[district_id]
    return SimulateResponse(
        district_id=district_id,
        district=place["name"],
        state=place["state"],
        scheme=setting.scheme,
        metric_base=METRIC_BASE[setting.scheme],
        custom=setting.target_group is not None,
        policy_name=setting.policy_name,
        result=_result(svc, out, 0, row),
        reasons=reasons,
        warnings=_warnings(svc, setting, out, 0, row),
        real_inputs=Inputs(**real.model_dump()),
        used_inputs=Inputs(**(inputs or real).model_dump()),
        state_level_traits=STATE_LEVEL_TRAITS,
    )


@router.post(
    "/simulate", response_model=SimulateResponse, operation_id="simulate", responses=ERRORS
)
def simulate(req: SimulateRequest, svc: Svc) -> SimulateResponse:
    return simulate_one(svc, req.district_id, req)


@router.post(
    "/simulate/state",
    response_model=StateSimulateResponse,
    operation_id="simulateState",
    responses=ERRORS,
)
def simulate_state(req: StateSimulateRequest, svc: Svc) -> StateSimulateResponse:
    """One row per district of the state. Districts with no data come back `has_data: false`."""
    if req.state not in {s["name"] for s in svc.states()}:
        raise UnknownState(req.state)
    inputs = _inputs(req.inputs)
    svc.check_inputs(req.scheme, inputs)
    found: list[tuple[dict, int | None, str | None]] = []
    for p in svc.districts(req.state):
        if not p["has_data"]:
            found.append((p, None, p["reason"]))
            continue
        row = svc.row_of.get((svc.d_index[p["id"]], req.scheme))
        found.append((p, row, None if row is not None else "no_baseline"))
    rows = np.array([r for _, r, _ in found if r is not None], dtype=int)
    out = svc.run(rows, inputs, req.target_group) if len(rows) else None
    result_rows: list[StateRow] = []
    k = 0  # position in `out`, which only has the rows that have a model row
    for p, row, reason in found:
        k_here = k
        if row is not None:
            k += 1
        too_small = (
            row is not None
            and out is not None
            and out.too_small is not None
            and bool(out.too_small[k_here])
        )
        if row is None or out is None or too_small:
            result_rows.append(
                StateRow(
                    district_id=p["id"],
                    district=p["name"],
                    has_data=False,
                    reason="group_too_small" if too_small else reason,
                )
            )
            continue
        result_rows.append(
            StateRow(
                district_id=p["id"],
                district=p["name"],
                has_data=True,
                result=_result(svc, out, k_here, row),
                warnings=_warnings(svc, req, out, k_here, row),
            )
        )
    return StateSimulateResponse(
        state=req.state,
        scheme=req.scheme,
        metric_base=METRIC_BASE[req.scheme],
        custom=req.target_group is not None,
        districts=result_rows,
    )


def _clip(v: float) -> float:
    return min(100.0, max(0.0, v))


def _difference(a: SimulateResponse, b: SimulateResponse, same_group: bool) -> Difference:
    """B minus A (D-050).

    Comparable only for the same real scheme and the same basis (and the same target
    group for custom policies). Then the NFHS level and the sampling band are shared, so
    they cancel: the range is the min / max of (B - A) across the weak / central / strong
    beta sets, not the range of B minus the range of A.
    """
    ra, rb = a.result, b.result
    same = a.scheme == b.scheme and ra.basis == rb.basis and same_group and ra.level == rb.level
    if not same:
        return Difference(comparable=False, point=None, low=None, high=None)
    ca, cb = ra.changes, rb.changes
    # Real schemes: level + change, kept inside 0-100 like the result. Custom policies:
    # the change is already measured in group uptake (same group, same real settings).
    gaps = [
        _clip(rb.level + y) - _clip(ra.level + x) if ra.basis == "all" else y - x
        for x, y in ((ca.weak, cb.weak), (ca.central, cb.central), (ca.strong, cb.strong))
    ]
    return Difference(
        comparable=True,
        point=round(gaps[1], 2),
        low=round(min(gaps), 2),
        high=round(max(gaps), 2),
    )


@router.post("/compare", response_model=CompareResponse, operation_id="compare", responses=ERRORS)
def compare(req: CompareRequest, svc: Svc) -> CompareResponse:
    a = simulate_one(svc, req.district_id, req.a)
    b = simulate_one(svc, req.district_id, req.b)
    return CompareResponse(
        a=a,
        b=b,
        difference=_difference(a, b, req.a.target_group == req.b.target_group),
    )
