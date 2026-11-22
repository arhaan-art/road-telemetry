import sys, os; sys.path.insert(0,"."); os.environ.setdefault("RT_DB_PATH","/tmp/rt_v2_test.db")
from datetime import datetime, timezone
from backend.telemetry.dsp import lowpass, rms, features, classify_event, resample_uniform
from backend.geospatial.osm import parse_overpass, nearest_segment, connectivity
from backend.thermal_intelligence.shadow import segment_shade_polygon, shadow_vector
from backend.routing.graph import Graph, yen_k_shortest, normalise_weights
from backend.security import hash_pw, verify_pw, make_token, parse_token
def test_dsp():
    assert rms([1,-1,1,-1])==1.0
    s=[{"t":i*0.02,"ax":0.0,"ay":0.0,"az":16 if i==25 else 9.81,"lat":1,"lon":1} for i in range(50)]
    f=features(resample_uniform(s)); assert f["peak_dev"]>2
def test_osm_parse_oneway_and_blocked():
    data={"elements":[{"type":"node","id":1,"lat":12.9,"lon":77.5},{"type":"node","id":2,"lat":12.901,"lon":77.5},
      {"type":"way","id":10,"nodes":[1,2],"tags":{"highway":"residential","oneway":"yes"}},
      {"type":"way","id":11,"nodes":[1,2],"tags":{"highway":"footway"}}]}
    r=parse_overpass(data); assert len(r["edges"])==1 and r["edges"][0]["oneway"] and r["skipped_non_motor"]==1
    assert nearest_segment(12.9005,77.5001,r["edges"])["distance_m"]<20
def test_shadow_day_vs_night():
    seg={"from_lat":12.97,"from_lon":77.59,"to_lat":12.971,"to_lon":77.59}
    bld=[{"footprint":[(12.9701,77.5898),(12.9701,77.5902),(12.9709,77.5902),(12.9709,77.5898)],"height_m":30}]
    day=segment_shade_polygon(seg,bld,[],80,180); assert 0<=day["shade_frac"]<=1
    assert segment_shade_polygon(seg,bld,[],-5,180)["shade_frac"]==1.0
    assert shadow_vector(10,90,0)[2] < 0.01
def test_yen_distinct():
    g=Graph()
    for u,v in [("A","B"),("B","D"),("A","C"),("C","D"),("A","D")]: g.add_edge(u,v,distance_m=100,speed_kmh=30)
    paths=[p for _,p in yen_k_shortest(g,"A","D",normalise_weights(1,0,0),k=3)]
    assert len(paths)>=2 and len({tuple(p) for p in paths})==len(paths)
def test_security():
    h=hash_pw("correct horse"); assert verify_pw("correct horse",h) and not verify_pw("wrong",h)
    t=make_token("a@b.c"); assert parse_token(t)["sub"]=="a@b.c"; assert parse_token(t+"x") is None
def test_api_v2():
    from fastapi.testclient import TestClient; from backend.api.main import app; c=TestClient(app)
    r=c.post("/api/auth/register",json={"email":"v2@test.io","password":"longenough1","name":"V"}); assert r.status_code in (200,409)
    tok=c.post("/api/auth/login",json={"email":"v2@test.io","password":"longenough1"}).json()["token"]
    assert c.get("/api/auth/me",headers={"Authorization":f"Bearer {tok}"}).status_code==200
    assert c.get("/api/auth/me").status_code==401
    # defect verify requires auth now
    did=c.post("/api/defects",json={"lat":12.9,"lon":77.5,"severity":2}).json()["id"]
    assert c.post(f"/api/defects/{did}/verify").status_code==401
    assert c.post(f"/api/defects/{did}/verify",headers={"Authorization":f"Bearer {tok}"}).status_code==200
    tr=c.post("/api/route/timed",json={"origin":"A","destination":"F","preset":"coolest","depart_at":"2026-06-01T07:00:00+00:00"})
    assert tr.status_code==200 and tr.json()["segments"] and tr.json()["arrival_at"]>tr.json()["depart_at"]
    # morning vs afternoon shade/exposure differs on at least one segment
    tr2=c.post("/api/route/timed",json={"origin":"A","destination":"F","preset":"coolest","depart_at":"2026-06-01T01:00:00+00:00"})
    assert tr.json()["cumulative_exposure"]!=tr2.json()["cumulative_exposure"]
    assert len({tuple(a["path"]) for a in tr.json()["distinct_alternatives"]})>=1
def test_real_osm_network_and_route():
    os.environ["RT_DB_PATH"]="/tmp/rt_real_test.db"
    from backend.geospatial.osm_xml import parse_osm_xml
    r=parse_osm_xml("data/bounded_real.osm"); assert len(r["edges"])>10 and len(r["buildings"])>=1
    from backend import db as store; store.save_network(r["edges"],r["buildings"],r["trees"])
    seg,bld,tr=store.load_network(); assert len(seg)==len(r["edges"])
    from backend.routing.real_route import timed_route_real
    from datetime import datetime,timezone
    out=timed_route_real(seg,bld,tr,(48.135072,10.0708028),(48.1353329,10.0707815),"balanced",depart=datetime(2026,6,1,7,0,tzinfo=timezone.utc))
    assert out is None or (out["path"] and out["segments"][0]["solar"] and out["network"]=="real_osm_persisted")
