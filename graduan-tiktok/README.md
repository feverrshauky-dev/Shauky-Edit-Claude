# Graduan — kereta pertama (TikTok / IG Reels, 9:16)

Editorial-green edit following `../reference/STYLE-GUIDE.md`, deliberately unlike `../shauky-tiktok` (Montserrat + lime, full-bleed).

- **Layout:** footage in a framed "plate" on forest-green paper. PLATE (full) for story beats with captions under the chin; HERO (plate scaled 0.886, dropped to y=700) for the hook, the program reveal and the CTA, with big serif type above the head. Nothing covers the face; all reading text sits inside 168–1330 px.
- **Cut (scripts/edl.py):** 35.9 s → 26.4 s. Hook "Baru satu hari bekerja, … layak … kereta pertama" moved to 0 s; "dan mereka sedang ini memulakan fasa hidup mereka" (stumble) and the repeated hook line removed; pauses over 0.3 s tightened.
- **Words:** whisper small on the tight a-roll (`transcript/aroll-whisper.json`) → `scripts/words.py` → `transcript/words.json` → `scripts/build_captions.py` → `compositions/captions.html`.
- **Audio:** voice cleaned and normalised to −15 LUFS in edl.py; music bed at 0.14 (≈ −17 dB) under the voice; SFX from the bundled HyperFrames/Pixabay library. Music credit in `assets/bgm/CREDITS.md`.

Rebuild the a-roll (not committed, 30+ MB):
```
python3 scripts/edl.py <source.mp4> transcript/edl.json assets/aroll.mp4
```
