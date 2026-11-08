"""compositions/captions.html from transcript/words.json.
Captions show only while the plate is full size (5.5-15.9 s and 19.25-22.1 s); in the hero
layouts the big type carries the words. One line, 1-3 words, upcoming words dim, each word
turns cream as it is spoken (the reference's reverse-karaoke).
usage: python3 scripts/build_captions.py transcript/words.json compositions/captions.html"""
import json, sys, html
words = json.load(open(sys.argv[1]))
words[49]["text"] = words[49]["text"].capitalize()   # a new sentence after the program reveal
# (first word index, last word index) per group, grouped by phrase
GROUPS = [(13, 14), (15, 16), (17, 19), (20, 22), (23, 25), (26, 28),
          (29, 31), (32, 33), (34, 35), (36, 38), (49, 49), (50, 51), (52, 54)]
WINDOWS = [(5.62, 15.84), (19.3, 21.95)]
LEAD, TAIL = 0.08, 0.3
win = lambda t: next(w for w in WINDOWS if w[0] - 1 <= t <= w[1] + 0.5)
spans = []
for gi, (a, b) in enumerate(GROUPS):
    lo, hi = win(words[a]["start"])
    start = max(lo, words[a]["start"] - LEAD)
    nxt = words[GROUPS[gi + 1][0]]["start"] - LEAD if gi + 1 < len(GROUPS) else 1e9
    end = min(hi, max(words[b]["end"] + TAIL, start + 0.5), nxt)
    spans.append((round(start, 2), round(end, 2), a, b))
markup, js = [], []
for gi, (s, e, a, b) in enumerate(spans):
    ws = "".join(f'<span class="cw" id="cap-{words[k]["id"]}">{html.escape(words[k]["text"].replace("FRESH", "“FRESH”"))}</span>' for k in range(a, b + 1))
    markup.append(f'    <div class="cg" id="cap-g{gi}"><div class="cbox">{ws}</div></div>')
    js.append(f'    show("#cap-g{gi}", {s}, {e});')
    for k in range(a, b + 1):
        js.append(f'    tl.to("#cap-{words[k]["id"]}", {{ color: CREAM, duration: 0.08, ease: "none" }}, {max(s, words[k]["start"])});')
TEMPLATE = open("scripts/captions.template.html").read()
out = TEMPLATE.replace("<!--GROUPS-->", "\n".join(markup)).replace("//TIMING", "\n".join(js))
open(sys.argv[2], "w").write(out)
for s, e, a, b in spans: print(s, e, " ".join(words[k]["text"] for k in range(a, b + 1)))
