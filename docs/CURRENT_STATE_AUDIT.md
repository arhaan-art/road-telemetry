# Current State Audit (2026-11-22, verified)
Baseline: `pytest -q` = 14 passed; /health ok; CI green on main+develop. Branches main/develop at 49122cf.
Verified problems: (1) in-memory USERS/DEFECTS in backend/api/main.py — restart loses data; (2) unsalted SHA256 passwords, deterministic demo token; (3) 6-node sample graph, import_osm stub prints query only; (4) route thermal uses static shade_frac + one weather set for all edges (no arrival-time solar); (5) segment_shade is lateral-offset arithmetic, no polygons; (6) vision heuristic only; (7) Android is one commented file, no Gradle; (8) alternatives = preset re-runs, may duplicate; (9) no rate limit/upload limits/roles; (10) no PostGIS, no migrations.
Potential (not verified defects): in-memory graph fine up to ~10k edges; FastAPI sync weather call blocks — move to cache.
Preserved: modular monolith, labelling honesty, cost model, hysteresis, NOAA solar baseline, heuristic fallbacks.
