"""Clean the a-roll transcript (whisper medium, Malay) into caption words.

Fixes misheard words, merges split tokens and drops the filler token the
model heard between "abang" and "ada". Times are on the cut timeline.
"""
import json
w = json.load(open("src/transcript-aroll.json"))
FIX = {0: "Nak", 13: "penjamin", 46: "terawal", 59: "rebate", 67: "WhatsApp", 70: "bawah,", 63: "akal,", 75: "yo!"}
DROP = {4, 16}
MERGE = {38: (39, "sangat-sangatnya."), 51: (52, "sesiapa"), 71: (73, "InsyaAllah,")}
out, skip = [], set()
for i, x in enumerate(w):
    if i in skip: continue
    t, s, e = FIX.get(i, x["text"]), x["start"], x["end"]
    if i in DROP:
        out[-1]["end"] = round(e, 3); continue
    if i in MERGE:
        j, t = MERGE[i]; e = w[j]["end"]; skip.update(range(i + 1, j + 1))
    out.append({"id": f"w{len(out)}", "text": t, "start": round(s, 3), "end": round(e, 3)})
# the clip opens mid-way into "Nak": whisper hears one token for "Nak beli"
out[0:1] = [{"text": "Nak", "start": 0.03, "end": 0.14}, {"text": "beli", "start": 0.14, "end": 0.31}]
# "nombor WhatsApp saya" was cut from the a-roll (edl.py): drop those words, pull later ones in
CUT_AT, CUT_LEN = 20.4333, 0.7667
out = [x for x in out if not (CUT_AT - 0.1 <= x["start"] < CUT_AT + CUT_LEN - 0.05 and x["text"] in ("nombor", "WhatsApp", "saya"))]
for x in out:
    if x["start"] >= CUT_AT:
        x["start"] = round(x["start"] - CUT_LEN, 3); x["end"] = round(x["end"] - CUT_LEN, 3)
for k, x in enumerate(out): x["id"] = f"w{k}"
json.dump(out, open("src/words.json", "w"), ensure_ascii=False, indent=0)
print(" ".join(x["text"] for x in out))
