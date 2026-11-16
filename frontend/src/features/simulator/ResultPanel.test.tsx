import { render, screen } from "@testing-library/react";
import type { SimulateResponse } from "@/api/types.gen";
import "@/i18n/setup";
import i18n from "@/i18n/setup";
import custom from "../../../../shared/mocks/simulate.custom.sample.json";
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

  describe("custom policy (group basis)", () => {
    const group = custom as unknown as SimulateResponse;

    it("says the number is within the target group and shows the reach", () => {
      render(<ResultPanel {...base} data={group} />);
      expect(screen.getByText(/Uptake within the target group/)).toBeTruthy();
      expect(screen.queryByText("Share of all people")).toBeNull();
      expect(screen.getByText("New policy")).toBeTruthy();
      expect(screen.getByText("Mock custom policy", { exact: false })).toBeTruthy();
      const reach = screen.getByTestId("reach").textContent ?? "";
      expect(reach).toContain("13,500 people");
      expect(reach).toContain("8,100");
      expect(reach).toContain("19,800");
      expect(reach).toContain("Estimated, Census 2011 base");
    });

    it("shows no reach block for a real scheme", () => {
      render(<ResultPanel {...base} data={data} />);
      expect(screen.queryByTestId("reach")).toBeNull();
    });

    it("explains a group that is too small", () => {
      render(<ResultPanel ready updating={false} error="no_data" noDataReason="group_too_small" />);
      expect(screen.getByRole("alert").textContent).toContain("too small");
    });
  });
});
