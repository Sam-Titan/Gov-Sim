from pydantic import BaseModel


class StateOut(BaseModel):
    name: str
    n_districts: int
    n_with_data: int


class DistrictOut(BaseModel):
    id: str  # Census 2011 district id (pc11_d_id) when there is one
    pc11_s_id: str | None
    name: str
    name_hi: str | None = None  # no Hindi district names in our data (rule 4)
    state: str
    has_data: bool
    reason: str | None = None  # unmapped | no_nfhs_sheet | no_state_income
