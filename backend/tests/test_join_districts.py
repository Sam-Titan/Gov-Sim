import polars as pl

from scripts import join_districts as jd

CENSUS = {("28", "hyderabad"): "541", ("24", "ahmadabad"): "474", ("18", "karbianglong"): "300"}


def test_exact_match() -> None:
    assert jd.match_district("TG", "Hyderabad", CENSUS) == ("28", "541", "exact")


def test_reviewed_spelling_match() -> None:
    assert jd.match_district("GJ", "Ahmedabad", CENSUS) == ("24", "474", "spelling")


def test_new_district_is_unmapped_not_guessed() -> None:
    # West Karbi Anglong looks like Karbi Anglong but is a different district.
    assert jd.match_district("AS", "West Karbi Anglong", CENSUS) == (None, None, "unmapped")


def test_same_name_in_other_state_does_not_match() -> None:
    census = {("10", "aurangabad"): "1"}
    assert jd.match_district("MH", "Aurangabad", census)[2] == "unmapped"


def test_build_marks_match_types() -> None:
    nfhs = pl.DataFrame(
        {
            "state_code": ["TG", "AS"],
            "state": ["Telangana", "Assam"],
            "district": ["Hyderabad", "Hojai"],
            "file": ["TG_Hyderabad.pdf", "AS_Hojai.pdf"],
        }
    )
    census_df = pl.DataFrame(
        {"pc11_s_id": ["28", "24"], "pc11_d_id": ["541", "474"], "name": ["Hyderabad", "Ahmadabad"]}
    )
    out = jd.build(nfhs, census_df, check_spelling=False)
    assert out["match_type"].to_list() == ["exact", "unmapped"]


def test_build_rejects_spelling_target_not_in_census() -> None:
    import pytest

    nfhs = pl.DataFrame({"state_code": [], "state": [], "district": [], "file": []})
    census_df = pl.DataFrame({"pc11_s_id": ["28"], "pc11_d_id": ["541"], "name": ["Hyderabad"]})
    with pytest.raises(ValueError):
        jd.build(nfhs, census_df)
