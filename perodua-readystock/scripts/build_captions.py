"""Build compositions/captions.html from transcript/words.json.
Captions run only where no title graphic speaks for the line; they sit at the top of the safe band (y 392) above the face."""
import json, html
W = json.load(open("transcript/words.json"))
# (first word id, last word id) per group; windows: place 5.34-9.87, sesuai 14.97-19.63, cta lead 26.9-29.5
GROUPS = [(17, 19), (20, 22), (23, 26), (27, 28), (29, 30),
          (45, 47), (48, 50), (51, 51), (52, 54), (55, 56),
          (81, 82), (83, 85), (86, 87)]
HL = {18: "o", 21: "o", 29: "y", 30: "y", 50: "o", 51: "y", 56: "o", 85: "o", 86: "y"}
WINDOW_END = {30: 9.82, 56: 19.6, 87: 29.48}
words = {int(w["id"][1:]): w for w in W}
CLEAN = {"ni,": "NI,", "3S": "3S"}
groups = []
for gi, (a, b) in enumerate(GROUPS):
    ws = [words[i] for i in range(a, b + 1)]
    start = round(max(0.0, ws[0]["start"] - 0.06), 3)
    if b in WINDOW_END:
        end = WINDOW_END[b]
    else:
        nxt = GROUPS[gi + 1][0]
        end = round(words[nxt]["start"] - 0.06, 3)
    text = " ".join(w["text"].upper() for w in ws)
    n = len(text)
    fs = int(min(90, 760 / (n * 0.66)))
    groups.append({"id": f"g{gi}", "start": start, "end": end, "fs": fs,
                   "words": [{"i": w_i, "t": words[w_i]["text"].upper(), "s": words[w_i]["start"]} for w_i in range(a, b + 1)]})
markup = []
for g in groups:
    spans = "".join(
        f'<span class="w{(" hl-" + HL[w["i"]]) if w["i"] in HL else ""}" id="w{w["i"]}">{html.escape(w["t"])}</span> '
        for w in g["words"])
    markup.append(f'    <div class="cg" id="{g["id"]}" style="font-size:{g["fs"]}px">{spans.strip()}</div>')
data = json.dumps([{"id": g["id"], "start": g["start"], "end": g["end"],
                    "words": [{"id": f'w{w["i"]}', "s": w["s"], "hl": HL.get(w["i"])} for w in g["words"]]} for g in groups])
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
      top: 392px;
      width: 100%;
      padding: 0 120px;
      text-align: center;
      font-family: "Inter", sans-serif;
      font-weight: 900;
      line-height: 1.08;
      letter-spacing: -0.01em;
      color: #ffffff;
      -webkit-text-stroke: 10px #0a1630;
      paint-order: stroke fill;
      text-shadow: 0 8px 0 #0a1630;
      white-space: nowrap;
      overflow: visible;
      opacity: 0;
    }}
    .w {{
      display: inline-block;
      margin: 0 0.06em;
      opacity: 0;
    }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(markup)}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
    const G = {data};
    const COL = {{ o: "#ff5b1f", y: "#ffd43b" }};
    G.forEach((g) => {{
      const el = "#" + g.id;
      tl.set(el, {{ opacity: 1 }}, g.start);
      g.words.forEach((w) => {{
        const t = Math.max(g.start + 0.02, w.s);
        const to = {{ opacity: 1, scale: 1, duration: 0.16, ease: "power3.out", immediateRender: false }};
        if (w.hl) to.color = COL[w.hl];
        tl.fromTo("#" + w.id, {{ opacity: 0, scale: 1.3, y: 12 }}, Object.assign(to, {{ y: 0 }}), t);
      }});
      tl.to(el, {{ opacity: 0, duration: 0.1, ease: "power2.in" }}, g.end - 0.1);
      tl.set(el, {{ opacity: 0, visibility: "hidden" }}, g.end);
    }});
    window.__timelines["captions"] = tl;
  </script>
</template>
"""
open("compositions/captions.html", "w").write(out)
for g in groups: print(g["id"], g["start"], g["end"], g["fs"], " ".join(w["t"] for w in g["words"]))
