"""Generate compositions/captions.html from transcript/words.json.

Phrase captions of 2-4 words, broken at punctuation, pauses >= 150 ms or the
word limit. Captions stay plain; only a few chosen words take the accent, and
the verdict words become chips on the word itself (LAYAK, TAK LAYAK, a struck
HARAPAN PALSU), so no card has to cover the face.
Re-run after editing words.json: python3 scripts/build_captions.py
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORDS = json.loads((ROOT / "transcript" / "words.json").read_text())
DURATION = json.loads((ROOT / "transcript" / "edl.json").read_text())["duration"]
MAX_WORDS = 4
MAX_CHARS = 22
# (segment, word) pairs that take the accent: the point of each line, nothing else
ACCENT = {(2, "approve"), (3, "hati-hati."), (5, "semakan."), (7, "bersesuaian"), (8, "keputusan."),
          (12, "awal-awal"), (16, "Perodua,"), (16, "loan"), (17, "bio,")}
# the payoff scene shows these phrases as its own type, so their captions are left out
HIDDEN_SEGS = {10, 11}
# where each take's captions sit: under the chin, above TikTok's caption zone (y 1330)
def top_for(seg):
    if seg <= 3:
        return 584  # take 1 frames the face low: between the hook title and the head
    if seg <= 11:
        return 1176
    return 1222


def clean(t):
    return t.strip(",.")


groups, cur = [], []
for i, w in enumerate(WORDS):
    if w["seg"] in HIDDEN_SEGS:
        continue
    cur.append(w)
    nxt = WORDS[i + 1] if i + 1 < len(WORDS) else None
    joined = lambda ws: sum(len(clean(x["text"])) + 1 for x in ws) - 1
    pair = nxt is not None and clean(w["text"]).lower() == "tak" and clean(nxt["text"]).lower() == "layak"
    # never strand the word that closes a clause on its own
    closes = (nxt is not None and nxt["seg"] == w["seg"] and nxt["text"][-1] in ",.?!" and w["text"][-1] not in ",.?!"
              and nxt["start"] - w["end"] < 0.15 and len(cur) < 5 and joined(cur + [nxt]) <= MAX_CHARS + 4
              and clean(nxt["text"]).lower() != "layak")
    pair = pair or closes
    brk = (
        nxt is None
        or nxt["seg"] in HIDDEN_SEGS
        or w["text"][-1] in ",.?!"
        or nxt["seg"] != w["seg"]
        or nxt["start"] - w["end"] >= 0.15
        or (len(cur) >= MAX_WORDS and not pair)
        or (joined(cur + [nxt]) > MAX_CHARS and not pair)
    )
    if brk:
        groups.append(cur)
        cur = []

# a group too short to read joins its neighbour in the same phrase
merged = []
for g in groups:
    if merged:
        prev = merged[-1]
        short = g[-1]["end"] - g[0]["start"] < 0.34 or prev[-1]["end"] - prev[0]["start"] < 0.34
        fits = sum(len(clean(x["text"])) + 1 for x in prev + g) - 1 <= MAX_CHARS + 2
        if short and prev[-1]["seg"] == g[0]["seg"] and prev[-1]["text"][-1] not in ".?" and len(prev) + len(g) <= 5 and fits:
            merged[-1] = prev + g
            continue
    merged.append(g)
groups = merged

CHECK = '<svg viewBox="0 0 24 24"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>'
CROSS = '<svg viewBox="0 0 24 24"><path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/></svg>'


def word_span(w, txt, cls="cw"):
    return f'<span class="{cls}" id="cap-{w["id"]}">{html.escape(txt)}</span>'


rows, js = [], []
for gi, g in enumerate(groups):
    start = max(g[0]["start"] - 0.04, 0.12)
    nxt_start = groups[gi + 1][0]["start"] - 0.04 if gi + 1 < len(groups) else DURATION
    end = min(g[-1]["end"] + 0.3, nxt_start - 0.02)
    if gi + 1 < len(groups) and groups[gi + 1][0]["seg"] in HIDDEN_SEGS:
        end = min(end, groups[gi + 1][0]["start"])
    parts, k, chars = [], 0, 0
    while k < len(g):
        w = g[k]
        txt = w["text"].rstrip(",.") if not w["text"].endswith("?") else w["text"]
        low = clean(w["text"]).lower()
        nxt = g[k + 1] if k + 1 < len(g) else None
        if low == "tak" and nxt and clean(nxt["text"]).lower() == "layak" and w["seg"] in (13, 14):
            parts.append(f'<span class="chip chip-no" id="cap-chip-{w["id"]}">{CROSS}'
                         f'{word_span(w, "TAK")} {word_span(nxt, "LAYAK")}</span>')
            js.append(f'  chip("#cap-chip-{w["id"]}", {w["start"]:.2f});')
            chars += 9 + 3
            k += 2
            continue
        if low == "layak" and w["seg"] in (13, 14):
            parts.append(f'<span class="chip chip-yes" id="cap-chip-{w["id"]}">{CHECK}{word_span(w, "LAYAK")}</span>')
            js.append(f'  chip("#cap-chip-{w["id"]}", {w["start"]:.2f});')
            chars += 5 + 3
            k += 1
            continue
        if low == "harapan" and nxt and clean(nxt["text"]).lower() == "palsu":
            parts.append(f'<span class="chip chip-palsu" id="cap-chip-{w["id"]}">'
                         f'{word_span(w, "HARAPAN")} {word_span(nxt, "PALSU")}<i class="strike"></i></span>')
            js.append(f'  chip("#cap-chip-{w["id"]}", {w["start"]:.2f});')
            js.append(f'  strike("#cap-chip-{w["id"]} .strike", {nxt["end"] - 0.06:.2f});')
            chars += 13 + 2
            k += 2
            continue
        cls = "cw acc" if (w["seg"], w["text"]) in ACCENT else "cw"
        parts.append(word_span(w, txt, cls))
        chars += len(txt) + 1
        k += 1
    # one line at a readable size: Inter 800 runs about 0.6 em a character
    size = max(48, min(66, int(900 / (max(chars, 1) * 0.6))))
    rows.append(
        f'    <div class="cg" id="cap-g{gi}" style="top: {top_for(g[0]["seg"])}px">'
        f'<div class="cg-in" style="font-size: {size}px">{" ".join(parts)}</div></div>'
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
      padding: 0 70px;
      text-align: center;
      opacity: 0;
      visibility: hidden;
      overflow: visible;
    }}
    .cg-in {{
      display: inline-block;
      max-width: 940px;
      padding: 10px 24px 16px;
      border-radius: 14px;
      background: rgba(11, 13, 16, 0.56);
      font-family: "Inter", sans-serif;
      font-weight: 800;
      line-height: 1.1;
      letter-spacing: -0.01em;
      color: #ffffff;
      white-space: nowrap;
      text-shadow: 0 2px 10px rgba(0, 0, 0, 0.45);
    }}
    .cw {{
      display: inline-block;
    }}
    .acc {{
      color: var(--lime, #c6e83a);
    }}
    .chip {{
      position: relative;
      display: inline-flex;
      align-items: center;
      gap: 0.18em;
      margin: 0 0.06em;
      padding: 0.06em 0.34em 0.1em 0.24em;
      border-radius: 10px;
      font-family: "Oswald", sans-serif;
      font-weight: 700;
      letter-spacing: 0.02em;
      text-shadow: none;
      vertical-align: middle;
    }}
    .chip svg {{
      width: 0.8em;
      height: 0.8em;
      fill: none;
      stroke: currentColor;
      stroke-width: 3.2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
    .chip-yes {{
      background: #1fa35a;
      color: #ffffff;
    }}
    .chip-no {{
      background: #ff4a3d;
      color: #ffffff;
    }}
    .chip-palsu {{
      padding: 0.06em 0.3em 0.1em;
      background: #f4f6f8;
      color: #0b0d10;
    }}
    .strike {{
      position: absolute;
      left: 0.16em;
      right: 0.16em;
      top: 52%;
      height: 0.14em;
      border-radius: 0.07em;
      background: #ff4a3d;
      transform-origin: 0% 50%;
      transform: scaleX(0);
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
      tl.fromTo(sel, {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.12, ease: "power2.out" }}, start);
      tl.to(sel, {{ opacity: 0, duration: 0.08, ease: "power2.in" }}, Math.max(end - 0.08, start + 0.13));
      tl.set(sel, {{ opacity: 0, visibility: "hidden" }}, end);
    }}
    // a verdict chip lands on its word
    function chip(sel, at) {{
      tl.fromTo(sel, {{ scale: 0.6 }}, {{ scale: 1, duration: 0.32, ease: "back.out(1.7)" }}, at);
    }}
    function strike(sel, at) {{
      tl.fromTo(sel, {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.22, ease: "power3.out" }}, at);
    }}
{chr(10).join(js)}
    window.__timelines["captions"] = tl;
  </script>
</template>
"""
(ROOT / "compositions" / "captions.html").write_text(out)
print(f"{len(groups)} groups")
for gi, g in enumerate(groups):
    print(f'g{gi:<3} {g[0]["start"]:6.2f}-{g[-1]["end"]:6.2f}  ' + " ".join(w["text"] for w in g))
