"""Generate compositions/captions.html from transcript/words.json.

Groups of 2-3 words (high-energy TikTok pacing), broken at punctuation,
pauses >= 150 ms or the word limit. The spoken word gets a lime pill.
Re-run after editing words.json: python3 scripts/build_captions.py
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORDS = json.loads((ROOT / "transcript" / "words.json").read_text())
DURATION = 43.2
MAX_WORDS = 3
MAX_CHARS = 18  # keeps a group on one line at a readable size
# Words that carry the point get the accent colour even when not spoken.
KEYWORDS = {"SA", "LOAN", "APPROVE", "HATI-HATI", "BANK", "KEPUTUSAN", "AKHIR", "LAYAK",
            "TAK", "HARAPAN", "PALSU", "PERODUA", "BIO", "JUJUR", "SEMAKAN"}

groups, cur = [], []
for i, w in enumerate(WORDS):
    cur.append(w)
    nxt = WORDS[i + 1] if i + 1 < len(WORDS) else None
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
        txt = w["text"].strip(",.?!").upper()
        if w["text"].endswith("?"):
            txt += "?"
        kw = " kw" if txt.strip("?") in KEYWORDS else ""
        spans.append(
            f'<span class="cw{kw}" id="cap-{w["id"]}"><span class="cw-bg"></span>'
            f'<span class="cw-t">{html.escape(txt)}</span></span>'
        )
        js.append(f'  word("#cap-{w["id"]}", {w["start"]:.2f}, {max(w["end"], w["start"] + 0.12):.2f});')
    # Take 1 frames the face low, so its captions sit above the head; later takes use the chest.
    top = 664 if g[0]["seg"] <= 3 else 1190
    # one line: shrink the type to fit the group instead of wrapping
    chars = sum(len(w["text"]) for w in g) + len(g) - 1
    size = max(60, min(74, int(860 / (chars * 0.74))))  # below 60 px: wrap to two lines instead
    rows.append(
        f'    <div class="cg" id="cap-g{gi}" style="top: {top}px">'
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
      top: 1190px;
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
      background: rgba(8, 10, 14, 0.46);
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
print(f"{len(groups)} caption groups, {len(WORDS)} words")
