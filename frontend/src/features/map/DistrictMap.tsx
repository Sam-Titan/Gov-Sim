import { setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import MapGL, { Layer, type MapLayerMouseEvent, type MapRef, Source } from "react-map-gl/maplibre";
import type { StateRow } from "@/api/types.gen";
import { DARK, LIGHT, type MapColors, SCALE, STEP_PP } from "./colors";
import { boundsOf, type GeoData, INDIA_BOUNDS, paintDistricts } from "./geo";
import { Legend } from "./Legend";

// Vite cannot find MapLibre's worker by itself (dev and build), so point to it.
setWorkerUrl(workerUrl);

interface Props {
  geo: GeoData;
  dark: boolean;
  state: string | null;
  stateDistrictIds: Set<string> | null;
  rows: StateRow[];
  selected: string | null;
  onPick: (districtId: string) => void;
  /** Custom policy: colours show uptake within the target group. */
  group?: boolean;
}

/** Diagonal stripes, 8x8 px, as raw RGBA. */
function hatchImage(rgba: MapColors["hatch"]) {
  const size = 8;
  const data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      if ((x + y) % size < 2) data.set(rgba, (y * size + x) * 4);
    }
  }
  return { width: size, height: size, data };
}

function fillColor(c: MapColors) {
  const steps: (string | number)[] = [];
  SCALE.forEach((col, i) => {
    if (i > 0) steps.push(i * STEP_PP);
    steps.push(col);
  });
  return [
    "case",
    ["get", "fixed"],
    c.noData,
    ["!", ["get", "inState"]],
    c.muted,
    ["<", ["get", "pt"], 0],
    c.noData,
    ["step", ["get", "pt"], ...steps],
  ];
}

export function DistrictMap(props: Props) {
  const { geo, dark, state, stateDistrictIds, rows, selected, onPick } = props;
  const { t } = useTranslation();
  const ref = useRef<MapRef>(null);
  const [loaded, setLoaded] = useState(false);
  const [hover, setHover] = useState(false);
  const colors = dark ? DARK : LIGHT;

  const style = useMemo(
    () => ({
      version: 8 as const,
      sources: {},
      layers: [
        { id: "bg", type: "background" as const, paint: { "background-color": colors.background } },
      ],
    }),
    [colors.background],
  );
  const painted = useMemo(
    () =>
      paintDistricts(geo.districts, {
        rows: new Map(rows.map((r) => [r.district_id, r])),
        inState: stateDistrictIds,
        selected,
      }),
    [geo.districts, rows, stateDistrictIds, selected],
  );

  // India first, then zoom to the chosen state.
  useEffect(() => {
    const map = ref.current;
    if (!loaded || !map) return;
    const b = (stateDistrictIds && boundsOf(geo.districts, stateDistrictIds)) || INDIA_BOUNDS;
    map.fitBounds(b, { padding: 24, duration: 600 });
  }, [loaded, stateDistrictIds, geo.districts]);

  const onLoad = () => {
    const m = ref.current?.getMap();
    if (m && !m.hasImage("hatch")) m.addImage("hatch", hatchImage(colors.hatch));
    setLoaded(true);
  };
  // Stripes change colour with the theme.
  useEffect(() => {
    const m = ref.current?.getMap();
    if (!loaded || !m) return;
    if (m.hasImage("hatch")) m.removeImage("hatch");
    m.addImage("hatch", hatchImage(colors.hatch));
  }, [loaded, colors.hatch]);

  const onClick = (e: MapLayerMouseEvent) => {
    const id = e.features?.[0]?.properties?.pc11_d_id;
    if (typeof id === "string") onPick(id);
  };

  return (
    <figure className="grid gap-2">
      <figcaption className="font-serif text-lg">
        {state ? t("map.titleState", { state }) : t("map.titleIndia")}
      </figcaption>
      <div
        className="h-[420px] overflow-hidden rounded border border-line lg:h-[520px]"
        role="img"
        aria-label={t("map.aria")}
      >
        <MapGL
          ref={ref}
          mapStyle={style}
          initialViewState={{ bounds: INDIA_BOUNDS }}
          interactiveLayerIds={["district-fill"]}
          onClick={onClick}
          onLoad={onLoad}
          onMouseEnter={() => setHover(true)}
          onMouseLeave={() => setHover(false)}
          cursor={hover ? "pointer" : "grab"}
          attributionControl={false}
          dragRotate={false}
          touchZoomRotate={false}
          style={{ width: "100%", height: "100%" }}
        >
          <Source id="districts" type="geojson" data={painted as never}>
            <Layer
              id="district-fill"
              type="fill"
              filter={["!", ["get", "fixed"]]}
              paint={{ "fill-color": fillColor(colors) as never, "fill-opacity": 1 }}
            />
            <Layer
              id="area-nodata"
              type="fill"
              filter={["get", "fixed"]}
              paint={{ "fill-color": colors.noData }}
            />
            <Layer
              id="area-nodata-line"
              type="line"
              filter={["get", "fixed"]}
              paint={{ "line-color": colors.state, "line-width": 1.2 }}
            />
            <Layer
              id="district-hatch"
              type="fill"
              filter={["==", ["get", "lowconf"], true]}
              paint={{ "fill-pattern": "hatch" }}
            />
            <Layer
              id="district-line"
              type="line"
              paint={{ "line-color": colors.line, "line-width": 0.4 }}
            />
            <Layer
              id="district-selected"
              type="line"
              filter={["==", ["get", "sel"], true]}
              paint={{ "line-color": colors.selected, "line-width": 3 }}
            />
          </Source>
          <Source id="states" type="geojson" data={geo.states as never}>
            <Layer
              id="state-line"
              type="line"
              paint={{ "line-color": colors.state, "line-width": 1.2 }}
            />
          </Source>
        </MapGL>
      </div>
      <Legend colors={colors} group={props.group} />
      <p className="text-xs opacity-80">{t("map.hint")}</p>
      <p className="text-xs font-semibold">{t("map.note")}</p>
      <p className="text-xs opacity-80">{t("map.credit")}</p>
    </figure>
  );
}
