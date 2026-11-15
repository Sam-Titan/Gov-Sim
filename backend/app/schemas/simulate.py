from enum import StrEnum

from pydantic import BaseModel, Field

from govsim.agents.eligibility import TargetGroup


class WarningCode(StrEnum):
    survey_estimate = "survey_estimate"
    low_confidence = "low_confidence"
    new_policy = "new_policy"
    out_of_range = "out_of_range"  # shown as "Beyond what real schemes do"
    partial_data = "partial_data"


class Inputs(BaseModel):
    """Slider values (SPEC section 6). PM-JAY cash is capped to 2.5 to 10 lakh by the route."""

    cash_benefit_inr: float = Field(ge=0, le=1_000_000)
    document_count: int = Field(ge=0, le=8)
    requires_bank_account: bool
    application_burden: int = Field(ge=1, le=5)
    benefit_immediacy: int = Field(ge=1, le=5)


class Setting(BaseModel):
    """One policy setting. `scheme` is the real scheme to start from.

    No `inputs` = the scheme's real settings. A `target_group` makes it a custom policy.
    """

    scheme: str
    inputs: Inputs | None = None
    target_group: TargetGroup | None = None
    policy_name: str | None = None


class SimulateRequest(Setting):
    district_id: str


class StateSimulateRequest(Setting):
    state: str


class CompareRequest(BaseModel):
    district_id: str
    a: Setting
    b: Setting


class Changes(BaseModel):
    """Slider change in percentage points at the weak / central / strong beta sets."""

    weak: float
    central: float
    strong: float


class Reason(BaseModel):
    term: str  # benefit | documents | bank_account | burden | speed | target_group
    effect_pp: float  # central beta set, anchored
    direction: str  # up | down


class Reach(BaseModel):
    """Custom policies (D-044): households / births / people reached. Estimated (Census 2011)."""

    base_count: int  # households (PM-JAY, PMUY), births in 5 years (JSY), people (SBM)
    group_share_pct: float  # target group as a % of the base (agent sample)
    group_count: int
    reached_point: int
    reached_low: int
    reached_high: int


class Result(BaseModel):
    """What point / low / high measure is given by `basis`.

    `all`: share of all households / births / people covered, % (NFHS-based, real schemes).
    `target_group`: uptake within the target group, % (custom policies; not comparable with
    `all`). Custom policies also carry `reach`.
    """

    basis: str  # all | target_group
    level: float  # actual NFHS-5 value of the scheme the policy starts from (share of all)
    point: float
    low: float
    high: float
    low_confidence: bool
    changes: Changes  # model assumption
    sampling_half_width_pp: float
    reach: Reach | None = None


class SimulateResponse(BaseModel):
    district_id: str
    district: str
    state: str
    scheme: str
    metric_base: str
    custom: bool
    policy_name: str | None
    result: Result
    reasons: list[Reason]
    warnings: list[WarningCode]
    real_inputs: Inputs  # the district's real settings (JSY by state group and area)
    used_inputs: Inputs
    state_level_traits: list[str]  # partial_data note: same value for the whole state


class StateRow(BaseModel):
    district_id: str
    district: str
    has_data: bool
    reason: str | None = None
    result: Result | None = None
    warnings: list[WarningCode] = []


class StateSimulateResponse(BaseModel):
    state: str
    scheme: str
    metric_base: str
    custom: bool
    districts: list[StateRow]


class Difference(BaseModel):
    """B minus A. None when A and B are measured on different bases (all vs target group)."""

    comparable: bool
    point: float | None
    low: float | None
    high: float | None


class CompareResponse(BaseModel):
    a: SimulateResponse
    b: SimulateResponse
    difference: Difference  # B minus A
