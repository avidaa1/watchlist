"""Step 1: fetch candidate works per category from Wikidata (subject / genre rules) with sitelink counts."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wdq, wl_rules as R
out = {}
cls = " ".join("wd:" + c for c in R.WORK_CLASSES)
for cat, d in R.CATS.items():
    cands = {}
    for prop, key in (("P921", "subjects"), ("P136", "genres")):
        vals = d[key]
        if not vals: continue
        vs = " ".join("wd:" + q for q in vals)
        q = ("SELECT ?item ?cls ?sl ?tag WHERE { VALUES ?cls { %s } VALUES ?tag { %s } ?item wdt:P31 ?cls . ?item wdt:%s ?tag . ?item wikibase:sitelinks ?sl . }" % (cls, vs, prop))
        for b in wdq.query(q, "c1_%s_%s" % (cat, prop)):
            i = wdq.qid(wdq.v(b, "item"))
            e = cands.setdefault(i, {"sl": int(wdq.v(b, "sl")), "cls": set(), "rules": set()})
            e["cls"].add(wdq.qid(wdq.v(b, "cls")))
            e["rules"].add("%s:%s" % (prop, wdq.qid(wdq.v(b, "tag"))))
    out[cat] = {k: {"sl": v["sl"], "cls": sorted(v["cls"]), "rules": sorted(v["rules"])} for k, v in cands.items()}
    print(cat, len(cands), "candidates;", sum(1 for v in cands.values() if v["sl"] >= R.MIN_SITELINKS), "with >=20 sitelinks", flush=True)
json.dump(out, open(wdq.CACHE + "/step1.json", "w"))
