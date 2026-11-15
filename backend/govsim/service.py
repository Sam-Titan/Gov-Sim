"""Live anchored agent model (D-043). Loaded once, then every request is a few milliseconds.

result = actual NFHS-5 level + anchored slider change; range = sampling band + the spread of
the change over the weak / central / strong beta sets, added end to end (D-040, D-041).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import polars as pl

from govsim.agents.adoption import (
    DOCS_SCALE,
    MONTHS,
    Design,
    build_design,
    covered_share,
    probabilities,
    subset,
)
from govsim.agents.eligibility import TargetGroup, eligible_mask
from govsim.agents.sampler import N_AGENTS, Agents, sample_agents
from govsim.data.rows import (
    INCOME,
    PROCESSED,
    build_rows,
    load_districts,
    load_state_baseline,
    sampling_n,
)
from govsim.hybrid import LOW_CONFIDENCE_PP, Range, anchor_shift, combine_range, sampling_band
from govsim.schemes import (
    SCHEMES,
    SchemeInputs,
    benefit_range,
    real_envelope,
)

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
SETS = ("weak", "central", "strong")
TERMS = ("benefit", "documents", "bank_account", "burden", "speed", "target_group")
MIN_EFFECT_PP = 0.005
MIN_GROUP_AGENTS = 10  # a target group under 10 of the 500 sampled agents is too small
BASE_COLUMN = {
    "pmjay": "pmjay_households_total",
    "pmuy": "pmuy_households_total",
    "jsy": "jsy_births_5y_est_total",
    "sbm": "sbm_population_total",
}
# Districts whose state changed after Census 2011 (hand-reviewed). Shown under the current
# state; the 2011 link (pc11_s_id) is kept internally.
CURRENT_STATE_OF_2011_DISTRICT = {"Warangal": "Telangana"}  # Telangana formed 2 June 2014


class NoData(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class UnknownDistrict(Exception):
    pass


class BadInput(Exception):
    pass


@dataclass(frozen=True)
class Outcome:
    """Model output for R rows (arrays) of one scheme."""

    level: np.ndarray
    changes: np.ndarray  # (R, 3) weak / central / strong
    ranges: list[Range]
    half_width: np.ndarray
    # Custom policies only (D-044): share of the base that is in the target group, and rows
    # whose group is too small to model.
    elig_share: np.ndarray | None = None
    too_small: np.ndarray | None = None


def _covered(x: Design, beta: dict[str, float]) -> np.ndarray:
    return covered_share(x, beta)


def _group_uptake(x: Design, beta: dict[str, float]) -> np.ndarray:
    """Sign-up probability averaged over the eligible agents only, in percent."""
    w = x.type_w.sum(axis=1)
    safe = np.where(w > 0, w, 1.0)
    return 100.0 * (probabilities(x, beta) * x.type_w).sum(axis=1) / safe


def _load_betas(artifacts: Path) -> dict[str, dict[str, float]]:
    b = json.loads((artifacts / "betas.json").read_text())
    return {k: {**b["fixed_sets_assumed_by_team"][k], **b["fitted"][k]} for k in SETS}


class Service:
    def __init__(self, processed: Path = PROCESSED, artifacts: Path = ARTIFACTS) -> None:
        self.betas = _load_betas(artifacts)
        d = load_districts(processed)
        rows = build_rows(d, load_state_baseline(processed)).filter(pl.col("era") == 0)
        self.d, self.rows = d, rows
        self.agents: Agents = sample_agents(d)
        self.x = build_design(d, rows, self.agents)
        self.dist = rows["district"].to_numpy()
        self.scheme = rows["scheme"].to_numpy()
        self.n_by_scheme = sampling_n(d, processed)
        self.income_month = d[INCOME].to_numpy()[self.dist] / MONTHS
        self.ben_r = rows["benefit_rural"].to_numpy()
        self.ben_u = rows["benefit_urban"].to_numpy()
        self.kind = (
            self.agents.rural * 4 + (~self.agents.literate) * 2 + (~self.agents.banked)
        ).astype(int)
        self.row_of = {
            (int(j), s): i for i, (j, s) in enumerate(zip(self.dist, self.scheme, strict=True))
        }
        self.partial = rows["baseline_partial"].to_numpy()
        self.envelope = real_envelope()
        counts = d.select("pc11_s_id", "pc11_d_id").join(
            pl.read_parquet(processed / "eligible_counts.parquet"),
            on=["pc11_s_id", "pc11_d_id"],
            how="left",
        )
        self.base = {k: counts[c].to_numpy().astype(float) for k, c in BASE_COLUMN.items()}
        self._index_places(processed)

    # ---- places -------------------------------------------------------------------------
    def _index_places(self, processed: Path) -> None:
        traits = pl.read_parquet(processed / "district_traits.parquet")
        census = pl.read_parquet(processed / "census2011_districts.parquet")
        states_of: dict[str, set[str]] = {}
        for sid, name in zip(traits["pc11_s_id"], traits["nfhs_state"], strict=True):
            if sid is not None:
                states_of.setdefault(sid, set()).add(name)
        v1_ids = set(self.d["pc11_d_id"])
        places: list[dict] = []
        for r in traits.iter_rows(named=True):
            reason = None
            if r["match_type"] == "unmapped":
                reason = "unmapped"
            elif r["pc11_d_id"] not in v1_ids:
                reason = "no_state_income"
            places.append(
                {
                    "id": r["pc11_d_id"] or "n-" + r["nfhs_file"].removesuffix(".pdf"),
                    "pc11_s_id": r["pc11_s_id"],
                    "name": r["nfhs_district"],
                    "state": r["nfhs_state"],
                    "has_data": reason is None,
                    "reason": reason,
                }
            )
        have = {p["id"] for p in places}
        for r in census.iter_rows(named=True):
            if r["pc11_d_id"] in have:
                continue
            state = self._current_state(r, states_of)
            places.append(
                {
                    "id": r["pc11_d_id"],
                    "pc11_s_id": r["pc11_s_id"],
                    "name": r["name"],
                    "state": state,
                    "has_data": False,
                    "reason": "no_nfhs_sheet",
                }
            )
        self.places = sorted(places, key=lambda p: (p["state"], p["name"]))
        self.place_by_id = {p["id"]: p for p in places}
        self.d_index = {str(i): k for k, i in enumerate(self.d["pc11_d_id"])}

    @staticmethod
    def _current_state(r: dict, states_of: dict[str, set[str]]) -> str:
        """Current state of a Census 2011 district that has no NFHS sheet.

        Hand-reviewed override first (state changed after 2011), then the one current state
        of its 2011 state id. Chandigarh and Lakshadweep have no NFHS state rows: the UT is
        its own state. An ambiguous 2011 state id with no override is an error, not a guess.
        """
        if r["name"] in CURRENT_STATE_OF_2011_DISTRICT:
            return CURRENT_STATE_OF_2011_DISTRICT[r["name"]]
        found = states_of.get(r["pc11_s_id"], set())
        if len(found) > 1:
            raise ValueError(f"{r['name']}: 2011 state split into {sorted(found)}; add an override")
        return next(iter(found), r["name"])

    def states(self) -> list[dict]:
        out: dict[str, list[int]] = {}
        for p in self.places:
            s = out.setdefault(p["state"], [0, 0])
            s[0] += 1
            s[1] += int(p["has_data"])
        return [{"name": n, "n_districts": a, "n_with_data": b} for n, (a, b) in out.items()]

    def districts(self, state: str | None) -> list[dict]:
        return [p for p in self.places if state is None or p["state"] == state]

    # ---- model --------------------------------------------------------------------------
    def row_for(self, district_id: str, scheme: str) -> int:
        place = self.place_by_id.get(district_id)
        if place is None:
            raise UnknownDistrict(district_id)
        if scheme not in SCHEMES:
            raise BadInput(f"unknown scheme {scheme}")
        if not place["has_data"]:
            raise NoData(place["reason"])
        row = self.row_of.get((self.d_index[district_id], scheme))
        if row is None:
            # PM-JAY / PMUY baseline: own, state mean (D-038), then official state value (D-046)
            raise NoData("no_baseline")
        return row

    def real_inputs(self, row: int) -> SchemeInputs:
        s = SCHEMES[str(self.scheme[row])].inputs
        return SchemeInputs(
            cash_benefit_inr=float(self.ben_r[row]),
            document_count=int(self.rows["documents"][row]),
            requires_bank_account=s.requires_bank_account,
            application_burden=s.application_burden,
            benefit_immediacy=s.benefit_immediacy,
        )

    def _type_w(self, j: np.ndarray, tg: TargetGroup) -> np.ndarray:
        elig = eligible_mask(self.agents, tg)[j]
        kind = self.kind[j]
        return np.stack([((kind == t) & elig).mean(axis=1) for t in range(8)], axis=1)

    def _apply(
        self, rows: np.ndarray, vals: dict[str, float | bool] | None, tg: TargetGroup | None
    ) -> Design:
        """Design for `rows` with the given slider values (keys of `vals`) and target group."""
        x = subset(self.x, rows)
        if vals:
            if "cash" in vals:
                ratio = self.ben_u[rows] / self.ben_r[rows]  # JSY urban:rural, 1 for the rest
                cash = float(vals["cash"])
                inc = self.income_month[rows]
                x = replace(
                    x,
                    log_ben_rural=np.log1p(cash / inc),
                    log_ben_urban=np.log1p(cash * ratio / inc),
                )
            if "docs" in vals:
                x = replace(x, docs=np.full(len(rows), float(vals["docs"]) / DOCS_SCALE))
            if "bank" in vals:
                x = replace(x, bank=np.full(len(rows), float(vals["bank"])))
            sc = x.scalar.copy()
            if "burden" in vals:
                sc[:, 0] = (float(vals["burden"]) - 3.0) / 2.0
            if "speed" in vals:
                sc[:, 1] = (float(vals["speed"]) - 3.0) / 2.0
            x = replace(x, scalar=sc)
        if tg is not None:
            x = replace(x, type_w=self._type_w(self.dist[rows], tg))
        return x

    @staticmethod
    def _vals(inputs: SchemeInputs) -> dict[str, float | bool]:
        return {
            "cash": inputs.cash_benefit_inr,
            "docs": inputs.document_count,
            "bank": inputs.requires_bank_account,
            "burden": inputs.application_burden,
            "speed": inputs.benefit_immediacy,
        }

    def run(self, rows: np.ndarray, inputs: SchemeInputs | None, tg: TargetGroup | None) -> Outcome:
        """Anchored change and range for `rows` (all the same scheme)."""
        if tg is not None:
            return self._run_group(rows, inputs, tg)
        real = subset(self.x, rows)
        new = self._apply(rows, self._vals(inputs) if inputs else None, tg)
        level = real.target
        scheme = str(self.scheme[rows[0]])
        n = np.array([self.n_by_scheme[scheme][j] for j in self.dist[rows]])
        err_lo, err_hi = sampling_band(level, n)
        changes = []
        for name in SETS:
            shift = anchor_shift(real, self.betas[name], level)
            changes.append(
                covered_share(replace(new, shift=shift), self.betas[name])
                - covered_share(replace(real, shift=shift), self.betas[name])
            )
        ch = np.stack(changes, axis=1)
        ranges = [
            combine_range(
                float(level[i]),
                (float(ch[i, 0]), float(ch[i, 1]), float(ch[i, 2])),
                float(err_lo[i]),
                float(err_hi[i]),
                new_policy=tg is not None,
            )
            for i in range(len(rows))
        ]
        return Outcome(level, ch, ranges, err_hi)

    def _run_group(self, rows: np.ndarray, inputs: SchemeInputs | None, tg: TargetGroup) -> Outcome:
        """Custom policy (D-044): uptake within the target group, in percent of the group.

        Anchored at the start scheme's NFHS level (everyone eligible, real settings). The range
        is the min and max over the three beta sets and the NFHS sampling band of the level.
        `changes` = new settings minus the real settings, for the same group.
        """
        real = subset(self.x, rows)
        new = self._apply(rows, self._vals(inputs) if inputs else None, tg)
        real_g = replace(real, type_w=new.type_w)
        elig = new.type_w.sum(axis=1)
        level = real.target
        scheme = str(self.scheme[rows[0]])
        n = np.array([self.n_by_scheme[scheme][j] for j in self.dist[rows]])
        err_lo, err_hi = sampling_band(level, n)
        levels = [np.clip(level + err_lo, 0, 100), level, np.clip(level + err_hi, 0, 100)]
        ups, changes = [], []
        for name in SETS:
            per_level = []
            for k, lv in enumerate(levels):
                shift = anchor_shift(real, self.betas[name], lv)
                u_new = _group_uptake(replace(new, shift=shift), self.betas[name])
                per_level.append(u_new)
                if k == 1:
                    u_real = _group_uptake(replace(real_g, shift=shift), self.betas[name])
                    changes.append(u_new - u_real)
            ups.append(np.stack(per_level, axis=1))  # (R, 3 levels)
        allu = np.stack(ups, axis=1).reshape(len(rows), -1)  # (R, 9)
        point = ups[1][:, 1]
        ch = np.stack(changes, axis=1)
        ranges = [
            Range(
                float(allu[i].min()),
                float(point[i]),
                float(allu[i].max()),
                bool(allu[i].max() - allu[i].min() > LOW_CONFIDENCE_PP),
                True,
            )
            for i in range(len(rows))
        ]
        return Outcome(level, ch, ranges, err_hi, elig, elig * N_AGENTS < MIN_GROUP_AGENTS)

    def reasons(
        self, row: int, inputs: SchemeInputs | None, tg: TargetGroup | None
    ) -> list[tuple[str, float]]:
        """Top 3 terms by size of change (central set): each term switched on alone.

        Custom policy: effects are in uptake within the group, against the real settings for the
        same group; `target_group` = how the group differs from everyone at the real settings.
        """
        rows = np.array([row])
        real = subset(self.x, rows)
        beta = self.betas["central"]
        shift = anchor_shift(real, beta, real.target)
        group_basis = tg is not None
        measure = _group_uptake if group_basis else _covered
        ref = self._apply(rows, None, tg) if group_basis else real
        base = measure(replace(ref, shift=shift), beta)[0]
        full = self._vals(inputs) if inputs else {}
        keys = {
            "benefit": "cash",
            "documents": "docs",
            "bank_account": "bank",
            "burden": "burden",
            "speed": "speed",
        }
        effects: list[tuple[str, float]] = []
        for term, key in keys.items():
            if key in full:
                x = self._apply(rows, {key: full[key]}, tg)
                effects.append((term, measure(replace(x, shift=shift), beta)[0] - base))
        if group_basis:
            everyone = _group_uptake(replace(real, shift=shift), beta)[0]
            effects.append(("target_group", base - everyone))
        effects = [e for e in effects if abs(e[1]) >= MIN_EFFECT_PP]
        return sorted(effects, key=lambda e: -abs(e[1]))[:3]

    # ---- warnings -----------------------------------------------------------------------
    def out_of_range(self, inputs: SchemeInputs | None) -> bool:
        if inputs is None:
            return False
        v = inputs.model_dump()
        return any(not (lo <= v[k] <= hi) for k, (lo, hi) in self.envelope.items())

    def check_inputs(self, scheme: str, inputs: SchemeInputs | None) -> None:
        if inputs is None:
            return
        lo, hi = benefit_range(scheme)
        if not lo <= inputs.cash_benefit_inr <= hi:
            raise BadInput(f"cash_benefit_inr for {scheme} must be between {lo:g} and {hi:g}")
