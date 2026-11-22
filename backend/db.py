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
