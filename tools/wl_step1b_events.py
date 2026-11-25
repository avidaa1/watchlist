"""Step 1b: resolve EVENTS titles to QIDs, then find works (film/series/documentary) whose main subject (P921) is one of them. Also records the event label and year."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wdq, wl_rules as R, wl_events as E, wl_seedres
cls = " ".join("wd:" + c for c in R.WORK_CLASSES) + " wd:Q93204 wd:Q21191270"
out = {}
for cat, titles in E.EVENTS.items():
    ent = {}
    for k in range(0, len(titles), 50):
        r = wl_seedres.api({"action": "wbgetentities", "sites": "enwiki", "titles": "|".join(titles[k:k+50]), "props": "sitelinks", "sitefilter": "enwiki", "format": "json"}, "evt")
        for qid, e in (r.get("entities") or {}).items():
            if qid.startswith("Q"): ent[qid] = e["sitelinks"]["enwiki"]["title"]
    ids = sorted(ent)
    cands = {}
    for k in range(0, len(ids), 25):
        part = ids[k:k+25]
        q = "SELECT ?item ?sl ?s WHERE { VALUES ?s { %s } ?item wdt:P921 ?s . { ?item wdt:P31 ?c } UNION { ?item wdt:P136 ?c } VALUES ?c { %s } ?item wikibase:sitelinks ?sl }" % (" ".join("wd:" + i for i in part), cls)
        for b in wdq.query(q, "ev_" + cat):
            i = wdq.qid(wdq.v(b, "item")); s = wdq.qid(wdq.v(b, "s"))
            e = cands.setdefault(i, {"sl": int(wdq.v(b, "sl")), "cls": [], "rules": []})
            e["rules"].append("P921:" + s)
    out[cat] = {"events": ent, "cands": cands}
    print(cat, len(ids), "events resolved,", len(cands), "works", flush=True)
json.dump(out, open(wdq.CACHE + "/step1b.json", "w"))
