"""Polygon building shadows: project footprint along shadow vector, sample road segment. Pure-python (no shapely dependency); ENU metres."""
import math
def _enu(lat,lon,lat0,lon0): return (math.radians(lon-lon0)*6371000*math.cos(math.radians(lat0)), math.radians(lat-lat0)*6371000)
def _ll(x,y,lat0,lon0): return (lat0+math.degrees(y/6371000), lon0+math.degrees(x/(6371000*math.cos(math.radians(lat0)))))
def shadow_vector(height_m,elev_deg,azim_deg):
    if elev_deg<=0: return (0.0,0.0,float("inf"))
    L=height_m/math.tan(math.radians(elev_deg)); direction=math.radians((azim_deg+180)%360)
    # azimuth from north clockwise: x=east, y=north
    return (L*math.sin(direction), L*math.cos(direction), L)
def _inside(pt,poly):
    x,y=pt; inside=False; n=len(poly)
    for i in range(n):
        x1,y1=poly[i]; x2,y2=poly[(i+1)%n]
        if (y1>y)!=(y2>y) and x < (x2-x1)*(y-y1)/(y2-y1+1e-12)+x1: inside=not inside
    return inside
def segment_shade_polygon(seg,buildings,trees,elev_deg,azim_deg,samples=25):
    """buildings: [{footprint:[(lat,lon)...],height_m}] trees:[{canopy:[(lat,lon)...]}]. Returns fraction of sampled travel points in any shadow/canopy."""
    if elev_deg<=0: return {"shade_frac":1.0,"method":"night_no_direct_sun"}
    lat0,lon0=seg["from_lat"],seg["from_lon"]
    a=_enu(seg["from_lat"],seg["from_lon"],lat0,lon0); b=_enu(seg["to_lat"],seg["to_lon"],lat0,lon0)
    polys=[]
    for bd in buildings:
        if not bd.get("height_m"): continue
        dx,dy,L=shadow_vector(bd["height_m"],elev_deg,azim_deg)
        fp=[_enu(p[0],p[1],lat0,lon0) for p in bd["footprint"]]
        shifted=[(x+dx,y+dy) for x,y in fp]
        # shadow quad strip: original + shifted footprint hull approximation = both polys + edge quads sampled via both polys
        polys.append(fp); polys.append(shifted)
        for i in range(len(fp)):
            polys.append([fp[i],fp[(i+1)%len(fp)],shifted[(i+1)%len(fp)],shifted[i]])
    for t in trees: polys.append([_enu(p[0],p[1],lat0,lon0) for p in t["canopy"]])
    shaded=0
    for i in range(samples):
        f=i/(samples-1) if samples>1 else 0; pt=(a[0]+(b[0]-a[0])*f, a[1]+(b[1]-a[1])*f)
        if any(_inside(pt,p) for p in polys): shaded+=1
    return {"shade_frac":round(shaded/samples,3),"shaded_samples":shaded,"samples":samples,"method":"polygon_projection_sampling","buildings":len(buildings),"trees":len(trees)}
