"""Auth: PBKDF2-HMAC-SHA256 (600k iters, per-user salt) — stdlib; upgrade path to Argon2id documented.
Tokens: HMAC-signed, expiring, JWT-shaped (not demo deterministic tokens)."""
import hashlib, hmac, os, base64, json, time
SECRET=os.environ.get("RT_SECRET","dev-only-change-me").encode()
def hash_pw(pw):
    salt=os.urandom(16); h=hashlib.pbkdf2_hmac("sha256",pw.encode(),salt,600_000)
    return base64.b64encode(salt).decode()+"$"+base64.b64encode(h).decode()
def verify_pw(pw,stored):
    try:
        s,h=stored.split("$"); calc=hashlib.pbkdf2_hmac("sha256",pw.encode(),base64.b64decode(s),600_000)
        return hmac.compare_digest(base64.b64encode(calc).decode(),h)
    except Exception: return False
def _b64(o): return base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")
def make_token(email,role="rider",ttl=3600):
    payload={"sub":email,"role":role,"exp":int(time.time())+ttl}
    body=_b64({"alg":"HS256"})+"."+_b64(payload); sig=hmac.new(SECRET,body.encode(),hashlib.sha256).hexdigest()
    return body+"."+sig
def parse_token(tok):
    try:
        h,p,s=tok.split("."); body=h+"."+p
        if not hmac.compare_digest(hmac.new(SECRET,body.encode(),hashlib.sha256).hexdigest(),s): return None
        payload=json.loads(base64.urlsafe_b64decode(p+"=="))
        return payload if payload["exp"]>time.time() else None
    except Exception: return None
