"""Word timings on the tight a-roll: spread each phrase's words over its voiced frames by syllable weight."""
import json, re, sys, numpy as np, soundfile as sf
edl = json.load(open(sys.argv[1])); x, sr = sf.read(sys.argv[2], dtype="float32")
hop = sr // 100
db = np.array([20*np.log10(np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2))+1e-9) for i in range(len(x)//hop)])
db = np.convolve(db, np.ones(3)/3, mode="same")
thr = np.percentile(db, 10) + (np.percentile(db, 95) - np.percentile(db, 10)) * 0.33
def syl(w):
    return max(1, len(re.findall(r"[aeiouAEIOU]+", w)))
words, wid = [], 0
for s in edl["segments"]:
    a, b = int(s["start"]*100), int(s["end"]*100)
    voiced = np.where(db[a:b] > thr)[0] + a
    if len(voiced) < 5: voiced = np.arange(a, b)
    toks = s["text"].split()
    wts = np.array([syl(t) for t in toks], float); cum = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
    n = len(voiced)
    for k, t in enumerate(toks):
        i0 = voiced[min(int(cum[k]*n), n-1)]; i1 = voiced[min(int(cum[k+1]*n)-1, n-1)] + 1
        words.append({"id": f"w{wid}", "seg": s["i"], "text": t, "start": round(i0/100, 2), "end": round(max(i1, i0+8)/100, 2)})
        wid += 1
json.dump(words, open(sys.argv[3], "w"), ensure_ascii=False, indent=0)
for w in words: print(w["id"], w["seg"], w["start"], w["end"], w["text"])
