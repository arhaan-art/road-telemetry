"""Fetch a bounded OSM area via Overpass and write graph JSON. Licence: ODbL, (c) OpenStreetMap contributors.
Usage: python3 scripts/import_osm.py --bbox 12.96,77.58,12.99,77.62 --out data/osm_graph.json"""
import argparse, json, sys
sys.path.insert(0,".")
from backend.geospatial.osm import fetch_bbox, connectivity
p=argparse.ArgumentParser(); p.add_argument("--bbox",default="12.96,77.58,12.99,77.62"); p.add_argument("--out",default="data/osm_graph.json"); a=p.parse_args()
s,w,n,e=[float(x) for x in a.bbox.split(",")]
r=fetch_bbox(s,w,n,e); print(connectivity(r["edges"]))
import os; os.makedirs("data",exist_ok=True); json.dump(r["edges"],open(a.out,"w")); print(f"wrote {len(r['edges'])} edges -> {a.out} (source: OpenStreetMap, ODbL)")
