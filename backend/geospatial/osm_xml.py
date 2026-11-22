"""Parse .osm XML (real OSM extracts) -> edges, buildings, trees. Source data: OSM, ODbL."""
import xml.etree.ElementTree as ET, math
from backend.geospatial.geo import haversine_m
BLOCKED={"footway","path","cycleway","steps","pedestrian"}
def _tags(el): return {t.get("k"):t.get("v") for t in el.findall("tag")}
def parse_osm_xml(path):
    root=ET.parse(path).getroot()
    nodes={}
    for n in root.findall("node"): nodes[n.get("id")]=(float(n.get("lat")),float(n.get("lon")),_tags(n))
    edges=[]; buildings=[]; trees=[]
    for w in root.findall("way"):
        tags=_tags(w); refs=[nd.get("ref") for nd in w.findall("nd")]; pts=[nodes[r][:2] for r in refs if r in nodes]; ids=[r for r in refs if r in nodes]
        if "building" in tags and len(pts)>=3:
            levels=tags.get("building:levels"); h=float(tags["height"]) if tags.get("height") else (float(levels)*3.0 if levels else None)
            buildings.append({"footprint":pts,"height_m":h,"height_confidence":0.8 if tags.get("height") else (0.4 if levels else 0.2),"osm_id":w.get("id")}); continue
        hw=tags.get("highway")
        if not hw or (hw in BLOCKED and tags.get("motor_vehicle")!="yes"): continue
        oneway=tags.get("oneway") in ("yes","true","1")
        for (a,b),(ia,ib) in zip(zip(pts,pts[1:]),zip(ids,ids[1:])):
            edges.append({"from_id":ia,"to_id":ib,"from_lat":a[0],"from_lon":a[1],"to_lat":b[0],"to_lon":b[1],
              "name":tags.get("name",hw),"highway":hw,"oneway":oneway,"distance_m":round(haversine_m(a[0],a[1],b[0],b[1]),1)})
    for nid,(lat,lon,tags) in nodes.items():
        if tags.get("natural")=="tree":
            r=4.0  # labelled approximation where canopy surveyed data absent
            canopy=[(lat+math.degrees((r/6371000)*math.cos(math.radians(a))), lon+math.degrees((r/6371000)*math.sin(math.radians(a))/math.cos(math.radians(lat)))) for a in range(0,360,45)]
            trees.append({"canopy":canopy,"osm_id":nid,"canopy_confidence":0.3,"approximation":"4m radius assumed"})
    return {"edges":edges,"buildings":buildings,"trees":trees,"node_count":len(nodes)}
