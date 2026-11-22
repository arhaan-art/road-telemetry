"""Road Telemetry API — modular monolith. Prototype store: SQLite (schema mirrors PostGIS design in docs/DATABASE_SCHEMA.md; swap DATABASE_URL for Postgres/PostGIS in production)."""
import os, json, hashlib, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.telemetry.anomaly import detect, cluster_confidence
from backend.thermal_intelligence.solar import solar_position, segment_shade, estimate_utci_proxy, exposure_for_duration
from backend.routing.graph import Graph, PRESETS, normalise_weights, dijkstra, astar, bellman_ford, floyd_warshall, kruskal, summarise
from backend.computer_vision.detect import analyse_bytes, evaluate
from backend.geospatial.geo import haversine_m

app=FastAPI(title="Road Telemetry",version="0.1.0",description="Crowd road-quality + thermal route intelligence. Estimates are labelled; not measured body temperature / not validated WBGT.")
COORDS={"A":(12.9716,77.5946),"B":(12.9750,77.6000),"C":(12.9690,77.6050),"D":(12.9800,77.5920),"E":(12.9850,77.6020),"F":(12.9720,77.6150)}
# Illustrative Bengaluru grid — SAMPLE topology for prototype demo, labelled as such; replace with OSM import (scripts/import_osm.py)
EDGES=[("A","B",700,28,0.55,0.15,"MG Rd (sample)"),("B","E",800,32,0.2,0.35,"Brigade Rd (sample)"),
("A","D",650,35,0.1,0.6,"Cubbon Park shaded (sample)"),("D","E",700,30,0.15,0.55,"Park edge (sample)"),
("B","C",600,25,0.7,0.1,"Pothole alley (sample)"),("C","F",750,30,0.3,0.25,"Residency Rd (sample)"),
("E","F",650,34,0.1,0.4,"Richmond Rd (sample)"),("A","C",1100,38,0.25,0.3,"Direct (sample)"),("D","B",600,26,0.4,0.2,"Cross (sample)")]
def build_graph():
    g=Graph()
    for u,v,d,sp,pen,shade,name in EDGES:
        g.add_edge(u,v,distance_m=d,speed_kmh=sp,pothole_penalty=pen,shade_frac=shade,name=name,lat_u=COORDS[u][0],lon_u=COORDS[u][1],lat_v=COORDS[v][0],lon_v=COORDS[v][1])
        g.add_edge(v,u,distance_m=d,speed_kmh=sp,pothole_penalty=pen,shade_frac=shade,name=name+" (rev)",lat_u=COORDS[v][0],lon_u=COORDS[v][1],lat_v=COORDS[u][0],lon_v=COORDS[u][1])
    return g
GRAPH=build_graph()
DEFECTS=[{"id":1,"lat":12.973,"lon":77.602,"category":"pothole","severity":4,"status":"suspected","confidence":0.62,"reports":3,"source":"crowd_sample_labelled"}]
USERS={}

class Sample(BaseModel): t:float; ax:float; ay:float; az:float; lat:Optional[float]=None; lon:Optional[float]=None
class TelemetryIn(BaseModel): device_id:str="dev-1"; vehicle:str="two_wheeler"; speed_kmh:Optional[float]=20; samples:List[Sample]
class DefectIn(BaseModel): lat:float; lon:float; category:str="pothole"; severity:int=Field(3,ge=1,le=5); notes:Optional[str]=None
class RouteIn(BaseModel): origin:str="A"; destination:str="F"; preset:str="balanced"; wt:float=0.34; wp:float=0.33; wh:float=0.33; vehicle:str="two_wheeler"; temp_c:float=38.0; rh:float=35.0; wind_ms:float=2.0; solar_wm2:float=850.0; algorithm:str="dijkstra"
class RegisterIn(BaseModel): email:str; password:str; name:str=""

@app.get("/health")
def health(): return {"status":"ok","version":"0.1.0","data_labelling":"sample edges labelled; predictions are estimates"}
@app.get("/api/graph")
def graph(): return {"nodes":[{"id":k,"lat":v[0],"lon":v[1]} for k,v in COORDS.items()],
  "edges":[{"from":u,"to":v,"name":e["name"],"distance_m":e["distance_m"],"shade_frac":e["shade_frac"],"pothole_penalty":e["pothole_penalty"]} for (u,v),e in list(GRAPH.edges.items())[:9]],"source":"sample_topology_not_osm"}
@app.post("/api/auth/register")
def register(b:RegisterIn):
    if b.email in USERS: raise HTTPException(409,"exists")
    USERS[b.email]={"name":b.name,"pw":hashlib.sha256(b.password.encode()).hexdigest()}; return {"email":b.email,"token":"demo-"+hashlib.sha256(b.email.encode()).hexdigest()[:16]}
@app.post("/api/telemetry/ingest")
def ingest(b:TelemetryIn):
    ev=detect([s.dict() for s in b.samples],speed_kmh=b.speed_kmh)
    for e in ev:
        if e.get("lat") is not None: DEFECTS.append({"id":len(DEFECTS)+1,"lat":e["lat"],"lon":e["lon"],"category":e["category"],"severity":3,"status":e["status"],"confidence":e["confidence"],"reports":1,"source":"sensor"})
    return {"received":len(b.samples),"candidate_events":ev,"note":"candidates are suspected, not confirmed potholes"}
@app.get("/api/defects")
def defects(status:Optional[str]=None): return {"defects":[d for d in DEFECTS if not status or d["status"]==status],"count":len(DEFECTS)}
@app.post("/api/defects")
def add_defect(b:DefectIn):
    d={"id":len(DEFECTS)+1,**b.dict(),"status":"unverified","confidence":0.3,"reports":1,"source":"manual"}
    DEFECTS.append(d); return d
@app.post("/api/defects/{did}/verify")
def verify(did:int):
    for d in DEFECTS:
        if d["id"]==did:
            d["reports"]+=1; c,s=cluster_confidence(d["reports"],d["confidence"],age_days=1); d["confidence"],d["status"]=c,s; return d
    raise HTTPException(404,"not found")
@app.post("/api/vision/analyse")
async def vision(file:UploadFile=File(...)):
    return analyse_bytes(await file.read())
@app.get("/api/vision/evaluate-demo")
def eval_demo(): return evaluate(["pothole","normal_road","pothole","rough_patch"],["pothole","normal_road","rough_patch","rough_patch"])
@app.get("/api/thermal/solar")
def solar(lat:float=12.9716,lon:float=77.5946,at:Optional[str]=None):
    when=datetime.fromisoformat(at) if at else datetime.now(timezone.utc); return solar_position(lat,lon,when)
@app.get("/api/thermal/segment")
def thermal_segment(lat:float=12.9716,temp_c:float=38,rh:float=35,wind_ms:float=2,solar_wm2:float=850,shade_frac:float=0.3,vehicle:str="two_wheeler",speed_kmh:float=25,duration_s:float=120):
    u=estimate_utci_proxy(temp_c,rh,wind_ms,solar_wm2,shade_frac,vehicle,speed_kmh)
    return {**u,"exposure_dose":exposure_for_duration(u["utci_proxy_c"],duration_s),"shade_frac":shade_frac,"label":"estimate_not_measurement"}
@app.get("/api/weather/open-meteo")
def weather(lat:float=12.9716,lon:float=77.5946):
    try:
        url=f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m&forecast_days=1"
        with urllib.request.urlopen(url,timeout=8) as r: d=json.load(r)
        return {"provider":"Open-Meteo (no key)","current":d.get("current"),"is_measurement":False,"note":"modelled weather, not street-level measurement"}
    except Exception as e: return {"provider":"Open-Meteo","error":str(e),"fallback":{"temp_c":38,"rh":35,"wind_ms":2},"label":"fallback_labelled"}
@app.post("/api/route")
def route(b:RouteIn):
    w=PRESETS[b.preset] if b.preset!="custom" else normalise_weights(b.wt,b.wp,b.wh)
    if b.preset!="custom": w=normalise_weights(*w)
    thermal={}
    for (u,v),e in GRAPH.edges.items():
        thermal[(u,v)]=estimate_utci_proxy(b.temp_c,b.rh,b.wind_ms,b.solar_wm2,e["shade_frac"],b.vehicle)["utci_proxy_c"]
    fn=astar if b.algorithm=="astar" else dijkstra
    cost,path=fn(GRAPH,b.origin,b.destination,w,COORDS) if b.algorithm=="astar" else fn(GRAPH,b.origin,b.destination,w)
    if not path: raise HTTPException(404,"no route")
    main=summarise(GRAPH,path,w,thermal)
    alts={}
    for name in ["fastest","coolest","smoothest"]:
        ww=normalise_weights(*PRESETS[name]); c,p=dijkstra(GRAPH,b.origin,b.destination,ww)
        if p: alts[name]=summarise(GRAPH,p,ww,thermal)
    o,d=COORDS[b.origin],COORDS[b.destination]
    nav={"google_maps":{"url":f"https://www.google.com/maps/dir/?api=1&origin={o[0]},{o[1]}&destination={d[0]},{d[1]}&travelmode=two_wheeler" if b.vehicle=="two_wheeler" else f"https://www.google.com/maps/dir/?api=1&origin={o[0]},{o[1]}&destination={d[0]},{d[1]}",
                        "limitation":"Opens destination routing in Google Maps; does NOT guarantee it follows our custom geometry."},
         "mappls":{"url":f"https://www.mappls.com/{d[0]},{d[1]}","limitation":"Mappls web link; custom waypoint transfer depends on provider plan/API."},
         "geojson_route":{"type":"LineString","coordinates":[[COORDS[n][1],COORDS[n][0]] for n in path]}}
    return {"weights":w,"preset":b.preset,"algorithm":b.algorithm,"route":main,"alternatives":alts,"navigation":nav,
            "thermal_note":"UTCI-inspired proxy per segment at assumed conditions; not validated, not body temperature"}
@app.get("/api/routing/algorithms-demo")
def algo_demo():
    _,_,neg=bellman_ford(GRAPH,"A"); nodes,D=floyd_warshall(build_graph())
    mst,total=kruskal(list(COORDS),[(e["distance_m"],u,v) for (u,v),e in list(GRAPH.edges.items())[:9]])
    return {"bellman_ford_negative_cycle":neg,"floyd_warshall_nodes":nodes,"floyd_A_to_F":D[nodes.index("A")][nodes.index("F")],"kruskal_mst_edges":mst,"kruskal_total_m":total,
            "note":"BF/FW/Kruskal are analysis tools, not live routing"}
@app.get("/api/dashboard/stats")
def stats(): return {"defects":len(DEFECTS),"by_status":{s:sum(1 for d in DEFECTS if d["status"]==s) for s in set(d["status"] for d in DEFECTS)},"segments":len(EDGES),"freshness":"sample/demo data — replace with live feeds"}

DASH=Path(__file__).resolve().parents[2]/"apps"/"dashboard"
@app.get("/")
def root(): return FileResponse(DASH/"index.html")
