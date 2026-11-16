import json
from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps import get_service
from app.schemas.report import ReportResponse
from govsim.service import ARTIFACTS, Service

router = APIRouter()
Svc = Annotated[Service, Depends(get_service)]


@router.get("/report", response_model=ReportResponse, operation_id="getReport")
def get_report(svc: Svc) -> ReportResponse:
    data = json.loads((ARTIFACTS / "report.json").read_text())
    data["pmjay_benefit_range_inr"] = list(data["pmjay_benefit_range_inr"])
    data["pmjay_nfhs5_not_above_nfhs4"] = svc.pmjay_fell()
    return ReportResponse.model_validate(data)
