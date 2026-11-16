export function locale(lang: string): string {
  return lang.startsWith("hi") ? "hi-IN" : "en-IN";
}

export function formatNumber(v: number, lang: string, digits = 0): string {
  return new Intl.NumberFormat(locale(lang), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(v);
}

/** Honest rounding for range ends: the low end rounds down, the high end rounds up. */
export function rangeEnds(low: number, high: number): [number, number] {
  return [Math.max(0, Math.floor(low)), Math.min(100, Math.ceil(high))];
}

export function signed(v: number, lang: string, digits = 1): string {
  const s = formatNumber(Math.abs(v), lang, digits);
  return v < 0 ? `−${s}` : `+${s}`;
}
