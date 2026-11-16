import type { Inputs } from "@/api/types.gen";
import {
  cashFromPosition,
  cleanOverrides,
  parsePolicy,
  parseScenario,
  positionFromCash,
  serializeScenario,
  toInputs,
  toSetting,
  writePolicy,
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
      custom: false,
      name: "",
      group: {},
    };
    expect(parseScenario(serializeScenario(s))).toEqual(s);
  });

  it("uses defaults for an empty or broken link", () => {
    const s = parseScenario(new URLSearchParams("cash=abc&docs=&bank=maybe"));
    expect(s).toEqual({
      state: null,
      district: null,
      scheme: "pmjay",
      overrides: {},
      custom: false,
      name: "",
      group: {},
    });
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

describe("custom policy URL", () => {
  const custom = {
    state: "Bihar",
    district: "9",
    scheme: "pmuy",
    overrides: { document_count: 3 },
    custom: true,
    name: "Women first",
    group: { female: true, rural: false, unbanked: true },
  };

  it("round-trips the name and the target group", () => {
    expect(parseScenario(serializeScenario(custom))).toEqual(custom);
  });

  it("leaves group and name out of the link for a real scheme", () => {
    const p = serializeScenario({ ...custom, custom: false });
    expect(p.has("name") || p.has("female")).toBe(false);
  });

  it("builds the request parts: group only for a custom policy", () => {
    const s = toSetting(custom, defaults);
    expect(s.target_group).toEqual({ female: true, rural: false, unbanked: true });
    expect(s.policy_name).toBe("Women first");
    expect(s.inputs).toEqual({ ...defaults, document_count: 3 });
    const plain = toSetting({ ...custom, custom: false }, defaults);
    expect(plain.target_group).toBeUndefined();
    expect(plain.policy_name).toBeUndefined();
  });

  it("keeps Compare settings A and B apart with prefixes", () => {
    const p = new URLSearchParams();
    writePolicy({ ...custom, custom: false, overrides: { application_burden: 1 } }, p, "a_");
    writePolicy({ ...custom, overrides: { application_burden: 5 } }, p, "b_");
    expect(parsePolicy(p, "a_").overrides).toEqual({ application_burden: 1 });
    expect(parsePolicy(p, "a_").custom).toBe(false);
    expect(parsePolicy(p, "b_").overrides).toEqual({ application_burden: 5 });
    expect(parsePolicy(p, "b_").group).toEqual(custom.group);
  });
});
