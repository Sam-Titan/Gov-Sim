import type { TFunction } from "i18next";
import type { Inputs, Reason } from "@/api/types.gen";

type Change = "more" | "less" | "added" | "removed";

const INPUT_OF: Record<string, keyof Inputs> = {
  benefit: "cash_benefit_inr",
  documents: "document_count",
  bank_account: "requires_bank_account",
  burden: "application_burden",
  speed: "benefit_immediacy",
};

/** Which way the user moved the slider for this term, or null (no slider, or not moved). */
export function sliderChange(term: string, real: Inputs, used: Inputs): Change | null {
  const key = INPUT_OF[term];
  if (!key) return null;
  const r = real[key];
  const u = used[key];
  if (typeof r === "boolean" || typeof u === "boolean") {
    if (r === u) return null;
    return u ? "added" : "removed";
  }
  if (u === r) return null;
  return u > r ? "more" : "less";
}

/**
 * One sentence for a reason: "Removing the bank account requirement raises uptake by 1.2 pp".
 * Without a slider direction (target group, or the setting equals the real one) it falls back
 * to the term name, "Benefit value raises uptake by 1.2 pp".
 */
export function reasonSentence(
  x: Reason,
  real: Inputs,
  used: Inputs,
  t: TFunction,
  pp: string,
): string {
  const change = sliderChange(x.term, real, used);
  if (change) {
    return `${t(`reason.change.${x.term}.${change}`)} ${t(
      x.direction === "up" ? "reason.effectUp" : "reason.effectDown",
      { pp },
    )}`;
  }
  return `${t(`reason.${x.term}`, { defaultValue: x.term })} ${t(
    x.direction === "up" ? "reason.up" : "reason.down",
    { pp },
  )}`;
}
