# Shauky reel workflow

One raw talking-head video in → a polished 1080×1920 reel for TikTok, Instagram Reels and Facebook Reels out.
Cinematic but natural: restrained grade, real skin tones, natural punch-ins, clean Malay subtitles,
tidy voice. No flashy transitions, no fake film damage, no invented content.

Everything runs on **FFmpeg + Python 3.8+ standard library**. Nothing is downloaded or uploaded.

## Run it

```bash
# full render (about 5 min for a 50 s clip on 4 CPU cores)
python3 reel-workflow/shauky_reel.py RAW.mp4 --transcript my-transcript.srt

# quick look first: cut list + subtitles only, no render (seconds)
python3 reel-workflow/shauky_reel.py RAW.mp4 --transcript my-transcript.srt --plan-only

# fast low-quality preview (one render, named *_DRAFT.mp4)
python3 reel-workflow/shauky_reel.py RAW.mp4 --transcript my-transcript.srt --draft

# with logo and background music
python3 reel-workflow/shauky_reel.py RAW.mp4 --transcript t.srt --logo shauky-logo.png --music track.mp3
```

Each run gets its own new folder `reel-output/<name>_<date-time>/` (change with `--out-dir`, name with `--name`):

| File | What it is |
|---|---|
| `<name>_final.mp4` | the reel, subtitles burned in |
| `<name>_clean.mp4` | same edit without burned subtitles (for Facebook's own SRT upload, or re-styling) |
| `<name>.ms.srt` | Malay subtitles timed to the **edited** video |
| `edit_report.md` / `.json` | every cut, every processing step, verification results |
| `subtitle_template_SOURCE_TIMING.srt` | only when no timed transcript was given (see below) |
| `work/` | intermediate audio, `subs.ass`, and `ffmpeg.log` with every command run |

The exit code is 0 only if every output passed verification.

## What it does

1. **Validates** the input with ffprobe (readable, has video, duration), hashes it (SHA-256) and confirms
   at the end that it is byte-for-byte unchanged. Outputs never overwrite anything (`ffmpeg -n`, fresh folder).
2. **Finds speech** from the audio energy (adaptive to the room's noise floor) and **only shortens pauses**:
   a pause longer than 0.45 s is trimmed to about 0.22 s, keeping 0.14 s after the last word and 0.08 s before
   the next. Speech, plus padding, is never cut; when a transcript is given, its timed lines are protected too.
   Dead air before the first and after the last word is trimmed. All cuts land on frame boundaries.
3. **Reframes** to 1080×1920 (cover-scale; landscape sources are centre-cropped, tune with `--focus-x`),
   keeps the source frame rate (variable-rate phone footage is locked to the nearest standard rate),
   tone-maps HDR phone footage to SDR.
4. **Punch-ins**: alternate segments get a 1.08× zoom anchored at face height, so each cut reads as deliberate.
5. **Grade** (`--grade natural`): light denoise, mild sharpen, soft S-curve with highlight roll-off,
   +4 % saturation, a hint of warmth, faint vignette. `--grade off` to disable.
6. **Voice**: 75 Hz high-pass, light FFT noise reduction (its 25 ms processing latency is measured and
   removed so lips stay in sync), gentle EQ, 2:1 compression, peak limiter, two-pass loudness
   normalisation to −14 LUFS / −1.5 dBTP.
7. **Music** (optional): looped/trimmed to length, 20 LU under the voice (`--music-gap`), ducked while you
   speak, faded in and out.
8. **Logo** (optional PNG): top-left by default, 170 px wide, 90 % opacity.
9. **Subtitles**: your text exactly as supplied, re-timed to the edit, split into short cues (sentence
   ends first, then commas), at most two lines, Inter SemiBold with outline, placed below the face and
   above the TikTok/Reels caption area. Size/position: `--sub-size`, `--sub-margin`.
10. **Verifies** each MP4: video stream present, 1080×1920, expected duration, audio present and not
    silent when the source had audio, and a full decode with no errors.

## Transcripts and subtitles

No speech-recognition engine is installed, so **subtitles come from a transcript you supply**:

- `.srt`: timed to the **raw** video (default) — the best option. Any SRT exported from CapCut, VN,
  or a transcription app works.
- `.json`: Whisper-style `{"segments":[{"start","end","text","words":[...]}]}` or a list of
  `{"text","start","end"}` words. Word timings give the most accurate subtitle timing.
- `.txt` (no timings) or no transcript: the video is still edited, and the run writes
  `subtitle_template_SOURCE_TIMING.srt` — one slot per detected spoken phrase, timed to the raw video.
  Type your words into each slot and run again with `--transcript` pointing at that file.

If your SRT is timed to an already-edited video, add `--transcript-timeline edited` (cuts are then
disabled so it stays in sync).

The script never changes, adds or "fixes" words. Long lines are split into shorter cues and their inner
timing is shared out by character count — the report says how many cues this applies to.

## Options worth knowing

| Option | Default | Use |
|---|---|---|
| `--no-cuts` | off | keep the full length |
| `--max-pause` | 0.45 | only pauses longer than this are shortened |
| `--threshold` | 0.30 | raise if background noise is mistaken for speech, lower if quiet words get treated as pauses |
| `--punch` | 1.08 | `1` turns punch-ins off |
| `--focus-y` | 0.35 | vertical anchor for crops/punch-ins (0 top, 1 bottom) |
| `--denoise` | light | `off` / `light` / `medium` |
| `--no-burn-subs` | off | SRT only |
| `--draft` | off | fast preview render |

## Limitations (honest)

- **No automatic transcription.** Adding it needs `pip install faster-whisper` plus a ~1.5–3 GB model
  download; Whisper's Malay is usable but mishears names and slang (e.g. "SA", "loan", "Perodua"), so a
  human check would still be needed. Not installed — ask first.
- Pause detection is energy-based: it knows *where* you speak, not *what* you say. It will not remove
  repeated takes or filler words ("err", "emm") — those need a word-level transcript and a human decision.
- Quality is capped by the input. Phone exports squeezed by messaging apps (~1 Mbps) stay soft; send the
  original file from the phone's gallery when possible.
- No face tracking: crops and punch-ins use a fixed anchor (`--focus-y`).
- The script cannot reach your phone. Copy the video into the session (or the repo machine) first.
