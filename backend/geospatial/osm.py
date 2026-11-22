"""OSM/Overpass parsing (offline-testable) + point-to-segment matching in local ENU metres."""
import math, json, urllib.request, urllib.parse
from backend.geospatial.geo import haversine_m
BLOCKED={"footway","path","cycleway","steps","pedestrian"}
def parse_overpass(data):
    nodes={e["id"]:(e["lat"],e["lon"]) for e in data.get("elements",[]) if e["type"]=="node"}
    edges=[]; skipped=0
    for e in data.get("elements",[]):
        if e["type"]!="way": continue
        tags=e.get("tags",{}); hw=tags.get("highway","")
        if hw in BLOCKED and tags.get("motor_vehicle")!="yes": skipped+=1; continue
        pts=[nodes[n] for n in e.get("nodes",[]) if n in nodes]
        oneway=tags.get("oneway") in ("yes","true","1")
        for a,b in zip(pts,pts[1:]):
            edges.append({"from_lat":a[0],"from_lon":a[1],"to_lat":b[0],"to_lon":b[1],"name":tags.get("name",hw),
                          "highway":hw,"oneway":oneway,"maxspeed":tags.get("maxspeed"),"osm_way_id":e["id"],
                          "distance_m":round(haversine_m(a[0],a[1],b[0],b[1]),1)})
    return {"edges":edges,"nodes":nodes,"skipped_non_motor":skipped}
def fetch_bbox(s,w,n,e,timeout=30):
    q=f'[out:json][timeout:25];way["highway"]({s},{w},{n},{e});out geom;'
    req=urllib.request.Request("https://overpass-api.de/api/interpreter",data=urllib.parse.urlencode({"data":q}).encode(),headers={"User-Agent":"RoadTelemetry/2.0 (https://github.com/arhaan-art/road-telemetry)","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r: return parse_overpass(json.load(r))
def connectivity(edges):
    seen={}
    for ed in edges:
        for k in ("from_lat","to_lat"): pass
    pts=set()
    for ed in edges: pts.add((round(ed["from_lat"],5),round(ed["from_lon"],5))); pts.add((round(ed["to_lat"],5),round(ed["to_lon"],5)))
    return {"distinct_junctions":len(pts),"edges":len(edges),"connected_hint":len(edges)>=len(pts)-1 if pts else False}
def _enu(lat,lon,lat0,lon0): return (math.radians(lon-lon0)*6371000*math.cos(math.radians(lat0)), math.radians(lat-lat0)*6371000)
def point_to_segment(lat,lon,seg):
    px,py=_enu(lat,lon,lat,lon); ax,ay=_enu(seg["from_lat"],seg["from_lon"],lat,lon); bx,by=_enu(seg["to_lat"],seg["to_lon"],lat,lon)
    dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy
    t=0 if L2==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L2))
    cx,cy=ax+t*dx,ay+t*dy; return {"distance_m":round(math.hypot(px-cx,py-cy),2),"along_fraction":round(t,3)}
def nearest_segment(lat,lon,edges):
    best=None
    for i,ed in enumerate(edges):
        r=point_to_segment(lat,lon,ed)
        if best is None or r["distance_m"]<best["distance_m"]: best={**r,"segment_index":i,"segment":ed}
    return best
