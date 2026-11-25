"""Resolve seed titles to QIDs through English Wikipedia titles (wbgetentities by sitelink, 50 per call, cached), then verify instance-of class and release year."""
import json, os, hashlib, time, urllib.request, urllib.parse
import wdq, wl_rules as R
def api(params, tag):
    q = urllib.parse.urlencode(params)
    fn = "%s/raw/api_%s_%s.json" % (wdq.CACHE, tag, hashlib.sha1(q.encode()).hexdigest()[:16])
    if os.path.exists(fn): return json.load(open(fn))
    time.sleep(1.2)
    for a in range(3):
        try:
            raw = urllib.request.urlopen(urllib.request.Request("https://www.wikidata.org/w/api.php?" + q, headers={"User-Agent": wdq.UA}), timeout=40).read()
            open(fn, "wb").write(raw); return json.loads(raw)
        except Exception as e:
            print("api retry", str(e)[:60], flush=True); time.sleep(6)
    return {}
def variants(t, y):
    return [t, "%s (%d film)" % (t, y), "%s (film)" % t, "%s (%d TV series)" % (t, y), "%s (TV series)" % t, "%s (American TV series)" % t, "%s (British TV series)" % t,
            "%s (%d American TV series)" % (t, y), "%s (miniseries)" % t, "%s (%d miniseries)" % (t, y), "%s (documentary)" % t, "%s (%d documentary film)" % (t, y), "%s (documentary film)" % t, "%s (Western film)" % t]
def year_of(ent):
    c = ent.get("claims", {})
    ys = []
    for p in ("P577", "P580"):
        for s in c.get(p, []):
            try: ys.append(int(s["mainsnak"]["datavalue"]["value"]["time"][1:5]))
            except Exception: pass
    return ys
def resolve(pairs):
    """pairs: list of (title, year) -> dict (title, year) -> qid or None"""
    need = {}
    for t, y in pairs:
        for v in variants(t, y): need.setdefault(v, []).append((t, y))
    titles = sorted(need)
    ent = {}   # wikipedia title -> entity
    for k in range(0, len(titles), 50):
        part = titles[k:k+50]
        r = api({"action": "wbgetentities", "sites": "enwiki", "titles": "|".join(part), "props": "claims|sitelinks", "sitefilter": "enwiki", "format": "json"}, "ent2")
        for qid, e in (r.get("entities") or {}).items():
            if qid.startswith("Q"):
                tt = ((e.get("sitelinks") or {}).get("enwiki") or {}).get("title")
                if tt: ent[tt] = e
    out = {}
    for t, y in pairs:
        out[(t, y)] = None
        for v in variants(t, y):
            e = ent.get(v)
            if not e: continue
            cl = set()
            for s in e.get("claims", {}).get("P31", []):
                try: cl.add(s["mainsnak"]["datavalue"]["value"]["id"])
                except Exception: pass
            if cl & set(R.WORK_CLASSES) and any(abs(yy - y) == 0 for yy in year_of(e)):
                out[(t, y)] = e["id"]; break
    return out
