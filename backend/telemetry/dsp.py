"""DSP v2: filtering, RMS, spectral peak, feature-based event typing (heuristic, needs labelled eval)."""
import math, cmath
def lowpass(x,alpha=0.25):
    y=[]; p=0.0
    for v in x: p=p+alpha*(v-p); y.append(p)
    return y
def highpass(x,alpha=0.25): lp=lowpass(x,alpha); return [a-b for a,b in zip(x,lp)]
def rms(x): return math.sqrt(sum(v*v for v in x)/len(x)) if x else 0.0
def dominant_freq_hz(x,fs):
    n=len(x)
    if n<8: return 0.0
    best=(0,0.0)
    for k in range(1,n//2):
        s=sum(x[i]*cmath.exp(-2j*math.pi*k*i/n) for i in range(n))
        if abs(s)>best[1]: best=(k,abs(s))
    return round(best[0]*fs/n,2)
def resample_uniform(samples,fs=50):
    if len(samples)<2: return samples
    t0,t1=samples[0]["t"],samples[-1]["t"]; out=[]; j=0
    steps=int((t1-t0)*fs)
    for i in range(steps+1):
        t=t0+i/fs
        while j<len(samples)-2 and samples[j+1]["t"]<t: j+=1
        a,b=samples[j],samples[j+1]; f=0 if b["t"]==a["t"] else (t-a["t"])/(b["t"]-a["t"])
        out.append({"t":t, **{k:a[k]+(b[k]-a[k])*f for k in ("ax","ay","az") if k in a}, "lat":a.get("lat"),"lon":a.get("lon")})
    return out
def features(samples,fs=50):
    dev=[abs(math.sqrt(s["ax"]**2+s["ay"]**2+s["az"]**2)-9.81) for s in samples]
    hp=highpass(dev)
    peak=max(hp) if hp else 0
    dur=sum(1 for v in hp if v>1.0)/fs
    return {"peak_dev":round(peak,3),"rms_vibration":round(rms(hp),3),"event_duration_s":round(dur,3),"dominant_freq_hz":dominant_freq_hz(hp,fs),"n":len(samples)}
def classify_event(f,speed_kmh=20):
    # Long low bump = speed breaker; short sharp = pothole; sustained rough = rough patch
    if f["peak_dev"]<1.2: return "normal_road",0.6
    if f["event_duration_s"]>=0.45 and f["peak_dev"]<5: return "speed_breaker",0.55
    if f["event_duration_s"]<0.3 and f["peak_dev"]>=3: return "suspected_pothole",0.6
    return "rough_patch",0.5
