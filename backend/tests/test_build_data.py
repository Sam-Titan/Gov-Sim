import polars as pl

from scripts import build_data


def test_state_coverage_counts() -> None:
    jt = pl.DataFrame(
        {
            "state_code": ["TG", "TG", "BR"],
            "nfhs_state": ["Telangana", "Telangana", "Bihar"],
            "match_type": ["exact", "unmapped", "exact"],
            "no_nfhs4": [True, True, False],
        }
    )
    out = build_data.state_coverage(jt).sort("state_code")
    tg = out.filter(pl.col("state_code") == "TG").row(0, named=True)
    assert (tg["nfhs_districts"], tg["mapped"], tg["unmapped"], tg["no_nfhs4"]) == (2, 1, 1, 2)


def test_md_table_shape() -> None:
    text = build_data.md_table(pl.DataFrame({"a": [1], "b": ["x"]}))
    assert text.splitlines()[0] == "| a | b |"
    assert text.splitlines()[-1] == "| 1 | x |"
