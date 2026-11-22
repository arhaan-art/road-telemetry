import sys; sys.path.insert(0,".")
from datetime import datetime,timezone
from backend.telemetry.anomaly import detect, cluster_confidence
from backend.thermal_intelligence.solar import solar_position, segment_shade, estimate_utci_proxy
from backend.routing.graph import Graph, dijkstra, astar, bellman_ford, floyd_warshall, kruskal, normalise_weights, should_switch, PRESETS
from backend.computer_vision.detect import evaluate
from backend.geospatial.geo import haversine_m
def g():
    x=Graph(); x.add_edge("A","B",distance_m=100,speed_kmh=36,pothole_penalty=0.9,shade_frac=0.0,name="bad")
    x.add_edge("A","C",distance_m=150,speed_kmh=36,pothole_penalty=0.0,shade_frac=1.0,name="good"); x.add_edge("C","B",distance_m=150,speed_kmh=36,pothole_penalty=0.0,shade_frac=1.0,name="good2"); return x
def test_weights_sum(): assert abs(sum(normalise_weights(2,1,1))-1)<1e-9
def test_smoothest_avoids_pothole():
    _,p=dijkstra(g(),"A","B",normalise_weights(*PRESETS["smoothest"])); assert p==["A","C","B"]
def test_fastest_direct():
    _,p=dijkstra(g(),"A","B",normalise_weights(*PRESETS["fastest"])); assert p==["A","B"]
def test_astar_matches_dijkstra():
    coords={"A":(0,0),"B":(1000,0),"C":(500,100)}; c1,_=dijkstra(g(),"A","B",normalise_weights(*PRESETS["balanced"])); c2,p=astar(g(),"A","B",normalise_weights(*PRESETS["balanced"]),coords); assert abs(c1-c2)<1e-6
def test_bf_fw_kruskal():
    _,_,neg=bellman_ford(g(),"A"); assert not neg
    n,D=floyd_warshall(g()); assert D[n.index("A")][n.index("B")]>0
    mst,t=kruskal(["A","B","C"],[(100,"A","B"),(150,"A","C"),(150,"C","B")]); assert len(mst)==2
def test_hysteresis(): assert not should_switch(100,97); assert should_switch(100,90)
def test_solar_noon_higher():
    a=solar_position(12.97,77.59,datetime(2026,6,1,6,30,tzinfo=timezone.utc)); b=solar_position(12.97,77.59,datetime(2026,6,1,1,0,tzinfo=timezone.utc)); assert a["elevation_deg"]>b["elevation_deg"]
def test_shade_and_utci():
    assert segment_shade(90,[{"height_m":20,"lateral_offset_m":5,"along_fraction":0.5}],[],60,180)>=0
    hot=estimate_utci_proxy(40,30,1,900,0.0); cool=estimate_utci_proxy(40,30,1,900,0.9); assert cool["utci_proxy_c"]<hot["utci_proxy_c"]
def test_anomaly_detects_bump():
    s=[{"t":i*0.1,"ax":0.1,"ay":0.1,"az":16 if i==5 else 9.8,"lat":12.9,"lon":77.5} for i in range(10)]
    assert detect(s,speed_kmh=20)
def test_anomaly_quiet_road(): assert detect([{"t":i*0.1,"ax":0,"ay":0,"az":9.8} for i in range(10)])==[]
def test_cluster(): c,s=cluster_confidence(5,0.8,1); assert s=="confirmed" and c>0.7
def test_eval(): assert evaluate(["a","b"],["a","a"])["accuracy"]==0.5
def test_haversine(): assert 900<haversine_m(12.97,77.59,12.98,77.59)<1200
def test_api():
    from fastapi.testclient import TestClient; from backend.api.main import app; c=TestClient(app)
    assert c.get("/health").json()["status"]=="ok"
    r=c.post("/api/route",json={"origin":"A","destination":"F","preset":"coolest"}); assert r.status_code==200 and r.json()["route"]["path"]
    assert c.get("/api/thermal/solar").status_code==200
    assert c.post("/api/defects",json={"lat":12.9,"lon":77.5,"category":"pothole","severity":3}).status_code==200
