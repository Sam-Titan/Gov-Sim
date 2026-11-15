import polars as pl

from scripts import census


def _row(tru: str, hh: int, pop: int, age06: int) -> dict[str, object]:
    base: dict[str, object] = {
        "State": "01",
        "District": "001",
        "Name": "Kupwara ",
        "Level": "DISTRICT",
        "TRU": tru,
    }
    for src in census.KEEP:
        base[src] = 1
    base.update({"No_HH": hh, "TOT_P": pop, "P_06": age06})
    return base


def test_to_wide_one_row_per_district() -> None:
    rows = [_row("Total", 10, 50, 14), _row("Rural", 8, 40, 12), _row("Urban", 2, 10, 2)]
    df = census.to_wide(rows)
    assert df.height == 1
    rec = df.row(0, named=True)
    assert rec["name"] == "Kupwara"
    assert rec["households_total"] == 10
    assert rec["population_rural"] == 40
    assert rec["age_0_6_urban"] == 2


def test_eligible_counts_bases() -> None:
    rows = [_row("Total", 10, 50, 14), _row("Rural", 8, 40, 12), _row("Urban", 2, 10, 2)]
    out = census.eligible_counts(census.to_wide(rows)).row(0, named=True)
    assert out["pmjay_households_total"] == 10
    assert out["pmuy_households_rural"] == 8
    assert out["sbm_population_total"] == 50
    assert out["jsy_births_5y_est_total"] == 10  # 14 * 5/7
    assert isinstance(census.eligible_counts(pl.DataFrame(census.to_wide(rows))), pl.DataFrame)
