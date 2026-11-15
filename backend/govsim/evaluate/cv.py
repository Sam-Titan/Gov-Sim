"""LOSO (leave-one-scheme-out) and LOSTO (leave-one-state-out): agent model vs GBM vs naive."""

from dataclasses import dataclass

import numpy as np

from govsim.agents.adoption import Design, covered_share, subset
from govsim.baseline.gbm import fit_predict
from govsim.calibrate.fit import fit


@dataclass
class Fold:
    name: str
    n: int
    agent_mae: float
    gbm_mae: float
    naive_mae: float


def _score(name, x, feat, y, train, test, start, fixed):
    beta = fit(subset(x, train), start=start, fixed=fixed, maxiter=800)
    agent = np.abs(covered_share(subset(x, test), beta) - y[test])
    gbm = np.abs(fit_predict(feat, y, train, test) - y[test])
    naive = np.abs(y[train].mean() - y[test])
    return Fold(name, int(test.sum()), float(agent.mean()), float(gbm.mean()), float(naive.mean()))


def cross_validate(
    x: Design, feat, labels: np.ndarray, start: dict, fixed: dict | None = None
) -> list[Fold]:
    """Hold out each value of `labels` in turn. Held-out NFHS-5 rows only are scored."""
    era5 = x.era == 0
    out = []
    for lab in sorted(set(labels)):
        test = (labels == lab) & era5
        train = labels != lab
        if test.sum():
            out.append(_score(lab, x, feat, x.target, train, test, start, fixed))
    return out


def summarize(folds: list[Fold]) -> dict[str, float]:
    w = np.array([f.n for f in folds], dtype=float)
    avg = lambda k: float(np.average([getattr(f, k) for f in folds], weights=w))  # noqa: E731
    return {"agent_mae": avg("agent_mae"), "gbm_mae": avg("gbm_mae"), "naive_mae": avg("naive_mae")}


def gbm_losto_errors(feat, y: np.ndarray, states: np.ndarray, era: np.ndarray) -> np.ndarray:
    """Signed GBM errors (actual - predicted, pp), leave-one-state-out. NaN for era-1 rows."""
    err = np.full(len(y), np.nan)
    for st in sorted(set(states)):
        test = (states == st) & (era == 0)
        if test.any():
            err[test] = y[test] - fit_predict(feat, y, states != st, test)
    return err
