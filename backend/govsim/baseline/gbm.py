"""LightGBM baseline (never deleted). Features: district traits + scheme values, no scheme ID."""

import lightgbm as lgb
import numpy as np
import polars as pl

from govsim.data.rows import GBM_TRAITS, INCOME

SCHEME_FEATURES = ["log_benefit_ratio", "documents", "bank_required", "burden", "immediacy"]
EXTRA = ["baseline", "era"]


def feature_table(d: pl.DataFrame, rows: pl.DataFrame) -> pl.DataFrame:
    """One feature row per (district, scheme, era) row."""
    j = rows["district"].to_numpy()
    income = d[INCOME].to_numpy()[j]
    base = d.select(GBM_TRAITS)[j]
    ratio = np.log1p(rows["benefit_mean"].to_numpy() / income)
    sch = rows.select("documents", "bank_required", "burden", "immediacy", "baseline", "era")
    return pl.concat([base, sch], how="horizontal").with_columns(
        pl.Series("log_benefit_ratio", ratio)
    )


def make_model() -> lgb.LGBMRegressor:
    return lgb.LGBMRegressor(
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=15,
        min_child_samples=20,
        subsample=0.8,
        subsample_freq=1,
        colsample_bytree=0.8,
        random_state=42,
        verbose=-1,
    )


def fit_predict(
    feat: pl.DataFrame, y: np.ndarray, train: np.ndarray, test: np.ndarray
) -> np.ndarray:
    """Train on rows where `train` is True, predict rows where `test` is True (pp)."""
    x = feat.to_numpy()
    model = make_model().fit(x[train], y[train])
    return model.predict(x[test])
