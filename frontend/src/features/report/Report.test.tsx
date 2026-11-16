import { render, screen, within } from "@testing-library/react";
import type { DistrictOut, ReportResponse } from "@/api/types.gen";
import i18n from "@/i18n/setup";
import report from "../../../../backend/artifacts/report.json";
import { ReportBody } from "./Report";
import { agentWins, parseReport } from "./reportData";

// The counts are added by the API at request time (not in report.json); test numbers only.
const raw = {
  ...report,
  pmjay_nfhs5_not_above_nfhs4: { n: 16, of: 63, n_own: 13, of_own: 57 },
} as unknown as ReportResponse;
const parsed = parseReport(raw);

const district = (id: string, has_data: boolean, reason: string | null = null): DistrictOut => ({
  id,
  pc11_s_id: "1",
  name: id,
  state: "S",
  has_data,
  reason,
});
const districts = [
  district("1", true),
  district("2", false, "unmapped"),
  district("3", false, "unmapped"),
  district("4", false, "no_nfhs_sheet"),
];

describe("report page", () => {
  beforeEach(() => i18n.changeLanguage("en"));

  it("reads the real report.json shape", () => {
    expect(parsed).not.toBeNull();
  });

  it("rejects a report with a missing block instead of showing wrong numbers", () => {
    expect(parseReport({ ...raw, losto_headline: {} })).toBeNull();
  });

  it("says the agent model does not beat the baseline, with numbers from the report", () => {
    if (!parsed) throw new Error("report did not parse");
    render(<ReportBody r={parsed} districts={districts} />);
    expect(screen.getByRole("status").textContent).toContain("does not beat");
    const m = parsed.losto.weighted_mean;
    const table = screen.getAllByRole("table")[0];
    if (!table) throw new Error("no table");
    expect(within(table).getByText(m.agent_mae.toFixed(1))).toBeTruthy();
    expect(within(table).getByText(m.gbm_mae.toFixed(1))).toBeTruthy();
    const wins = agentWins(parsed.losto);
    expect(
      screen.getAllByText(new RegExp(`${wins} of ${parsed.losto.folds.length} states`)).length,
    ).toBeGreaterThan(0);
  });

  it("takes the district counts from the API list, not from text", () => {
    if (!parsed) throw new Error("report did not parse");
    render(<ReportBody r={parsed} districts={districts} />);
    expect(
      screen.getByText(
        "3 of 4 listed districts have no result; 2 of them are new districts with no 2011 parent.",
      ),
    ).toBeTruthy();
  });

  it("describes the JSY band as estimated births, not understated", () => {
    if (!parsed) throw new Error("report did not parse");
    render(<ReportBody r={parsed} districts={districts} />);
    expect(screen.getByText(/uses estimated births/)).toBeTruthy();
    expect(screen.queryByText(/understated/i)).toBeNull();
  });

  it("explains the slider method in one sentence and lists the NFHS-4 to NFHS-5 data issue", () => {
    if (!parsed) throw new Error("report did not parse");
    render(<ReportBody r={parsed} districts={districts} />);
    expect(screen.getByText(/moves the district's real NFHS-5 level up or down/)).toBeTruthy();
    expect(
      screen.getByText(/In 16 of 63 districts, PM-JAY coverage in NFHS-5 is at or below NFHS-4/),
    ).toBeTruthy();
    expect(screen.getByText(/whether coverage really fell or the two surveys/)).toBeTruthy();
  });

  it("labels the assumed values", () => {
    if (!parsed) throw new Error("report did not parse");
    render(<ReportBody r={parsed} districts={districts} />);
    expect(screen.getAllByText(/assumed by team/).length).toBeGreaterThan(0);
  });
});
