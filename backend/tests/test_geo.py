import geopandas as gpd
from shapely.geometry import Polygon

from scripts import geo


def test_simplify_renames_and_flags() -> None:
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0.5, 1.0001), (0, 1)])
    gdf = gpd.GeoDataFrame(
        {"pc11_s_id": ["01", "01"], "pc11_d_id": ["001", "000"], "d_name": ["Kupwara ", None]},
        geometry=[poly, poly],
        crs="EPSG:4326",
    )
    out = geo.simplify(gdf, tolerance=0.01)
    assert "name" in out.columns
    assert out["name"].iloc[0] == "Kupwara"
    assert out["has_census_data"].tolist() == [True, False]
    assert len(out) == 2
    assert out.geometry.is_valid.all()
