"""Small cached Wikidata SPARQL client (CC0 data). Respectful: descriptive User-Agent, >=2.5 s between calls, raw results cached on disk."""
import json, hashlib, os, time, urllib.request, urllib.parse
UA = "AvidaaWatchlistBuilder/1.0 (static film catalogue build; https://avidaa1.github.io/watchlist/)"
CACHE = os.environ.get("WL_CACHE", "/home/avidaa/+avidaa/work/watchlist_work")
os.makedirs(CACHE + "/raw", exist_ok=True)
_last = [0.0]
def query(q, tag="q", retries=3):
    h = hashlib.sha1(q.encode()).hexdigest()[:16]
    fn = "%s/raw/%s_%s.json" % (CACHE, tag, h)
    if os.path.exists(fn):
        return json.load(open(fn))["results"]["bindings"]
    for a in range(retries):
        wait = 2.5 - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        req = urllib.request.Request("https://query.wikidata.org/sparql",
            data=urllib.parse.urlencode({"query": q, "format": "json"}).encode(),
            headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
        try:
            _last[0] = time.time()
            raw = urllib.request.urlopen(req, timeout=70).read()
            j = json.loads(raw)
            open(fn, "wb").write(raw)
            return j["results"]["bindings"]
        except Exception as e:
            print("retry", a, tag, str(e)[:80], flush=True)
            time.sleep(8 * (a + 1))
    raise RuntimeError("query failed " + tag)
def v(b, k):
    return b[k]["value"] if k in b else None
def qid(uri):
    return uri.rsplit("/", 1)[-1]
