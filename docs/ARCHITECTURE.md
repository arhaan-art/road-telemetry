# Architecture
Modular monolith (one FastAPI process): api → telemetry | computer_vision | thermal_intelligence | routing | geospatial. Road segment is the shared unit. Extract services only on proven scaling need. Prototype store is in-memory; production target PostgreSQL+PostGIS (DATABASE_URL), S3-compatible media, GitHub Actions CI.
