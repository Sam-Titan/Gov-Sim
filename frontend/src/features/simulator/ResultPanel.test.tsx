import { render, screen } from "@testing-library/react";
import type { SimulateResponse } from "@/api/types.gen";
import "@/i18n/setup";
import i18n from "@/i18n/setup";
import mock from "../../../../shared/mocks/simulate.sample.json";
import { ResultPanel } from "./ResultPanel";

const data = mock as unknown as SimulateResponse;
const base = { updating: false, error: null, ready: true };

describe("ResultPanel", () => {
  beforeEach(() => i18n.changeLanguage("en"));

  it("shows a range, the metric label, reasons and warnings", () => {
    render(<ResultPanel {...base} data={data} />);
    expect(screen.getByTestId("range").textContent).toBe("38–56%");
    expect(screen.getByText("Share of all people")).toBeTruthy();
    expect(screen.getByText("Benefit value")).toBeTruthy();
    expect(screen.getAllByRole("listitem").length).toBeGreaterThanOrEqual(5);
    expect(screen.getByText(/Based on a household survey/)).toBeTruthy();
    expect(screen.getByText(/Beyond what real schemes do/)).toBeTruthy();
  });

  it("rounds the range outward so it is never narrower than the data", () => {
    const wide = { ...data, result: { ...data.result, low: 37.2, high: 55.1 } };
    render(<ResultPanel {...base} data={wide} />);
    expect(screen.getByTestId("range").textContent).toBe("37–56%");
  });

  it("keeps the old result visible while updating", () => {
    render(<ResultPanel {...base} data={data} updating />);
    expect(screen.getByTestId("range")).toBeTruthy();
    expect(screen.getAllByText("Updating…").length).toBeGreaterThan(0);
  });

  it("explains a district with no data", () => {
    render(<ResultPanel ready updating={false} error="no_data" noDataReason="unmapped" />);
    expect(screen.getByRole("alert").textContent).toContain("created after the 2011 Census");
  });

  it("asks the user to choose when nothing is selected", () => {
    render(<ResultPanel ready={false} updating={false} error={null} />);
    expect(screen.getByText(/Choose a state/)).toBeTruthy();
  });

  it("shows an error, never a made-up number", () => {
    render(<ResultPanel ready updating={false} error="other" />);
    expect(screen.queryByTestId("range")).toBeNull();
    expect(screen.getByRole("alert").textContent).toBe("Could not get a result. Try again.");
  });

  it("renders in Hindi", async () => {
    await i18n.changeLanguage("hi");
    render(<ResultPanel {...base} data={data} />);
    expect(screen.getByText("सभी लोगों में हिस्सा")).toBeTruthy();
  });
});
