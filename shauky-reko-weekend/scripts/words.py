"""Caption words on the tight a-roll.

Timings come from Whisper (small, Malay) run on assets/aroll.mp4 -> transcript/aroll-whisper.json.
Whisper mishears a few words; FIX corrects the text, MERGE joins split reduplications.
Writes transcript/words.json. Re-run after re-cutting: python3 scripts/words.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
segs = json.loads((ROOT / "transcript" / "aroll-whisper.json").read_text())["segments"]

FIX = {
    "Pada": None,  # cut artefact at the "hujung" splice, not spoken
    "Satu": "Sabtu",
    "Rekor,": "Reko,",
    "bank,": "banker",
    "seseorang": "siapa",
    "menyedihkan": "menyediakan",
    "pemainan": "permainan",
    "kajang": "Kajang",
    "SSH.": "Shauky.",
    "S.H.": "Shauky.",
    "S.H.O.K.": "Shauky.",
    "Untuk": "untuk",
    "Boleh": "boleh",
}
words = []
for si, s in enumerate(segs):
    for w in s["words"]:
        t = w["text"]
        if t[:1] in "-." and words:  # kereta -kereta / mengalu -alukan / S .H.
            words[-1]["text"] = FIX.get(words[-1]["text"] + t, words[-1]["text"] + t)
            words[-1]["end"] = w["end"]
            continue
        t = FIX.get(t, t)
        if t is None:
            continue
        words.append({"id": f"w{len(words)}", "seg": si, "text": t, "start": w["start"], "end": w["end"]})
# "hujung" starts where the splice lands, not where Whisper put the dropped artefact
for w in words:
    if w["text"] == "hujung":
        w["start"] = 1.98
(ROOT / "transcript" / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=0))
print(" ".join(w["text"] for w in words))
print(len(words), "words")
