"""Word timings on the tight a-roll: whisper (small) run on assets/aroll.mp4, spellings corrected,
hyphenated doubles merged, whisper's hallucinated outro dropped, and a 0.05 s lead so a word lights
as it starts rather than after.
usage: python3 scripts/words.py transcript/aroll-whisper.json transcript/words.json"""
import json, sys
src, out = sys.argv[1], sys.argv[2]
FIX = {"Hanya": "Tanya", "memili": "memiliki", "sesih": "sesi", "Boleh": "boleh", "Mereka": "mereka"}
SHIFT_AFTER, SHIFT = 7.33, 0.07          # the a-roll was rebuilt with 'Tanya' 0.07 s longer
LEAD, END = 0.05, 25.5   # raw whisper time; after "bio." it hallucinated "Terima kasih kerana menonton"
raw = [w for s in json.load(open(src)) for w in s["words"]]
words = []
for w in raw:
    t, s, e = w["t"], w["s"], w["e"]
    if s >= END: continue
    if s >= SHIFT_AFTER: s, e = s + SHIFT, e + SHIFT
    t = FIX.get(t, t)
    if t.startswith("-") and words:              # graduan -graduan -> graduan-graduan
        words[-1]["text"] += t; words[-1]["end"] = round(e, 2); continue
    words.append({"text": t, "start": round(max(0, s - LEAD), 2), "end": round(e, 2)})
# whisper missed the 'dan' that opens the 11.97 s segment
i = next(k for k, w in enumerate(words) if w["start"] > 11.9)
words.insert(i, {"text": "dan", "start": 11.99, "end": 12.12})
words[0]["text"] = "Baru"
for k, w in enumerate(words): w["id"] = f"w{k}"
json.dump(words, open(out, "w"), ensure_ascii=False, indent=0)
for w in words: print(w["id"], w["start"], w["end"], w["text"])
