from pydantic import BaseModel


class ErrorBody(BaseModel):
    """Error body for 404s: `code` is `unknown_district`, `no_data` or `unknown_state`."""

    code: str
    message: str
    reason: str | None = None  # no_data only: unmapped, no_nfhs_sheet, no_state_income, no_baseline
