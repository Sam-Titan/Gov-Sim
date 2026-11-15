from pydantic import BaseModel

from govsim.schemes import SchemeInputs


class Range2(BaseModel):
    min: float
    max: float


class SchemeOut(BaseModel):
    code: str
    name: str
    label: str = "proxy"
    metric_base: str  # households | births | people (D-030)
    defaults: SchemeInputs  # JSY: high-performing-state rural values (see /simulate real_inputs)
    defaults_vary_by_district: bool  # JSY only (state group, rural/urban)
    non_cash: bool
    assumed: list[str]
    ranges: dict[str, Range2]
    real_envelope: dict[str, Range2]
