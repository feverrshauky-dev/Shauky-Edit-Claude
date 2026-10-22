"""Word timings on the tight a-roll, from real ASR word timestamps.

The corrected words of each kept phrase (transcript/edl.json) are matched in
order to the ASR words (transcript/source-transcript.json). Matched words take
their ASR times; words the ASR misheard are spread by syllables between their
matched neighbours. ASR times drift over long segments, so each phrase is then
stretched onto its measured speech bounds before mapping into film time.
Usage: python3 scripts/align_words.py
"""
import difflib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
edl = json.loads((ROOT / "transcript" / "edl.json").read_text())
asr = [w for s in json.loads((ROOT / "transcript" / "source-transcript.json").read_text())["segments"] for w in s["words"]]


def norm(t):
    return re.sub(r"[^a-z]", "", t.lower())


def syl(t):
    return max(1, len(re.findall(r"[aeiou]+", t.lower())))


words = [{"seg": s["i"], "text": t} for s in edl["segments"] for t in s["text"].split()]
sm = difflib.SequenceMatcher(None, [norm(w["text"]) for w in words], [norm(w["text"]) for w in asr], autojunk=False)
for a, b, n in sm.get_matching_blocks():
    for k in range(n):
        words[a + k]["a0"], words[a + k]["a1"] = asr[b + k]["start"], asr[b + k]["end"]

out = []
for s in edl["segments"]:
    ws = [w for w in words if w["seg"] == s["i"]]
    # fill misheard words between matched neighbours (or the phrase's speech bounds)
    i = 0
    while i < len(ws):
        if "a0" in ws[i]:
            i += 1
            continue
        j = i
        while j < len(ws) and "a0" not in ws[j]:
            j += 1
        lo = ws[i - 1]["a1"] if i else s["speech"][0]
        hi = ws[j]["a0"] if j < len(ws) else s["speech"][1]
        total = sum(syl(w["text"]) for w in ws[i:j])
        t = lo
        for w in ws[i:j]:
            d = (hi - lo) * syl(w["text"]) / total
            w["a0"], w["a1"] = t, t + d
            t += d
        i = j
    # stretch the phrase onto its speech bounds, then into film time
    a0, a1 = ws[0]["a0"], ws[-1]["a1"]
    s0, s1 = s["speech"]
    k = (s1 - s0) / (a1 - a0) if a1 > a0 else 1.0
    for w in ws:
        st = s["start"] + (s0 + (w["a0"] - a0) * k) - s["src_start"]
        en = s["start"] + (s0 + (w["a1"] - a0) * k) - s["src_start"]
        out.append({"seg": s["i"], "text": w["text"], "start": round(max(st, s["start"]), 3), "end": round(min(en, s["end"]), 3)})

for n, w in enumerate(out):
    w["id"] = f"w{n}"
    # a word ends where the next one in its phrase starts
    if n + 1 < len(out) and out[n + 1]["seg"] == w["seg"]:
        w["end"] = round(min(max(w["end"], w["start"] + 0.08), out[n + 1]["start"]), 3)
out = [{"id": w["id"], "seg": w["seg"], "text": w["text"], "start": w["start"], "end": w["end"]} for w in out]
(ROOT / "transcript" / "words.json").write_text(json.dumps(out, ensure_ascii=False, indent=0))
for w in out:
    print(f'{w["id"]:>5} {w["seg"]:2d} {w["start"]:6.2f} {w["end"]:6.2f} {w["text"]}')
