"""Stream-crop a large .osm / .osm.gz city extract to a bounded bbox, writing a small .osm XML
parseable by backend.geospatial.osm_xml. Keeps: nodes in bbox, ways whose nodes are kept, relations dropped.
Usage: python3 scripts/crop_extract.py --in /tmp/NewDelhi.osm.gz --bbox 28.618,77.205,28.640,77.230 --out data/bounded_delhi.osm"""
import argparse, gzip, xml.etree.ElementTree as ET
def crop(src,out,bbox):
    s,w,n,e=bbox; kept=set(); counts={"node":0,"way":0}
    op=gzip.open(src,"rb") if src.endswith(".gz") else open(src,"rb")
    with op, open(out,"wb") as fh:
        fh.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6" generator="road-telemetry-crop">\n')
        fh.write(f'<bounds minlat="{s}" minlon="{w}" maxlat="{n}" maxlon="{e}"/>\n'.encode())
        ctx=ET.iterparse(op,events=("end",))
        for _,el in ctx:
            if el.tag=="node":
                lat,lon=float(el.get("lat")),float(el.get("lon"))
                if s<=lat<=n and w<=lon<=e: kept.add(el.get("id")); fh.write(ET.tostring(el)); counts["node"]+=1
                el.clear()
            elif el.tag=="way":
                refs=[nd.get("ref") for nd in el.findall("nd")]
                if refs and sum(r in kept for r in refs)>=max(2,len(refs)//2): fh.write(ET.tostring(el)); counts["way"]+=1
                el.clear()
            elif el.tag in ("relation","bounds"): el.clear()
        fh.write(b"</osm>\n")
    return counts
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--in",dest="src",required=True); p.add_argument("--out",required=True)
    p.add_argument("--bbox",default="28.618,77.205,28.640,77.230"); a=p.parse_args()
    print(crop(a.src,a.out,[float(x) for x in a.bbox.split(",")]))
