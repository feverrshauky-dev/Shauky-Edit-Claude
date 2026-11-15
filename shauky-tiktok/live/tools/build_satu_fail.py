"""Inline fonts and car images into single-file copies so they open on a phone/tablet
with no assets folder: overlay.html -> overlay-satu-fail.html, eksklusif.html -> eksklusif-satu-fail.html."""
import base64, pathlib, re, sys
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
def b64(path, mime):
    return f"data:{mime};base64," + base64.b64encode((root / path).read_bytes()).decode()
for src, out in [("overlay.html", "overlay-satu-fail.html"), ("eksklusif.html", "eksklusif-satu-fail.html")]:
    html = (root / src).read_text()
    html = re.sub(r"url\((assets/fonts/[^)]+\.woff2)\)", lambda m: f"url({b64(m.group(1), 'font/woff2')})", html)
    html = re.sub(r'"(assets/cars/[a-z-]+\.jpg)"', lambda m: f'"{b64(m.group(1), "image/jpeg")}"', html)
    assert "assets/" not in html, f"unresolved asset path in {src}"
    (root / out).write_text(html)
    print("wrote", root / out, len(html) // 1024, "KB")
