import type { Inputs, TargetGroup } from "@/api/types.gen";

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

/** Custom-policy target group fields and their short URL names. */
export const GROUP_PARAM = {
  age_60_plus: "age60",
  female: "female",
  disabled: "disabled",
  rural: "rural",
  unbanked: "unbanked",
} as const satisfies Record<keyof TargetGroup, string>;

export type GroupField = keyof TargetGroup;
export const GROUP_FIELDS = Object.keys(GROUP_PARAM) as GroupField[];

/** One policy setting: a real scheme with moved sliders, or a custom policy built on it. */
export interface Policy {
  scheme: string;
  /** Only the sliders the user moved. No override = the scheme's real value. */
  overrides: Overrides;
  custom: boolean;
  name: string;
  /** A field that is missing means "no filter on that trait". */
  group: TargetGroup;
}

export interface Scenario extends Policy {
  state: string | null;
  district: string | null;
}

export const DEFAULT_SCHEME = "pmjay";

export function emptyPolicy(scheme = DEFAULT_SCHEME): Policy {
  return { scheme, overrides: {}, custom: false, name: "", group: {} };
}

/** Read one policy from the URL. `prefix` is "" (Simulator) or "a_" / "b_" (Compare). */
export function parsePolicy(p: URLSearchParams, prefix = ""): Policy {
  const overrides: Overrides = {};
  const get = (key: string) => p.get(`${prefix}${key}`);
  const num = (key: string): number | undefined => {
    const raw = get(key);
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
  const bank = get(FIELD_PARAM.requires_bank_account);
  if (bank === "1" || bank === "0") overrides.requires_bank_account = bank === "1";
  const group: TargetGroup = {};
  for (const f of GROUP_FIELDS) {
    const v = get(GROUP_PARAM[f]);
    if (v === "1" || v === "0") group[f] = v === "1";
  }
  return {
    scheme: get("scheme") || DEFAULT_SCHEME,
    overrides,
    custom: get("custom") === "1",
    name: get("name") ?? "",
    group,
  };
}

export function writePolicy(pol: Policy, p: URLSearchParams, prefix = ""): void {
  p.set(`${prefix}scheme`, pol.scheme);
  for (const f of FIELDS) {
    const v = pol.overrides[f];
    if (v === undefined) continue;
    p.set(`${prefix}${FIELD_PARAM[f]}`, typeof v === "boolean" ? (v ? "1" : "0") : String(v));
  }
  if (!pol.custom) return;
  p.set(`${prefix}custom`, "1");
  if (pol.name) p.set(`${prefix}name`, pol.name);
  for (const f of GROUP_FIELDS) {
    const v = pol.group[f];
    if (typeof v === "boolean") p.set(`${prefix}${GROUP_PARAM[f]}`, v ? "1" : "0");
  }
}

export function parseScenario(p: URLSearchParams): Scenario {
  return {
    state: p.get("state") || null,
    district: p.get("district") || null,
    ...parsePolicy(p),
  };
}

export function serializeScenario(s: Scenario): URLSearchParams {
  const p = new URLSearchParams();
  if (s.state) p.set("state", s.state);
  if (s.district) p.set("district", s.district);
  writePolicy(s, p);
  return p;
}

/** The request body parts that describe a policy (shared by simulate, state and compare). */
export function toSetting(pol: Policy, defaults: Inputs) {
  return {
    scheme: pol.scheme,
    inputs: toInputs(pol.overrides, defaults),
    target_group: pol.custom ? cleanGroup(pol.group) : undefined,
    policy_name: pol.custom && pol.name.trim() ? pol.name.trim() : undefined,
  };
}

export function cleanGroup(g: TargetGroup): TargetGroup {
  const out: TargetGroup = {};
  for (const f of GROUP_FIELDS) {
    const v = g[f];
    if (typeof v === "boolean") out[f] = v;
  }
  return out;
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
