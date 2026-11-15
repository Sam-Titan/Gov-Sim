import polars as pl

from scripts import census, traits


def test_disability_wide_sums_age_groups() -> None:
    rec = [
        ("01", "001", "Total", "Total", 100),
        ("01", "001", "Total", "0-4", 10),
        ("01", "001", "Total", "20-29", 30),
        ("01", "001", "Total", "60-69", 20),
        ("01", "001", "Total", "90+", 5),
    ]
    row = census.disability_wide(rec).row(0, named=True)
    assert row["disabled_all_total"] == 100
    assert row["disabled_20plus_total"] == 55
    assert row["disabled_60plus_total"] == 25


def test_build_keeps_unmapped_with_null_census_and_flags() -> None:
    nfhs = pl.DataFrame(
        {
            "file": ["a", "b"],
            **{f"{k}_nfhs5": [90.0, 80.0] for k in traits.DEPRIVATION_SIGNS},
            **{f"{k}_nfhs4": [None, 70.0] for k in traits.DEPRIVATION_SIGNS},
        }
    )
    jt = pl.DataFrame(
        {
            "nfhs_file": ["a", "b"],
            "nfhs_state": ["S", "S"],
            "pc11_s_id": ["01", None],
            "pc11_d_id": ["001", None],
            "match_type": ["exact", "unmapped"],
        }
    )
    cen = pl.DataFrame(
        {
            "pc11_s_id": ["01"],
            "pc11_d_id": ["001"],
            "name": ["X"],
            **{
                f"{k}_{s}": [10]
                for k in ("population", "female", "age_0_6", "sc", "st", "literate", "workers")
                for s in ("total", "rural")
            },
        }
    )
    dis = pl.DataFrame(
        {
            "pc11_s_id": ["01"],
            "pc11_d_id": ["001"],
            "disabled_all_total": [1],
            "disabled_20plus_total": [1],
            "disabled_60plus_total": [1],
        }
    )
    age = pl.DataFrame(
        {"pc11_s_id": ["01"], "pc11_d_id": ["001"], "age_all": [100], "age_60plus": [12]}
    )
    st = pl.DataFrame(
        {
            "state": ["S"],
            **{f"women_{k}_nfhs5": [50.0] for k in ("bank_account", "mobile_phone", "internet")},
            "women_bank_account_nfhs4": [40.0],
            "women_mobile_phone_nfhs4": [30.0],
        }
    )
    inc = pl.DataFrame({"state": ["S"], "per_capita_nsdp_2021_22": [100000]})
    out = traits.build(nfhs, jt, cen, dis, age, st, inc)
    assert out["census_age_60plus_share"].to_list() == [0.12, None]
    assert out["state_per_capita_nsdp_2021_22"].to_list() == [100000, 100000]
    assert out["in_v1"].to_list() == [True, False]
    assert out["census_rural_share"].null_count() == 1
    assert out["state_traits_partial_data"].all()
    assert out["state_women_bank_account_nfhs5"].to_list() == [50.0, 50.0]


def test_deprivation_score_direction() -> None:
    nt = pl.DataFrame({f"nfhs_{k}_nfhs5": [10.0, 90.0] for k in traits.DEPRIVATION_SIGNS})
    score = nt.select(traits.deprivation_score(nt))["deprivation_score"].to_list()
    # z = -/+0.7071. 4 "less is worse" traits, 2 "more is worse": (4 - 2) * 0.7071 / 6.
    assert abs(score[0] - 0.2357022603955158) < 1e-9
    assert abs(score[1] + 0.2357022603955158) < 1e-9
