"""Phase 2: fit beta0 / beta7, evaluate (LOSTO headline, LOSO), write the error bands.

D-039 to D-041: beta2, 3, 5, 6, 8 are fixed assumed values (weak / central / strong);
beta0, beta7 and the nuisance era_shift are fitted; beta1 is fixed. Writes
backend/artifacts/report.json and betas.json. Surrogate training is Phase 3.
"""

import json
from pathlib import Path

import numpy as np
import polars as pl

from govsim.agents.adoption import BETA1, FITTED, TRUST, build_design
from govsim.agents.sampler import N_AGENTS, SEED, sample_agents
from govsim.baseline.gbm import feature_table, fit_predict
from govsim.calibrate.fit import fit, mae
from govsim.calibrate.recovery import recover
from govsim.data.rows import PROCESSED, build_rows, load_districts
from govsim.evaluate.cv import cross_validate, gbm_losto_errors, summarize
from govsim.evaluate.sanity import sanity_table
from govsim.hybrid import DEFF, LOW_CONFIDENCE_PP, sampling_band
from govsim.schemes import CODES, PMJAY_BENEFIT_RANGE

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"

# Assumed by team (D-039, D-040): no effect sizes found in the literature.
FIXED_SETS = {
    "weak": {"b2": 0.2, "b3": -0.3, "b5": -0.2, "b6": 0.1, "b8": -0.3},
    "central": {"b2": 0.5, "b3": -0.8, "b5": -0.6, "b6": 0.4, "b8": -0.9},
    "strong": {"b2": 1.0, "b3": -1.5, "b5": -1.2, "b6": 0.8, "b8": -1.8},
}
FIT_TERMS = ("b0", "b7", "era_shift")


def _folds(folds) -> dict:
    return {"folds": [vars(f) for f in folds], "weighted_mean": summarize(folds)}


def _pct(a: np.ndarray, q: float) -> float:
    return round(float(np.percentile(a, q)), 2)


def main() -> None:
    d = load_districts()
    rows = build_rows(d)
    x = build_design(d, rows, sample_agents(d))
    feat = feature_table(d, rows)
    y, era = x.target, x.era
    schemes = rows["scheme"].to_numpy()
    states = d["nfhs_state"].to_numpy()[rows["district"].to_numpy()]
    report: dict = {
        "n_districts": d.height,
        "n_rows": rows.height,
        "n_agents": N_AGENTS,
        "seed": SEED,
        "baseline_partial_rows": int(rows["baseline_partial"].sum()),
        "decisions": "D-037 to D-041",
        "agent_model_beats_gbm": False,
    }

    # 1. Fit beta0, beta7, era_shift for each fixed set (the others stay fixed).
    beta_sets, fitted = {}, {}
    for name, fixed in FIXED_SETS.items():
        b = fit(x, fixed=fixed)
        beta_sets[name] = b
        fitted[name] = {k: round(float(b[k]), 4) for k in FIT_TERMS}
    central = beta_sets["central"]
    report["betas"] = {
        "b1_fixed_assumed": BETA1,
        "trust_latent_assumed": TRUST,
        "fixed_sets_assumed_by_team": FIXED_SETS,
        "fitted": fitted,
    }
    report["in_sample_mae_unanchored"] = {k: round(mae(x, b), 3) for k, b in beta_sets.items()}
    gbm_in = fit_predict(feat, y, np.ones(len(y), bool), np.ones(len(y), bool))
    report["gbm_in_sample_mae"] = round(float(np.abs(gbm_in - y).mean()), 3)

    # 2. Evaluation: LOSTO headline, LOSO kept with a note (4 schemes are too few).
    fixed_c = FIXED_SETS["central"]
    report["losto_headline"] = _folds(cross_validate(x, feat, states, central, fixed_c))
    report["loso"] = _folds(cross_validate(x, feat, schemes, central, fixed_c))
    report["loso_note"] = (
        "4 schemes are too few: a held-out scheme has slider values never seen in training."
    )

    # 3. GBM error band per scheme (LOSTO), kept in the report.
    # The UI band is the NFHS sampling band (step 4).
    err = gbm_losto_errors(feat, y, states, era)
    report["gbm_losto_error_band_pp"] = {
        s: {
            "p10": _pct(err[(schemes == s) & (era == 0)], 10),
            "p90": _pct(err[(schemes == s) & (era == 0)], 90),
        }
        for s in CODES
    }

    # 4. NFHS sampling band at each district's actual value (D-041).
    n_tab = pl.read_parquet(PROCESSED / "nfhs_sample_sizes.parquet")
    n_map = dict(
        zip(n_tab["file"], zip(n_tab["n_households"], n_tab["n_women"], strict=True), strict=True)
    )
    files = d["nfhs_file"].to_numpy()[rows["district"].to_numpy()]
    n_hh = np.array([n_map[f][0] for f in files], dtype=float)
    n_women = np.array([n_map[f][1] for f in files], dtype=float)
    n = np.where(schemes == "jsy", n_women, n_hh)
    lo, hi = sampling_band(y, n)
    report["sampling_band"] = {
        "deff_assumed_by_team": DEFF,
        "method": "SE = sqrt(deff * p * (1-p) / n); band = +-1.2816 * SE (10th-90th percentile)",
        "n_used": (
            "households (PM-JAY, PMUY, SBM); women interviewed for JSY "
            "(upper bound on births, so the JSY band is understated)"
        ),
        "by_scheme": {
            s: {
                "median_half_width_pp": _pct(hi[(schemes == s) & (era == 0)], 50),
                "max_half_width_pp": _pct(hi[(schemes == s) & (era == 0)], 100),
                "share_over_30pp_wide_at_real_settings": round(
                    float(((hi - lo)[(schemes == s) & (era == 0)] > LOW_CONFIDENCE_PP).mean()), 3
                ),
            }
            for s in CODES
        },
    }

    # 5. Sanity table (anchored at the actual NFHS value) and the PM-JAY benefit cap.
    report["sanity_table_pp"] = sanity_table(x, schemes, beta_sets)
    report["pmjay_benefit_range_inr"] = PMJAY_BENEFIT_RANGE

    # 6. Recovery of the fitted terms (beta0, beta7, era_shift) with the rest fixed.
    report["recovery"] = {
        f"noise_{k}pp": recover(x, central, noise_sd=k, fixed=fixed_c) for k in (1.0, 3.0)
    }
    report["fitted_terms"] = [k for k in FITTED if k in FIT_TERMS]

    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "report.json").write_text(json.dumps(report, indent=2))
    (ARTIFACTS / "betas.json").write_text(json.dumps(report["betas"], indent=2))
    for k in ("losto_headline", "loso"):
        print(k, report[k]["weighted_mean"])
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "betas",
                    "in_sample_mae_unanchored",
                    "gbm_losto_error_band_pp",
                    "sampling_band",
                )
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
