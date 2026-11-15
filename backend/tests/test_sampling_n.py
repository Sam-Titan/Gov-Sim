import numpy as np
import polars as pl

from govsim.data.rows import births_per_woman, sampling_n


def _processed(tmp_path):
    ids = {"pc11_s_id": ["01", "01"], "pc11_d_id": ["001", "002"]}
    pl.DataFrame({**ids, "jsy_births_5y_est_total": [4000, 3000]}).write_parquet(
        tmp_path / "eligible_counts.parquet"
    )
    pl.DataFrame({**ids, "women_15_49": [10000, 5000]}).write_parquet(
        tmp_path / "census_age.parquet"
    )
    pl.DataFrame(
        {"file": ["a.pdf", "b.pdf"], "n_households": [900, 800], "n_women": [1000, 500]}
    ).write_parquet(tmp_path / "nfhs_sample_sizes.parquet")
    return tmp_path


def test_births_per_woman(tmp_path) -> None:
    got = births_per_woman(_processed(tmp_path))
    assert got["births_per_woman"].to_list() == [0.4, 0.6]


def test_jsy_n_is_estimated_births_others_households(tmp_path) -> None:
    p = _processed(tmp_path)
    d = pl.DataFrame(
        {"nfhs_file": ["a.pdf", "b.pdf"], "pc11_s_id": ["01", "01"], "pc11_d_id": ["001", "002"]}
    )
    n = sampling_n(d, p)
    assert np.allclose(n["jsy"], [400.0, 300.0])  # women x births per woman
    for s in ("pmjay", "pmuy", "sbm"):
        assert np.allclose(n[s], [900.0, 800.0])
