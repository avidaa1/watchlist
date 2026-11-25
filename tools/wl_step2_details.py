"""Step 2: resolve seeds, fetch details (label, date, people, country, runtime, genres, awards, enwiki link, sitelinks) for all candidates."""
import sys, json, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wdq, wl_rules as R, wl_seeds as S
step1 = json.load(open(wdq.CACHE + "/step1.json"))
cls = " ".join("wd:" + c for c in R.WORK_CLASSES)
# resolve seeds: exact en label + P577 year + work class
import wl_seedres
seedmap = {}
seedlog = {"resolved": 0, "unresolved": []}
allpairs = sorted(set((t, y) for lst in S.SEEDS.values() for t, y in lst))
res = wl_seedres.resolve(allpairs)
for cat, lst in S.SEEDS.items():
    for t, y in sorted(set(lst)):
        i = res.get((t, y))
        if i: seedmap.setdefault(i, {"cats": set(), "sl": 0})["cats"].add(cat)
        else: seedlog["unresolved"].append([cat, t, y])
seedlog["resolved"] = len(seedmap)
ids_s = sorted(seedmap)
for k in range(0, len(ids_s), 250):
    part = ids_s[k:k+250]
    q = "SELECT ?item ?sl WHERE { VALUES ?item { %s } ?item wikibase:sitelinks ?sl }" % " ".join("wd:" + i for i in part)
    for b in wdq.query(q, "seedsl_%d" % k): seedmap[wdq.qid(wdq.v(b, "item"))]["sl"] = int(wdq.v(b, "sl"))
# union
allc = {}
for cat, d in step1.items():
    for i, e in d.items():
        a = allc.setdefault(i, {"sl": e["sl"], "cats": {}})
        a["cats"].setdefault(cat, []).extend(e["rules"])
step1b = json.load(open(wdq.CACHE + "/step1b.json"))
evname = {}
for cat, d in step1b.items():
    evname.update(d["events"])
    for i, e in d["cands"].items():
        a = allc.setdefault(i, {"sl": e["sl"], "cats": {}})
        a["cats"].setdefault(cat, []).extend(e["rules"])
for i, e in seedmap.items():
    a = allc.setdefault(i, {"sl": e["sl"], "cats": {}})
    for c in e["cats"]: a["cats"].setdefault(c, []).append("seed")
print("union candidates", len(allc), "seeds resolved", len(seedmap), "unresolved", len(seedlog["unresolved"]))
ids = sorted(allc)
def batches(lst, n):
    for k in range(0, len(lst), n): yield lst[k:k+n]
def run(props, tag, sel, extra):
    res = {}
    for k, part in enumerate(batches(props, 60)):
        vs = " ".join("wd:" + i for i in part)
        body, _, tail = extra.partition(" GROUP BY ")
        q = "SELECT %s WHERE { VALUES ?item { %s } %s }%s" % (sel, vs, body, (" GROUP BY " + tail) if tail else "")
        for b in wdq.query(q, "%s_%d" % (tag, k)):
            res.setdefault(wdq.qid(wdq.v(b, "item")), []).append(b)
    return res
AW = re.compile(r"Academy Award|Palme d'Or|Golden Lion|Golden Bear|BAFTA|Golden Globe|Primetime Emmy|Emmy Award|Hugo Award|Saturn Award|Peabody|César|Grand Prix|Golden Palm|Jury Prize|Sundance|Directors Guild|Screen Actors Guild|Writers Guild|Critics|Nebula|Silver Bear|Silver Lion|Ariel|Goya|European Film Award|Satellite|National Film Registry|Annie Award|Independent Spirit|Critics' Choice|Audience Award|Grand Jury|IDFA|Hot Docs|Grierson|duPont|Cinema Eye|Gotham|Tribeca|Edgar Award|Cannes|Venice|Berlin|Locarno|Toronto|Rose d'Or|Prix Italia|International Emmy|BAFTA TV|Television Critics|Golden Reel", re.I)
# cheap first: awards for everybody (needed for the OR rule)
need_aw = [i for i in ids if allc[i]["sl"] >= 8]   # rule: the award check is run for works with at least 8 sitelinks (below that a notable award is practically absent)
def run_small(lst, tag, sel, extra, n):
    res = {}
    for k in range(0, len(lst), n):
        part = lst[k:k+n]
        q = "SELECT %s WHERE { VALUES ?item { %s } %s }" % (sel, " ".join("wd:" + i for i in part), extra)
        for b in wdq.query(q, "%s_%d" % (tag, k)):
            res.setdefault(wdq.qid(wdq.v(b, "item")), []).append(b)
    return res
aw = run_small(need_aw, "aw2", "?item ?a ?p", "{ ?item wdt:P166 ?a . BIND('won' AS ?p) } UNION { ?item wdt:P1411 ?a . BIND('nominated' AS ?p) }", 80)
alla = sorted(set(wdq.qid(wdq.v(b, "a")) for bs in aw.values() for b in bs))
alabel = {}
for k in range(0, len(alla), 300):
    q = "SELECT ?a ?al WHERE { VALUES ?a { %s } ?a rdfs:label ?al FILTER(lang(?al) IN ('en','en-gb','en-ca','mul')) }" % " ".join("wd:" + x for x in alla[k:k+300])
    for b in wdq.query(q, "awl_%d" % k): alabel[wdq.qid(wdq.v(b, "a"))] = wdq.v(b, "al")
award = {}
for i, bs in aw.items():
    for b in bs:
        l = alabel.get(wdq.qid(wdq.v(b, "a")), "")
        if AW.search(l): award.setdefault(i, {})[l] = wdq.v(b, "p")
keep = [i for i in ids if allc[i]["sl"] >= R.MIN_SITELINKS or i in award]
print("pass quality gate", len(keep))
det = {}
LANGS = "('en','en-gb','en-ca','mul')"
PRI = {"en": 0, "en-gb": 1, "en-ca": 2, "mul": 3}
def pick_labels(rows, key_x="x", key_l="l"):
    best = {}
    for b in rows:
        if key_x not in b: continue
        x = wdq.qid(wdq.v(b, key_x)); lg = b[key_l].get("xml:lang", "mul"); pr = PRI.get(lg, 9)
        if x not in best or pr < best[x][0]: best[x] = (pr, wdq.v(b, key_l))
    return best
def grp(tag, prop):
    res = run(keep, tag, "?item ?x ?l", "OPTIONAL { ?item wdt:%s ?x . ?x rdfs:label ?l FILTER(lang(?l) IN %s) }" % (prop, LANGS))
    out = {}
    for i, rows in res.items():
        lab = pick_labels(rows)
        seen = []
        for b in rows:
            if "x" in b:
                x = wdq.qid(wdq.v(b, "x"))
                if x in lab and lab[x][1] not in seen: seen.append(lab[x][1])
        out[i] = "|".join(seen)
    return out
labs_rows = run(keep, "lab2", "?item ?l", "?item rdfs:label ?l FILTER(lang(?l) IN %s)" % LANGS)
def item_label(i):
    best = None
    for b in labs_rows.get(i, []):
        pr = PRI.get(b["l"].get("xml:lang", "mul"), 9)
        if best is None or pr < best[0]: best = (pr, wdq.v(b, "l"))
    return best[1] if best else None
core = run(keep, "core", "?item ?cls (MIN(?d) AS ?date) (SAMPLE(?rt) AS ?rt1) (SAMPLE(?art) AS ?art1)",
  "?item wdt:P31 ?cls OPTIONAL { ?item wdt:P577 ?d } OPTIONAL { ?item wdt:P2047 ?rt } OPTIONAL { ?art schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> } GROUP BY ?item ?cls")
dirs = grp("dir", "P57"); creators = grp("cre", "P170"); cast = grp("cast", "P161"); ctry = grp("ctry", "P495"); genres = grp("gen", "P136")
# also first-air date for series
start = run(keep, "st", "?item (MIN(?d) AS ?date)", "OPTIONAL { ?item wdt:P580 ?d } OPTIONAL { ?item wdt:P577 ?d } GROUP BY ?item")
evids = sorted(evname)
evyear = {}
for k in range(0, len(evids), 60):
    part = evids[k:k+60]
    q = "SELECT ?e (MIN(?d) AS ?d1) WHERE { VALUES ?e { %s } { ?e wdt:P585 ?d } UNION { ?e wdt:P580 ?d } UNION { ?e wdt:P571 ?d } UNION { ?e wdt:P577 ?d } UNION { ?e wdt:P569 ?d } } GROUP BY ?e" % " ".join("wd:" + x for x in part)
    for b in wdq.query(q, "evy_%d" % k): evyear[wdq.qid(wdq.v(b, "e"))] = wdq.v(b, "d1")[:4]
recs = {}
for i in keep:
    bs = core.get(i)
    if not bs: continue
    clss = set(wdq.qid(wdq.v(b, "cls")) for b in bs if "cls" in b)
    kinds = [R.WORK_CLASSES[c] for c in clss if c in R.WORK_CLASSES]
    t = "documentary" if ("documentary" in kinds or any(g.strip().lower() in ("documentary film","documentary television series","documentary","television documentary") for g in genres.get(i, "").split("|"))) else ("series" if "series" in kinds else "film")
    if not item_label(i): continue
    dts = [wdq.v(b, "date") for b in bs if "date" in b] + [wdq.v(b, "date") for b in start.get(i, []) if "date" in b]
    art = next((wdq.v(b, "art1") for b in bs if "art1" in b), None)
    rt = next((wdq.v(b, "rt1") for b in bs if "rt1" in b), None)
    recs[i] = {"qid": i, "title": item_label(i), "type": t, "date": (min(dts)[:10] if dts else ""), "sl": allc[i]["sl"],
      "director": dirs.get(i, ""), "creator": creators.get(i, ""), "cast": cast.get(i, ""), "country": ctry.get(i, ""),
      "runtime": rt, "genres": genres.get(i, ""), "awards": award.get(i, {}), "wiki": art, "cats": allc[i]["cats"], "events": sorted(set((evname[r.split(":")[1]], evyear.get(r.split(":")[1], "")) for rs in allc[i]["cats"].values() for r in rs if r.startswith("P921:") and r.split(":")[1] in evname))}
json.dump({"records": recs, "seeds_unresolved": seedlog["unresolved"], "union": len(allc), "gate": len(keep), "allc": {i: {"sl": a["sl"], "cats": a["cats"], "aw": i in award} for i, a in allc.items()}}, open(wdq.CACHE + "/step2.json", "w"))
print("records", len(recs))
