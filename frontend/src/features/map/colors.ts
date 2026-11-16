/** ColorBrewer YlGnBu, 8 classes: sequential and colourblind-safe. Classes are 12.5 pp wide. */
export const SCALE = [
  "#ffffd9",
  "#edf8b1",
  "#c7e9b4",
  "#7fcdbb",
  "#41b6c4",
  "#1d91c0",
  "#225ea8",
  "#0c2c84",
] as const;
export const STEP_PP = 12.5;

export interface MapColors {
  muted: string; // districts outside the chosen state
  noData: string;
  line: string; // district borders
  state: string; // state outlines
  selected: string;
  background: string;
  hatch: [number, number, number, number]; // RGBA of the low-confidence stripes
}

export const LIGHT: MapColors = {
  muted: "#e9e7de",
  noData: "#b5b3a9",
  line: "#9d9b90",
  state: "#15161a",
  selected: "#b7342f",
  background: "#f5f5f2",
  hatch: [21, 22, 26, 200],
};

export const DARK: MapColors = {
  muted: "#232320", // surface-2
  noData: "#46453d", // line-strong
  line: "#46453d", // line-strong
  state: "#f2f1ea", // ink
  selected: "#e2726d", // stamp
  background: "#131311", // bg
  hatch: [242, 241, 234, 200],
};

export function classLabel(i: number): string {
  const lo = i * STEP_PP;
  return `${lo}–${lo + STEP_PP}`;
}
