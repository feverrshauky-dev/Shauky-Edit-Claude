"""Word timings on the tight a-roll.

Phrase bounds come from whisper large-v3 run on assets/aroll.mp4 (Malay), snapped to the EDL cuts and energy dips; inside each
phrase the words are spread over its voiced 10 ms frames by syllable weight.
usage: python3 scripts/words.py <aroll 16k mono wav> transcript/words.json
"""
import json, re, sys, numpy as np, soundfile as sf
PHRASES = [
 (0.00, 1.85, "Abang Akak mesti pernah ada masalah"),
 (1.85, 3.77, "bila Abang Akak nak jual kereta lama,"),
 (3.80, 5.12, "baki loan masih lagi tinggi."),
 (5.12, 7.00, "Tapi dekat sini kita ada satu cara"),
 (7.00, 9.60, "Abang Akak boleh gunakan duit rebate kereta"),
 (9.60, 12.55, "sebagai duit untuk tutup loan kereta lama."),
 (12.55, 15.30, "Jadi kalau Abang Akak nak tahu macam mana caranya,"),
 (15.30, 16.50, "klik nombor saya di bio."),
 (16.50, 18.20, "InsyaAllah saya akan bantu Abang Akak"),
 (18.20, 18.82, "sampai jadi."),
 (18.82, 19.70, "Assalamualaikum."),
]
x, sr = sf.read(sys.argv[1], dtype="float32")
hop = sr // 100
db = np.array([20*np.log10(np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2))+1e-9) for i in range(len(x)//hop)])
db = np.convolve(db, np.ones(3)/3, mode="same")
thr = np.percentile(db, 10) + (np.percentile(db, 95) - np.percentile(db, 10)) * 0.30
syl = lambda w: max(1, len(re.findall(r"[aeiouAEIOU]+", w)))
words, wid = [], 0
for pi, (a0, b0, text) in enumerate(PHRASES):
    a, b = int(a0*100), min(int(b0*100), len(db))
    voiced = np.where(db[a:b] > thr)[0] + a
    if len(voiced) < 5: voiced = np.arange(a, b)
    toks = text.split()
    wts = np.array([syl(t) for t in toks], float); cum = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
    n = len(voiced)
    for k, t in enumerate(toks):
        i0 = voiced[min(int(cum[k]*n), n-1)]; i1 = voiced[min(int(cum[k+1]*n)-1, n-1)] + 1
        words.append({"id": f"w{wid}", "seg": pi, "text": t, "start": round(i0/100, 2), "end": round(max(i1, i0+8)/100, 2)})
        wid += 1
json.dump(words, open(sys.argv[2], "w"), ensure_ascii=False, indent=0)
for w in words: print(w["id"], w["seg"], w["start"], w["end"], w["text"])
