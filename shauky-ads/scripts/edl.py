"""Cut the pauses out of the source and write the tight a-roll plus its timeline.

usage: python3 scripts/edl.py src/source.mp4 src/edl.json assets/aroll.mp4
Bounds come from a 10 ms loudness envelope of the source (speech vs the
digital silence left between the original takes).
"""
import json, subprocess, sys
src, out_json, out_mp4 = sys.argv[1:4]
K = [  # (src_in, src_out, words)
 (0.27, 3.10, "Nak beli kereta tapi abang ada masalah, tiada lesen,"),
 (3.38, 5.10, "tiada deposit ataupun tiada penjamin,"),
 (5.36, 7.18, "ataupun abang ada masalah macam ni,"),
 (7.99, 8.55, "macam ni,"),
 (8.99, 9.98, "atau macam ni."),
 (10.55, 15.29, "Tapi kalau abang tak ada masalah macam ni, saya minta maaf banyak sangat-sangatnya."),
 (16.34, 23.55, "Saya nak bantu lima orang yang terawal sahaja sekarang ni. Jadi siapa yang nak memiliki kereta baru dengan rebate yang tak masuk akal,"),
 (23.80, 27.90, "boleh klik nombor WhatsApp saya di bawah, insyaAllah, peace yo!"),
]
fr = lambda x: round(round(x * 30) / 30, 4)
segs = [(fr(a), fr(b), t) for a, b, t in K]
parts, labels, tl, cur = [], [], [], 0.0
for i, (a, b, t) in enumerate(segs):
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{i}];")
    labels.append(f"[v{i}][a{i}]")
    tl.append({"i": i, "src_start": a, "src_end": b, "start": round(cur, 4), "end": round(cur + b - a, 4), "text": t})
    cur += b - a
fc = "".join(parts) + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[vc][ac];"
fc += "[vc]hqdn3d=1.0:0.8:3:3,unsharp=5:5:0.6:3:3:0.0,format=yuv420p[vout];"
fc += ("[ac]highpass=f=85,afftdn=nr=8:nf=-42,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=2.5,"
       "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,"
       "loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000[aout]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc,
    "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
    "-g", "30", "-keyint_min", "30", "-sc_threshold", "0", "-r", "30", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_mp4], check=True)
json.dump({"duration": round(cur, 4), "segments": tl}, open(out_json, "w"), ensure_ascii=False, indent=1)
print(f"tight duration {cur:.2f}s")
for s in tl: print(f'{s["start"]:6.2f}-{s["end"]:6.2f}  [{s["src_start"]:.2f}-{s["src_end"]:.2f}] {s["text"]}')
