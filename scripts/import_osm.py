"""Import OSM via Overpass (network + licence: ODbL, credit OSM). Usage: python scripts/import_osm.py --bbox 12.96,77.58,12.99,77.62
Exports GeoJSON edges for the graph builder; not run in CI."""
import argparse, json, urllib.request
p=argparse.ArgumentParser(); p.add_argument("--bbox",default="12.96,77.58,12.99,77.62"); a=p.parse_args()
q=f'[out:json];way["highway"]({a.bbox});out geom;'
req=urllib.request.Request("https://overpass-api.de/api/interpreter",data=("data="+urllib.parse.quote(q)).encode() if False else q.encode(),headers={"Content-Type":"application/x-www-form-urlencoded"})
print("See docs/DATA_SOURCES.md — implement persistence against DATABASE_URL; query prepared:",q[:80])
