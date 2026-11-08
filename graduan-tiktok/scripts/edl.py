"""Tight a-roll for the graduan video: hook moved to the front, stumbles and pauses removed.
usage: python3 scripts/edl.py <source.mp4> transcript/edl.json assets/aroll.mp4"""
import json, subprocess, sys
src, out_json, out_mp4 = sys.argv[1], sys.argv[2], sys.argv[3]
# (src_start, src_end, text) in playback order; edges sit in measured silences (10 ms RMS)
K = [
 (20.56, 22.47, "Baru satu hari bekerja,"),                       # hook, taken from the middle
 (22.84, 25.12, "mereka juga telah layak untuk memiliki"),         # 0.37 s pause cut
 (25.28, 26.58, "kereta pertama mereka."),                         # 0.16 s pause cut
 (0.00, 1.82, "Kereta pertama untuk graduan."),
 (2.98, 7.60, "Tanya kepada graduan-graduan di luar sana yang baru sahaja tamatkan sesi pelajaran,"),
 # dropped 7.60-10.96: "dan mereka sedang ini memulakan fasa hidup mereka" (stumble)
 (10.96, 12.60, "dan mereka juga ada keinginan"),
 (12.86, 15.14, "untuk memiliki kereta pertama mereka."),
 (15.28, 18.62, "Jadi, hari ini kita ada satu program khas untuk graduan."),
 # dropped 18.62-27.55: the hook line (already used up front) and "Jadi,"
 (27.55, 30.46, "Graduan-graduan yang inginkan info lebih lanjut,"),
 (30.80, 34.52, "boleh komen FRESH ataupun WhatsApp saya, nombor di bio."),
 (34.76, 35.22, "Ciao!"),
]
fr = lambda x: round(round(x * 30) / 30, 4)
parts, labels, tl, cur = [], [], [], 0.0
for i, (a, b, t) in enumerate(K):
    a, b = fr(a), fr(b)
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30[v{i}];"
                 f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b-a-0.02:.3f}:d=0.02[a{i}];")
    labels.append(f"[v{i}][a{i}]")
    tl.append({"i": i, "src_start": a, "src_end": b, "start": round(cur, 4), "end": round(cur + b - a, 4), "text": t})
    cur += b - a
fc = "".join(parts) + "".join(labels) + f"concat=n={len(K)}:v=1:a=1[vc][ac];"
fc += "[vc]hqdn3d=1.0:1.0:2:2,unsharp=5:5:0.5:3:3:0.0,format=yuv420p[vout];"
# voice: rumble cut, car-noise reduction, presence, glue, social loudness
fc += ("[ac]highpass=f=85,afftdn=nr=12:nf=-42,equalizer=f=3000:t=q:w=1.2:g=2,"
       "equalizer=f=220:t=q:w=1:g=-1.5,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,"
       "loudnorm=I=-15:TP=-1.5:LRA=7,aresample=48000[aout]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc,
    "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
    "-g", "30", "-keyint_min", "30", "-sc_threshold", "0", "-r", "30", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_mp4], check=True)
json.dump({"duration": round(cur, 4), "segments": tl}, open(out_json, "w"), ensure_ascii=False, indent=1)
print(f"tight duration {cur:.2f}s from 35.93s")
for s in tl: print(f'{s["start"]:6.2f}-{s["end"]:6.2f}  [{s["src_start"]:.2f}-{s["src_end"]:.2f}] {s["text"]}')
