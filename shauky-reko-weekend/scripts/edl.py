"""Build the tight a-roll from the kept phrases and write the new timeline.

Usage: python3 scripts/edl.py <source.mp4> transcript/edl.json assets/aroll.mp4

Cuts: the "Assalamualaikum guys. So," opener, the "yang dimana" filler, the repeated
"Hari Sabtu dan Ahad ni." at 21.6s, and the hesitant "Jadi..." before the CTA.
The closing salam stays so the end card can hold. Inside each kept phrase, any pause longer than GAP_MAX is shortened to GAP_KEEP.
"""
import json
import subprocess
import sys

import numpy as np
import soundfile as sf

src, out_json, out_mp4 = sys.argv[1], sys.argv[2], sys.argv[3]

# (src_start, src_end, text) - bounds from the word timings + energy analysis
K = [
    (2.30, 4.27, "aku nak bagi tahu satu info yang penting,"),
    (4.99, 7.36, "hujung minggu ni, hari Sabtu dan Ahad"),
    (7.74, 15.10, "di Perodua 3S Jalan Reko, kita ada beberapa program menarik lah. Seperti kita ada buat free inspection untuk kereta-kereta lama."),
    (15.42, 21.26, "Kita juga ada buat sediakan untuk submission loan face to face. Sebab kita ada bawa banker panel sekali."),
    (23.22, 32.68, "Kita juga ada untuk siapa yang nak cek kesihatan, boleh datang juga dekat sini. Ataupun kita juga menyediakan permainan VR game dan makanan juga disediakan."),
    (32.68, 41.24, "Jadi siapa-siapa orang yang berdekatan dengan Kajang ataupun sekitarnya, kami mengalu-alukan kedatangan anda untuk datang ke showroom kami."),
    (42.72, 48.84, "Hari Sabtu dan Ahad ni, kalau siapa nak datang boleh jumpa dengan Shauky. InsyaAllah kita jumpa nanti. Assalamualaikum."),
]
GAP_MAX, GAP_KEEP = 0.26, 0.12
FPS = 30

# --- energy envelope (10 ms) to snap edges and find pauses
probe = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "wav", "-"],
                       capture_output=True, check=True).stdout
import io
x, sr = sf.read(io.BytesIO(probe), dtype="float32")
hop = sr // 100
db = np.array([20 * np.log10(np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) + 1e-9) for i in range(len(x) // hop)])
db = np.convolve(db, np.ones(3) / 3, mode="same")
p10, p95 = np.percentile(db, 10), np.percentile(db, 95)
thr = p10 + (p95 - p10) * 0.30


def snap(t, win=0.05):
    a, b = int((t - win) * 100), int((t + win) * 100)
    return (a + int(np.argmin(db[a:b]))) / 100


def pauses(a, b):
    """Low-energy runs inside [a, b] longer than GAP_MAX."""
    out, i, lo, hi = [], int(a * 100), int(a * 100), int(b * 100)
    while i < hi:
        if db[i] < thr:
            j = i
            while j < hi and db[j] < thr:
                j += 1
            if (j - i) / 100 > GAP_MAX and i > lo + 5 and j < hi - 5:
                out.append((i / 100, j / 100))
            i = j
        else:
            i += 1
    return out


fr = lambda t: round(round(t * FPS) / FPS, 4)

pieces = []  # (src_a, src_b, phrase_index)
for k, (a, b, _) in enumerate(K):
    # "hujung" opens on a soft h: take the hand-set start, do not snap it later
    a, b = (a if k == 1 else snap(a)), snap(b)
    cur = a
    for ga, gb in pauses(a, b):
        # keep GAP_KEEP of silence: a breath on each side of the cut
        pieces.append((cur, ga + GAP_KEEP / 2, k))
        cur = gb - GAP_KEEP / 2
    pieces.append((cur, b, k))
pieces = [(fr(a), fr(b), k) for a, b, k in pieces if b - a > 0.05]

parts, labels, segs, t = [], [], [], 0.0
for i, (a, b, k) in enumerate(pieces):
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b - a - 0.015:.3f}:d=0.015[a{i}];")
    labels.append(f"[v{i}][a{i}]")
    segs.append({"i": i, "phrase": k, "src_start": a, "src_end": b, "start": round(t, 4), "end": round(t + b - a, 4)})
    t += b - a

fc = "".join(parts) + "".join(labels) + f"concat=n={len(pieces)}:v=1:a=1[vc][ac];"
# picture: light denoise + sharpen (phone footage, outdoor), keep 1080x1920
fc += "[vc]hqdn3d=1.0:0.8:3:3,unsharp=5:5:0.6:3:3:0.0,scale=1080:1920:flags=lanczos,format=yuv420p[vout];"
# voice: rumble/wind cut, broadband denoise for the outdoor bed, presence, glue, TikTok loudness
fc += ("[ac]highpass=f=90,afftdn=nr=12:nf=-38,equalizer=f=3000:t=q:w=1.2:g=2.5,"
       "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,"
       "loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000[aout]")
cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc,
       "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
       "-g", "30", "-keyint_min", "30", "-sc_threshold", "0", "-r", str(FPS), "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_mp4]
subprocess.run(cmd, check=True)

phrases = []
for k, (_, _, text) in enumerate(K):
    ps = [s for s in segs if s["phrase"] == k]
    phrases.append({"k": k, "start": ps[0]["start"], "end": ps[-1]["end"], "text": text})
json.dump({"duration": round(t, 4), "phrases": phrases, "segments": segs}, open(out_json, "w"), ensure_ascii=False, indent=1)
print(f"tight duration {t:.2f}s from {len(x) / sr:.2f}s, {len(pieces)} pieces")
for s in segs:
    print(f'{s["start"]:6.2f}-{s["end"]:6.2f}  [{s["src_start"]:.2f}-{s["src_end"]:.2f}] p{s["phrase"]}')
