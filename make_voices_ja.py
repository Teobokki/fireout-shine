"""Japanese NPC lines, generated OFFLINE at build time with Open JTalk (pyopenjtalk) + HTS voice "Mei"
(Nagoya Institute of Technology / MMDAgent, CC BY 3.0). Output: assets/voice/ja_<n>.wav + entries in index.json"""
import os, sys, json, wave, numpy as np, pyopenjtalk
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fs_lines import LINES_JA
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "voice")
idxp = os.path.join(OUT, "index.json"); idx = json.load(open(idxp, encoding="utf-8")) if os.path.exists(idxp) else {}
idx["ja"] = []
VAR = [(1.0, 0.0), (1.05, 2.0), (0.95, -1.5), (1.0, 3.5)]
for i, (dist, jp, en) in enumerate(LINES_JA):
    sp, ht = VAR[i % len(VAR)]
    x, sr = pyopenjtalk.tts(jp, speed=sp, half_tone=ht)
    n = int(len(x) * 16000 / sr); y = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)
    y = y / max(1, np.abs(y).max()) * 26000
    fn = "ja_%02d.wav" % i
    with wave.open(os.path.join(OUT, fn), "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(y.astype(np.int16).tobytes())
    idx["ja"].append({"file": fn, "district": dist, "text": jp, "en": en})
json.dump(idx, open(idxp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("ja voices ok", len(idx["ja"]))
