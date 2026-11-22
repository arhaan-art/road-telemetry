"""Image heuristic v1 — NOT a trained YOLO model. Dark, textured blobs are *candidates*.
Trained-model interface: replace `analyse_bytes` internals, keep return schema. See ml/README."""
import io
def analyse_bytes(data:bytes):
    trained=analyse_trained(data)
    if trained: return trained
    try:
        from PIL import Image
        im=Image.open(io.BytesIO(data)).convert("L"); im.thumbnail((320,320))
        px=list(im.getdata()); w,h=im.size
        if not px: raise ValueError("empty")
        mean=sum(px)/len(px)
        dark=sum(1 for p in px if p<mean*0.55)/len(px)
        # local contrast via horizontal diffs
        diffs=sum(abs(px[i]-px[i-1]) for i in range(1,len(px)))/len(px)
        if dark>0.04 and diffs>12:
            label,conf="suspected_pothole",min(0.75,0.3+dark*2)
        elif diffs>28:
            label,conf="rough_patch",0.45
        elif dark>0.02:
            label,conf="shadow_or_dark_patch_uncertain",0.3
        else:
            label,conf="normal_road",0.55
        return {"label":label,"confidence":round(conf,3),"method":"heuristic_v1_not_trained_ml",
                "is_trained_model":False,"dark_fraction":round(dark,4),"texture":round(diffs,2),"width":w,"height":h}
    except Exception as e:
        return {"label":"unprocessable","confidence":0.0,"method":"heuristic_v1_not_trained_ml","is_trained_model":False,"error":str(e)}
CLASSES=["pothole","speed_breaker","rough_patch","road_crack","normal_road"]
def evaluate(y_true,y_pred):
    labels=sorted(set(y_true)|set(y_pred)); out={}
    for lab in labels:
        tp=sum(1 for a,b in zip(y_true,y_pred) if a==lab and b==lab)
        fp=sum(1 for a,b in zip(y_true,y_pred) if a!=lab and b==lab); fn=sum(1 for a,b in zip(y_true,y_pred) if a==lab and b!=lab)
        out[lab]={"precision":round(tp/(tp+fp),3) if tp+fp else 0.0,"recall":round(tp/(tp+fn),3) if tp+fn else 0.0}
    acc=sum(1 for a,b in zip(y_true,y_pred) if a==b)/len(y_true) if y_true else 0
    return {"accuracy":round(acc,3),"per_class":out,"n":len(y_true)}
CLASSES_TRAIN=["pothole","rough_patch","road_crack","speed_breaker","normal_road"]
def image_features(im):
    import numpy as np
    a=np.asarray(im.convert("L").resize((128,128)),dtype=float)/255.0
    dark=float((a<a.mean()*0.6).mean()); tex=float(np.abs(np.diff(a,axis=1)).mean())
    band=float(a[55:75,:].mean()-a.mean()); std=float(a.std())
    crack=float((np.abs(np.diff(a,axis=0))>0.25).mean())
    return [dark,tex,band,std,crack,float(a.mean())]
_MODEL=None
def analyse_trained(data:bytes):
    """Use synthetic-trained model if present; caller must label dataset limitation."""
    global _MODEL
    try:
        import numpy as np, io
        from PIL import Image
        if _MODEL is None: _MODEL=np.load("ml/models/vision_synth.npz",allow_pickle=True)
        f=np.array(image_features(Image.open(io.BytesIO(data))))
        z=((f-_MODEL["mu"])/_MODEL["sd"])@_MODEL["W"]+_MODEL["b"]; z-=z.max(); p=np.exp(z); p/=p.sum()
        i=int(p.argmax()); return {"label":str(_MODEL["classes"][i]),"confidence":round(float(p[i]),3),"method":"softmax_synthetic_trained_v1","is_trained_model":True,"training_data":"synthetic_only_not_real_world_validated"}
    except Exception as e: return None
