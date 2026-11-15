from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from govsim.service import BadInput, NoData, UnknownDistrict


class UnknownState(Exception):
    pass


NO_DATA_TEXT = {
    "unmapped": "This district was created after Census 2011 and could not be matched to one.",
    "no_nfhs_sheet": "There is no NFHS-5 district sheet for this district.",
    "no_state_income": "No state income figure exists for this state or union territory.",
    "no_baseline": "There is no NFHS-4 baseline for this scheme in this district or its state.",
    "group_too_small": "The target group is too small in this district to model.",
}


def _body(status: int, code: str, message: str, reason: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"code": code, "message": message, "reason": reason}
    )


def add_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NoData)
    async def _no_data(_: Request, e: NoData) -> JSONResponse:
        return _body(404, "no_data", NO_DATA_TEXT.get(e.reason, "No data."), e.reason)

    @app.exception_handler(UnknownDistrict)
    async def _unknown_district(_: Request, e: UnknownDistrict) -> JSONResponse:
        return _body(404, "unknown_district", f"Unknown district id: {e}")

    @app.exception_handler(UnknownState)
    async def _unknown_state(_: Request, e: UnknownState) -> JSONResponse:
        return _body(404, "unknown_state", f"Unknown state: {e}")

    @app.exception_handler(BadInput)
    async def _bad_input(_: Request, e: BadInput) -> JSONResponse:
        return _body(422, "bad_input", str(e))
