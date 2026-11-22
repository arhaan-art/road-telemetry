"""Sensor anomaly pipeline. Labels are *candidates*, never confirmed potholes."""
import math
def normalise(samples):
    out=[]
    for s in samples:
        ax,ay,az=s["ax"],s["ay"],s["az"]
        mag=math.sqrt(ax*ax+ay*ay+az*az)
        # vertical proxy: deviation from gravity magnitude (mounting-invariant first pass)
        out.append({**s,"mag":mag,"vertical_dev":abs(mag-9.81)})
    return out
def detect(samples, speed_kmh=None):
    """samples sorted by t (seconds). Returns candidate events."""
    s=normalise(sorted(samples,key=lambda x:x["t"]))
    events=[]
    for i in range(1,len(s)):
        dt=s[i]["t"]-s[i-1]["t"]
        if dt<=0 or dt>2: continue
        jerk=abs(s[i]["vertical_dev"]-s[i-1]["vertical_dev"])/dt
        dev=s[i]["vertical_dev"]
        # braking/turn guard: sustained horizontal change lowers confidence
        horiz=math.sqrt(s[i]["ax"]**2+s[i]["ay"]**2)
        if dev>2.2 and jerk>4.0:
            kind="rough_patch" if dev<4.5 else "suspected_pothole"
            conf=min(0.92,0.35+dev/12+jerk/40)
            if speed_kmh and speed_kmh<5: conf*=0.5  # stationary bumps are not road defects
            if horiz>7: conf*=0.7; kind="unverified_anomaly"
            events.append({"t":s[i]["t"],"lat":s[i].get("lat"),"lon":s[i].get("lon"),
              "category":kind,"confidence":round(conf,3),"vertical_dev":round(dev,3),"jerk":round(jerk,3),
              "status":"suspected","method":"accelerometer_heuristic_v1"})
    # de-duplicate within 1.5s
    dedup=[]
    for e in events:
        if not dedup or e["t"]-dedup[-1]["t"]>1.5: dedup.append(e)
    return dedup
def cluster_confidence(n_independent, mean_sensor_conf, age_days, revalidate_days=14):
    crowd=min(0.35,0.08*n_independent)
    recency=max(0.0,1-age_days/max(revalidate_days,1))*0.15
    conf=max(0.0,min(0.98,mean_sensor_conf*0.6+crowd+recency))
    status="confirmed" if (n_independent>=3 and conf>=0.7) else ("suspected" if conf>=0.35 else "unverified")
    if age_days>revalidate_days: status="stale" if status!="confirmed" else status
    return round(conf,3),status
