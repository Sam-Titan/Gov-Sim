import numpy as np
import pytest

from govsim.agents.eligibility import TargetGroup
from govsim.schemes import SCHEMES, SchemeInputs, real_envelope
from govsim.service import NoData, Service, UnknownDistrict


@pytest.fixture(scope="module")
def svc() -> Service:
    return Service()


def _first_district(svc: Service, state: str) -> str:
    return next(p["id"] for p in svc.districts(state) if p["has_data"])


def test_places_cover_map_districts_and_flag_no_data(svc: Service) -> None:
    assert len(svc.places) == 710  # 704 NFHS sheets + 6 Census districts with no sheet
    reasons = {p["reason"] for p in svc.places if not p["has_data"]}
    assert reasons == {"unmapped", "no_state_income", "no_nfhs_sheet"}
    assert sum(p["has_data"] for p in svc.places) == 629
    names = {p["name"] for p in svc.places if p["reason"] == "no_nfhs_sheet"}
    assert {"Vidisha", "Lakshadweep", "Chandigarh"} <= names


def test_no_data_and_unknown(svc: Service) -> None:
    unmapped = next(p["id"] for p in svc.places if p["reason"] == "unmapped")
    with pytest.raises(NoData) as e:
        svc.row_for(unmapped, "sbm")
    assert e.value.reason == "unmapped"
    with pytest.raises(UnknownDistrict):
        svc.row_for("nope", "sbm")


def test_real_settings_give_zero_change(svc: Service) -> None:
    row = svc.row_for(_first_district(svc, "Bihar"), "pmuy")
    out = svc.run(np.array([row]), svc.real_inputs(row), None)
    assert np.allclose(out.changes, 0.0, atol=1e-6)
    r = out.ranges[0]
    assert r.low <= r.point <= r.high
    assert r.point == pytest.approx(float(out.level[0]), abs=1e-6)


def test_higher_burden_lowers_result_and_orders_sets(svc: Service) -> None:
    row = svc.row_for(_first_district(svc, "Bihar"), "sbm")
    real = svc.real_inputs(row)
    worse = real.model_copy(update={"application_burden": real.application_burden + 1})
    ch = svc.run(np.array([row]), worse, None).changes[0]
    assert ch[0] > ch[1] > ch[2]  # weak is the smallest drop, strong the largest
    assert ch[2] < 0


def test_jsy_urban_rural_ratio_kept(svc: Service) -> None:
    row = svc.row_for(_first_district(svc, "Uttar Pradesh"), "jsy")
    assert svc.real_inputs(row).cash_benefit_inr == 1400.0  # LPS rural (D-037)
    assert svc.ben_u[row] / svc.ben_r[row] == pytest.approx(1000 / 1400)


def test_reasons_top3_and_target_group(svc: Service) -> None:
    row = svc.row_for(_first_district(svc, "Bihar"), "pmuy")
    real = svc.real_inputs(row)
    new = SchemeInputs(
        cash_benefit_inr=real.cash_benefit_inr * 2,
        document_count=real.document_count + 1,
        requires_bank_account=False,
        application_burden=1,
        benefit_immediacy=5,
    )
    reasons = svc.reasons(row, new, TargetGroup(female=True))
    assert 1 <= len(reasons) <= 3
    sizes = [abs(e) for _, e in reasons]
    assert sizes == sorted(sizes, reverse=True)
    assert svc.reasons(row, svc.real_inputs(row), None) == []


def test_custom_policy_is_uptake_within_the_group(svc: Service) -> None:
    row = svc.row_for(_first_district(svc, "Bihar"), "pmuy")
    rows = np.array([row])
    tg = TargetGroup(age_60_plus=True, rural=True)
    out = svc.run(rows, None, tg)
    r = out.ranges[0]
    assert out.elig_share is not None and 0 < out.elig_share[0] < 0.2
    assert r.new_policy and 0 < r.low <= r.point <= r.high < 100
    assert np.allclose(out.changes, 0.0, atol=1e-6)  # real settings, same group: no change
    everyone = svc.run(rows, None, None).ranges[0].point
    assert r.point != pytest.approx(everyone, abs=0.01)  # a group differs from everyone
    worse = svc.real_inputs(row).model_copy(update={"application_burden": 5})
    assert svc.run(rows, worse, tg).changes[0, 1] < 0


def test_group_too_small(svc: Service) -> None:
    rows = np.array([svc.row_for(_first_district(svc, "Bihar"), "pmuy")])
    tiny = TargetGroup(disabled=True, age_60_plus=True, female=True, unbanked=True)
    out = svc.run(rows, None, tiny)
    assert out.too_small is not None and out.too_small[0]


def test_state_mean_baseline_is_flagged_partial(svc: Service) -> None:
    assert svc.partial.sum() > 0  # districts without NFHS-4 in a state that has it (D-038)
    row = int(np.flatnonzero(svc.partial & (svc.scheme == "pmuy"))[0])
    assert svc.row_of[(int(svc.dist[row]), "pmuy")] == row


def test_delhi_and_telangana_use_official_nfhs4_state_value(svc: Service) -> None:
    """Their districts have no NFHS-4 column: PM-JAY / PMUY use the state value, flagged (D-046)."""
    want = {  # NFHS-4 state totals read from the NFHS-5 state compendium
        ("Telangana", "pmjay"): 66.4,
        ("Telangana", "pmuy"): 67.3,
        ("NCT Delhi", "pmjay"): 15.7,
        ("NCT Delhi", "pmuy"): 97.9,
    }
    for (state, scheme), value in want.items():
        for p in svc.districts(state):
            if not p["has_data"]:
                continue
            row = svc.row_for(p["id"], scheme)
            assert svc.partial[row]
            assert 100 * svc.x.baseline[row] == pytest.approx(value)
    assert (svc.scheme == "pmjay").sum() == 629 == (svc.scheme == "pmuy").sum()


def test_no_baseline_error_if_a_row_is_missing(svc: Service) -> None:
    pid = _first_district(svc, "Telangana")
    key = (svc.d_index[pid], "pmjay")
    saved = svc.row_of.pop(key)
    try:
        with pytest.raises(NoData) as e:
            svc.row_for(pid, "pmjay")
        assert e.value.reason == "no_baseline"
    finally:
        svc.row_of[key] = saved


def test_warangal_listed_under_current_state(svc: Service) -> None:
    w = next(p for p in svc.places if p["name"] == "Warangal")
    assert w["state"] == "Telangana" and w["pc11_s_id"] == "28"  # 2011 link kept
    assert "Warangal" not in {p["name"] for p in svc.districts("Andhra Pradesh")}


def test_out_of_range_uses_real_scheme_envelope(svc: Service) -> None:
    env = real_envelope()
    assert env["application_burden"] == (2, 3)
    inside = SCHEMES["pmuy"].inputs
    assert not svc.out_of_range(inside)
    assert svc.out_of_range(inside.model_copy(update={"application_burden": 5}))
