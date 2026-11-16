"""Rewrite only `sanity_table_pp` in artifacts/report.json (D-052), without refitting anything.

The fitted betas stay as they are in betas.json; the slider-change method changed, not the fit.
"""

import json

from govsim.agents.adoption import build_design
from govsim.agents.sampler import sample_agents
from govsim.data.rows import build_rows, load_districts
from govsim.evaluate.sanity import sanity_table
from scripts.train import ARTIFACTS


def main() -> None:
    d = load_districts()
    rows = build_rows(d)
    x = build_design(d, rows, sample_agents(d))
    b = json.loads((ARTIFACTS / "betas.json").read_text())
    sets = {k: {**b["fixed_sets_assumed_by_team"][k], **b["fitted"][k]} for k in b["fitted"]}
    path = ARTIFACTS / "report.json"
    report = json.loads(path.read_text())
    report["sanity_table_pp"] = sanity_table(x, rows["scheme"].to_numpy(), sets)
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report["sanity_table_pp"], indent=1))


if __name__ == "__main__":
    main()
