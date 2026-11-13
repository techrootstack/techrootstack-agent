#!/usr/bin/env python3
"""Techrootstack Instagram carousel agent.
Posts due carousels from schedule.csv via the Instagram Graph API.
Env: IG_USER_ID, IG_ACCESS_TOKEN, PUBLIC_BASE_URL (no trailing slash), optional DRY_RUN=1, MAX_PER_RUN, TOKEN_EXPIRES (YYYY-MM-DD)
"""
import csv, json, os, re, sys, time, glob
from datetime import datetime, date
from zoneinfo import ZoneInfo
import requests

API = "https://graph.facebook.com/v21.0"
ROOT = os.path.dirname(os.path.abspath(__file__))
IST = ZoneInfo("Asia/Kolkata")
DRY = os.environ.get("DRY_RUN") == "1"

def env(k, req=True):
    v = os.environ.get(k)
    if req and not v and not DRY: sys.exit(f"Missing env var {k}")
    return v

def captions():
    txt = open(f"{ROOT}/captions.md", encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"^## (\S+)\n(.+?)(?=\n## |\Z)", txt, re.S | re.M):
        out[m.group(1)] = m.group(2).strip()
    return out

def call(method, url, **kw):
    r = requests.request(method, url, timeout=60, **kw)
    data = r.json()
    if r.status_code >= 400 or "error" in data:
        raise RuntimeError(f"API error {r.status_code}: {data}")
    return data

def wait_ready(cid, token):
    for _ in range(30):
        s = call("GET", f"{API}/{cid}", params={"fields": "status_code", "access_token": token})
        if s.get("status_code") == "FINISHED": return
        if s.get("status_code") in ("ERROR", "EXPIRED"): raise RuntimeError(f"container {cid}: {s}")
        time.sleep(4)
    raise RuntimeError(f"container {cid} not ready in time")

def post_carousel(name, caption):
    uid, token, base = env("IG_USER_ID"), env("IG_ACCESS_TOKEN"), env("PUBLIC_BASE_URL")
    slides = sorted(glob.glob(f"{ROOT}/{name}__slide_*.jpg"))
    if not 2 <= len(slides) <= 10: raise RuntimeError(f"{name}: need 2-10 slides, found {len(slides)}")
    urls = [f"{base}/{os.path.basename(s)}" for s in slides]
    if DRY:
        print(f"[DRY RUN] would post {name} with {len(urls)} slides\n  first: {urls[0]}\n  caption: {caption[:80]}...")
        return "dry-run"
    kids = []
    for u in urls:
        c = call("POST", f"{API}/{uid}/media", data={"image_url": u, "is_carousel_item": "true", "access_token": token})
        wait_ready(c["id"], token); kids.append(c["id"])
    car = call("POST", f"{API}/{uid}/media", data={"media_type": "CAROUSEL", "children": ",".join(kids), "caption": caption, "access_token": token})
    wait_ready(car["id"], token)
    pub = call("POST", f"{API}/{uid}/media_publish", data={"creation_id": car["id"], "access_token": token})
    return pub["id"]

def main():
    exp = os.environ.get("TOKEN_EXPIRES")
    if exp:
        left = (date.fromisoformat(exp) - date.today()).days
        if left <= 10: print(f"WARNING: access token expires in {left} days. Renew it.")
    posted = json.load(open(f"{ROOT}/posted.json"))
    done = {p["carousel"] for p in posted}
    caps = captions()
    now = datetime.now(IST)
    limit = int(os.environ.get("MAX_PER_RUN", "1"))
    count = 0
    for row in csv.DictReader(open(f"{ROOT}/schedule.csv")):
        n = row["carousel"]
        if n in done: continue
        when = datetime.fromisoformat(f"{row['date']}T{row['time_ist']}").replace(tzinfo=IST)
        if when > now: continue
        if n not in caps: print(f"skip {n}: no caption"); continue
        try:
            mid = post_carousel(n, caps[n])
        except Exception as e:
            print(f"FAILED {n}: {e}"); continue
        print(f"posted {n} -> {mid}")
        if not DRY: posted.append({"carousel": n, "media_id": mid, "posted_at": now.isoformat()})
        count += 1
        if count >= limit: break
    if not DRY: json.dump(posted, open(f"{ROOT}/posted.json", "w"), indent=2)
    if count == 0: print("nothing due")

if __name__ == "__main__":
    main()
