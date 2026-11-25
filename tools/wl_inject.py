"""Inject (or refresh) the finder fragment into index.html between the WLF markers. Additions only: the section goes right before the Machine vs. Machine section.
Also sets CSP connect-src to 'self' (same-origin JSON) and adds a small anchor link to the hero meta line."""
import re, sys, os
here = os.path.dirname(os.path.abspath(__file__))
repo = os.path.dirname(here)
idx = os.path.join(repo, "index.html")
s = open(idx, encoding="utf-8").read()
frag = open(os.path.join(here, "finder_fragment.html"), encoding="utf-8").read()
if "<!--WLF-START-->" in s:
    s = re.sub(r"<!--WLF-START-->.*?<!--WLF-END-->", lambda m: frag.strip(), s, flags=re.S)
else:
    anchor = '<section class="vs-section" id="versus">'
    assert anchor in s
    s = s.replace(anchor, frag.strip() + "\n\n" + anchor, 1)
if "connect-src 'self'" not in s:
    s = s.replace("connect-src;", "connect-src 'self';", 1)
if 'id="wlf-jump"' not in s:
    s = s.replace('<span>STATUS <b>RECEIVING</b></span>', '<span>STATUS <b>RECEIVING</b></span>\n    <span><a id="wlf-jump" href="#finder" style="color:var(--cyan);display:inline-flex;align-items:center;min-height:44px">OPEN THE FINDER</a></span>', 1)
open(idx, "w", encoding="utf-8").write(s)
print("injected", len(s))
