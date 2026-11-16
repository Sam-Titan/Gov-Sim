import type { CompareResponse, SimulateResponse, StateSimulateResponse } from "@/api/types.gen";
import i18n from "@/i18n/setup";
import custom from "../../../../shared/mocks/simulate.custom.sample.json";
import mock from "../../../../shared/mocks/simulate.sample.json";
import { formatCell, guardText, toCsv, today } from "./csv";
import { compareCsv, simulateCsv, stateCsv } from "./rows";

const meta = { link: "http://x/?a=1,2", date: "2026-11-16", version: "2026-11-16" };
const sim = mock as unknown as SimulateResponse;
const cust = custom as unknown as SimulateResponse;

describe("toCsv", () => {
  it("starts with a BOM and uses CRLF", () => {
    const csv = toCsv(["a", "b"], [[1, "x"]]);
    expect(csv.startsWith("﻿a,b\r\n")).toBe(true);
    expect(csv.endsWith("1,x\r\n")).toBe(true);
  });

  it("quotes commas, quotes and new lines", () => {
    expect(formatCell("a,b")).toBe('"a,b"');
    expect(formatCell('say "hi"')).toBe('"say ""hi"""');
    expect(formatCell("a\nb")).toBe('"a\nb"');
  });

  it("keeps Hindi text as it is", () => {
    expect(toCsv(["राज्य"], [["बैंक खाता"]])).toContain("राज्य\r\nबैंक खाता");
  });

  it("guards text that starts like a formula, but not numbers", () => {
    for (const s of ["=SUM(A1)", "+1", "-2", "@cmd"]) expect(guardText(s)).toBe(`'${s}`);
    expect(formatCell("=SUM(A1)")).toBe("'=SUM(A1)");
    expect(formatCell(-3.1)).toBe("-3.1");
    expect(formatCell(0)).toBe("0");
    expect(guardText("Women 60+")).toBe("Women 60+");
  });

  it("leaves missing values empty", () => {
    expect(toCsv(["a"], [[null], [undefined]])).toContain("a\r\n\r\n\r\n");
  });

  it("formats the date as YYYY-MM-DD", () => {
    expect(today(new Date(2026, 10, 5))).toBe("2026-11-05");
  });
});

describe("simulateCsv", () => {
  beforeEach(() => i18n.changeLanguage("en"));

  it("has as many cells as headers, with link, date and version last", () => {
    const { header, rows } = simulateCsv(sim, i18n.t, "en", meta);
    expect(rows[0]?.length).toBe(header.length);
    expect(rows[0]?.slice(-3)).toEqual([meta.link, meta.date, meta.version]);
  });

  it("guards a custom policy named =SUM(A1) and keeps negative numbers as numbers", () => {
    const named = { ...cust, policy_name: "=SUM(A1)" };
    const { rows } = simulateCsv(named, i18n.t, "en", meta);
    const csv = toCsv([], rows);
    expect(csv).toContain("'=SUM(A1)");
    expect(csv).not.toContain(",=SUM(A1)");
    const neg = {
      ...sim,
      result: { ...sim.result, changes: { weak: -3.1, central: -1, strong: -5 } },
    };
    const text = toCsv([], simulateCsv(neg, i18n.t, "en", meta).rows);
    expect(text).toContain(",-3.1,-1,-5,");
  });

  it("is written in Hindi when the language is Hindi", async () => {
    await i18n.changeLanguage("hi");
    const { header } = simulateCsv(sim, i18n.t, "hi", meta);
    expect(header).toContain("राज्य");
    expect(header).toContain("तारीख");
  });

  it("compare has A, B and a B minus A row", () => {
    const cmp: CompareResponse = {
      a: sim,
      b: sim,
      difference: { comparable: true, point: 1.5, low: -0.5, high: 3 },
    };
    const { header, rows } = compareCsv(cmp, i18n.t, "en", meta);
    expect(rows).toHaveLength(3);
    for (const r of rows) expect(r.length).toBe(header.length);
    expect(rows[2]?.[0]).toBe("B minus A");
    expect(
      compareCsv(
        { ...cmp, difference: { comparable: false, point: null, low: null, high: null } },
        i18n.t,
        "en",
        meta,
      ).rows,
    ).toHaveLength(2);
  });
});

describe("stateCsv", () => {
  beforeEach(() => i18n.changeLanguage("en"));
  const real = sim.real_inputs;
  const state: StateSimulateResponse = {
    state: "Bihar",
    scheme: "pmuy",
    metric_base: "households",
    custom: true,
    districts: [
      { district_id: "209", district: "Araria", has_data: true, result: sim.result, warnings: [] },
      { district_id: "1", district: "Nowhere", has_data: false, reason: "unmapped" },
    ],
  };

  it("adds the sent sliders and target group to every row", () => {
    const sent = {
      inputs: { ...real, document_count: 2, requires_bank_account: false },
      target_group: { age_60_plus: true, rural: false },
    };
    const { header, rows } = stateCsv(state, sent, real, i18n.t, meta);
    const col = (name: string) => header.indexOf(name);
    for (const r of rows) {
      expect(r.length).toBe(header.length);
      expect(r[col("Documents needed (used)")]).toBe(2);
      expect(r[col("Documents needed (real)")]).toBe(real.document_count);
      expect(r[col("Bank account required (used)")]).toBe("No");
      expect(r[col("Target group: Age")]).toBe("60 or older");
      expect(r[col("Target group: Area")]).toBe("Urban");
      expect(r[col("Target group: Gender")]).toBe("Anyone");
    }
  });

  it("uses the real settings when no slider moved, and no group for a real scheme", () => {
    const { header, rows } = stateCsv({ ...state, custom: false }, {}, real, i18n.t, meta);
    const row = rows[0] ?? [];
    expect(row[header.indexOf("Documents needed (used)")]).toBe(real.document_count);
    expect(row[header.indexOf("Target group: Age")]).toBe("");
  });
});
