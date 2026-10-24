"""Align the known voiceover script to the ElevenLabs take without ASR.

Speech runs come from ffmpeg silencedetect; script pieces (split at , . ? !)
are matched to runs with a DP that keeps the speaking rate even and prefers
pauses at punctuation. Word times inside a run are spread by letter count.

usage: python3 scripts/align.py assets/vo/voiceover.mp3 SKRIP-ELEVENLABS.txt transcript/words.json
"""
import json
import re
import subprocess
import sys

audio, script, out = sys.argv[1:4]

log = subprocess.run(
    ["ffmpeg", "-hide_banner", "-i", audio, "-af", "silencedetect=noise=-38dB:d=0.2", "-f", "null", "-"],
    capture_output=True, text=True,
).stderr
dur = float(subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio],
    capture_output=True, text=True,
).stdout)
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
# speech runs = gaps between silences
runs, t = [], 0.0
sil = list(zip(starts, ends + [dur] * (len(starts) - len(ends))))
for s, e in sil:
    if s - t > 0.08:
        runs.append((t, s))
    t = e
if dur - t > 0.08:
    runs.append((t, dur))

text = open(script).read().replace("\n", " ")
pieces = []  # (words, strength of the punctuation that ends it)
for m in re.finditer(r"[^,.?!]+[,.?!]?", text):
    p = m.group().strip()
    if not p:
        continue
    strength = 2 if p[-1] in ".?!" else 1 if p[-1] == "," else 0
    pieces.append((p.split(), strength))

letters = lambda ws: sum(len(re.sub(r"[^\w]", "", w)) for w in ws) + 0.6 * len(ws)
c = [letters(ws) for ws, _ in pieces]
d = [e - s for s, e in runs]
rate = sum(d) / sum(c)
N, M = len(pieces), len(runs)
INF = float("inf")
best = [[INF] * (M + 1) for _ in range(N + 1)]
back = [[None] * (M + 1) for _ in range(N + 1)]
best[0][0] = 0.0
for i in range(N + 1):
    for j in range(M + 1):
        if best[i][j] == INF:
            continue
        for k in range(1, 6):
            for l in range(1, 6):
                if i + k > N or j + l > M:
                    continue
                cc = sum(c[i:i + k])
                dd = sum(d[j:j + l])
                cost = (dd - rate * cc) ** 2 / max(dd, 0.3)
                cost += sum(4.0 if pieces[x][1] == 2 else 0.6 for x in range(i, i + k - 1))
                cost += 3.0 * (l - 1)
                if best[i][j] + cost < best[i + k][j + l]:
                    best[i + k][j + l] = best[i][j] + cost
                    back[i + k][j + l] = (i, j)

groups, i, j = [], N, M
while (i, j) != (0, 0):
    pi, pj = back[i][j]
    groups.append((pi, i, pj, j))
    i, j = pi, pj
groups.reverse()

words = []
for pi, i, pj, j in groups:
    ws = [w for p in pieces[pi:i] for w in p[0]]
    t0, t1 = runs[pj][0], runs[j - 1][1]
    span = [(runs[x][0], runs[x][1]) for x in range(pj, j)]
    speech = sum(e - s for s, e in span)
    w_len = [letters([w]) for w in ws]
    total = sum(w_len)
    # map cumulative letter share onto speech time, skipping inner pauses
    def at(frac):
        need = frac * speech
        for s, e in span:
            if need <= e - s:
                return s + need
            need -= e - s
        return span[-1][1]
    acc = 0.0
    for w, n in zip(ws, w_len):
        words.append({"text": w, "start": round(at(acc / total), 3), "end": round(at((acc + n) / total), 3)})
        acc += n

# ids, and seg = sentence index (captions never span sentences)
seg = 0
for k, w in enumerate(words):
    w["id"] = f"w{k}"
    w["seg"] = seg
    if w["text"][-1] in ".?!":
        seg += 1

json.dump(words, open(out, "w"), ensure_ascii=False, indent=1)
print(f"{len(runs)} speech runs, {N} pieces, {len(words)} words, rate {rate:.3f}s/letter")
