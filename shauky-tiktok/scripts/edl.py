"""Build the tight a-roll from the kept phrases and write the new timeline."""
import json, subprocess, sys
src, out_json, out_mp4 = sys.argv[1], sys.argv[2], sys.argv[3]
# (src_start, src_end, text) - speech bounds from the energy analysis
K = [
 (0.57, 2.49, "Kalau kau jumpa SA,"),
 (2.98, 3.61, "yang cakap"),
 (4.22, 5.10, "loan kau boleh approve"),
 (5.85, 7.82, "sebelum bank bagi approval, kau kena hati-hati."),
 (8.31, 11.75, "SA yang kerja dekat sini, bila dapat dokumen daripada korang,"),
 (12.17, 13.71, "perkara yang pertama mereka akan buat semakan."),
 (14.31, 15.94, "Dan yang kedua, mereka akan tengok"),
 (16.39, 18.59, "bank mana yang bersesuaian dengan dokumen korang."),
 (19.11, 22.57, "Selepas itu mereka akan follow up pula dengan bank untuk dapatkan keputusan."),
 (23.05, 23.98, "Tapi apa-apa pun,"),
 (24.43, 25.30, "keputusan akhir"),
 (25.72, 27.65, "terletak di tangan bank."),
 (28.61, 32.73, "Tapi kalau untuk aku, aku lebih rela explain awal-awal dekat customer."),
 (33.05, 34.78, "Kalau dia layak, aku akan cakap layak."),
 (35.00, 37.40, "Kalau dia tak layak, aku akan bagi tahu tak layak. Sebab apa?"),
 (37.75, 41.60, "Aku tak nak bagi harapan palsu kepada customer-customer aku."),
 (42.58, 47.67, "Kalau kau tengah cari kereta Perodua, nak tahu pasal loan dengan lebih jelas,"),
 (48.24, 50.37, "nombor aku dekat bio, boleh contact aku. InsyaAllah."),
]
HARD = [0.57, 7.82, 8.31, 28.24, 28.61, 41.60, 42.58]  # existing cuts in the source
PRE, POST = 0.06, 0.10
segs = []
for i, (a, b, t) in enumerate(K):
    lo = K[i-1][1] if i else 0.0
    hi = K[i+1][0] if i + 1 < len(K) else 51.5
    a2 = max(a - PRE, lo + 0.02, *[h for h in HARD if h <= a + 1e-6])
    b2 = min(b + POST, hi - 0.02, *[h for h in HARD if h >= b - 1e-6])
    segs.append((round(a2, 3), round(b2, 3), t))
# snap to frame grid (30 fps)
fr = lambda x: round(round(x * 30) / 30, 4)
segs = [(fr(a), fr(b), t) for a, b, t in segs]
parts, labels, tl, cur = [], [], [], 0.0
for i, (a, b, t) in enumerate(segs):
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[1:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b-a-0.015:.3f}:d=0.015[a{i}];")
    labels.append(f"[v{i}][a{i}]")
    tl.append({"i": i, "src_start": a, "src_end": b, "start": round(cur, 4), "end": round(cur + b - a, 4), "text": t})
    cur += b - a
fc = "".join(parts) + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[vc][ac];"
# quality: deblock + light temporal denoise + sharpen; voice: rumble cut, denoise, presence, glue, loudness
fc += ("[vc]deblock=filter=strong:block=8,hqdn3d=1.2:1.0:3:3,unsharp=5:5:0.75:3:3:0.0,"
       "scale=1080:1920:flags=lanczos,format=yuv420p[vout];")
fc += ("[ac]highpass=f=80,afftdn=nr=10:nf=-40,equalizer=f=3200:t=q:w=1.2:g=2.5,"
       "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,"
       "loudnorm=I=-14:TP=-1.5:LRA=7,aresample=48000[aout]")
cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-i", src, "-filter_complex", fc,
       "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
       "-g", "30", "-keyint_min", "30", "-sc_threshold", "0", "-r", "30", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_mp4]
subprocess.run(cmd, check=True)
json.dump({"duration": round(cur, 4), "segments": tl}, open(out_json, "w"), ensure_ascii=False, indent=1)
print(f"tight duration {cur:.2f}s from 51.57s")
for s in tl: print(f'{s["start"]:6.2f}-{s["end"]:6.2f}  [{s["src_start"]:.2f}-{s["src_end"]:.2f}] {s["text"]}')
