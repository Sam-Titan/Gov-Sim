from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.deps import get_service
from app.errors import UnknownState
from app.schemas.errors import ErrorBody
from app.schemas.places import DistrictOut, StateOut
from app.schemas.schemes import Range2, SchemeOut
from govsim.schemes import (
    BURDEN_RANGE,
    DOCUMENTS_RANGE,
    IMMEDIACY_RANGE,
    METRIC_BASE,
    SCHEMES,
    benefit_range,
    real_envelope,
)
from govsim.service import Service

router = APIRouter()
Svc = Annotated[Service, Depends(get_service)]
NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorBody}}


@router.get("/states", response_model=list[StateOut], operation_id="getStates")
def get_states(svc: Svc) -> list[dict]:
    return svc.states()


@router.get(
    "/districts",
    response_model=list[DistrictOut],
    operation_id="getDistricts",
    responses=NOT_FOUND,
)
def get_districts(svc: Svc, state: str | None = None) -> list[dict]:
    """All districts of a state, with `has_data` and a `reason` when there is no data."""
    if state is not None and state not in {s["name"] for s in svc.states()}:
        raise UnknownState(state)
    return svc.districts(state)


@router.get("/schemes", response_model=list[SchemeOut], operation_id="getSchemes")
def get_schemes() -> list[SchemeOut]:
    env = {k: Range2(min=lo, max=hi) for k, (lo, hi) in real_envelope().items()}
    out = []
    for code, s in SCHEMES.items():
        lo, hi = benefit_range(code)
        out.append(
            SchemeOut(
                code=code,
                name=s.name,
                metric_base=METRIC_BASE[code],
                defaults=s.inputs,
                defaults_vary_by_district=code == "jsy",
                non_cash=s.non_cash,
                assumed=s.assumed,
                ranges={
                    "cash_benefit_inr": Range2(min=lo, max=hi),
                    "document_count": Range2(min=DOCUMENTS_RANGE[0], max=DOCUMENTS_RANGE[1]),
                    "application_burden": Range2(min=BURDEN_RANGE[0], max=BURDEN_RANGE[1]),
                    "benefit_immediacy": Range2(min=IMMEDIACY_RANGE[0], max=IMMEDIACY_RANGE[1]),
                },
                real_envelope=env,
            )
        )
    return out
