import { act, fireEvent, render, screen } from "@testing-library/react";
import type { SchemeOut } from "@/api/types.gen";
import i18n from "@/i18n/setup";
import { Sliders } from "./Sliders";

const scheme: SchemeOut = {
  code: "sbm",
  name: "SBM",
  metric_base: "people",
  defaults: {
    cash_benefit_inr: 12000,
    document_count: 1,
    requires_bank_account: true,
    application_burden: 3,
    benefit_immediacy: 2,
  },
  defaults_vary_by_district: false,
  non_cash: false,
  assumed: ["requires_bank_account"],
  ranges: {
    cash_benefit_inr: { min: 0, max: 500000 },
    document_count: { min: 0, max: 8 },
    application_burden: { min: 1, max: 5 },
    benefit_immediacy: { min: 1, max: 5 },
  },
  real_envelope: {
    cash_benefit_inr: { min: 600, max: 500000 },
    document_count: { min: 1, max: 6 },
    application_burden: { min: 2, max: 3 },
    benefit_immediacy: { min: 2, max: 4 },
  },
};

describe("Sliders", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    i18n.changeLanguage("en");
  });
  afterEach(() => vi.useRealTimers());

  it("shows one control per setting with the real value", () => {
    render(<Sliders scheme={scheme} overrides={{}} onChange={() => {}} />);
    expect(screen.getAllByRole("slider")).toHaveLength(4);
    expect(screen.getByRole("switch")).toBeTruthy();
    expect(screen.getByText("₹12,000")).toBeTruthy();
    expect(screen.getAllByText(/Real value/).length).toBeGreaterThan(0);
  });

  it("flags a value outside what real schemes do", () => {
    render(<Sliders scheme={scheme} overrides={{ application_burden: 5 }} onChange={() => {}} />);
    expect(screen.getByText("Outside what real schemes do")).toBeTruthy();
  });

  it("sends one debounced change, only with the moved setting", () => {
    const onChange = vi.fn();
    render(<Sliders scheme={scheme} overrides={{}} onChange={onChange} />);
    const burden = screen.getAllByRole("slider")[2];
    if (!burden) throw new Error("no slider");
    act(() => burden.focus());
    fireEvent.keyDown(burden, { key: "ArrowRight" });
    fireEvent.keyDown(burden, { key: "ArrowRight" });
    expect(onChange).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith({ application_burden: 5 });
  });

  it("resets to the real settings", () => {
    const onChange = vi.fn();
    render(<Sliders scheme={scheme} overrides={{ document_count: 4 }} onChange={onChange} />);
    fireEvent.click(screen.getByText("Back to real settings"));
    expect(onChange).toHaveBeenCalledWith({});
  });
});
