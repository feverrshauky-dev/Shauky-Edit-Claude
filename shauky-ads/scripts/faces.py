"""Track the speaker's face box (source time) every 0.2 s so no graphic covers it."""
import cv2, json, sys
src, out = sys.argv[1], sys.argv[2]
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS)
casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
res, i, prev = [], 0, None
while True:
    ok, f = cap.read()
    if not ok: break
    if i % 6 == 0:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        fs = casc.detectMultiScale(g, 1.1, 6, minSize=(50, 50))
        best = None
        for (x, y, w, h) in fs:
            if y > 1300: continue
            c = (x + w / 2, y + h / 2)
            score = w * h - (0 if prev is None else 30 * (abs(c[0] - prev[0]) + abs(c[1] - prev[1])))
            if best is None or score > best[0]: best = (score, x, y, w, h)
        if best:
            _, x, y, w, h = best; prev = (x + w / 2, y + h / 2)
            res.append({"t": round(i / fps, 2), "x": int(x), "y": int(y), "w": int(w), "h": int(h)})
        else:
            res.append({"t": round(i / fps, 2), "x": None})
    i += 1
json.dump(res, open(out, "w"))
for r in res: print(r["t"], r.get("x"), r.get("y"), r.get("w"), r.get("h"))
