"""Generate compositions/captions.html from transcript/words.json.

Sticker captions: Archivo Black, white fill with a thick ink outline and a hard
drop; the spoken word turns sunflower and tips a few degrees. Keywords stay
sunflower. Groups are hand-picked so the hook card and the CTA button (which
carry those words themselves) are never doubled by a caption.

  TOP  = above the head, over the sky (full-bleed shots)
  SLOT = between the infographic and the shrunken camera card (split layout)

Re-run after editing words.json: python3 scripts/build_captions.py
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
W = {w["id"]: w for w in json.loads((ROOT / "transcript" / "words.json").read_text())}
DURATION = 20.03
TOP, SLOT = 318, 576
KEYWORDS = {"CARA", "REBATE", "TUTUP", "LOAN", "CARANYA?", "BANTU", "SATU", "SAMPAI", "JADI"}

# (first word, last word, position, hold-until override)
GROUPS = [
    (18, 20, TOP, None),    # TAPI DEKAT SINI
    (21, 22, TOP, None),    # KITA ADA
    (23, 24, TOP, 7.02),    # SATU CARA
    (25, 27, SLOT, None),   # ABANG AKAK BOLEH
    (28, 29, SLOT, None),   # GUNAKAN DUIT
    (30, 31, SLOT, None),   # REBATE KERETA
    (32, 33, SLOT, None),   # SEBAGAI DUIT
    (34, 35, SLOT, None),   # UNTUK TUTUP
    (36, 38, SLOT, 12.62),  # LOAN KERETA LAMA
    (39, 42, TOP, None),    # JADI KALAU ABANG AKAK
    (43, 44, TOP, None),    # NAK TAHU
    (45, 47, TOP, 15.3),    # MACAM MANA CARANYA?
    (53, 55, SLOT, None),   # INSYAALLAH SAYA AKAN
    (56, 58, SLOT, None),   # BANTU ABANG AKAK
    (59, 60, SLOT, None),   # SAMPAI JADI (replaces the old stamp)
    (61, 61, SLOT, 19.66),  # ASSALAMUALAIKUM, then the outro takes the frame
]


def est_width(words, size):
    # Archivo Black caps average ~0.74 em; word gap 0.3 em
    return sum(len(t) for t in words) * 0.74 * size + (len(words) - 1) * 0.3 * size


rows, js = [], []
for gi, (a, b, top, hold) in enumerate(GROUPS):
    ws = [W[f"w{i}"] for i in range(a, b + 1)]
    start = ws[0]["start"] - 0.04
    if gi == 0:
        start = 5.32  # wait for the hook card to whip off
    if gi == 9:
        start = 12.8  # wait for the infographic to clear
    nxt = GROUPS[gi + 1] if gi + 1 < len(GROUPS) else None
    nxt_start = W[f"w{nxt[0]}"]["start"] - 0.04 if nxt else DURATION
    end = hold if hold is not None else min(ws[-1]["end"] + 0.3, nxt_start)
    end = max(end, ws[-1]["end"])
    texts = []
    spans = []
    for w in ws:
        txt = w["text"].strip(",.!").upper()
        texts.append(txt)
        kw = " kw" if txt in KEYWORDS else ""
        spans.append(f'<span class="cw{kw}" id="cap-{w["id"]}">{html.escape(txt)}</span>')
        ws_ = max(w["start"], start)
        js.append(f'  word("#cap-{w["id"]}", {ws_:.2f}, {max(w["end"], ws_ + 0.14):.2f});')
    base = 92 if top == TOP else 80
    size = base
    while est_width(texts, size) > 920 and size > 54:
        size -= 2
    rows.append(
        f'    <div class="cg" id="cap-g{gi}" style="top: {top}px; font-size: {size}px">{" ".join(spans)}</div>'
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
      padding: 0 60px;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      align-items: center;
      gap: 0 0.28em;
      text-align: center;
      opacity: 0;
      visibility: hidden;
      overflow: visible;
    }}
    .cw {{
      display: inline-block;
      font-family: "Archivo Black", sans-serif;
      font-size: inherit;
      line-height: 1.08;
      letter-spacing: 0.005em;
      color: #ffffff;
      -webkit-text-stroke: 0.16em #141414;
      paint-order: stroke fill;
      text-shadow: 0 0.09em 0 #141414;
      transform-origin: 50% 70%;
    }}
    .cw.kw {{
      color: #ffc93c;
    }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(rows)}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
    function group(sel, start, end) {{
      tl.set(sel, {{ visibility: "visible", opacity: 1 }}, start);
      tl.to(sel, {{ opacity: 0, filter: "blur(6px)", duration: 0.12, ease: "power2.in" }}, Math.max(end - 0.12, start + 0.2));
      tl.set(sel, {{ opacity: 0, visibility: "hidden", filter: "blur(0px)" }}, end);
    }}
    function word(sel, start, end) {{
      // each word pops up as it is spoken, turns sunflower and tips, then settles white
      tl.fromTo(sel, {{ opacity: 0, y: 26, scale: 0.7 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.2, ease: "back.out(2.2)" }}, start);
      if (!document.querySelector(sel).classList.contains("kw")) {{
        tl.fromTo(sel, {{ color: "#ffffff" }}, {{ color: "#ffc93c", duration: 0.05 }}, start);
        tl.to(sel, {{ color: "#ffffff", duration: 0.12 }}, end);
      }}
      tl.fromTo(sel, {{ rotation: 0 }}, {{ rotation: -3, duration: 0.12, ease: "power2.out" }}, start);
      tl.to(sel, {{ rotation: 0, duration: 0.16, ease: "power2.out" }}, end);
    }}
{chr(10).join(js)}
    window.__timelines["captions"] = tl;
  </script>
</template>
"""
(ROOT / "compositions" / "captions.html").write_text(out)
print(f"{len(GROUPS)} caption groups")
