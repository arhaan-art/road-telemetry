"""Route on persisted real OSM segments: nearest-node snapping, oneway respected, arrival-time thermal with real buildings/trees."""
from backend.routing.graph import Graph, dijkstra, yen_k_shortest, normalise_weights, PRESETS, summarise
from backend.geospatial.geo import haversine_m
from backend.thermal_intelligence.solar import timed_segment_exposure
from datetime import timedelta
SPEED={"residential":25,"service":15,"track":15,"unclassified":30,"tertiary":35,"secondary":40,"primary":45,"living_street":15}
def build_real_graph(segments):
    g=Graph(); coords={}
    for e in segments:
        sp=SPEED.get(e["highway"],25); u,v=str(e["from_id"]),str(e["to_id"]); coords[u]=(e["from_lat"],e["from_lon"]); coords[v]=(e["to_lat"],e["to_lon"])
        kw=dict(distance_m=e["distance_m"] or haversine_m(e["from_lat"],e["from_lon"],e["to_lat"],e["to_lon"]),speed_kmh=sp,pothole_penalty=e.get("pothole_penalty") or 0,shade_frac=e.get("shade_frac") or 0,name=e["name"])
        g.add_edge(u,v,**kw)
        if not e["oneway"]: g.add_edge(v,u,**kw)
    return g,coords
def nearest_node(lat,lon,coords):
    return min(coords, key=lambda n: haversine_m(lat,lon,coords[n][0],coords[n][1]))
def _near(seg,items,key,pad=0.0015):
    mlat=(seg["from_lat"]+seg["to_lat"])/2; mlon=(seg["from_lon"]+seg["to_lon"])/2
    out=[]
    for it in items:
        pts=it[key]
        if any(abs(p[0]-mlat)<pad and abs(p[1]-mlon)<pad for p in pts): out.append(it)
    return out
def timed_route_real(segments,buildings,trees,origin,dest,preset="balanced",custom=(0.34,0.33,0.33),depart=None,temp_c=32,rh=45,wind_ms=2,solar_wm2=800,cloud_frac=0,vehicle="two_wheeler"):
    g,coords=build_real_graph(segments)
    o=nearest_node(origin[0],origin[1],coords); d=nearest_node(dest[0],dest[1],coords)
    w=normalise_weights(*(PRESETS[preset] if preset!="custom" else custom))
    cost,path=dijkstra(g,o,d,w)
    if not path: return None
    segs=[]; t=depart; dose=0.0; shaded=0.0
    seg_by_pair={}
    for e in segments: seg_by_pair.setdefault((str(e["from_id"]),str(e["to_id"])),e); seg_by_pair.setdefault((str(e["to_id"]),str(e["from_id"])),e)
    for a,b in zip(path,path[1:]):
        e=g.edges.get((a,b)) or g.edges.get((b,a)); raw=seg_by_pair.get((a,b),{})
        seg={"from_lat":coords[a][0],"from_lon":coords[a][1],"to_lat":coords[b][0],"to_lon":coords[b][1],"travel_s":e["travel_s"],"speed_kmh":e["speed_kmh"],"shade_frac":e["shade_frac"]}
        nb=_near(seg,buildings,"footprint"); nt=_near(seg,trees,"canopy")
        # buildings missing height: cautious 6m at low confidence, labelled in output
        nb=[{**x,"height_m":x["height_m"] or 6.0} for x in nb]
        r=timed_segment_exposure(seg,t,temp_c,rh,wind_ms,90,solar_wm2,cloud_frac,nb,nt,vehicle)
        r["from"],r["to"],r["name"],r["buildings_used"],r["trees_used"]=a,b,e["name"],len(nb),len(nt)
        segs.append(r); dose+=r["exposure_dose"]; shaded+=r["shade_frac"]*e["travel_s"]; t=t+timedelta(seconds=e["travel_s"])
    alts=[]
    seen={tuple(path)}
    for c,p in yen_k_shortest(build_real_graph(segments)[0],o,d,w,k=3):
        if tuple(p) not in seen: seen.add(tuple(p)); alts.append({"path":p,"cost":round(c,4)})
    return {"origin_node":o,"destination_node":d,"path":path,"coords":[[coords[n][1],coords[n][0]] for n in path],
            "depart_at":depart.isoformat(),"arrival_at":t.isoformat(),"segments":segs,"cumulative_exposure":round(dose,1),
            "shaded_duration_s":round(shaded,1),"distinct_alternatives":alts,"network":"real_osm_persisted","geometry_source":"OpenStreetMap (ODbL)"}
