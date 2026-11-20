"""Write compositions/captions.html from src/words.json.

Sticker-style karaoke captions: 1-3 uppercase words per group, white with a
thick ink outline, the spoken word turns sun-yellow and kicks up; keywords
sit on a hot-red tape. Groups sit under the face, and move to the top band
while the problem stickers cover the lower frame (TOP_WINDOWS).
"""
import json, re, html
W = json.load(open("src/words.json"))
KEY = {"masalah", "tiada", "lesen", "deposit", "penjamin", "maaf", "lima", "terawal", "sahaja",
       "baru", "rebate", "akal", "whatsapp", "klik", "sekarang"}
# TikTok/Reels clear area: y 269-1248; below y 840 only x 120-780 (right-hand buttons)
TOP_WINDOWS = [(4.55, 6.28)]      # lower frame is busy with the cover stickers: captions go up top
MUTE = [(6.28, 7.867)]            # the numbered problem list says these words ("macam ni" x3)
BOTTOM_Y, TOP_Y = 1122, 282
# group starts (word indices), chosen by phrase: 1-3 words, never across a cut into the top band
STARTS = [0, 3, 6, 7, 9, 11, 13, 14, 17, 20, 22, 25, 28, 31, 33, 36, 37, 38, 41, 43, 45, 46, 48, 50, 52, 54, 55, 57, 59, 61, 63, 65, 66]
groups = [W[a:b] for a, b in zip(STARTS, STARTS[1:] + [len(W)])]
rows, js = [], []
for gi, g in enumerate(groups):
    start = g[0]["start"] - 0.06
    nxt = groups[gi + 1][0]["start"] - 0.06 if gi + 1 < len(groups) else 24.0
    end = min(g[-1]["end"] + 0.35, nxt)
    if gi == 0: start = 0.0
    if any(a <= g[0]["start"] < b for a, b in MUTE): continue
    for a, b in MUTE:
        if start < a < end: end = a
    chars = sum(len(x["text"].strip(",.!?")) for x in g) + len(g) - 1
    mid = (start + end) / 2
    top = any(a <= mid <= b for a, b in TOP_WINDOWS)
    y = TOP_Y if top else BOTTOM_Y
    size = int(min(76 if top else 74, (800 if top else 620) / (chars * 0.8)))
    words = []
    for w in g:
        t = w["text"].strip(",.!?").upper()
        kw = re.sub(r"[^a-z]", "", w["text"].lower()) in KEY
        words.append(f'<span class="cw{" kw" if kw else ""}" id="cap-{w["id"]}"><span class="cw-tape"></span><span class="cw-t">{html.escape(t)}</span></span>')
    rows.append(f'    <div class="cg" id="cap-g{gi}" style="top: {y}px; font-size: {size}px; {'left: 120px; width: 840px' if top else 'left: 120px; width: 660px'}">{" ".join(words)}</div>')
    js.append(f'  G({gi}, {start:.3f}, {end:.3f}, [{", ".join(f"[{json.dumps(w["id"])}, {w["start"]:.3f}]" for w in g)}]);')
doc = """<template>
  <style>
    #root { position: absolute; inset: 0; pointer-events: none; }
    .cg {
      position: absolute; padding: 0;
      display: flex; flex-wrap: wrap; justify-content: center; align-items: center;
      gap: 0 0.22em; text-align: center; opacity: 0; visibility: hidden; overflow: visible;
    }
    .cw { position: relative; display: inline-block; line-height: 1; padding: 0.08em 0.12em 0.12em; }
    .cw-t {
      position: relative; z-index: 1; display: inline-block;
      font-family: "Archivo Black", sans-serif; color: #ffffff;
      -webkit-text-stroke: 0.15em #0f0f12; paint-order: stroke fill;
      text-shadow: 0.06em 0.07em 0 #0f0f12;
    }
    .cw-tape {
      position: absolute; left: -0.02em; right: -0.02em; top: 0.12em; bottom: 0.06em; z-index: 0;
      background: #ff3b30; border: 0.06em solid #0f0f12; border-radius: 0.12em;
      transform: scaleX(0) rotate(-2deg); transform-origin: 0% 50%;
    }
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
__ROWS__
  </div>
  <script>
    window.__timelines = window.__timelines || {};
    const tl = gsap.timeline({ paused: true });
    const SUN = "#ffd60a";
    function G(i, start, end, words) {
      const g = "#cap-g" + i;
      tl.set(g, { visibility: "visible" }, start);
      tl.fromTo(g, { opacity: 0, y: 26, scale: 0.94 }, { opacity: 1, y: 0, scale: 1, duration: 0.16, ease: "back.out(2.4)", immediateRender: false }, start);
      words.forEach(([id, t], k) => {
        const w = "#cap-" + id;
        const next = k + 1 < words.length ? words[k + 1][1] : end;
        const isKey = document.querySelector(w).classList.contains("kw");
        tl.fromTo(w + " .cw-t", { y: 0, scale: 1, rotation: 0 }, { y: -10, scale: 1.12, rotation: k % 2 ? 2 : -2, duration: 0.09, ease: "power3.out", immediateRender: false }, t);
        tl.to(w + " .cw-t", { color: SUN, duration: 0.04 }, t);
        if (isKey) tl.to(w + " .cw-tape", { scaleX: 1, duration: 0.14, ease: "power4.out" }, t);
        if (isKey) tl.to(w + " .cw-t", { color: "#ffffff", duration: 0.04 }, t + 0.14);
        tl.to(w + " .cw-t", { y: 0, scale: 1, rotation: 0, duration: 0.14, ease: "power2.out" }, Math.min(next, t + 0.22));
        if (!isKey) tl.to(w + " .cw-t", { color: "#ffffff", duration: 0.06 }, Math.max(t + 0.1, next - 0.02));
      });
      tl.to(g, { opacity: 0, duration: 0.08, ease: "power2.in" }, end - 0.08);
      tl.set(g, { opacity: 0, visibility: "hidden" }, end);
    }
__JS__
    window.__timelines["captions"] = tl;
  </script>
</template>
"""
open("compositions/captions.html", "w").write(doc.replace("__ROWS__", "\n".join(rows)).replace("__JS__", "\n".join(js)))
for gi, g in enumerate(groups): print(gi, round(g[0]["start"], 2), " ".join(x["text"] for x in g))
