"""Generate compositions/lyrics.html: the song's three lines as a karaoke strip.

Source: transcript/lyrics-whisper.json (whisper medium, Malay, sung vocal).
One line per take; each word lights hazard-yellow while it is sung.
The strip sits right under the burned-in "POV" text (y 706), clear of every face:
centred on takes 1 and 3, left-aligned on take 2 where his head rises to x 700+, y 770.
Re-run after edits: python3 scripts/build_lyrics.py
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORDS = json.loads((ROOT / "transcript" / "lyrics-whisper.json").read_text())
DURATION = 20.3

# (first word index, last word index, show, hide, align)
LINES = [
    (0, 3, 2.3, 6.6, "center"),  # after the hook reel clears
    (4, 7, 6.78, 13.9, "left"),
    (8, 11, 14.08, 20.28, "center"),  # fades with the song
]

rows, js = [], []
for li, (a, b, show, hide, align) in enumerate(LINES):
    spans = []
    for w in WORDS[a : b + 1]:
        spans.append(f'<span class="lw" id="ly-{w["id"]}">{html.escape(w["text"])}</span>')
        start = max(w["start"], show)
        js.append(f'    word("#ly-{w["id"]}", {start:.2f});')
    rows.append(
        f'    <div class="ln ln-{align}" id="ly-l{li}"><div class="ln-in">'
        f'<svg class="note" viewBox="0 0 24 24"><path d="M9 3 L21 1 L21 15.5 A3.5 3.5 0 1 1 19 12.4 L19 6.2 L11 7.6 L11 18.5 A3.5 3.5 0 1 1 9 15.4 Z" fill="#ffd400"/></svg>'
        f'{" ".join(spans)}</div></div>'
    )
    js.append(f'    line("#ly-l{li}", {show:.2f}, {hide:.2f});')

out = f"""<template>
  <style>
    #root {{
      position: absolute;
      inset: 0;
      pointer-events: none;
    }}
    .ln {{
      position: absolute;
      left: 0;
      width: 100%;
      top: 706px;
      padding: 0 48px;
      display: flex;
      opacity: 0;
      visibility: hidden;
      overflow: visible;
    }}
    .ln-center {{
      justify-content: center;
    }}
    .ln-left {{
      justify-content: flex-start;
    }}
    .ln-center .ln-in {{
      max-width: 984px;
    }}
    .ln-in {{
      display: inline-flex;
      align-items: center;
      gap: 0 12px;
      max-width: 640px;
      padding: 6px 20px 10px 16px;
      border-radius: 999px;
      background: rgba(11, 11, 11, 0.5);
      font-family: "Playfair Display", serif;
      font-style: italic;
      font-weight: 700;
      font-size: 42px;
      line-height: 1.15;
      white-space: nowrap;
    }}
    .note {{
      width: 30px;
      height: 30px;
      flex: none;
    }}
    .lw {{
      display: inline-block;
      color: rgba(255, 255, 255, 0.62);
      text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
    }}
  </style>
  <div id="root" data-composition-id="lyrics" data-width="1080" data-height="1920">
{chr(10).join(rows)}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
    function line(sel, show, hide) {{
      tl.set(sel, {{ visibility: "visible" }}, show);
      tl.fromTo(sel, {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power2.out" }}, show);
      if (hide < {DURATION}) {{
        tl.to(sel, {{ opacity: 0, filter: "blur(8px)", duration: 0.14, ease: "power2.in" }}, hide - 0.14);
        tl.set(sel, {{ opacity: 0, visibility: "hidden" }}, hide);
      }}
    }}
    function word(sel, t) {{
      tl.fromTo(sel, {{ color: "rgba(255,255,255,0.62)", scale: 1 }}, {{ color: "#ffd400", scale: 1.08, duration: 0.12, ease: "power2.out" }}, t);
      tl.to(sel, {{ scale: 1, duration: 0.25, ease: "power2.out" }}, t + 0.12);
    }}
{chr(10).join(js)}
    window.__timelines["lyrics"] = tl;
  </script>
</template>
"""
(ROOT / "compositions" / "lyrics.html").write_text(out)
print(f"{len(LINES)} lines, {len(WORDS)} words")
