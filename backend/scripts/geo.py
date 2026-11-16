"""Simplify the district map to a small GeoJSON for the frontend.

The map is SHRUG v2.1 open district polygons (Development Data Lab), hosted on AIKosh,
CC BY-NC-SA 4.0. Any file made from it keeps that licence and must be credited.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import polars as pl

from govsim.service import Service

ROOT = Path(__file__).resolve().parents[2]
SHP = ROOT / "data" / "raw" / "district.shp"
OUT = ROOT / "data" / "processed" / "districts.geojson"
STATES_OUT = ROOT / "data" / "processed" / "states.geojson"
TOLERANCE_DEG = 0.01  # about 1 km: fine for a district-level choropleth
ATTRIBUTION = (
    "District polygons: SHRUG v2.1 open district polygons (Development Data Lab), "
    "hosted on AIKosh. Licence CC BY-NC-SA 4.0 (share alike, non-commercial). "
    "Simplified by GovSim."
)


def simplify(
    gdf: gpd.GeoDataFrame,
    tolerance: float = TOLERANCE_DEG,
    mapped_ids: set[str] | None = None,
) -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["geometry"] = out.geometry.simplify(tolerance, preserve_topology=True)
    out = out.rename(columns={"d_name": "name"})
    out["name"] = out["name"].str.strip()
    # The polygon with district id 000 has no Census row (no name); kept for the outline.
    out["has_census_data"] = out["pc11_d_id"] != "000"
    # True if at least one NFHS district maps to this 2011 district. Others show "no data".
    if mapped_ids is not None:
        out["has_nfhs_data"] = out["pc11_d_id"].isin(mapped_ids)
    return out


def mapped_district_ids() -> set[str]:
    table = pl.read_parquet(ROOT / "data" / "processed" / "district_map.parquet")
    return set(table.filter(pl.col("match_type") != "unmapped")["pc11_d_id"].to_list())


def current_state_by_district() -> dict[str, str]:
    """Current state of every 2011 district id, by the same rule as the API (D-045)."""
    processed = ROOT / "data" / "processed"
    traits = pl.read_parquet(processed / "district_traits.parquet")
    census = pl.read_parquet(processed / "census2011_districts.parquet")
    states_of: dict[str, set[str]] = {}
    for sid, name in zip(traits["pc11_s_id"], traits["nfhs_state"], strict=True):
        if sid is not None:
            states_of.setdefault(sid, set()).add(name)
    out = {
        r["pc11_d_id"]: r["nfhs_state"]
        for r in traits.iter_rows(named=True)
        if r["pc11_d_id"] is not None
    }
    for r in census.iter_rows(named=True):
        if r["pc11_d_id"] not in out:
            out[r["pc11_d_id"]] = Service._current_state(r, states_of)
    return out


def state_outlines(gdf: gpd.GeoDataFrame, state_of: dict[str, str]) -> gpd.GeoDataFrame:
    """One outline per current state: district polygons merged by `state_of` (D-045).

    The input is already simplified, so outlines follow the district edges.
    Polygons with no entry (the unnamed id 000) are left out of the outlines.
    """
    g = gdf[["pc11_d_id", "geometry"]].copy()
    g["state"] = g["pc11_d_id"].map(state_of)
    g = g.dropna(subset=["state"])
    states = g[["state", "geometry"]].dissolve(by="state", as_index=False)
    return states


def main() -> None:
    gdf = simplify(gpd.read_file(SHP), mapped_ids=mapped_district_ids())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUT, driver="GeoJSON", COORDINATE_PRECISION=4)
    data = json.loads(OUT.read_text(encoding="utf-8"))
    data["attribution"] = ATTRIBUTION
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    state_outlines(gdf, current_state_by_district()).to_file(
        STATES_OUT, driver="GeoJSON", COORDINATE_PRECISION=4
    )
    print(f"{len(gdf)} polygons -> {OUT.name} ({OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
