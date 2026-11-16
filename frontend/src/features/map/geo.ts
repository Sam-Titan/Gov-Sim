import type { DistrictOut, StateRow } from "@/api/types.gen";

/** The little GeoJSON we need (no extra type package). */
export interface Geometry {
  type: string;
  coordinates: unknown;
}
export interface Feature<P> {
  type: "Feature";
  geometry: Geometry;
  properties: P;
}
export interface FeatureCollection<P> {
  type: "FeatureCollection";
  features: Feature<P>[];
}

/** Unnamed polygon (Gilgit-Baltistan / Aksai Chin region): no data, never clickable (D-049). */
export const NO_DATA_AREA_ID = "000";

export type Bounds = [[number, number], [number, number]];
export const INDIA_BOUNDS: Bounds = [
  [68, 6],
  [98, 37],
];

export interface DistrictProps {
  pc11_d_id: string;
  name: string;
}

export interface GeoData {
  districts: FeatureCollection<DistrictProps>;
  states: FeatureCollection<{ state: string }>;
}

function walk(coords: unknown, acc: Bounds): void {
  if (!Array.isArray(coords)) return;
  if (typeof coords[0] === "number") {
    const [x, y] = coords as [number, number];
    acc[0][0] = Math.min(acc[0][0], x);
    acc[0][1] = Math.min(acc[0][1], y);
    acc[1][0] = Math.max(acc[1][0], x);
    acc[1][1] = Math.max(acc[1][1], y);
    return;
  }
  for (const c of coords) walk(c, acc);
}

/** Bounding box of the given district ids; null when none has a polygon. */
export function boundsOf(geo: GeoData["districts"], ids: Set<string>): Bounds | null {
  const acc: Bounds = [
    [180, 90],
    [-180, -90],
  ];
  let found = false;
  for (const f of geo.features) {
    if (!ids.has(f.properties.pc11_d_id)) continue;
    walk(f.geometry.coordinates, acc);
    found = true;
  }
  return found ? acc : null;
}

export interface Paint {
  /** Result rows of the chosen state, by district id. */
  rows: Map<string, StateRow>;
  /** Districts of the chosen state (null = India view, nothing is painted). */
  inState: Set<string> | null;
  selected: string | null;
}

export type PaintedProps = DistrictProps & {
  inState: boolean;
  pt: number;
  lowconf: boolean;
  sel: boolean;
  fixed: boolean;
};

/** Copy of the polygons with the values the layers read: pt (middle %, -1 = none), lowconf, inState, sel. */
export function paintDistricts(
  geo: GeoData["districts"],
  p: Paint,
): FeatureCollection<PaintedProps> {
  return {
    type: "FeatureCollection",
    features: geo.features.map((f) => {
      const id = f.properties.pc11_d_id;
      const row = p.rows.get(id);
      const res = row?.has_data ? row.result : null;
      return {
        ...f,
        properties: {
          ...f.properties,
          inState: p.inState?.has(id) ?? false,
          pt: res ? res.point : -1,
          lowconf: res?.low_confidence ?? false,
          sel: id === p.selected,
          fixed: id === NO_DATA_AREA_ID,
        },
      };
    }),
  };
}

export function stateIds(districts: DistrictOut[], state: string | null): Set<string> | null {
  return state ? new Set(districts.filter((d) => d.state === state).map((d) => d.id)) : null;
}
