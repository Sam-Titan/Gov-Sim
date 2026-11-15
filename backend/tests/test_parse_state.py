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
