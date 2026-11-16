import { useQuery } from "@tanstack/react-query";
import type { GeoData } from "./geo";

async function load(): Promise<GeoData> {
  const base = import.meta.env.BASE_URL;
  const [districts, states] = await Promise.all(
    ["geo/districts.geojson", "geo/states.geojson"].map(async (f) => {
      const r = await fetch(`${base}${f}`);
      if (!r.ok) throw new Error(`${f}: ${r.status}`);
      return r.json();
    }),
  );
  return { districts, states };
}

export function useGeo() {
  return useQuery({ queryKey: ["geo"], queryFn: load, staleTime: Number.POSITIVE_INFINITY });
}
