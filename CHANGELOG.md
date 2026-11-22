# Changelog
## 0.1.0 — 2026-11-22
Initial end-to-end prototype: telemetry anomaly candidates, vision heuristic, solar/shade + thermal proxy, multi-objective routing, dashboard, CI.
## 2.0.0-dev — 2026-11-22
SQLite persistence (+PostGIS DDL migration), PBKDF2 auth + signed expiring tokens + protected verify, telemetry DSP v2, OSM Overpass parser/ingestion (live fetch currently 502 upstream — fixture-tested), polygon building shadows, arrival-time timed routing, Yen distinct alternatives, Android Gradle project, dashboard departure-time selector. Vision remains heuristic; no trained model claimed.
## 2.1.0 — 2026-11-22
Real New Delhi network replaces Augsburg fixture: BBBike NewDelhi city extract (OSM, ODbL) stream-cropped to Connaught Place bbox via scripts/crop_extract.py -> data/bounded_delhi.osm (7,296 segments, 1,479 buildings, 74 trees). Arrival-time routing demonstrated on it (exposure differs morning vs afternoon); polygon shade hits verified on real geometry.
