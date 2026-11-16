from typing import Any

from pydantic import BaseModel


class ReportResponse(BaseModel):
    """Model report data: `artifacts/report.json` as written by `just train`.

    `agent_model_beats_gbm` is False: the report page must say so (D-039).
    """

    agent_model_beats_gbm: bool
    n_districts: int
    n_rows: int
    n_agents: int
    baseline_partial_rows: int  # rows whose PM-JAY / PMUY baseline is a state value
    losto_headline: dict[str, Any]
    loso: dict[str, Any]
    loso_note: str
    betas: dict[str, Any]
    gbm_losto_error_band_pp: dict[str, Any]
    sampling_band: dict[str, Any]
    sanity_table_pp: dict[str, Any]
    recovery: dict[str, Any]
    in_sample_mae_unanchored: dict[str, float]
    gbm_in_sample_mae: float
    pmjay_benefit_range_inr: list[float]
    decisions: str
