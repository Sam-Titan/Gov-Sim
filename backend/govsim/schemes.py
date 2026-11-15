"""The four V1 schemes and their slider values. Sources: docs/DECISIONS.md D-037."""

from pydantic import BaseModel

# JSY low-performing states (JSY guidelines para 4.1; nhm.gov.in JSY page).
JSY_LPS_STATES = frozenset(
    {
        "Uttar Pradesh",
        "Uttarakhand",
        "Bihar",
        "Jharkhand",
        "Madhya Pradesh",
        "Chhattisgarh",
        "Assam",
        "Rajasthan",
        "Odisha",
        "Jammu & Kashmir",
    }
)


class SchemeInputs(BaseModel):
    """The slider values of one scheme (SPEC section 6)."""

    cash_benefit_inr: float
    document_count: int
    requires_bank_account: bool
    application_burden: int
    benefit_immediacy: int


class Scheme(BaseModel):
    code: str
    name: str
    nfhs_column: str  # NFHS indicator, base name in nfhs_districts.parquet
    inputs: SchemeInputs
    nfhs4_is_baseline: bool  # True: NFHS-4 is pre-scheme (a baseline, never a target)
    assumed: list[str] = []  # slider fields with no source (D-037)
    non_cash: bool = False


SCHEMES: dict[str, Scheme] = {
    "pmjay": Scheme(
        code="pmjay",
        name="PM-JAY",
        nfhs_column="health_insurance",
        inputs=SchemeInputs(
            cash_benefit_inr=500_000,
            document_count=2,
            requires_bank_account=False,
            application_burden=2,
            benefit_immediacy=4,
        ),
        nfhs4_is_baseline=True,
        non_cash=True,
    ),
    "pmuy": Scheme(
        code="pmuy",
        name="PMUY",
        nfhs_column="clean_fuel",
        inputs=SchemeInputs(
            cash_benefit_inr=1_600,
            document_count=6,
            requires_bank_account=True,
            application_burden=3,
            benefit_immediacy=4,
        ),
        nfhs4_is_baseline=True,
    ),
    "jsy": Scheme(
        code="jsy",
        name="JSY",
        nfhs_column="institutional_births",
        # Defaults are the HPS rural values; use jsy_inputs() for a state and area.
        inputs=SchemeInputs(
            cash_benefit_inr=700,
            document_count=2,
            requires_bank_account=False,
            application_burden=2,
            benefit_immediacy=3,
        ),
        nfhs4_is_baseline=False,
    ),
    "sbm": Scheme(
        code="sbm",
        name="SBM",
        nfhs_column="sanitation",
        inputs=SchemeInputs(
            cash_benefit_inr=12_000,
            document_count=1,
            requires_bank_account=True,
            application_burden=3,
            benefit_immediacy=2,
        ),
        nfhs4_is_baseline=False,
        assumed=["document_count", "requires_bank_account"],
    ),
}

CODES = tuple(SCHEMES)


def jsy_benefit(state: str, rural: bool) -> float:
    """JSY mother's package by state group and area (D-037)."""
    if state in JSY_LPS_STATES:
        return 1_400.0 if rural else 1_000.0
    return 700.0 if rural else 600.0


def jsy_documents(state: str) -> int:
    """JSY: LPS 1 (JSY/MCH card); HPS 2 (plus BPL or SC/ST certificate)."""
    return 1 if state in JSY_LPS_STATES else 2


# PM-JAY benefit slider: half to double the real cover, "non-cash cover" (D-041).
PMJAY_BENEFIT_RANGE = (250_000.0, 1_000_000.0)


def clamp_benefit(code: str, value: float) -> float:
    """Keep a benefit slider value in its allowed range (PM-JAY capped, others 0-5,00,000)."""
    lo, hi = PMJAY_BENEFIT_RANGE if code == "pmjay" else (0.0, 500_000.0)
    return min(max(value, lo), hi)
