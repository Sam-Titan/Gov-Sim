from scripts import parse_nfhs as pn

SHEET = """
District Fact Sheet
                       Ajmer
                       Rajasthan
9. Population living in households that use an improved sanitation facility 2 (%)   77.5   69.9
10. Households using clean fuel for cooking3 (%)   52.9   50.6
12. Households with a member covered under a health insurance/financing scheme (%)  88.7  na
42. Institutional births (%)   (95.1)   *
43. Institutional births in public facility (%)   82.1   69.5
"""


def test_parse_value() -> None:
    assert pn.parse_value("77.5") == (77.5, False)
    assert pn.parse_value("(45.2)") == (45.2, True)
    assert pn.parse_value("*") == (None, False)
    assert pn.parse_value("na") == (None, False)


def test_parse_sheet() -> None:
    row = pn.parse_sheet(SHEET)
    assert (row["district"], row["state"]) == ("Ajmer", "Rajasthan")
    assert row["sanitation_nfhs5"] == 77.5
    assert row["sanitation_nfhs4"] == 69.9
    assert row["health_insurance_nfhs4"] is None
    assert row["institutional_births_nfhs5"] == 95.1
    assert row["institutional_births_few_cases"] is True
    assert "institutional_births_nfhs4" in row


def test_parse_sheet_old_insurance_wording_and_shifted_numbers() -> None:
    text = (
        "District Fact Sheet\n   Wardha\n   Maharashtra\n"
        "11. Households using clean fuel for cooking3 (%)  83.9  54.9\n"
        "13. Households with any usual member covered by a health scheme or "
        "health insurance (%)  27.1  14.8\n"
    )
    row = pn.parse_sheet(text)
    assert row["clean_fuel_nfhs5"] == 83.9
    assert row["health_insurance_nfhs4"] == 14.8


def test_parse_header_wrapped_state_name() -> None:
    text = (
        "District Fact Sheet\n  Daman\n  Dadra & Nagar Haveli and\n  Daman & Diu\n"
        "International Institute for Population Sciences\n"
    )
    assert pn.parse_header(text) == ("Daman", "Dadra & Nagar Haveli and Daman & Diu")


def test_parse_sheet_traits_do_not_include_targets() -> None:
    text = SHEET + "3. Sex ratio of the total population (females per 1,000 males)  1020  990\n"
    row = pn.parse_sheet(text, pn.TRAITS)
    assert row["sex_ratio_nfhs5"] == 1020.0
    assert not any(k.startswith(("sanitation", "clean_fuel")) for k in row)


def test_traits_never_match_target_labels() -> None:
    targets = ("improved sanitation", "clean fuel", "health insurance", "institutional births")
    for keys in pn.TRAITS.values():
        assert not any(t in k for k in keys for t in targets)
