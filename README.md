# Road Telemetry

Open-source, crowd-powered **road-quality intelligence** (potholes/rough roads from phone sensors + images) and **thermal route intelligence** (shade/solar/heat exposure per road segment), feeding a multi-objective routing engine: *fastest / smoothest / coolest / balanced*.

Target: cars and two-wheelers; first users: delivery riders in Indian cities.

> **Honesty labels:** sample road topology is marked `sample`; thermal output is a *UTCI-inspired proxy estimate* — not measured WBGT/UTCI and never a rider's body temperature; vision v1 is a heuristic, not a trained model. See Known limitations.

## Run the prototype (one process, no Docker)

```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn backend.api.main:app --port 8000
# open http://localhost:8000  (dashboard)  •  http://localhost:8000/docs (OpenAPI)
python3 -m pytest -q
```

**2.0 additions:** persistent SQLite store (PostGIS DDL in `migrations/`), secure auth (`/api/auth/login`, Bearer required to verify defects), DSP v2 (`/api/telemetry/features`), OSM ingestion (`scripts/import_osm.py`), polygon shadows, arrival-time routing (`POST /api/route/timed` with `depart_at`), Yen distinct alternatives, Android Gradle project in `apps/mobile`. Still not claimed: trained vision model, live Overpass fetch (upstream 502 at audit time), cloud deployment, field validation.

## What's implemented

| Area | Status |
|---|---|
| Telemetry ingestion + anomaly candidates | ✅ heuristic v1, suspected ≠ confirmed |
| Crowd confidence / duplicate & status lifecycle | ✅ unverified→suspected→confirmed→stale, 14-day revalidation (configurable) |
| Vision image analysis | ⚠️ heuristic v1 (labelled, not trained ML); eval harness included |
| Solar position, building/tree shade | ✅ NOAA approx; canopy must overhang path |
| Thermal exposure | ✅ per-segment UTCI-inspired proxy + cumulative dose, two-wheeler/car configs |
| Routing | ✅ Dijkstra, A*, weight normalisation, hysteresis; Bellman-Ford/Floyd–Warshall/Kruskal as analysis tools |
| Weather | ✅ Open-Meteo adapter (no key) with labelled fallback |
| Navigation handoff | ✅ Google Maps / Mappls links with explicit limitations (custom geometry not guaranteed) |
| Dashboard | ✅ Leaflet map, defects, route comparison, thermal panel |
| Mobile | ⚠️ Kotlin skeleton in `apps/mobile` (needs Android Studio/device) |
| DB | ⚠️ prototype in-memory/SQLite-ready; PostGIS schema documented, not yet migrated |

## Layout
`backend/{api,telemetry,computer_vision,thermal_intelligence,routing,geospatial}` • `apps/{dashboard,mobile}` • `ml/` • `docs/` • `tests/`

## Contributing / License
See [CONTRIBUTING.md](CONTRIBUTING.md). MIT — see [LICENSE](LICENSE).
