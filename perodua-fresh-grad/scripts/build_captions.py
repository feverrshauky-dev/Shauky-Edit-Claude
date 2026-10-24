"""Generate compositions/captions.html from transcript/words.json.

Same look as the SA video: groups of 2-3 words, broken at punctuation,
pauses >= 150 ms or the word limit, and the spoken word gets a lime pill.
Spelled-out numbers read as figures on screen ("empat ratus lima puluh"
becomes RM450). Re-run after editing words.json: python3 scripts/build_captions.py
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORDS = json.loads((ROOT / "transcript" / "words.json").read_text())
DURATION = 89.5
TOP = 1530  # below every scene's content, above the TikTok caption/UI band
MAX_WORDS = 3
MAX_CHARS = 18  # keeps a group on one line at a readable size
# Words that carry the point get the accent colour even when not spoken.
KEYWORDS = {"PERODUA", "JANGAN", "SIGN", "BAJET", "MODEL", "POKET", "AXIA", "BEZZA", "MYVI", "NGAM-NGAM",
            "DOKUMEN", "CCRIS", "CTOS", "PTPTN", "DITOLAK", "SETTLE", "TERSEMBUNYI", "KUNCI", "SAVE",
            "SHARE", "BIO"}
DIGITS = {"satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5, "enam": 6, "tujuh": 7, "lapan": 8, "sembilan": 9}
NUM_WORDS = set(DIGITS) | {"sepuluh", "belas", "puluh", "ratus", "ribu"}
SAY_AS = {"I-C": "IC", "K-W-S-P": "KWSP"}


def bare(w):
    return w["text"].strip(",.?!").lower()


def value(ws):
    total, cur = 0, 0
    for w in ws:
        t = bare(w)
        if t in DIGITS:
            cur += DIGITS[t]
        elif t == "sepuluh":
            cur += 10
        elif t == "belas":
            cur += 10
        elif t == "puluh":
            cur *= 10
        elif t == "ratus":
            total += cur * 100
            cur = 0
        elif t == "ribu":
            total = (total + cur) * 1000
            cur = 0
    return total + cur


# Collapse spoken numbers into one display token. A lone step word ("Satu.")
# stays a word; money (>= 100, or followed by "ringgit") gets "RM"; "peratus"
# after a number becomes "%".
tokens, i = [], 0
while i < len(WORDS):
    w = WORDS[i]
    sentence_alone = w["text"][-1] in ".?!" and (i == 0 or WORDS[i - 1]["text"][-1] in ".?!")
    if bare(w) in NUM_WORDS and not sentence_alone:
        j = i
        while j < len(WORDS) and bare(WORDS[j]) in NUM_WORDS and (j == i or WORDS[j - 1]["text"][-1] not in ",.?!"):
            j += 1
        run = WORDS[i:j]
        v = value(run)
        end, tail = run[-1]["end"], run[-1]["text"][-1] if run[-1]["text"][-1] in ",.?!" else ""
        txt = f"{v:,}"
        money = v >= 100
        if j < len(WORDS) and bare(WORDS[j]) == "ringgit":
            money, end = True, WORDS[j]["end"]
            tail = WORDS[j]["text"][-1] if WORDS[j]["text"][-1] in ",.?!" else ""
            j += 1
        elif j < len(WORDS) and bare(WORDS[j]) == "peratus":
            txt += "%"
            end = WORDS[j]["end"]
            tail = WORDS[j]["text"][-1] if WORDS[j]["text"][-1] in ",.?!" else ""
            j += 1
        if money:
            txt = "RM" + txt
        tokens.append({"id": run[0]["id"], "seg": run[0]["seg"], "start": run[0]["start"], "end": end,
                       "text": txt + tail, "kw": True})
        i = j
        continue
    core = w["text"].strip(",.?!")
    tail = w["text"][len(core):]
    tokens.append({**w, "text": SAY_AS.get(core, core) + tail, "kw": False})
    i += 1

groups, cur = [], []
for i, w in enumerate(tokens):
    cur.append(w)
    nxt = tokens[i + 1] if i + 1 < len(tokens) else None
    brk = (
        nxt is None
        or len(cur) >= MAX_WORDS
        or w["text"][-1] in ",.?!"
        or nxt["start"] - w["end"] >= 0.15
        or nxt["seg"] != w["seg"]
        or sum(len(x["text"]) + 1 for x in cur) + len(nxt["text"]) > MAX_CHARS
    )
    if brk:
        groups.append(cur)
        cur = []

# a group too short to read joins its neighbour in the same phrase
merged = []
for g in groups:
    if merged:
        prev = merged[-1]
        short = g[-1]["end"] - g[0]["start"] < 0.32 or prev[-1]["end"] - prev[0]["start"] < 0.32
        fits = sum(len(x["text"]) + 1 for x in prev + g) - 1 <= MAX_CHARS + 4
        if short and prev[-1]["seg"] == g[0]["seg"] and len(prev) + len(g) <= 4 and fits:
            merged[-1] = prev + g
            continue
    merged.append(g)
groups = merged

rows, js = [], []
for gi, g in enumerate(groups):
    start = max(g[0]["start"], 0.15) if gi == 0 else g[0]["start"]
    nxt_start = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else DURATION
    end = min(g[-1]["end"] + 0.35, nxt_start)
    end = max(end, g[-1]["end"])
    spans = []
    for w in g:
        txt = w["text"].strip(",.!").upper()
        kw = " kw" if w["kw"] or txt.strip("?") in KEYWORDS else ""
        spans.append(
            f'<span class="cw{kw}" id="cap-{w["id"]}"><span class="cw-bg"></span>'
            f'<span class="cw-t">{html.escape(txt)}</span></span>'
        )
        js.append(f'  word("#cap-{w["id"]}", {w["start"]:.2f}, {max(w["end"], w["start"] + 0.12):.2f});')
    # one line: shrink the type to fit the group instead of wrapping
    chars = sum(len(w["text"]) for w in g) + len(g) - 1
    size = max(56, min(70, int(860 / (chars * 0.74))))
    rows.append(
        f'    <div class="cg" id="cap-g{gi}" style="top: {TOP}px">'
        f'<div class="cg-in" style="font-size: {size}px">{" ".join(spans)}</div></div>'
    )
    js.append(f'  group("#cap-g{gi}", {start:.2f}, {end:.2f});')

out = f"""<template>
  <style>
    #root {{
      position: absolute;
      inset: 0;
      pointer-events: none;
    }}
    .cg {{
      position: absolute;
      left: 0;
      width: 100%;
      top: {TOP}px;
      padding: 0 70px;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      align-items: center;
      gap: 6px 14px;
      text-align: center;
      opacity: 0;
      visibility: hidden;
      overflow: visible;
    }}
    .cg-in {{
      display: inline-flex;
      flex-wrap: wrap;
      justify-content: center;
      align-items: center;
      gap: 6px 10px;
      max-width: 940px;
      padding: 12px 16px 14px;
      border-radius: 26px;
      background: rgba(8, 10, 14, 0.6);
    }}
    .cw {{
      position: relative;
      display: inline-block;
      padding: 4px 14px 8px;
      font-family: "Montserrat", sans-serif;
      font-weight: 800;
      font-size: inherit;
      line-height: 1;
      letter-spacing: 0.01em;
      color: #ffffff;
      text-shadow:
        0 0 2px rgba(0, 0, 0, 0.9),
        0 4px 0 rgba(0, 0, 0, 0.55),
        0 8px 22px rgba(0, 0, 0, 0.55);
    }}
    .cw.kw .cw-t {{
      color: var(--lime, #c8ec3c);
    }}
    .cw-t {{
      position: relative;
      z-index: 1;
    }}
    .cw-bg {{
      position: absolute;
      inset: 0;
      border-radius: 14px;
      background: var(--lime, #c8ec3c);
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.35);
      transform-origin: 0% 50%;
      opacity: 0;
      z-index: 0;
    }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(rows)}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
    function group(sel, start, end) {{
      tl.set(sel, {{ visibility: "visible" }}, start);
      tl.fromTo(sel, {{ opacity: 0, y: 18, scale: 0.94 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.16, ease: "expo.out" }}, start);
      tl.to(sel, {{ opacity: 0, duration: 0.1, ease: "power2.in" }}, Math.max(end - 0.1, start + 0.17));
      tl.set(sel, {{ opacity: 0, visibility: "hidden" }}, end);
    }}
    function word(sel, start, end) {{
      const bg = sel + " .cw-bg";
      const t = sel + " .cw-t";
      tl.fromTo(bg, {{ opacity: 0, scaleX: 0 }}, {{ opacity: 1, scaleX: 1, duration: 0.12, ease: "power3.out" }}, start);
      tl.fromTo(t, {{ color: "#ffffff", textShadow: "0 0 0 rgba(0,0,0,0)" }}, {{ color: "#0e1116", textShadow: "0 0 0 rgba(0,0,0,0)", duration: 0.06 }}, start);
      tl.fromTo(sel, {{ scale: 1 }}, {{ scale: 1.08, duration: 0.1, ease: "power2.out" }}, start);
      tl.to(sel, {{ scale: 1, duration: 0.14, ease: "power2.out" }}, end);
      tl.to(bg, {{ opacity: 0, duration: 0.1, ease: "power2.in" }}, end);
      tl.set(t, {{ clearProps: "color,textShadow" }}, end + 0.06);
    }}
{chr(10).join(js)}
    window.__timelines["captions"] = tl;
  </script>
</template>
"""
(ROOT / "compositions" / "captions.html").write_text(out)
print(f"{len(groups)} caption groups, {len(tokens)} tokens")
for g in groups:
    print(f'{g[0]["start"]:6.2f}  ' + " ".join(w["text"] for w in g))
