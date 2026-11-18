"""Build the tight a-roll from the kept phrases and write the new timeline.

Cuts (source seconds):
  - opening "Assalamualaikum" (0.56-1.30): the hook starts on the problem instead
  - pauses at 5.55-6.06, 7.40-7.56, 22.84-23.10
  - "yang di mana" filler (9.42-10.42)
  - the false start "Abang Akak boleh" (18.80-19.76) before "klik nombor saya"
  - the repeated "InsyaAllah" (23.70-24.40) before the sign-off
"""
import json, subprocess, sys
src, out_json, out_mp4 = sys.argv[1], sys.argv[2], sys.argv[3]
K = [
 (1.80, 5.58, "Abang Akak mesti pernah ada masalah bila Abang Akak nak jual kereta lama,"),
 (6.06, 7.40, "baki loan masih lagi tinggi."),
 (7.56, 9.42, "Tapi dekat sini kita ada satu cara"),
 (10.42, 18.74, "Abang Akak boleh gunakan duit rebate kereta sebagai duit untuk tutup loan kereta lama. Jadi kalau Abang Akak nak tahu macam mana caranya,"),
 (19.92, 22.84, "klik nombor saya di bio. InsyaAllah saya akan bantu Abang Akak"),
 (23.10, 23.70, "sampai jadi."),
 (24.40, 25.66, "Assalamualaikum."),
]
fr = lambda x: round(round(x * 30) / 30, 4)  # 30 fps frame grid
segs = [(fr(a), fr(b), t) for a, b, t in K]
parts, labels, tl, cur = [], [], [], 0.0
for i, (a, b, t) in enumerate(segs):
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[1:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b-a-0.018:.3f}:d=0.018[a{i}];")
    labels.append(f"[v{i}][a{i}]")
    tl.append({"i": i, "src_start": a, "src_end": b, "start": round(cur, 4), "end": round(cur + b - a, 4), "text": t})
    cur += b - a
fc = "".join(parts) + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[vc][ac];"
# picture: light deblock + temporal denoise + gentle sharpen
fc += ("[vc]hqdn3d=1.0:0.8:3:3,unsharp=5:5:0.6:3:3:0.0,"
       "scale=1080:1920:flags=lanczos,format=yuv420p[vout];")
# voice: rumble/wind cut, denoise, de-mud, presence, glue, loudness for social
fc += ("[ac]highpass=f=90,afftdn=nr=12:nf=-38,equalizer=f=250:t=q:w=1.0:g=-2.5,"
       "equalizer=f=3200:t=q:w=1.2:g=2.5,"
       "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,"
       "loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000[aout]")
cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-i", src, "-filter_complex", fc,
       "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
       "-g", "30", "-keyint_min", "30", "-sc_threshold", "0", "-r", "30", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_mp4]
subprocess.run(cmd, check=True)
json.dump({"duration": round(cur, 4), "segments": tl}, open(out_json, "w"), ensure_ascii=False, indent=1)
print(f"tight duration {cur:.2f}s from 25.70s")
for s in tl: print(f'{s["start"]:6.2f}-{s["end"]:6.2f}  [{s["src_start"]:.2f}-{s["src_end"]:.2f}] {s["text"]}')
