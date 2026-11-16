import os
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app

SBM = {
    "cash_benefit_inr": 24000,
    "document_count": 1,
    "requires_bank_account": True,
    "application_burden": 2,
    "benefit_immediacy": 2,
}

PMUY_EASY = {**SBM, "cash_benefit_inr": 3000, "application_burden": 1}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def bihar(client) -> list[dict]:
    return client.get("/api/districts", params={"state": "Bihar"}).json()


def test_states_and_districts(client, bihar) -> None:
    states = client.get("/api/states").json()
    assert len(states) == 36
    assert bihar[0]["has_data"] and bihar[0]["name_hi"] is None
    allp = client.get("/api/districts").json()
    assert len(allp) == 710
    bad = [p for p in allp if not p["has_data"]]
    assert all(p["reason"] for p in bad)
    assert client.get("/api/districts", params={"state": "Nowhere"}).json()["code"] == (
        "unknown_state"
    )


def test_schemes(client) -> None:
    schemes = client.get("/api/schemes").json()
    assert [s["code"] for s in schemes] == ["pmjay", "pmuy", "jsy", "sbm"]
    pmjay = schemes[0]
    assert pmjay["non_cash"] and pmjay["ranges"]["cash_benefit_inr"]["min"] == 250000
    assert schemes[2]["defaults_vary_by_district"]


def test_simulate_real_settings_and_changes(client, bihar) -> None:
    did = bihar[0]["id"]
    same = client.post("/api/simulate", json={"district_id": did, "scheme": "sbm"}).json()
    assert same["result"]["point"] == same["result"]["level"]
    assert same["warnings"] == ["survey_estimate"] and same["reasons"] == []
    r = client.post(
        "/api/simulate", json={"district_id": did, "scheme": "sbm", "inputs": SBM}
    ).json()
    assert r["result"]["low"] <= r["result"]["point"] <= r["result"]["high"]
    assert r["reasons"] and len(r["reasons"]) <= 3
    assert r["metric_base"] == "people" and not r["custom"]
    assert r["state_level_traits"]


def test_simulate_warnings(client, bihar) -> None:
    did = bihar[0]["id"]
    far = {**SBM, "application_burden": 5, "benefit_immediacy": 1}
    w = client.post(
        "/api/simulate", json={"district_id": did, "scheme": "sbm", "inputs": far}
    ).json()["warnings"]
    assert "out_of_range" in w
    custom = client.post(
        "/api/simulate",
        json={
            "district_id": did,
            "scheme": "pmuy",
            "target_group": {"unbanked": True},
            "policy_name": "Test",
        },
    ).json()
    assert custom["custom"] and {"new_policy", "partial_data"} <= set(custom["warnings"])
    assert custom["state_level_traits"] == ["bank_account"]


def test_simulate_errors(client, bihar) -> None:
    allp = client.get("/api/districts").json()
    nod = next(p for p in allp if p["reason"] == "unmapped")
    r = client.post("/api/simulate", json={"district_id": nod["id"], "scheme": "sbm"})
    assert r.status_code == 404
    assert r.json()["code"] == "no_data" and r.json()["reason"] == "unmapped"
    r = client.post("/api/simulate", json={"district_id": "nope", "scheme": "sbm"})
    assert r.status_code == 404 and r.json()["code"] == "unknown_district"
    did = bihar[0]["id"]
    big = {**SBM, "application_burden": 9}  # outside the 1-5 slider
    assert (
        client.post(
            "/api/simulate", json={"district_id": did, "scheme": "sbm", "inputs": big}
        ).status_code
        == 422
    )
    cap = {**SBM, "cash_benefit_inr": 1000}  # PM-JAY cover must be 2.5 to 10 lakh
    r = client.post("/api/simulate", json={"district_id": did, "scheme": "pmjay", "inputs": cap})
    assert r.status_code == 422 and r.json()["code"] == "bad_input"


def test_simulate_state_marks_no_data(client) -> None:
    r = client.post("/api/simulate/state", json={"state": "Uttar Pradesh", "scheme": "jsy"}).json()
    rows = r["districts"]
    assert len(rows) == 75
    grey = [x for x in rows if not x["has_data"]]
    assert grey and all(x["result"] is None and x["reason"] for x in grey)
    assert all(x["result"]["low"] <= x["result"]["high"] for x in rows if x["has_data"])
    bad = client.post("/api/simulate/state", json={"state": "Nowhere", "scheme": "jsy"})
    assert bad.status_code == 404


def test_compare_difference(client, bihar) -> None:
    did = bihar[0]["id"]
    body = {
        "district_id": did,
        "a": {"scheme": "sbm"},
        "b": {"scheme": "sbm", "inputs": SBM},
    }
    r = client.post("/api/compare", json=body).json()
    gap = r["b"]["result"]["point"] - r["a"]["result"]["point"]
    assert r["difference"]["point"] == pytest.approx(gap, abs=0.01)
    assert r["difference"]["point"] > 0


def test_report(client) -> None:
    r = client.get("/api/report").json()
    assert r["agent_model_beats_gbm"] is False
    assert isinstance(r["baseline_partial_rows"], int)
    assert r["sampling_band"]["deff"] == {"value": 2.0, "label": "assumed by team"}
    assert "estimated" in r["sampling_band"]["n_used"]["jsy"]


def _time_ms(fn) -> float:
    fn()  # warm up
    runs = []
    for _ in range(10):
        t = time.perf_counter()
        fn()
        runs.append((time.perf_counter() - t) * 1000)
    return sorted(runs)[len(runs) // 2]


def _speed_calls(client, bihar):
    one = {"district_id": bihar[0]["id"], "scheme": "sbm", "inputs": SBM}
    state = {"state": "Uttar Pradesh", "scheme": "sbm", "inputs": SBM}
    return (
        lambda: client.post("/api/simulate", json=one),
        lambda: client.post("/api/simulate/state", json=state),
    )


def test_speed_loose(client, bihar) -> None:
    for call in _speed_calls(client, bihar):
        assert _time_ms(call) < 1000  # loose bound, safe on slow CI machines


@pytest.mark.skipif(bool(os.environ.get("CI")), reason="strict 200 ms check is local-only")
def test_speed_strict_local(client, bihar) -> None:
    for call in _speed_calls(client, bihar):
        assert _time_ms(call) < 200


def test_custom_policy_reports_group_uptake_and_reach(client, bihar) -> None:
    body = {
        "district_id": bihar[0]["id"],
        "scheme": "pmuy",
        "target_group": {"female": True, "rural": True},
        "policy_name": "Test",
    }
    r = client.post("/api/simulate", json=body).json()
    res = r["result"]
    assert res["basis"] == "target_group" and "new_policy" in r["warnings"]
    reach = res["reach"]
    assert reach["group_count"] <= reach["base_count"]
    assert reach["reached_low"] <= reach["reached_point"] <= reach["reached_high"]
    assert reach["reached_point"] == pytest.approx(
        reach["group_count"] * res["point"] / 100, rel=1e-3
    )
    plain = client.post("/api/simulate", json={**body, "target_group": None}).json()
    assert plain["result"]["basis"] == "all" and plain["result"]["reach"] is None


def test_compare_custom_vs_plain_is_not_comparable(client, bihar) -> None:
    did = bihar[0]["id"]
    body = {
        "district_id": did,
        "a": {"scheme": "pmuy"},
        "b": {"scheme": "pmuy", "target_group": {"female": True}},
    }
    d = client.post("/api/compare", json=body).json()["difference"]
    assert d == {"comparable": False, "point": None, "low": None, "high": None}


def test_state_custom_marks_small_groups(client) -> None:
    body = {
        "state": "Bihar",
        "scheme": "pmuy",
        "target_group": {"disabled": True, "age_60_plus": True, "female": True},
    }
    rows = client.post("/api/simulate/state", json=body).json()["districts"]
    small = [x for x in rows if x["reason"] == "group_too_small"]
    assert small and all(not x["has_data"] and x["result"] is None for x in small)
    r = client.post(
        "/api/simulate",
        json={
            "district_id": small[0]["district_id"],
            "scheme": "pmuy",
            "target_group": body["target_group"],
        },
    )
    assert r.status_code == 404 and r.json()["reason"] == "group_too_small"


def test_districts_show_current_state_for_warangal(client) -> None:
    tg = client.get("/api/districts", params={"state": "Telangana"}).json()
    assert "Warangal" in {p["name"] for p in tg}


def test_compare_range_is_min_max_of_set_differences(client, bihar) -> None:
    """D-050: same district and scheme share the NFHS level and band, so they cancel."""
    did = bihar[0]["id"]
    body = {"district_id": did, "a": {"scheme": "sbm"}, "b": {"scheme": "sbm", "inputs": SBM}}
    r = client.post("/api/compare", json=body).json()
    ca, cb = r["a"]["result"]["changes"], r["b"]["result"]["changes"]
    gaps = [cb[k] - ca[k] for k in ("weak", "central", "strong")]
    d = r["difference"]
    assert d["comparable"] is True
    assert d["low"] == pytest.approx(min(gaps), abs=0.02)
    assert d["high"] == pytest.approx(max(gaps), abs=0.02)
    assert d["point"] == pytest.approx(gaps[1], abs=0.02)
    assert d["low"] <= d["point"] <= d["high"]


def test_compare_swapped_flips_sign(client, bihar) -> None:
    did = bihar[0]["id"]
    ab = {"district_id": did, "a": {"scheme": "sbm"}, "b": {"scheme": "sbm", "inputs": SBM}}
    ba = {"district_id": did, "a": ab["b"], "b": ab["a"]}
    d1 = client.post("/api/compare", json=ab).json()["difference"]
    d2 = client.post("/api/compare", json=ba).json()["difference"]
    assert d2["point"] == pytest.approx(-d1["point"], abs=0.02)
    assert d2["low"] == pytest.approx(-d1["high"], abs=0.02)
    assert d2["high"] == pytest.approx(-d1["low"], abs=0.02)


def test_compare_different_schemes_not_comparable(client, bihar) -> None:
    did = bihar[0]["id"]
    body = {"district_id": did, "a": {"scheme": "sbm"}, "b": {"scheme": "pmuy"}}
    d = client.post("/api/compare", json=body).json()["difference"]
    assert d["comparable"] is False and d["point"] is None


def test_compare_custom_different_groups_not_comparable(client, bihar) -> None:
    did = bihar[0]["id"]
    body = {
        "district_id": did,
        "a": {"scheme": "pmuy", "target_group": {"female": True}},
        "b": {"scheme": "pmuy", "target_group": {"rural": True}},
    }
    assert client.post("/api/compare", json=body).json()["difference"]["comparable"] is False


def test_compare_two_custom_policies_same_group(client, bihar) -> None:
    did = bihar[0]["id"]
    group = {"female": True}
    body = {
        "district_id": did,
        "a": {"scheme": "pmuy", "target_group": group},
        "b": {"scheme": "pmuy", "target_group": group, "inputs": PMUY_EASY},
    }
    r = client.post("/api/compare", json=body).json()
    d = r["difference"]
    assert d["comparable"] is True
    assert d["point"] == pytest.approx(
        r["b"]["result"]["point"] - r["a"]["result"]["point"], abs=0.05
    )
    assert d["low"] <= d["point"] <= d["high"]


def test_partial_data_only_where_state_traits_matter(client, bihar) -> None:
    """D-053: an imputed baseline alone gives no warning; income / bank terms do."""
    ar = client.get("/api/districts", params={"state": "Arunachal Pradesh"}).json()
    did = next(p["id"] for p in ar if p["name"] == "East Siang")  # imputed PM-JAY baseline
    real = client.get("/api/schemes").json()
    d = next(s for s in real if s["code"] == "pmjay")["defaults"]

    def warns(inputs):
        body = {"district_id": did, "scheme": "pmjay", "inputs": inputs}
        r = client.post("/api/simulate", json=body).json()
        return set(r["warnings"]), r["state_level_traits"]

    assert "partial_data" not in warns(d)[0]
    assert "partial_data" not in warns({**d, "application_burden": 4, "document_count": 5})[0]
    w, traits = warns({**d, "cash_benefit_inr": d["cash_benefit_inr"] * 1.5})
    assert "partial_data" in w and traits == ["per_capita_income"]
    w, traits = warns({**d, "requires_bank_account": True})
    assert "partial_data" in w and traits == ["bank_account"]


def test_report_counts_pmjay_nfhs5_not_above_nfhs4(client) -> None:
    c = client.get("/api/report").json()["pmjay_nfhs5_not_above_nfhs4"]
    assert c["of"] == 629 and 0 < c["n"] < c["of"]
    assert c["n_own"] <= c["n"] and c["of_own"] <= c["of"]


def test_east_siang_burden_through_simulate_state_and_compare(client) -> None:
    """D-052: the district whose NFHS-5 level is far below its baseline still responds."""
    ar = client.get("/api/districts", params={"state": "Arunachal Pradesh"}).json()
    did = next(p["id"] for p in ar if p["name"] == "East Siang")
    real = client.get("/api/schemes").json()
    pmjay = next(s for s in real if s["code"] == "pmjay")["defaults"]
    worse = {**pmjay, "application_burden": pmjay["application_burden"] + 1}
    one = client.post(
        "/api/simulate", json={"district_id": did, "scheme": "pmjay", "inputs": worse}
    )
    assert one.json()["result"]["point"] - 30.5 <= -1.0
    st = client.post(
        "/api/simulate/state",
        json={"state": "Arunachal Pradesh", "scheme": "pmjay", "inputs": worse},
    ).json()
    mine = next(x for x in st["districts"] if x["district_id"] == did)
    assert mine["result"]["point"] == pytest.approx(one.json()["result"]["point"])
    cmp = client.post(
        "/api/compare",
        json={
            "district_id": did,
            "a": {"scheme": "pmjay"},
            "b": {"scheme": "pmjay", "inputs": worse},
        },
    ).json()
    assert cmp["difference"]["point"] <= -1.0
