"""Classification rules for the WATCHLIST finder (documented, transparent).
A work is a CANDIDATE for a category when it has instance-of (P31) one of WORK_CLASSES AND at least one of:
  (a) main subject (P921) in the category SUBJECTS list,
  (b) genre (P136) in the category GENRES list,
  (c) it is on the curated SEED list (title + year, resolved to a QID by exact English label + release year),
  (d) CURATED_QIDS added by hand after review.
Then the quality filter and the hand review (REMOVALS in wl_review.py) apply."""
WORK_CLASSES = {
  "Q11424": "film", "Q202866": "film", "Q226730": "film", "Q506240": "film",
  "Q5398426": "series", "Q1259759": "series", "Q21191270": "documentary", "Q93204": "documentary",
  "Q24862": "film",  # short film is kept only if award/sitelinks pass; shown as film
  "Q116741207": "series",
}
CATS = {
 "ai": {"name": "AI: apocalypse, takeover, rogue AI, uprising, machine consciousness",
   "subjects": {"Q11660": "artificial intelligence", "Q11012": "robot", "Q181787": "android", "Q2993663": "artificial consciousness",
                "Q2264109": "artificial general intelligence", "Q2254427": "AI takeover", "Q237525": "technological singularity", "Q2488994": "sentience", "Q25933185": "AI in fiction"},
   "genres": {"Q25933185": "AI in fiction"}},
 "hackers": {"name": "Hackers and cyber (Mr. Robot class)",
   "subjects": {"Q1487": "hacker", "Q2144405": "hacking", "Q3083944": "hacker culture", "Q22685": "hacktivism", "Q10920": "Anonymous", "Q174526": "cyberpunk"},
   "genres": {"Q174526": "cyberpunk", "Q580850": "techno-thriller"}},
 "aliens": {"name": "Aliens and extraterrestrials",
   "subjects": {"Q181508": "extraterrestrial life", "Q2447078": "alien invasion", "Q2090195": "first contact", "Q421": "UFO", "Q15107669": "extraterrestrial intelligence", "Q1307329": "extraterrestrials in fiction"},
   "genres": {"Q1307329": "extraterrestrials in fiction"}},
 "cyberwar": {"name": "Cyber attacks and cyber war",
   "subjects": {"Q4071928": "cyberattack", "Q849340": "cyberwarfare", "Q926331": "ransomware", "Q1172486": "data breach", "Q1137004": "cyberterrorism",
                "Q3510521": "computer security", "Q29137": "cybercrime", "Q14001": "malware", "Q485": "computer virus", "Q180712": "computer worm"},
   "genres": {}},
 "crypto": {"name": "Crypto: Bitcoin, blockchain, exchanges, crashes, fraud",
   "subjects": {"Q131723": "Bitcoin", "Q13479982": "cryptocurrency", "Q25401607": "cryptocurrency exchange", "Q20514253": "blockchain"},
   "genres": {}},
 "westerns": {"name": "Westerns: classic, modern, neo-western, space-western",
   "subjects": {"Q21590660": "Western"},
   "genres": {"Q172980": "Western film", "Q212781": "Spaghetti Western", "Q491158": "revisionist Western", "Q116955088": "neo-Western",
              "Q78528852": "contemporary Western", "Q4235011": "space Western", "Q135246202": "space Western film", "Q7433678": "science fiction Western",
              "Q1278107": "Ostern", "Q8066387": "Zapata Western", "Q7988576": "Western on television", "Q21590660": "Western"}},
}
MIN_SITELINKS = 20
