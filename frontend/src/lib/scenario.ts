import type { Inputs } from "@/api/types.gen";

/** Slider fields and their short URL names (a scenario is shared by link). */
export const FIELD_PARAM = {
  cash_benefit_inr: "cash",
  document_count: "docs",
  requires_bank_account: "bank",
  application_burden: "burden",
  benefit_immediacy: "speed",
} as const satisfies Record<keyof Inputs, string>;

export type Field = keyof Inputs;
export const FIELDS = Object.keys(FIELD_PARAM) as Field[];
export type Overrides = Partial<Inputs>;

export interface Scenario {
  state: string | null;
  district: string | null;
  scheme: string;
  /** Only the sliders the user moved. No override = the scheme's real value. */
  overrides: Overrides;
}

export const DEFAULT_SCHEME = "pmjay";

export function parseScenario(p: URLSearchParams): Scenario {
  const overrides: Overrides = {};
  const num = (key: string): number | undefined => {
    const raw = p.get(key);
    const v = raw === null || raw === "" ? Number.NaN : Number(raw);
    return Number.isFinite(v) ? v : undefined;
  };
  const cash = num(FIELD_PARAM.cash_benefit_inr);
  if (cash !== undefined) overrides.cash_benefit_inr = cash;
  const docs = num(FIELD_PARAM.document_count);
  if (docs !== undefined) overrides.document_count = Math.round(docs);
  const burden = num(FIELD_PARAM.application_burden);
  if (burden !== undefined) overrides.application_burden = Math.round(burden);
  const speed = num(FIELD_PARAM.benefit_immediacy);
  if (speed !== undefined) overrides.benefit_immediacy = Math.round(speed);
  const bank = p.get(FIELD_PARAM.requires_bank_account);
  if (bank === "1" || bank === "0") overrides.requires_bank_account = bank === "1";
  return {
    state: p.get("state") || null,
    district: p.get("district") || null,
    scheme: p.get("scheme") || DEFAULT_SCHEME,
    overrides,
  };
}

export function serializeScenario(s: Scenario): URLSearchParams {
  const p = new URLSearchParams();
  if (s.state) p.set("state", s.state);
  if (s.district) p.set("district", s.district);
  p.set("scheme", s.scheme);
  for (const f of FIELDS) {
    const v = s.overrides[f];
    if (v === undefined) continue;
    p.set(FIELD_PARAM[f], typeof v === "boolean" ? (v ? "1" : "0") : String(v));
  }
  return p;
}

/** Full inputs for a request, or undefined when nothing was moved (= real settings). */
export function toInputs(overrides: Overrides, defaults: Inputs): Inputs | undefined {
  const moved = FIELDS.some((f) => overrides[f] !== undefined && overrides[f] !== defaults[f]);
  return moved ? { ...defaults, ...overrides } : undefined;
}

/** Drop overrides that equal the real value, so the link stays short. */
export function cleanOverrides(overrides: Overrides, defaults: Inputs): Overrides {
  const out: Overrides = {};
  for (const f of FIELDS) {
    const v = overrides[f];
    if (v !== undefined && v !== defaults[f]) Object.assign(out, { [f]: v });
  }
  return out;
}

/** Log-scale slider helpers: position 0..1 <-> rupees (benefit value). */
export function cashFromPosition(pos: number, min: number, max: number): number {
  const lo = Math.log1p(min);
  const v = Math.expm1(lo + pos * (Math.log1p(max) - lo));
  const step = v >= 10000 ? 1000 : v >= 1000 ? 100 : 10;
  return Math.min(max, Math.max(min, Math.round(v / step) * step));
}

export function positionFromCash(v: number, min: number, max: number): number {
  const lo = Math.log1p(min);
  const span = Math.log1p(max) - lo;
  return span <= 0 ? 0 : Math.min(1, Math.max(0, (Math.log1p(v) - lo) / span));
}
