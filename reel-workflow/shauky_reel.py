#!/usr/bin/env python3
"""Shauky reel workflow: one raw talking-head video -> polished 1080x1920 reel.

Outputs (in a fresh run folder, never overwriting anything):
  <name>_final.mp4      vertical reel, subtitles burned in (when a timed transcript is given)
  <name>_clean.mp4      same edit without burned subtitles (only when subtitles are burned)
  <name>.ms.srt         Malay subtitles on the edited timeline
  edit_report.md/.json  every cut, every processing step, verification results
  work/                 intermediate audio, subtitle files and the full ffmpeg log

Needs only ffmpeg/ffprobe and the Python 3.8+ standard library (numpy is used if present).
The input file is opened read-only and its SHA-256 is checked before and after.
"""
import argparse
import datetime
import hashlib
import json
import math
import re
import shlex
import shutil
import subprocess
import sys
from array import array
from fractions import Fraction
from pathlib import Path

W, H = 1080, 1920
SR = 48000
HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv"}


class StepError(Exception):
    pass


# ---------------------------------------------------------------- helpers

class Runner:
    """Runs ffmpeg/ffprobe, logs every command and its stderr to work/ffmpeg.log."""

    def __init__(self, log_path):
        self.log = open(log_path, "a", encoding="utf-8")

    def __call__(self, step, cmd, capture=False, cwd=None, stdin_bytes=False):
        self.log.write(f"\n### {step}\n$ {' '.join(shlex.quote(str(c)) for c in cmd)}\n")
        self.log.flush()
        p = subprocess.run([str(c) for c in cmd], cwd=cwd, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        err = p.stderr.decode("utf-8", "replace")
        self.log.write(err[-20000:])
        self.log.flush()
        if p.returncode != 0:
            tail = "\n".join(err.strip().splitlines()[-12:])
            raise StepError(f"{step} failed (ffmpeg exit {p.returncode}):\n{tail}")
        return p.stdout if capture else err


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt_t(t):
    return f"{int(t // 60):d}:{t % 60:06.3f}"


def srt_time(t):
    ms = int(round(max(t, 0) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def ass_time(t):
    cs = int(round(max(t, 0) * 100))
    return f"{cs // 360000:d}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def unique_dir(base: Path, name: str) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    for i in range(1, 1000):
        d = base / (name if i == 1 else f"{name}-{i}")
        try:
            d.mkdir()
            return d
        except FileExistsError:
            continue
    raise StepError(f"could not create a fresh output folder under {base}")


# ---------------------------------------------------------------- probe

def probe(path: Path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json",
                        str(path)], capture_output=True, text=True)
    if p.returncode != 0:
        raise StepError(f"ffprobe could not read {path}: {p.stderr.strip()[:400]}")
    d = json.loads(p.stdout)
    vids = [s for s in d.get("streams", []) if s.get("codec_type") == "video"
            and not s.get("disposition", {}).get("attached_pic")]
    auds = [s for s in d.get("streams", []) if s.get("codec_type") == "audio"]
    info = {"duration": float(d.get("format", {}).get("duration") or 0),
            "size": int(d.get("format", {}).get("size") or 0),
            "video": vids[0] if vids else None, "audio": auds[0] if auds else None}
    return info


def video_facts(v):
    def frac(s):
        try:
            f = Fraction(s)
            return f if f > 0 else None
        except (ValueError, ZeroDivisionError, TypeError):
            return None
    r, avg = frac(v.get("r_frame_rate")), frac(v.get("avg_frame_rate"))
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    rot = int(v.get("tags", {}).get("rotate", rot))
    w, h = int(v["width"]), int(v["height"])
    if abs(rot) % 180 == 90:
        w, h = h, w
    vfr = bool(r and avg and abs(float(r) - float(avg)) / float(avg) > 0.01)
    if vfr or not r or float(r) > 120:
        # Android phones often record variable frame rate: lock to the nearest standard rate.
        base = float(avg or r or 30)
        fps = min([Fraction(24000, 1001), Fraction(24), Fraction(25), Fraction(30000, 1001),
                   Fraction(30), Fraction(50), Fraction(60000, 1001), Fraction(60)],
                  key=lambda f: abs(float(f) - base))
    else:
        fps = r
    return {"width": w, "height": h, "rotation": rot, "fps": fps, "vfr": vfr,
            "hdr": v.get("color_transfer") in HDR_TRANSFERS, "codec": v.get("codec_name"),
            "pix_fmt": v.get("pix_fmt"), "color_transfer": v.get("color_transfer")}


# ---------------------------------------------------------------- speech detection

def energy_db(run, src, duration):
    """Short-term loudness in dB, one value per 10 ms of audio."""
    raw = run("decode audio for speech detection",
              ["ffmpeg", "-nostdin", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
               "-f", "s16le", "-"], capture=True)
    hop = 160
    try:
        import numpy as np
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
        n = len(x) // hop
        rms = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1))
        db = [float(v) for v in 20 * np.log10(rms + 1e-9)]
    except ImportError:
        a = array("h", raw)
        db = []
        for i in range(len(a) // hop):
            s = a[i * hop:(i + 1) * hop]
            db.append(20 * math.log10(math.sqrt(sum(v * v for v in s) / hop) / 32768 + 1e-9))
    # light smoothing so a single quiet 10 ms frame does not split a word
    sm = [sum(db[max(0, i - 1):i + 2]) / len(db[max(0, i - 1):i + 2]) for i in range(len(db))]
    return sm


def speech_regions(db, args):
    if not db:
        return [], {}
    s = sorted(db)
    pct = lambda q: s[int(q * (len(s) - 1))]
    floor, loud = pct(0.10), pct(0.95)
    thr = max(floor + 6, floor + args.threshold * (loud - floor))
    regions, start = [], None
    for i, v in enumerate(db + [-200]):
        if v > thr and start is None:
            start = i
        elif v <= thr and start is not None:
            regions.append([start / 100, i / 100])
            start = None
    merged = []
    for a, b in regions:
        if merged and a - merged[-1][1] < args.min_gap:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    stats = {"noise_floor_db": round(floor, 1), "speech_level_db": round(loud, 1),
             "threshold_db": round(thr, 1)}
    return merged, stats


def union(regions, extra):
    allr = sorted([list(r) for r in regions] + [list(r) for r in extra])
    out = []
    for a, b in allr:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def plan_cuts(regions, duration, fps, args):
    """Kept source ranges, frame-snapped. Only silence is ever removed; speech plus padding is kept."""
    f = float(fps)
    down = lambda t: math.floor(t * f + 1e-6) / f
    up = lambda t: math.ceil(t * f - 1e-6) / f
    end_limit = math.floor(duration * f + 1e-6) / f
    if args.no_cuts or not regions:
        return [(0.0, end_limit)], []
    keep, cuts = [], []
    a = max(0.0, down(regions[0][0] - args.lead_in))
    if a >= args.min_cut:
        cuts.append({"src_start": 0.0, "src_end": a, "length": a,
                     "reason": "dead air before first word"})
    else:
        a = 0.0
    seg_start = a
    for prev, nxt in zip(regions, regions[1:]):
        gap = nxt[0] - prev[1]
        if gap <= args.max_pause:
            continue
        cut_a = up(prev[1] + args.tail)
        cut_b = down(nxt[0] - args.head)
        if cut_b - cut_a < args.min_cut:
            continue
        keep.append((seg_start, cut_a))
        cuts.append({"src_start": cut_a, "src_end": cut_b, "length": cut_b - cut_a,
                     "reason": f"pause {gap:.2f}s shortened to {gap - (cut_b - cut_a):.2f}s"})
        seg_start = cut_b
    b = min(end_limit, up(regions[-1][1] + args.tail_out))
    if end_limit - b >= args.min_cut:
        cuts.append({"src_start": b, "src_end": end_limit, "length": end_limit - b,
                     "reason": "dead air after last word"})
    else:
        b = end_limit
    keep.append((seg_start, b))
    keep = [(round(x, 6), round(y, 6)) for x, y in keep if y - x > 0.5 / f]
    return keep, cuts


def make_mapper(keep):
    offsets, acc = [], 0.0
    for a, b in keep:
        offsets.append(acc)
        acc += b - a

    def to_out(t):
        for (a, b), o in zip(keep, offsets):
            if t < a:
                return o            # inside a removed gap: snap to the next kept frame
            if t <= b:
                return o + t - a
        return acc
    return to_out, acc


# ---------------------------------------------------------------- transcript / subtitles

def parse_srt(text):
    cues = []
    for block in re.split(r"\n\s*\n", text.replace("\r", "").strip()):
        lines = block.strip().split("\n")
        for i, line in enumerate(lines):
            m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", line)
            if m:
                g = [int(x) for x in m.groups()]
                a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 10 ** len(m.group(4))
                b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 10 ** len(m.group(8))
                txt = " ".join(l.strip() for l in lines[i + 1:] if l.strip())
                if txt:
                    cues.append({"start": a, "end": b, "text": txt})
                break
    return cues


def load_transcript(path):
    """Returns (cues, words, note). cues/words carry source-timeline times, or None if untimed."""
    p = Path(path)
    raw = p.read_text(encoding="utf-8-sig")
    ext = p.suffix.lower()
    if ext in (".srt", ".vtt"):
        cues = parse_srt(raw)
        if not cues:
            raise StepError(f"no subtitle cues found in {p}")
        return cues, None, f"timed transcript from {p.name} ({len(cues)} cues)"
    if ext == ".json":
        d = json.loads(raw)
        segs = d.get("segments") if isinstance(d, dict) else None
        if isinstance(d, list) and d and "start" in d[0]:
            words = [{"start": float(w["start"]), "end": float(w["end"]), "text": w["text"].strip()}
                     for w in d if w.get("text", "").strip()]
            return None, words, f"word-timed transcript from {p.name} ({len(words)} words)"
        if segs:
            cues, words = [], []
            for s in segs:
                a = float(s.get("src_start", s.get("start")))
                b = float(s.get("src_end", s.get("end")))
                cues.append({"start": a, "end": b, "text": s["text"].strip()})
                for w in s.get("words") or []:
                    words.append({"start": float(w["start"]), "end": float(w["end"]),
                                  "text": w.get("text", w.get("word", "")).strip()})
            return cues, (words or None), f"timed transcript from {p.name} ({len(cues)} segments)"
        raise StepError(f"unrecognised JSON transcript layout in {p}")
    return None, None, "untimed"


def wrap2(text, max_line):
    """Split a cue into at most two balanced lines."""
    if len(text) <= max_line + 4:  # a slightly long single line reads better than a split
        return [text]
    words = text.split()
    best, best_score = [text], 1e9
    for i in range(1, len(words)):
        l1, l2 = " ".join(words[:i]), " ".join(words[i:])
        score = max(len(l1), len(l2)) + (0 if l1.endswith((",", ".", "?", "!")) else 3) \
            + (6 if i == 1 or i == len(words) - 1 else 0)
        if score < best_score:
            best, best_score = [l1, l2], score
    return best


def chunk_words(words, max_chars, max_dur):
    """Group timed words into readable cues; break after sentence punctuation."""
    cues, cur = [], []
    for w in words:
        if cur:
            text = " ".join(x["text"] for x in cur + [w])
            if len(text) > max_chars or w["end"] - cur[0]["start"] > max_dur:
                cues.append(cur)
                cur = []
        cur.append(w)
        if w["text"].endswith((".", "?", "!")) or (w["text"].endswith(",") and
                                                     len(" ".join(x["text"] for x in cur)) > max_chars * 0.5):
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    return [{"start": c[0]["start"], "end": c[-1]["end"], "text": " ".join(x["text"] for x in c),
             "timing": "word"} for c in cues]


def balanced_split(words, max_chars):
    """Split a phrase into readable chunks: at sentence ends first, then commas, then by balance."""
    j = lambda ws: " ".join(ws)
    if len(j(words)) <= max_chars or len(words) < 2:
        return [words]
    for marks in ((".", "?", "!"), (",", ";", ":")):
        cands = [i for i in range(1, len(words)) if words[i - 1].endswith(marks)
                 and min(len(j(words[:i])), len(j(words[i:]))) >= 6]
        if cands:
            i = min(cands, key=lambda i: max(len(j(words[:i])), len(j(words[i:]))))
            return balanced_split(words[:i], max_chars) + balanced_split(words[i:], max_chars)
    i = min(range(1, len(words)), key=lambda i: max(len(j(words[:i])), len(j(words[i:])))
            + (6 if i == 1 or i == len(words) - 1 else 0))
    return balanced_split(words[:i], max_chars) + balanced_split(words[i:], max_chars)


def split_cue(cue, max_chars):
    """Split a long phrase into readable cues; time is shared by character count."""
    if len(cue["text"]) <= max_chars:
        return [dict(cue, timing="phrase")]
    parts = balanced_split(cue["text"].split(), max_chars)
    total = sum(len(" ".join(p)) + 1 for p in parts)
    out, t = [], cue["start"]
    for p in parts:
        s = " ".join(p)
        d = (cue["end"] - cue["start"]) * (len(s) + 1) / total
        out.append({"start": t, "end": t + d, "text": s, "timing": "estimated"})
        t += d
    return out


def build_cues(cues, words, to_out, total, args):
    if words:
        out = chunk_words(words, args.sub_max_chars, 2.6)
    else:
        out = [c for cue in cues for c in split_cue(cue, args.sub_max_chars)]
    res = []
    for c in out:
        a, b = to_out(c["start"]), to_out(c["end"])
        if b - a < 0.05:
            continue  # the words of this cue were not kept (should not happen: speech is never cut)
        res.append({"start": a, "end": min(b, total), "text": c["text"], "timing": c["timing"]})
    # readability: minimum on-screen time, hold briefly into short gaps, never overlap
    for i, c in enumerate(res):
        nxt = res[i + 1]["start"] if i + 1 < len(res) else total
        c["end"] = min(max(c["end"] + 0.15, c["start"] + 0.8), nxt)
    return res


def write_srt(cues, path, max_line):
    with open(path, "x", encoding="utf-8") as f:
        for i, c in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n"
                    + "\n".join(wrap2(c["text"], max_line)) + "\n\n")


def write_ass(cues, path, args):
    esc = lambda s: s.replace("\\", "\\\\").replace("{", "(").replace("}", ")")
    style = (f"Style: Main,{args.sub_font},{args.sub_size},&H00FFFFFF,&H00FFFFFF,&H28000000,"
             f"&H64000000,-1,0,0,0,100,100,0.5,0,1,3.2,1.4,2,80,80,{args.sub_margin},1")
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
             "WrapStyle: 2", "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
             "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
             "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             style, "", "[Events]",
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for c in cues:
        txt = "\\N".join(esc(l) for l in wrap2(c["text"], args.sub_line_chars))
        lines.append(f"Dialogue: 0,{ass_time(c['start'])},{ass_time(c['end'])},Main,,0,0,0,,"
                     f"{{\\fad(70,50)}}{txt}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_template(regions, path):
    """Untimed transcript: give the user a source-timeline SRT skeleton to fill in."""
    phrases = []
    for a, b in regions:
        if phrases and a - phrases[-1][1] < 0.3:
            phrases[-1][1] = b
        else:
            phrases.append([a, b])
    with open(path, "x", encoding="utf-8") as f:
        for i, (a, b) in enumerate(phrases, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n[taip ayat di sini]\n\n")
    return len(phrases)


# ---------------------------------------------------------------- audio

def afftdn_delay(run, nr, nf):
    """afftdn delays audio by its window length without compensating; measure it with a tone burst."""
    raw = run("audio: measure denoise latency",
              ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
               f"aevalsrc='0.5*sin(2*PI*1000*t)*between(t,0.5,0.52)':s={SR}:d=1",
               "-af", f"afftdn=nr={nr}:nf={nf}", "-f", "s16le", "-"], capture=True)
    a = array("h", raw)
    onset = next((i for i, v in enumerate(a) if abs(v) > 2000), None)
    return max(0, onset - SR // 2) if onset is not None else 0


def build_audio(run, args, src, keep, total, work, has_music):
    """Cut + clean the voice, optionally duck music under it, then two-pass loudness normalise."""
    n = len(keep)
    fd = 0.008
    parts = [f"[0:a]aresample={SR},aformat=channel_layouts=stereo,asplit={n}" +
             "".join(f"[s{i}]" for i in range(n)) + ";"]
    for i, (a, b) in enumerate(keep):
        d = b - a
        parts.append(f"[s{i}]atrim={a:.6f}:{b:.6f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d={fd},afade=t=out:st={max(d - fd, 0):.6f}:d={fd}[c{i}];")
    parts.append("".join(f"[c{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[cut];")
    chain = ["highpass=f=75"]
    delay = 0
    if args.denoise != "off":
        nr = {"light": 10, "medium": 15}[args.denoise]
        nf = f"{args._noise_floor:.0f}"
        delay = afftdn_delay(run, nr, nf)
        chain.append(f"afftdn=nr={nr}:nf={nf}")
        if delay:  # keep lip sync: drop the latency at the start, re-pad the end
            chain.append(f"atrim=start_sample={delay},asetpts=PTS-STARTPTS")
    n_samples = int(round(total * SR))
    chain += ["equalizer=f=250:t=q:w=1.2:g=-1.5", "equalizer=f=3500:t=q:w=1.0:g=1.5",
              "acompressor=threshold=-14dB:ratio=2:attack=5:release=150",
              "alimiter=limit=0.7:attack=5:release=60:level=0:latency=1",
              f"apad=whole_len={n_samples},atrim=end_sample={n_samples}"]
    args._denoise_delay_ms = delay * 1000 / SR
    parts.append(f"[cut]{','.join(chain)}[voice]")
    voice = work / "voice_clean.wav"
    run("audio: cut + voice cleanup", ["ffmpeg", "-nostdin", "-n", "-v", "error", "-i", src,
        "-filter_complex", "".join(parts), "-map", "[voice]", "-c:a", "pcm_s16le", voice])
    pre = voice
    if has_music:
        mix = work / "voice_music_mix.wav"
        mlevel = -14 - args.music_gap
        fo = max(total - 2.5, 0)
        fc = (f"[1:a]aresample={SR},aformat=channel_layouts=stereo,atrim=0:{total:.3f},"
              f"asetpts=PTS-STARTPTS,loudnorm=I={mlevel}:TP=-6:LRA=7,aresample={SR},"
              f"afade=t=in:d=1.5,afade=t=out:st={fo:.3f}:d=2.5[m];"
              f"[0:a]asplit=2[v][key];"
              f"[m][key]sidechaincompress=threshold=0.03:ratio=4:attack=40:release=450[duck];"
              f"[v][duck]amix=inputs=2:normalize=0:duration=first[out]")
        run("audio: duck + mix music", ["ffmpeg", "-nostdin", "-n", "-v", "error", "-i", voice,
            "-stream_loop", "-1", "-i", args.music, "-filter_complex", fc, "-map", "[out]",
            "-t", f"{total:.6f}", "-c:a", "pcm_s16le", mix])
        pre = mix
    target = f"I={args.lufs}:TP=-1.5:LRA=11"
    err = run("audio: loudness measure", ["ffmpeg", "-nostdin", "-v", "info", "-i", pre,
              "-af", f"loudnorm={target}:print_format=json", "-f", "null", "-"])
    m = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    final = work / "audio_final.wav"
    run("audio: loudness normalise", ["ffmpeg", "-nostdin", "-n", "-v", "error", "-i", pre, "-af",
        f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
        f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
        f"offset={m['target_offset']}:linear=true,aresample={SR}",
        "-c:a", "pcm_s16le", final])
    return final, {"input_lufs": float(m["input_i"]), "input_true_peak": float(m["input_tp"])}


# ---------------------------------------------------------------- video

def video_filter(keep, fps, facts, args, subs_ass, logo_idx):
    f = float(fps)
    half = 0.5 / f
    sel = "+".join(f"between(t,{a - half:.6f},{b - half - 1e-4:.6f})" for a, b in keep)
    chain = []
    if facts["hdr"]:
        chain.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
                     "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    chain.append(f"fps={fps}")
    if len(keep) > 1 or keep[0][0] > 0 or keep[0][1] < facts["_dur"] - 1 / f:
        chain.append(f"select='{sel}',setpts=N/({fps})/TB")
    chain.append(f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
                 f"crop={W}:{H}:(iw-ow)*{args.focus_x}:(ih-oh)*{args.focus_y},setsar=1")
    # Punch-ins: alternate framing at every cut so jump cuts read as deliberate.
    zooms, frame_marks, acc = [], [], 0
    for i, (a, b) in enumerate(keep):
        z = args.punch if (args.punch > 1 and i % 2 == 1) else 1.0
        zooms.append(z)
        frame_marks.append((acc, z))
        acc += int(round((b - a) * f))
    if args.punch > 1 and len(keep) > 1:
        expr = "1"
        for start, z in frame_marks:
            expr = f"if(gte(in,{start}),{z},{expr})"
        chain.append(f"zoompan=z='{expr}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)*{args.focus_y}':"
                     f"d=1:s={W}x{H}:fps={fps}")
    if args.grade == "natural":
        chain += ["hqdn3d=1.0:1.0:3:3",
                  "unsharp=5:5:0.35:5:5:0",
                  "curves=master='0/0 0.12/0.105 0.5/0.5 0.88/0.885 1/0.985'",
                  "eq=saturation=1.04",
                  "colorbalance=rm=0.012:bm=-0.012",
                  "vignette=angle=PI/7"]
    graph = "[0:v]" + ",".join(chain) + "[base];"
    last = "[base]"
    if logo_idx is not None:
        mx, my = 60, 150
        pos = {"top-left": f"x={mx}:y={my}", "top-right": f"x=W-w-{mx}:y={my}"}[args.logo_pos]
        graph += (f"[{logo_idx}:v]scale={args.logo_width}:-1:flags=lanczos,format=rgba,"
                  f"colorchannelmixer=aa={args.logo_opacity}[lg];{last}[lg]overlay={pos}:"
                  f"format=auto[withlogo];")
        last = "[withlogo]"
    clean_graph = graph + f"{last}format=yuv420p[vout]"
    subs_graph = None
    if subs_ass:
        fontsdir = f":fontsdir='{args.fonts_dir}'" if args.fonts_dir else ""
        subs_graph = graph + f"{last}subtitles=filename={subs_ass}{fontsdir},format=yuv420p[vout]"
    return clean_graph, subs_graph, zooms


def x264_opts(draft):
    return ["-preset", "veryfast", "-crf", "23"] if draft else ["-preset", "slow", "-crf", "18"]


def encode(run, step, src, audio, logo, graph, fps, total, out, cwd, draft=False):
    cmd = ["ffmpeg", "-nostdin", "-n", "-v", "error", "-i", src, "-i", audio]
    if logo:
        cmd += ["-i", logo]
    cmd += ["-filter_complex", graph, "-map", "[vout]", "-map", "1:a",
            "-c:v", "libx264", *x264_opts(draft), "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-r", str(fps), "-g", str(int(round(float(fps) * 2))),
            "-maxrate", "16M", "-bufsize", "32M",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-color_range", "tv",
            "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
            "-t", f"{total:.6f}", "-movflags", "+faststart", out]
    run(step, cmd, cwd=cwd)


def encode_silent(run, step, src, logo, graph, fps, total, out, cwd, draft=False):
    cmd = ["ffmpeg", "-nostdin", "-n", "-v", "error", "-i", src]
    if logo:
        cmd += ["-i", logo]
    cmd += ["-filter_complex", graph,
            "-map", "[vout]", "-c:v", "libx264", *x264_opts(draft),
            "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(fps),
            "-t", f"{total:.6f}", "-movflags", "+faststart", out]
    run(step, cmd, cwd=cwd)


def verify(run, out, expect_audio, total):
    res = {"file": str(out.name), "ok": True, "problems": []}
    if not out.exists() or out.stat().st_size < 10000:
        res.update(ok=False, problems=["file missing or empty"])
        return res
    info = probe(out)
    v, a = info["video"], info["audio"]
    res.update(size_mb=round(out.stat().st_size / 1e6, 2), duration=round(info["duration"], 3))
    if not v:
        res["problems"].append("no video stream")
    else:
        res.update(resolution=f"{v['width']}x{v['height']}", codec=v["codec_name"],
                   fps=v.get("r_frame_rate"))
        if (int(v["width"]), int(v["height"])) != (W, H):
            res["problems"].append(f"resolution {v['width']}x{v['height']} is not {W}x{H}")
    if expect_audio:
        if not a:
            res["problems"].append("source has audio but output has none")
        else:
            err = run(f"verify: audio level {out.name}", ["ffmpeg", "-nostdin", "-v", "info", "-i",
                      out, "-map", "0:a", "-af", "volumedetect", "-f", "null", "-"])
            mv = re.search(r"max_volume: (-?[\d.]+) dB", err)
            res["audio_max_db"] = float(mv.group(1)) if mv else None
            if not mv or float(mv.group(1)) < -50:
                res["problems"].append("audio track is silent")
    if abs(info["duration"] - total) > 0.2:
        res["problems"].append(f"duration {info['duration']:.2f}s, expected {total:.2f}s")
    err = run(f"verify: full decode {out.name}", ["ffmpeg", "-nostdin", "-v", "error", "-i", out,
              "-f", "null", "-"])
    if err.strip():
        res["problems"].append("decode errors: " + err.strip().splitlines()[0][:200])
    res["ok"] = not res["problems"]
    return res


# ---------------------------------------------------------------- report

def write_report(run_dir, rep):
    (run_dir / "edit_report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False),
                                              encoding="utf-8")
    L = [f"# Edit report — {rep['input']['name']}", "",
         f"Run: {rep['run_at']}  ·  status: **{rep['status']}**", ""]
    i = rep["input"]
    L += ["## Input", "",
          f"- File: `{i['path']}` ({i['size_mb']} MB, SHA-256 `{i['sha256'][:16]}…`)",
          f"- {i['width']}x{i['height']}, {i['fps']} fps{' (variable — locked to CFR)' if i['vfr'] else ''}"
          f", {i['duration']:.2f}s, codec {i['codec']}, audio: {'yes' if i['has_audio'] else 'NO'}"
          + (", HDR (tone-mapped to SDR)" if i["hdr"] else ""),
          f"- Input unchanged after run: {rep.get('input_unchanged', 'not checked')}", ""]
    t = rep["timeline"]
    L += ["## Timeline", "",
          f"- {t['source_duration']:.2f}s → **{t['final_duration']:.2f}s** "
          f"(removed {t['removed']:.2f}s in {len(rep['cuts'])} cuts)",
          f"- Speech detection: noise floor {t['detect'].get('noise_floor_db')} dB, speech "
          f"{t['detect'].get('speech_level_db')} dB, threshold {t['detect'].get('threshold_db')} dB; "
          f"pauses longer than {t['max_pause']}s are shortened, speech + padding is never cut", ""]
    if rep["cuts"]:
        L += ["| # | Removed (source time) | Length | Why |", "|---|---|---|---|"]
        for k, c in enumerate(rep["cuts"], 1):
            L.append(f"| {k} | {fmt_t(c['src_start'])} → {fmt_t(c['src_end'])} | "
                     f"{c['length']:.2f}s | {c['reason']} |")
        L.append("")
    L += ["| Seg | Source range | Output starts at | Framing |", "|---|---|---|---|"]
    for k, s in enumerate(rep["segments"], 1):
        L.append(f"| {k} | {fmt_t(s['src_start'])} → {fmt_t(s['src_end'])} | {fmt_t(s['out_start'])} | "
                 f"{'punch-in ' + str(s['zoom']) + 'x' if s['zoom'] > 1 else 'wide'} |")
    L += ["", "## Processing", ""] + [f"- {x}" for x in rep["processing"]] + [""]
    L += ["## Subtitles", ""] + [f"- {x}" for x in rep["subtitles"]] + [""]
    L += ["## Outputs and verification", ""]
    for v in rep.get("verification", []):
        mark = "PASS" if v["ok"] else "FAIL"
        L.append(f"- **{mark}** `{v['file']}` — {v.get('resolution', '?')}, {v.get('fps', '?')} fps, "
                 f"{v.get('duration', '?')}s, {v.get('size_mb', '?')} MB, audio peak "
                 f"{v.get('audio_max_db', 'n/a')} dB" + (f" — {'; '.join(v['problems'])}" if v["problems"] else ""))
    for f in rep.get("files", []):
        L.append(f"- `{f}`")
    if rep["warnings"]:
        L += ["", "## Warnings", ""] + [f"- {w}" for w in rep["warnings"]]
    if rep.get("error"):
        L += ["", "## Failed step", "", "```", rep["error"], "```"]
    (run_dir / "edit_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="raw MP4/MOV from the phone (never modified)")
    ap.add_argument("--transcript", help=".srt / .json (timed) or .txt (untimed) Malay transcript")
    ap.add_argument("--transcript-timeline", choices=["source", "edited"], default="source",
                    help="whether transcript times refer to the raw video (default) or the edited one")
    ap.add_argument("--logo", help="PNG logo with transparency")
    ap.add_argument("--logo-pos", choices=["top-left", "top-right"], default="top-left")
    ap.add_argument("--logo-width", type=int, default=170)
    ap.add_argument("--logo-opacity", type=float, default=0.9)
    ap.add_argument("--music", help="background music track (looped/trimmed, ducked under voice)")
    ap.add_argument("--music-gap", type=float, default=20, help="music sits this many LU below the voice")
    ap.add_argument("--out-dir", default="reel-output", help="parent folder for run folders")
    ap.add_argument("--name", help="base name for outputs (default: input file name)")
    ap.add_argument("--plan-only", action="store_true", help="analyse and report cuts, render nothing")
    ap.add_argument("--draft", action="store_true", help="fast low-quality preview, single render")
    ap.add_argument("--no-cuts", action="store_true", help="keep the full length")
    ap.add_argument("--max-pause", type=float, default=0.45, help="pauses longer than this get shortened")
    ap.add_argument("--min-cut", type=float, default=0.25, help="never make a cut that saves less than this")
    ap.add_argument("--tail", type=float, default=0.14, help="silence kept after each phrase")
    ap.add_argument("--head", type=float, default=0.08, help="silence kept before each phrase")
    ap.add_argument("--lead-in", type=float, default=0.12)
    ap.add_argument("--tail-out", type=float, default=0.45)
    ap.add_argument("--min-gap", type=float, default=0.18, help="quieter gaps shorter than this count as speech")
    ap.add_argument("--threshold", type=float, default=0.30, help="speech threshold between floor (0) and peak (1)")
    ap.add_argument("--punch", type=float, default=1.08, help="punch-in zoom on alternate segments (1 = off)")
    ap.add_argument("--focus-x", type=float, default=0.5, help="horizontal crop anchor 0-1 (landscape sources)")
    ap.add_argument("--focus-y", type=float, default=0.35, help="vertical anchor 0-1 for crops/punch-ins (face height)")
    ap.add_argument("--grade", choices=["natural", "off"], default="natural")
    ap.add_argument("--denoise", choices=["off", "light", "medium"], default="light")
    ap.add_argument("--lufs", type=float, default=-14, help="final loudness target")
    ap.add_argument("--no-burn-subs", action="store_true", help="SRT only, no burned-in subtitles")
    ap.add_argument("--sub-font", default="Inter SemiBold")
    ap.add_argument("--fonts-dir", help="folder with the subtitle font, if it is not installed system-wide")
    ap.add_argument("--sub-size", type=int, default=66)
    ap.add_argument("--sub-margin", type=int, default=430, help="subtitle distance from bottom edge (px)")
    ap.add_argument("--sub-line-chars", type=int, default=28)
    ap.add_argument("--sub-max-chars", type=int, default=40)
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"ERROR: {tool} not found. Install FFmpeg first.")
    src = Path(args.input).expanduser().resolve()
    if not src.is_file():
        sys.exit(f"ERROR: input not found: {src}")
    if src.suffix.lower() not in VIDEO_EXTS:
        print(f"note: unusual extension {src.suffix}; trying anyway")
    for opt in ("transcript", "logo", "music"):
        val = getattr(args, opt)
        if val and not Path(val).expanduser().is_file():
            sys.exit(f"ERROR: --{opt} file not found: {val}")
        if val:
            setattr(args, opt, str(Path(val).expanduser().resolve()))

    try:
        info = probe(src)
    except StepError as e:
        sys.exit(f"ERROR: input is not a readable video. {e}")
    if not info["video"]:
        sys.exit("ERROR: input has no video stream")
    if info["duration"] <= 0.5:
        sys.exit("ERROR: input is too short or has no duration")
    facts = video_facts(info["video"])
    facts["_dur"] = info["duration"]
    has_audio = info["audio"] is not None

    name = args.name or re.sub(r"[^\w.-]+", "_", src.stem)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = unique_dir(Path(args.out_dir).expanduser().resolve(), f"{name}_{stamp}")
    work = run_dir / "work"
    work.mkdir()
    run = Runner(work / "ffmpeg.log")
    print(f"→ run folder: {run_dir}")

    rep = {"run_at": stamp, "status": "running", "warnings": [], "processing": [], "subtitles": [],
           "settings": {k: v for k, v in vars(args).items() if not k.startswith("_")}}
    src_hash = sha256(src)
    rep["input"] = {"path": str(src), "name": src.name, "size_mb": round(info["size"] / 1e6, 2),
                    "sha256": src_hash, "duration": info["duration"], "width": facts["width"],
                    "height": facts["height"], "fps": str(facts["fps"]), "vfr": facts["vfr"],
                    "hdr": facts["hdr"], "codec": facts["codec"], "has_audio": has_audio}
    fps = facts["fps"]
    try:
        # 1. transcript
        cues = words = None
        tnote = None
        if args.transcript:
            cues, words, tnote = load_transcript(args.transcript)
            if tnote == "untimed":
                rep["warnings"].append("transcript has no timings: subtitles left as a pending step")
        # 2. speech detection + cut plan
        if has_audio:
            print("→ detecting speech and pauses")
            db = energy_db(run, src, info["duration"])
            regions, detect = speech_regions(db, args)
            args._noise_floor = min(max(detect.get("noise_floor_db", -50), -80), -20)
        else:
            regions, detect = [], {}
            args._noise_floor = -50
            rep["warnings"].append("source has no audio: no pause removal, no subtitles timing")
        protect = []
        if args.transcript_timeline == "source":
            protect = [(w["start"], w["end"]) for w in (words or [])] + \
                      [(c["start"], c["end"]) for c in (cues or [])]
        if args.transcript_timeline == "edited" and (cues or words):
            args.no_cuts = True
            rep["warnings"].append("transcript is on an edited timeline: cuts disabled so it stays in sync")
        keep, cuts = plan_cuts(union(regions, protect) if regions else [], info["duration"], fps, args)
        to_out, total = make_mapper(keep)
        removed = info["duration"] - total
        rep["timeline"] = {"source_duration": info["duration"], "final_duration": total,
                           "removed": removed, "detect": detect, "max_pause": args.max_pause}
        rep["cuts"] = cuts
        if removed > 0.4 * info["duration"]:
            rep["warnings"].append("more than 40% removed — check the cut list; raise --threshold "
                                   "sensitivity or use --no-cuts if speech was mistaken for silence")
        _, _, zooms = video_filter(keep, fps, facts, args, None, None)
        rep["segments"] = [{"src_start": a, "src_end": b, "out_start": to_out(a), "zoom": z}
                           for (a, b), z in zip(keep, zooms)]
        print(f"→ {info['duration']:.2f}s → {total:.2f}s, {len(cuts)} cuts")

        # 3. subtitles
        ass = None
        if cues or words:
            mapper = to_out if args.transcript_timeline == "source" else (lambda t: min(t, total))
            final_cues = build_cues(cues, words, mapper, total, args)
            srt = run_dir / f"{name}.ms.srt"
            write_srt(final_cues, srt, args.sub_line_chars)
            est = sum(1 for c in final_cues if c["timing"] == "estimated")
            rep["subtitles"] += [tnote, f"{len(final_cues)} cues written to {srt.name} (edited timeline)",
                                 "text is used exactly as supplied — no words added or changed"]
            if est:
                rep["subtitles"].append(f"{est} cues come from splitting long phrases; their inner "
                                        "timing is shared by character count (approximate)")
            if not args.no_burn_subs:
                ass = "subs.ass"
                write_ass(final_cues, work / ass, args)
        else:
            if has_audio:
                tpl = run_dir / "subtitle_template_SOURCE_TIMING.srt"
                n = write_template(regions, tpl)
                rep["subtitles"] += [
                    "PENDING — no timed transcript and no speech-recognition engine available",
                    f"{tpl.name}: {n} phrase slots timed to the RAW video; type the Malay text in each "
                    "slot and re-run with --transcript <that file>"]
            else:
                rep["subtitles"].append("none (no audio)")

        if args.plan_only:
            rep["status"] = "plan only (nothing rendered)"
            write_report(run_dir, rep)
            print(f"✓ plan written: {run_dir / 'edit_report.md'}")
            return 0

        # 4. audio
        audio = None
        if has_audio:
            print("→ processing audio")
            audio, loud = build_audio(run, args, src, keep, total, work, bool(args.music))
            rep["processing"] += [
                f"Audio: cut with 8 ms micro-fades at each join; 75 Hz high-pass; "
                + (f"FFT denoise ({args.denoise}, its {args._denoise_delay_ms:.0f} ms latency "
                   "removed to keep lip sync); " if args.denoise != "off" else "no denoise; ")
                + "gentle EQ (-1.5 dB @250 Hz, +1.5 dB @3.5 kHz); 2:1 compression; peak limiter",
                f"Loudness: {loud['input_lufs']:.1f} LUFS before normalising → {args.lufs} LUFS, "
                f"true peak ≤ -1.5 dBTP (two-pass loudnorm)"]
            if args.music:
                rep["processing"].append(f"Music: {Path(args.music).name}, looped/trimmed to length, "
                                         f"{args.music_gap} LU under voice, ducked while speaking, "
                                         "1.5 s fade in / 2.5 s fade out")
        elif args.music:
            rep["warnings"].append("music ignored: source has no voice track to mix with")
        rep["processing"] += [
            f"Video: {facts['width']}x{facts['height']} → {W}x{H} (cover-scale, anchor x={args.focus_x}, "
            f"y={args.focus_y}), {fps} fps" + (" (VFR locked to CFR)" if facts["vfr"] else ""),
            f"Punch-ins: {args.punch}x on alternate segments, anchored at face height"
            if args.punch > 1 and len(keep) > 1 else "Punch-ins: none",
            "Grade: light denoise, mild sharpen, soft S-curve with highlight roll-off, +4% saturation, "
            "slight warm balance, faint vignette" if args.grade == "natural" else "Grade: off",
            ("DRAFT encode: H.264 veryfast CRF 23 — preview only" if args.draft else
             "Encode: H.264 High, CRF 18, preset slow, BT.709, AAC 192 kbps 48 kHz, faststart")]
        if args.logo:
            rep["processing"].append(f"Logo: {Path(args.logo).name}, {args.logo_width}px wide, "
                                     f"{args.logo_pos}, {int(args.logo_opacity * 100)}% opacity")

        # 5. video
        logo_idx = 2 if (args.logo and audio) else (1 if args.logo else None)
        clean_g, subs_g, _ = video_filter(keep, fps, facts, args, ass, logo_idx)
        outputs = []
        main_out = run_dir / f"{name}_{'DRAFT' if args.draft else 'final'}.mp4"
        print("→ rendering final video")
        if audio:
            encode(run, "video: final render", src, audio, args.logo, subs_g or clean_g, fps, total,
                   main_out, work, args.draft)
        else:
            encode_silent(run, "video: final render", src, args.logo, subs_g or clean_g, fps, total,
                          main_out, work, args.draft)
        outputs.append(main_out)
        if subs_g and not args.draft:
            clean_out = run_dir / f"{name}_clean.mp4"
            print("→ rendering clean (no burned subtitles) version")
            if audio:
                encode(run, "video: clean render", src, audio, args.logo, clean_g, fps, total, clean_out, work)
            else:
                encode_silent(run, "video: clean render", src, args.logo, clean_g, fps, total, clean_out, work)
            outputs.append(clean_out)

        # 6. verify
        print("→ verifying outputs")
        rep["verification"] = [verify(run, o, has_audio, total) for o in outputs]
        rep["input_unchanged"] = sha256(src) == src_hash
        if not rep["input_unchanged"]:
            rep["warnings"].append("INPUT FILE CHANGED DURING RUN — investigate")
        rep["files"] = sorted(str(p.relative_to(run_dir)) for p in run_dir.iterdir() if p.is_file())
        ok = all(v["ok"] for v in rep["verification"]) and rep["input_unchanged"]
        rep["status"] = "complete" if ok else "FAILED verification"
        write_report(run_dir, rep)
        print(f"{'✓' if ok else '✗'} {rep['status']}: {run_dir}")
        return 0 if ok else 2
    except StepError as e:
        rep["status"] = "FAILED"
        rep["error"] = str(e)
        rep.setdefault("timeline", {"source_duration": info["duration"], "final_duration": 0,
                                    "removed": 0, "detect": {}, "max_pause": args.max_pause})
        rep.setdefault("cuts", [])
        rep.setdefault("segments", [])
        write_report(run_dir, rep)
        print(f"✗ {e}\n  details: {work / 'ffmpeg.log'}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
