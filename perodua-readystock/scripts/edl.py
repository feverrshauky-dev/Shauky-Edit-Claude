"""Cut the tight a-roll: hook first, repeats and dead air removed. Writes transcript/edl.json + assets/aroll.mp4.
usage: python3 scripts/edl.py assets/src/source.mp4 transcript/edl.json assets/aroll.mp4"""
import json, subprocess, sys
src, out_json, out_mp4 = sys.argv[1:4]
# (src_in, src_out, text) - cut points sit inside measured silences (energy < -27 dB)
K = [
 (10.81, 16.12, "Kalau abang kakak bagi dokumen hari ni, kita submit, minggu depan abang kakak dah boleh dapat kereta."),  # HOOK
 (5.40,  9.95,  "Perodua 3S Jalan Kajang ni, sekarang ni kita ada banyak sangat ready stock."),
 (18.46, 21.43, "Sekarang ni kita ada Bezza, Ativa, Alza,"),
 (22.44, 22.95, "Aruz,"),
 (23.92, 24.95, "Myvi dan Axia,"),
 (25.22, 25.86, "dan banyak lagi."),
 (26.88, 27.83, "So sekarang adalah"),
 (28.22, 31.92, "masa yang sangat sesuai untuk abang kakak beli kereta."),
 (32.18, 34.24, "Sebabnya apa? Yang pertama, kereta ready stock,"),
 (34.60, 37.58, "dan yang kedua, rebate yang Perodua bagi sangat-sangat tinggi."),
 (37.84, 39.16, "Jadi rugi kalau abang kakak"),
 (39.40, 40.30, "tak grab sekarang."),
 (40.69, 41.99, "Jadi siapa-siapa yang"),
 (42.53, 46.05, "nak kereta Perodua boleh contact Shauky, nombor saya di bio, insyaAllah."),
]
fr = lambda x: round(round(x * 30) / 30, 4)
segs = [(fr(a), fr(b), t) for a, b, t in K]
parts, labels, tl, cur = [], [], [], 0.0
for i, (a, b, t) in enumerate(segs):
    d = b - a
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={d-0.02:.3f}:d=0.02[a{i}];")
    labels.append(f"[v{i}][a{i}]")
    tl.append({"i": i, "src_start": a, "src_end": b, "start": round(cur, 4), "end": round(cur + d, 4), "text": t})
    cur += d
fc = "".join(parts) + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[vc][ac];"
fc += "[vc]hqdn3d=1.0:1.0:3:3,unsharp=5:5:0.6:3:3:0.0,eq=contrast=1.04:saturation=1.08,format=yuv420p[vout];"
# voice: rumble + wind cut, broadband denoise, presence lift, de-harsh, glue, broadcast loudness
fc += ("[ac]highpass=f=90,afftdn=nr=12:nf=-35:tn=1,equalizer=f=250:t=q:w=1.0:g=-2,"
       "equalizer=f=3000:t=q:w=1.2:g=2.5,equalizer=f=7500:t=q:w=1.5:g=-1.5,"
       "acompressor=threshold=-21dB:ratio=3:attack=6:release=120:makeup=2,"
       "loudnorm=I=-15:TP=-1.5:LRA=7,aresample=48000[aout]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc,
    "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
    "-g", "30", "-keyint_min", "30", "-sc_threshold", "0", "-r", "30", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_mp4], check=True)
json.dump({"duration": round(cur, 4), "segments": tl}, open(out_json, "w"), ensure_ascii=False, indent=1)
print(f"tight duration {cur:.2f}s from 46.72s")
for s in tl: print(f'{s["start"]:6.2f}-{s["end"]:6.2f}  [{s["src_start"]:.2f}-{s["src_end"]:.2f}] {s["text"]}')
