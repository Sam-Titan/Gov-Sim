import type { TFunction } from "i18next";
import type {
  CompareResponse,
  Inputs,
  SimulateResponse,
  StateRow,
  StateSimulateResponse,
  TargetGroup,
} from "@/api/types.gen";
import { formatNumber } from "@/lib/format";
import { reasonSentence } from "../simulator/reasonText";
import type { Cell } from "./csv";

/** Link, date and model/data version, written into every CSV and the print summary. */
export interface Meta {
  link: string;
  date: string;
  version: string;
}

const INPUTS: (keyof Inputs)[] = [
  "cash_benefit_inr",
  "document_count",
  "requires_bank_account",
  "application_burden",
  "benefit_immediacy",
];

const r2 = (v: number): number => Math.round(v * 100) / 100;

function metricLabel(t: TFunction, base: string, group: boolean): string {
  return group ? t("metric.group") : t(`metric.${base}`);
}

function inputCell(t: TFunction, v: number | boolean): Cell {
  return typeof v === "boolean" ? t(v ? "download.yes" : "download.no") : v;
}

function tail(t: TFunction, meta: Meta): { head: string[]; cells: Cell[] } {
  return {
    head: [t("download.col.link"), t("download.col.date"), t("download.col.version")],
    cells: [meta.link, meta.date, meta.version],
  };
}

function warningsText(t: TFunction, w: string[]): string {
  return w.map((x) => t(`warning.${x}`)).join(" | ");
}

export function simulateHeader(t: TFunction, meta: Meta): string[] {
  const inputHead = INPUTS.flatMap((k) => {
    const name = t(`sliders.${k}`);
    return [t("download.col.used", { name }), t("download.col.real", { name })];
  });
  return [
    t("download.col.state"),
    t("download.col.district"),
    t("download.col.scheme"),
    t("download.col.metric"),
    t("download.col.custom"),
    t("download.col.policyName"),
    t("download.col.groupShare"),
    t("download.col.groupCount"),
    ...inputHead,
    t("download.col.level"),
    t("download.col.changeWeak"),
    t("download.col.changeCentral"),
    t("download.col.changeStrong"),
    t("download.col.low"),
    t("download.col.middle"),
    t("download.col.high"),
    t("download.col.reachPoint"),
    t("download.col.reachLow"),
    t("download.col.reachHigh"),
    t("download.col.reasons"),
    t("download.col.warnings"),
    t("download.col.note"),
    ...tail(t, meta).head,
  ];
}

export function simulateRow(d: SimulateResponse, t: TFunction, lang: string, meta: Meta): Cell[] {
  const r = d.result;
  const reach = r.reach;
  const reasons = d.reasons
    .filter((x) => Math.abs(x.effect_pp) >= 0.05)
    .map((x) =>
      reasonSentence(
        x,
        d.real_inputs,
        d.used_inputs,
        t,
        formatNumber(Math.abs(x.effect_pp), lang, 1),
      ),
    )
    .join(" | ");
  return [
    d.state,
    d.district,
    t(`scheme.${d.scheme}`),
    metricLabel(t, d.metric_base, r.basis === "target_group"),
    t(d.custom ? "download.yes" : "download.no"),
    d.policy_name ?? "",
    reach ? r2(reach.group_share_pct) : null,
    reach ? Math.round(reach.group_count) : null,
    ...INPUTS.flatMap((k) => [inputCell(t, d.used_inputs[k]), inputCell(t, d.real_inputs[k])]),
    r2(r.level),
    r2(r.changes.weak),
    r2(r.changes.central),
    r2(r.changes.strong),
    r2(r.low),
    r2(r.point),
    r2(r.high),
    reach ? Math.round(reach.reached_point) : null,
    reach ? Math.round(reach.reached_low) : null,
    reach ? Math.round(reach.reached_high) : null,
    reasons,
    warningsText(t, d.warnings),
    t("download.modelNote"),
    ...tail(t, meta).cells,
  ];
}

export function simulateCsv(d: SimulateResponse, t: TFunction, lang: string, meta: Meta) {
  return { header: simulateHeader(t, meta), rows: [simulateRow(d, t, lang, meta)] };
}

/** Compare: one row for A, one for B, and a B minus A row (only when comparable). */
export function compareCsv(d: CompareResponse, t: TFunction, lang: string, meta: Meta) {
  const head = simulateHeader(t, meta);
  const side = (label: string, row: Cell[]): Cell[] => [label, ...row];
  const rows: Cell[][] = [
    side(t("print.sideA"), simulateRow(d.a, t, lang, meta)),
    side(t("print.sideB"), simulateRow(d.b, t, lang, meta)),
  ];
  const df = d.difference;
  if (df.comparable && df.low !== null && df.point !== null && df.high !== null) {
    const blank = simulateRow(d.b, t, lang, meta).map(() => null as Cell);
    const at = (name: string) => head.indexOf(t(name));
    blank[0] = d.b.state;
    blank[1] = d.b.district;
    blank[2] = t(`scheme.${d.b.scheme}`);
    blank[at("download.col.low")] = r2(df.low);
    blank[at("download.col.middle")] = r2(df.point);
    blank[at("download.col.high")] = r2(df.high);
    const n = blank.length;
    [blank[n - 3], blank[n - 2], blank[n - 1]] = [meta.link, meta.date, meta.version];
    rows.push(side(t("download.differenceRow"), blank));
  }
  return { header: [t("download.col.side"), ...head], rows };
}

const GROUP_VALUE: Record<keyof TargetGroup, string> = {
  age_60_plus: "age",
  female: "gender",
  disabled: "disabled",
  rural: "area",
  unbanked: "bank",
};

/** The settings the page sent: moved sliders (absent = real settings) and the target group. */
export interface SentSetting {
  inputs?: Inputs | undefined;
  target_group?: TargetGroup | undefined;
}

/**
 * State table: one row per district. The slider columns (used and real value) and, for a custom
 * policy, the target group come from the settings the page sent, since the response has none.
 */
export function stateCsv(
  d: StateSimulateResponse,
  sent: SentSetting,
  real: Inputs,
  t: TFunction,
  meta: Meta,
) {
  const used = sent.inputs ?? real;
  const traits = Object.keys(GROUP_VALUE) as (keyof TargetGroup)[];
  const groupCells = traits.map((k): Cell => {
    if (!d.custom) return "";
    const v = sent.target_group?.[k];
    return typeof v === "boolean"
      ? t(`custom.${GROUP_VALUE[k]}.${v ? "yes" : "no"}`)
      : t("custom.any");
  });
  const header = [
    t("download.col.state"),
    t("download.col.district"),
    t("download.col.districtId"),
    t("download.col.scheme"),
    t("download.col.metric"),
    t("download.col.custom"),
    ...traits.map((k) => t("download.col.group", { trait: t(`custom.trait.${k}`) })),
    ...INPUTS.flatMap((k) => {
      const name = t(`sliders.${k}`);
      return [t("download.col.used", { name }), t("download.col.real", { name })];
    }),
    t("download.col.hasData"),
    t("download.col.reason"),
    t("download.col.level"),
    t("download.col.changeWeak"),
    t("download.col.changeCentral"),
    t("download.col.changeStrong"),
    t("download.col.low"),
    t("download.col.middle"),
    t("download.col.high"),
    t("download.col.warnings"),
    t("download.col.note"),
    ...tail(t, meta).head,
  ];
  const row = (x: StateRow): Cell[] => {
    const r = x.result;
    return [
      d.state,
      x.district,
      x.district_id,
      t(`scheme.${d.scheme}`),
      metricLabel(t, d.metric_base, r?.basis === "target_group" || d.custom),
      t(d.custom ? "download.yes" : "download.no"),
      ...groupCells,
      ...INPUTS.flatMap((k) => [inputCell(t, used[k]), inputCell(t, real[k])]),
      t(x.has_data ? "download.yes" : "download.no"),
      x.reason ? t(`noDataReason.${x.reason}`, { defaultValue: x.reason }) : "",
      r ? r2(r.level) : null,
      r ? r2(r.changes.weak) : null,
      r ? r2(r.changes.central) : null,
      r ? r2(r.changes.strong) : null,
      r ? r2(r.low) : null,
      r ? r2(r.point) : null,
      r ? r2(r.high) : null,
      warningsText(t, x.warnings ?? []),
      t("download.modelNote"),
      ...tail(t, meta).cells,
    ];
  };
  return { header, rows: d.districts.map(row) };
}
