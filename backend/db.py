"""Persistence: SQLite for dev/tests (RT_DB_PATH), PostGIS DDL in migrations/001_postgis.sql for production.
Same repository API either way; geometries stored as WKT + lat/lon columns (GiST in PostGIS)."""
import sqlite3, os, json, threading
_PATH=os.environ.get("RT_DB_PATH","data/rt.db")
_lock=threading.Lock()
def conn():
    os.makedirs(os.path.dirname(_PATH) or ".",exist_ok=True)
    c=sqlite3.connect(_PATH); c.row_factory=sqlite3.Row
    c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE,pw_hash TEXT,name TEXT,role TEXT DEFAULT 'rider');
    CREATE TABLE IF NOT EXISTS defects(id INTEGER PRIMARY KEY,lat REAL,lon REAL,category TEXT,severity INT,status TEXT,confidence REAL,reports INT,source TEXT,segment_id TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS telemetry_events(id INTEGER PRIMARY KEY,device_id TEXT,payload TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,entity TEXT,entity_id INT,action TEXT,actor TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);""")
    return c
def create_user(email,pw_hash,name=""):
    with _lock, conn() as c:
        try: c.execute("INSERT INTO users(email,pw_hash,name) VALUES(?,?,?)",(email,pw_hash,name)); return True
        except sqlite3.IntegrityError: return False
def get_user(email):
    with conn() as c: r=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); return dict(r) if r else None
def add_defect(d):
    with _lock, conn() as c:
        cur=c.execute("INSERT INTO defects(lat,lon,category,severity,status,confidence,reports,source,segment_id) VALUES(?,?,?,?,?,?,?,?,?)",
            (d["lat"],d["lon"],d["category"],d["severity"],d["status"],d["confidence"],d["reports"],d["source"],d.get("segment_id")))
        return cur.lastrowid
def list_defects(status=None):
    with conn() as c:
        q="SELECT * FROM defects"+(" WHERE status=?" if status else ""); rows=c.execute(q,(status,) if status else ()).fetchall(); return [dict(r) for r in rows]
def get_defect(did):
    with conn() as c: r=c.execute("SELECT * FROM defects WHERE id=?",(did,)).fetchone(); return dict(r) if r else None
def update_defect(did,**kw):
    with _lock, conn() as c:
        c.execute("UPDATE defects SET "+",".join(f"{k}=?" for k in kw)+" WHERE id=?",(*kw.values(),did))
    return get_defect(did)
def log_audit(entity,eid,action,actor="system"):
    with _lock, conn() as c: c.execute("INSERT INTO audit(entity,entity_id,action,actor) VALUES(?,?,?,?)",(entity,eid,action,actor))
def seed_if_empty(sample):
    if not list_defects():
        for d in sample: add_defect(d)
def init_network_tables():
    with _lock, conn() as c:
        c.executescript("""CREATE TABLE IF NOT EXISTS road_segments(id TEXT,from_id TEXT,to_id TEXT,from_lat REAL,from_lon REAL,to_lat REAL,to_lon REAL,name TEXT,highway TEXT,oneway INT,distance_m REAL,shade_frac REAL DEFAULT 0,pothole_penalty REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS buildings_osm(id INTEGER PRIMARY KEY,footprint TEXT,height_m REAL,height_confidence REAL);
        CREATE TABLE IF NOT EXISTS trees_osm(id INTEGER PRIMARY KEY,canopy TEXT,canopy_confidence REAL);""")
def save_network(edges,buildings,trees):
    init_network_tables()
    with _lock, conn() as c:
        c.execute("DELETE FROM road_segments"); c.execute("DELETE FROM buildings_osm"); c.execute("DELETE FROM trees_osm")
        c.executemany("INSERT INTO road_segments VALUES(?,?,?,?,?,?,?,?,?,?,?,0,0)",[(f"{e['from_id']}-{e['to_id']}-{i}",e["from_id"],e["to_id"],e["from_lat"],e["from_lon"],e["to_lat"],e["to_lon"],e["name"],e["highway"],1 if e["oneway"] else 0,e["distance_m"]) for i,e in enumerate(edges)])
        c.executemany("INSERT INTO buildings_osm(footprint,height_m,height_confidence) VALUES(?,?,?)",[(json.dumps(b["footprint"]),b.get("height_m"),b.get("height_confidence",0.3)) for b in buildings])
        c.executemany("INSERT INTO trees_osm(canopy,canopy_confidence) VALUES(?,?)",[(json.dumps(t["canopy"]),t.get("canopy_confidence",0.3)) for t in trees])
def load_network():
    init_network_tables()
    with conn() as c:
        seg=[dict(r) for r in c.execute("SELECT * FROM road_segments").fetchall()]
        bld=[{"footprint":json.loads(r["footprint"]),"height_m":r["height_m"],"height_confidence":r["height_confidence"]} for r in c.execute("SELECT * FROM buildings_osm").fetchall()]
        tr=[{"canopy":json.loads(r["canopy"]),"canopy_confidence":r["canopy_confidence"]} for r in c.execute("SELECT * FROM trees_osm").fetchall()]
    return seg,bld,tr
