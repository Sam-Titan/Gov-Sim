import type { StateRow } from "@/api/types.gen";
import { boundsOf, type GeoData, NO_DATA_AREA_ID, paintDistricts } from "./geo";

const geo: GeoData["districts"] = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: { pc11_d_id: "1", name: "A" },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [80, 20],
            [82, 20],
            [82, 22],
            [80, 20],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: { pc11_d_id: "2", name: "B" },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [70, 10],
            [71, 10],
            [71, 11],
            [70, 10],
          ],
        ],
      },
    },
  ],
};

const row = (id: string, point: number, lowconf = false): StateRow => ({
  district_id: id,
  district: id,
  has_data: true,
  result: {
    basis: "all",
    level: point,
    point,
    low: point - 2,
    high: point + 2,
    low_confidence: lowconf,
    changes: { weak: 0, central: 0, strong: 0 },
    sampling_half_width_pp: 2,
  },
});

describe("map data", () => {
  it("finds the bounds of a state's districts", () => {
    expect(boundsOf(geo, new Set(["1"]))).toEqual([
      [80, 20],
      [82, 22],
    ]);
    expect(boundsOf(geo, new Set(["9"]))).toBeNull();
  });

  it("paints chosen-state districts and marks no-data and low-confidence", () => {
    const out = paintDistricts(geo, {
      rows: new Map([["1", row("1", 40, true)]]),
      inState: new Set(["1", "2"]),
      selected: "1",
    });
    const [a, b] = out.features.map((f) => f.properties);
    expect(a).toMatchObject({ pt: 40, lowconf: true, inState: true, sel: true });
    expect(b).toMatchObject({ pt: -1, lowconf: false, inState: true, sel: false });
  });

  it("marks the unnamed polygon as fixed no-data", () => {
    const g = {
      ...geo,
      features: [
        ...geo.features,
        {
          ...(geo.features[0] as (typeof geo.features)[number]),
          properties: { pc11_d_id: NO_DATA_AREA_ID, name: "" },
        },
      ],
    };
    const out = paintDistricts(g, { rows: new Map(), inState: new Set(["000"]), selected: "000" });
    expect(out.features.at(-1)?.properties).toMatchObject({ fixed: true, pt: -1 });
  });

  it("paints nothing in the India view", () => {
    const out = paintDistricts(geo, { rows: new Map(), inState: null, selected: null });
    expect(out.features.every((f) => !f.properties.inState)).toBe(true);
  });
});
