/** A CSV cell. Numbers stay numbers (negatives included); text is guarded against formulas. */
export type Cell = string | number | null | undefined;

const BOM = "﻿";
// Excel and Sheets read a text cell starting with these as a formula (CSV injection).
const FORMULA_START = /^[=+\-@\t\r]/;

/** Text cells that start like a formula get a ' in front. Numbers are never touched. */
export function guardText(s: string): string {
  return FORMULA_START.test(s) ? `'${s}` : s;
}

export function formatCell(c: Cell): string {
  if (c === null || c === undefined) return "";
  const raw = typeof c === "number" ? (Number.isFinite(c) ? String(c) : "") : guardText(c);
  return /[",\r\n]/.test(raw) ? `"${raw.replace(/"/g, '""')}"` : raw;
}

/** UTF-8 text with a BOM (so Excel shows Hindi) and CRLF line ends. */
export function toCsv(header: string[], rows: Cell[][]): string {
  const lines = [header, ...rows].map((r) => r.map(formatCell).join(","));
  return `${BOM}${lines.join("\r\n")}\r\n`;
}

export function downloadCsv(filename: string, csv: string): void {
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/** Today as YYYY-MM-DD in the browser's time zone. */
export function today(d = new Date()): string {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}
