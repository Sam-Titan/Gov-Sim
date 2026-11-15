import json

from fastapi import APIRouter

from app.schemas.report import ReportResponse
from govsim.service import ARTIFACTS

router = APIRouter()


@router.get("/report", response_model=ReportResponse, operation_id="getReport")
def get_report() -> ReportResponse:
    data = json.loads((ARTIFACTS / "report.json").read_text())
    data["pmjay_benefit_range_inr"] = list(data["pmjay_benefit_range_inr"])
    return ReportResponse.model_validate(data)
