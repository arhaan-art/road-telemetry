"""Migrate users/defects/segments/buildings/trees from SQLite (RT source data/rt.db) to Postgres/PostGIS.
Requires DATABASE_URL=postgresql://... and migrations 001+002 executed. Idempotent for network (replace), defects/users inserted once per run — run against fresh PG tables."""
import os, sys, sqlite3, json
sys.path.insert(0,".")
os.environ.setdefault("DATABASE_URL","postgresql://rtadmin@127.0.0.1:5433/road_telemetry")
from backend import db as store
assert store._PG, "DATABASE_URL must point at Postgres"
src=sqlite3.connect(os.environ.get("RT_DB_PATH","data/rt.db")); src.row_factory=sqlite3.Row
users=0
for r in src.execute("SELECT * FROM users"):
    if store.create_user(r["email"],r["pw_hash"],r["name"] or ""): users+=1
defects=0
for r in src.execute("SELECT * FROM defects"):
    store.add_defect({"lat":r["lat"],"lon":r["lon"],"category":r["category"],"severity":r["severity"],"status":r["status"],"confidence":r["confidence"],"reports":r["reports"],"source":r["source"],"segment_id":None}); defects+=1
edges=[dict(r) for r in src.execute("SELECT * FROM road_segments")]
bld=[{"footprint":json.loads(r["footprint"]),"height_m":r["height_m"],"height_confidence":r["height_confidence"]} for r in src.execute("SELECT * FROM buildings_osm")]
trees=[{"canopy":json.loads(r["canopy"]),"canopy_confidence":r["canopy_confidence"]} for r in src.execute("SELECT * FROM trees_osm")]
store.save_network(edges,bld,trees)
seg,b,t=store.load_network()
print({"users":users,"defects":defects,"segments":len(seg),"buildings":len(b),"trees":len(t)})
