import type { Inputs, Reason } from "@/api/types.gen";
import i18n from "@/i18n/setup";
import { reasonSentence, sliderChange } from "./reasonText";

const real: Inputs = {
  cash_benefit_inr: 1000,
  document_count: 3,
  requires_bank_account: true,
  application_burden: 3,
  benefit_immediacy: 3,
};
const r = (term: string, direction: "up" | "down"): Reason => ({ term, effect_pp: 1.2, direction });

describe("reason text", () => {
  beforeEach(() => i18n.changeLanguage("en"));

  it("finds the slider direction", () => {
    expect(sliderChange("bank_account", real, { ...real, requires_bank_account: false })).toBe(
      "removed",
    );
    expect(sliderChange("bank_account", { ...real, requires_bank_account: false }, real)).toBe(
      "added",
    );
    expect(sliderChange("documents", real, { ...real, document_count: 5 })).toBe("more");
    expect(sliderChange("burden", real, { ...real, application_burden: 1 })).toBe("less");
    expect(sliderChange("benefit", real, real)).toBeNull();
    expect(sliderChange("target_group", real, real)).toBeNull();
  });

  it("says what the user did", () => {
    const used = { ...real, requires_bank_account: false };
    expect(reasonSentence(r("bank_account", "up"), real, used, i18n.t, "1.2")).toBe(
      "Removing the bank account requirement raises uptake by 1.2 pp",
    );
    expect(
      reasonSentence(r("documents", "down"), real, { ...real, document_count: 5 }, i18n.t, "1.2"),
    ).toBe("Asking for more documents lowers uptake by 1.2 pp");
    expect(
      reasonSentence(r("speed", "up"), real, { ...real, benefit_immediacy: 5 }, i18n.t, "1.2"),
    ).toBe("Making the benefit faster raises uptake by 1.2 pp");
  });

  it("falls back to the term name when no slider moved", () => {
    expect(reasonSentence(r("target_group", "down"), real, real, i18n.t, "1.2")).toBe(
      "Target group lowers uptake by 1.2 pp",
    );
  });

  it("works in Hindi", async () => {
    await i18n.changeLanguage("hi");
    const used = { ...real, requires_bank_account: false };
    expect(reasonSentence(r("bank_account", "up"), real, used, i18n.t, "1.2")).toBe(
      "बैंक खाते की शर्त हटाने से नामांकन 1.2 प्रतिशत अंक बढ़ता है",
    );
  });
});
