# Geography provenance

`zcta_boundaries_2020.geojson` contains the 238 ZIP Code Tabulation Areas represented in `data/analysis_ready.csv`.

- Source: U.S. Census Bureau TIGERweb, 2020 Census ZCTA layer 84
- Endpoint: <https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/84>
- Coordinate system: WGS84 (`EPSG:4326`)
- Simplification: `0.0003` degrees through TIGERweb's `maxAllowableOffset`
- Retrieval: `python3 scripts/build_site_data.py --refresh-geometry`

The build script validates that the committed geography contains exactly the same ZIP set as the analysis CSV before producing the public site extract.
