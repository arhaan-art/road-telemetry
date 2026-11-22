"""Solar position (NOAA approximation, ~0.01-0.1 deg) + building/tree shade. Estimates, not measurements."""
import math
from datetime import datetime, timezone
def solar_position(lat,lon,when:datetime):
    if when.tzinfo is None: when=when.replace(tzinfo=timezone.utc)
    doy=when.timetuple().tm_yday
    frac=(when.hour+when.minute/60+when.second/3600)/24
    gamma=2*math.pi/365*(doy-1+frac-0.5)
    decl=0.006918-0.399912*math.cos(gamma)+0.070257*math.sin(gamma)-0.006758*math.cos(2*gamma)+0.000907*math.sin(2*gamma)-0.002697*math.cos(3*gamma)+0.00148*math.sin(3*gamma)
    eqtime=229.18*(0.000075+0.001868*math.cos(gamma)-0.032077*math.sin(gamma)-0.014615*math.cos(2*gamma)-0.040849*math.sin(2*gamma))
    tst=(when.hour*60+when.minute+eqtime+4*lon)%1440
    ha=math.radians(tst/4-180 if tst/4>=180 else tst/4+180)
    phi=math.radians(lat)
    cosz=math.sin(phi)*math.sin(decl)+math.cos(phi)*math.cos(decl)*math.cos(ha)
    elev=90-math.degrees(math.acos(max(-1,min(1,cosz))))
    azim=math.degrees(math.atan2(math.sin(ha),math.cos(ha)*math.sin(phi)-math.tan(decl)*math.cos(phi)))+180
    return {"elevation_deg":round(elev,3),"azimuth_deg":round(azim%360,3),"declination_deg":round(math.degrees(decl),3)}
def shadow_length_m(height_m,elev_deg):
    if elev_deg<=0: return float("inf")
    return height_m/math.tan(math.radians(elev_deg))
def segment_shade(road_bearing_deg, buildings, trees, elev_deg, azim_deg):
    """buildings/trees: [{height_m|canopy_radius_m, lateral_offset_m, along_fraction}]. Returns 0..1 estimate."""
    if elev_deg<=0: return 1.0  # night: no direct sun
    shade_dir=(azim_deg+180)%360
    # shadow reaches road if shadow direction roughly perpendicular component covers lateral offset
    shaded=0.0; n=max(1,len(buildings)+len(trees))
    for b in buildings:
        L=shadow_length_m(b.get("height_m",0),elev_deg)
        reach=L*abs(math.sin(math.radians(shade_dir-road_bearing_deg)))
        if reach>=b.get("lateral_offset_m",999): shaded+=b.get("along_fraction",0.2)
    for t in trees:
        # canopy shade only if canopy actually overhangs path (not tree count)
        if t.get("canopy_overhang_m",0)>0:
            shaded+=min(t.get("along_fraction",0.15), t["canopy_overhang_m"]/max(1.0,t.get("segment_length_m",30))*0.5+0.1)
    return round(max(0.0,min(1.0,shaded)),3)
def estimate_utci_proxy(temp_c,rh_pct,wind_ms,solar_wm2,shade_frac,vehicle="two_wheeler",speed_kmh=25):
    """Simplified apparent-exposure proxy inspired by UTCI inputs. NOT measured WBGT/UTCI; labelled estimate."""
    rel_wind=wind_ms+(speed_kmh/3.6 if vehicle=="two_wheeler" else 0.0)
    mrt=temp_c+(solar_wm2*(1-shade_frac)*0.028)  # mean radiant temp proxy
    if vehicle=="car": mrt=temp_c+solar_wm2*0.008; rel_wind=wind_ms*0.3
    vapour=6.112*math.exp(17.67*temp_c/(temp_c+243.5))*rh_pct/100/10  # kPa
    utci=mrt+0.33*vapour-0.70*rel_wind-4.0  # Steadman-like apparent temp form
    return {"utci_proxy_c":round(utci,2),"mrt_proxy_c":round(mrt,2),"relative_wind_ms":round(rel_wind,2),
            "index":"UTCI-inspired proxy (not validated UTCI/WBGT)","is_measurement":False}
def exposure_for_duration(utci_proxy_c,duration_s):
    # cumulative dose above 26C reference, degree-seconds
    return round(max(0.0,utci_proxy_c-26.0)*duration_s,1)
