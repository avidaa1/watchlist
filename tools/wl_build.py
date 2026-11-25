"""Step 3: build watchlist-data.json + watchlist-search.json + report from step2.json, the review lists and our own content (wl_own.py)."""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wdq, wl_review as RV, wl_rules as R
try:
    import wl_own as OWN
except ImportError:
    OWN = None
repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(wdq.CACHE + "/step2.json")); recs = d["records"]; allc = d["allc"]
CATSHORT = {"ai": "AI", "hackers": "Hackers", "aliens": "Aliens", "cyberwar": "Cyber war", "crypto": "Crypto", "westerns": "Westerns"}
ORDER = ["ai", "hackers", "cyberwar", "aliens", "crypto", "westerns"]
key = lambda r: "%s|%s" % (r["title"], r["date"][:4])
report = {"per_cat": {}, "removals": [], "seeds_unresolved": d["seeds_unresolved"]}
items = {}
for cat in ORDER:
    cand = [i for i, a in allc.items() if cat in a["cats"]]
    kept_auto = [i for i in cand if i in recs and cat in recs[i]["cats"]]
    reasons = {"below 20 sitelinks and no notable award": 0, "not a film/series/documentary item or no English label": 0, "removed in hand review (misfit)": 0}
    for i in cand:
        if i not in recs:
            if allc[i]["sl"] < R.MIN_SITELINKS and not allc[i]["aw"]: reasons["below 20 sitelinks and no notable award"] += 1
            else: reasons["not a film/series/documentary item or no English label"] += 1
    kept = []
    for i in kept_auto:
        k = key(recs[i])
        if cat in RV.KEEP_ONLY and k not in RV.KEEP_ONLY[cat]: ok = False
        elif k in RV.REMOVE.get(cat, []): ok = False
        else: ok = True
        if not ok:
            reasons["removed in hand review (misfit)"] += 1; report["removals"].append([cat, k])
        else: kept.append(i)
    report["per_cat"][cat] = {"candidates": len(cand), "kept": len(kept), "filtered": len(cand) - len(kept), "reasons": reasons}
    for i in kept:
        items.setdefault(i, set()).add(cat)
def own(r):
    if OWN is None: return {}
    return OWN.OWN.get(key(r), {})
out = []; ev_missing = 0
for i, cats in items.items():
    r = recs[i]; o = own(r)
    cast = [x for x in r["cast"].split("|") if x][:5]
    dirs = [x for x in (r["director"] or r["creator"]).split("|") if x][:3]
    aw = ["%s (%s)" % (k, v) for k, v in sorted(r["awards"].items())][:5]
    ev = o.get("ev", "")
    if not ev and r["type"] == "documentary" and r["events"]:
        n, y = r["events"][0]; ev = "%s%s" % (n, ", " + y if y else "")
    out.append({"q": i, "t": r["title"], "ty": r["type"], "d": r["date"], "dir": ", ".join(dirs), "cast": cast, "co": ", ".join([x for x in r["country"].split("|") if x][:2]),
      "rt": str(r["runtime"] or "").split(".")[0], "g": ", ".join([x for x in r["genres"].split("|") if x][:4]), "aw": aw, "wp": r["wiki"] or "", "cat": [c for c in ORDER if c in cats],
      "s": o.get("s", ""), "tags": o.get("tags", []), "ev": ev})
out.sort(key=lambda x: x["d"], reverse=True)
byq = {x["q"]: x for x in out}
top = {}; bytitle = {key(recs[q]) : q for q in byq}
for cat in ORDER:
    lst = []
    for k, why in (getattr(OWN, "TOP", {}).get(cat, []) if OWN else []):
        q = bytitle.get(k)
        assert q and cat in byq[q]["cat"], "top pick not kept in %s: %s" % (cat, k)
        lst.append({"q": q, "why": why})
    top[cat] = lst
data = {"built": "2026-11-25", "source": "Wikidata (CC0), queried at build time through the public SPARQL endpoint; Wikipedia language-edition counts via wikibase:sitelinks.",
        "cats": [{"id": c, "name": R.CATS[c]["name"], "short": CATSHORT[c]} for c in ORDER], "top": top, "items": out}
json.dump(data, open(os.path.join(repo, "watchlist-data.json"), "w"), ensure_ascii=False, separators=(",", ":"))
# site search index entries: [pageIdxPlaceholder, type, title, snippet, anchor]
se = []
for x in out:
    sn = x["s"] or ("%s, %s%s" % (x["ty"], x["d"][:4], (" - " + ", ".join(x["cast"][:3])) if x["cast"] else ""))
    se.append([0, "item", x["t"], sn[:160], "find=" + x["t"]])
json.dump({"page": "watchlist", "note": "pageIdxPlaceholder (0) is replaced by the home index page id of Watchlist when merged", "e": se}, open(os.path.join(repo, "watchlist-search.json"), "w"), ensure_ascii=False, separators=(",", ":"))
report["total_items"] = len(out); report["summaries"] = sum(1 for x in out if x["s"]); report["empty"] = sum(1 for x in out if not x["s"])
json.dump(report, open(wdq.CACHE + "/report.json", "w"), indent=1)
print(json.dumps(report["per_cat"], indent=0)); print("items", len(out), "summaries", report["summaries"])
for cat in ORDER: print("##", cat, "; ".join(key(recs[q]) for q in byq if cat in byq[q]["cat"]))
