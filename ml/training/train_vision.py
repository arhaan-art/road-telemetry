"""Train vision classifier on SYNTHETIC generated road images (no real-world accuracy claimed).
Real-data path: replace generate() with licensed dataset loader, keep features/model/eval contract.
Split is by scene-seed group (proxy for geographic separation) to reduce leakage."""
import sys, os, json, random
sys.path.insert(0,".")
import numpy as np
from PIL import Image, ImageDraw
from backend.computer_vision.detect import image_features, CLASSES_TRAIN
def generate(cls,seed):
    rng=random.Random(seed); im=Image.new("L",(128,128),rng.randint(95,125)); d=ImageDraw.Draw(im)
    for _ in range(400): x,y=rng.random()*128,rng.random()*128; g=rng.randint(80,150); d.point((x,y),fill=g)
    if cls=="pothole": d.ellipse((40,50,90,85),fill=rng.randint(15,35))
    elif cls=="road_crack":
        x=10
        for y in range(0,128,12): d.line((x,y,x+rng.randint(-8,14),y+12),fill=25,width=2); x+=rng.randint(-4,8)
    elif cls=="rough_patch":
        for _ in range(900): x,y=rng.random()*128,rng.random()*128; d.point((x,y),fill=rng.randint(30,190))
    elif cls=="speed_breaker": d.rectangle((0,55,128,75),fill=rng.randint(165,195))
    return im
def main(n_per=120):
    X=[]; y=[]; groups=[]
    for ci,cls in enumerate(CLASSES_TRAIN):
        for i in range(n_per): X.append(image_features(generate(cls,hash((cls,i))%100000))); y.append(ci); groups.append(i%4)
    X=np.array(X); y=np.array(y); groups=np.array(groups)
    tr=groups!=0; te=groups==0  # held-out scene group
    mu,sd=X[tr].mean(0),X[tr].std(0)+1e-9; Xn=(X-mu)/sd
    W=np.zeros((Xn.shape[1],len(CLASSES_TRAIN))); b=np.zeros(len(CLASSES_TRAIN)); rng=np.random.default_rng(0)
    for epoch in range(300):
        z=Xn[tr]@W+b; z-=z.max(1,keepdims=True); p=np.exp(z); p/=p.sum(1,keepdims=True)
        g=p.copy(); g[np.arange(tr.sum()),y[tr]]-=1; g/=tr.sum()
        W-=0.3*(Xn[tr].T@g+0.01*W); b-=0.3*g.sum(0)
    def pred(idx): return (Xn[idx]@W+b).argmax(1)
    acc=float((pred(np.where(te)[0])==y[te]).mean())
    per={}
    for ci,cls in enumerate(CLASSES_TRAIN):
        tp=int(((pred(np.where(te)[0])==ci)&(y[te]==ci)).sum()); fp=int(((pred(np.where(te)[0])==ci)&(y[te]!=ci)).sum()); fn=int(((pred(np.where(te)[0])!=ci)&(y[te]==ci)).sum())
        per[cls]={"precision":round(tp/(tp+fp),3) if tp+fp else 0,"recall":round(tp/(tp+fn),3) if tp+fn else 0}
    os.makedirs("ml/models",exist_ok=True); np.savez("ml/models/vision_synth.npz",W=W,b=b,mu=mu,sd=sd,classes=np.array(CLASSES_TRAIN))
    metrics={"dataset":"SYNTHETIC generated images only - NOT real-world validation","holdout_accuracy":round(acc,3),"per_class":per,"n_train":int(tr.sum()),"n_holdout":int(te.sum())}
    os.makedirs("ml/evaluation",exist_ok=True); json.dump(metrics,open("ml/evaluation/vision_synth_metrics.json","w"),indent=1); print(metrics)
if __name__=="__main__": main()
