from scripts import parse_state as ps

TEXT = """
                                  Kerala - Key Indicators
122. Women having a bank or savings account that they themselves use (%)  78.0  89.3  83.6  46.5
123. Women having a mobile phone that they themselves use (%)    75.4   45.5   60.5   46.0
19. Women who have ever used the internet (%)    44.1   27.9   34.8   na
                                  Goa - Key Indicators
122. Women having a bank or savings account that they themselves use (%)    1.0   2.0   88.3   82.8
"""


def test_parse_text_reads_total_column() -> None:
    rows = {r["state"]: r for r in ps.parse_text(TEXT)}
    assert rows["Kerala"]["women_bank_account_nfhs5"] == 83.6
    assert rows["Kerala"]["women_bank_account_nfhs4"] == 46.5
    assert rows["Kerala"]["women_internet_nfhs5"] == 34.8
    assert rows["Kerala"]["women_internet_nfhs4"] is None
    assert rows["Goa"]["women_bank_account_nfhs5"] == 88.3


INS = "12. Households with any usual member covered under a health insurance/financing scheme (%)"
BASELINE_TEXT = (
    "  NCT Delhi - Key Indicators\n"
    "10. Households using clean fuel for cooking3 (%)     99.0   97.6   98.9   97.9\n"
    f"{INS}   25.0   27.1   25.0   15.7\n"
    "  Telangana - Key Indicators\n"
    "10. Households using clean fuel for cooking3 (%)     98.2   88.3   91.8   67.3\n"
    f"{INS}   52.9   65.0   60.8   66.4\n"
)


def test_parse_baseline_reads_nfhs4_total_column() -> None:
    rows = {r["state"]: r for r in ps.parse_baseline(BASELINE_TEXT)}
    assert rows["NCT Delhi"] == {
        "state": "NCT Delhi",
        "clean_fuel_nfhs4": 97.9,
        "health_insurance_nfhs4": 15.7,
    }
    assert rows["Telangana"]["health_insurance_nfhs4"] == 66.4
