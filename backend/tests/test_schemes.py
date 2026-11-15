from govsim.schemes import CODES, SCHEMES, jsy_benefit, jsy_documents


def test_four_schemes_with_sourced_values() -> None:
    assert CODES == ("pmjay", "pmuy", "jsy", "sbm")
    assert SCHEMES["pmjay"].inputs.cash_benefit_inr == 500_000
    assert SCHEMES["pmjay"].non_cash
    assert SCHEMES["pmuy"].inputs.document_count == 6
    assert SCHEMES["sbm"].assumed == ["document_count", "requires_bank_account"]


def test_jsy_state_rule() -> None:
    assert jsy_benefit("Bihar", True) == 1400
    assert jsy_benefit("Bihar", False) == 1000
    assert jsy_benefit("Kerala", True) == 700
    assert jsy_benefit("Kerala", False) == 600
    assert jsy_documents("Bihar") == 1
    assert jsy_documents("Kerala") == 2
