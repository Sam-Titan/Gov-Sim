import type { Inputs } from "@/api/types.gen";
import {
  cashFromPosition,
  cleanOverrides,
  parseScenario,
  positionFromCash,
  serializeScenario,
  toInputs,
} from "./scenario";

const defaults: Inputs = {
  cash_benefit_inr: 12000,
  document_count: 1,
  requires_bank_account: true,
  application_burden: 3,
  benefit_immediacy: 2,
};

describe("scenario URL", () => {
  it("round-trips state, district, scheme and sliders", () => {
    const s = {
      state: "Bihar",
      district: "123",
      scheme: "sbm",
      overrides: { cash_benefit_inr: 24000, requires_bank_account: false, application_burden: 2 },
    };
    expect(parseScenario(serializeScenario(s))).toEqual(s);
  });

  it("uses defaults for an empty or broken link", () => {
    const s = parseScenario(new URLSearchParams("cash=abc&docs=&bank=maybe"));
    expect(s).toEqual({ state: null, district: null, scheme: "pmjay", overrides: {} });
  });
});

describe("inputs", () => {
  it("sends nothing when no slider differs from the real value", () => {
    expect(toInputs({ document_count: 1 }, defaults)).toBeUndefined();
  });
  it("sends the full inputs when one slider moved", () => {
    expect(toInputs({ document_count: 3 }, defaults)).toEqual({ ...defaults, document_count: 3 });
  });
  it("drops overrides equal to the real value", () => {
    expect(cleanOverrides({ document_count: 1, application_burden: 2 }, defaults)).toEqual({
      application_burden: 2,
    });
  });
});

describe("log cash slider", () => {
  it("covers the whole range and stays inside it", () => {
    expect(cashFromPosition(0, 0, 500000)).toBe(0);
    expect(cashFromPosition(1, 0, 500000)).toBe(500000);
    expect(cashFromPosition(0, 250000, 1000000)).toBe(250000);
    expect(cashFromPosition(1, 250000, 1000000)).toBe(1000000);
  });
  it("is the inverse of the position (within rounding)", () => {
    const pos = positionFromCash(12000, 0, 500000);
    expect(Math.abs(cashFromPosition(pos, 0, 500000) - 12000)).toBeLessThanOrEqual(1000);
  });
});
