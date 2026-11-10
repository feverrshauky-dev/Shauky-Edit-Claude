"""Build overlay-satu-fail.html: overlay.html with fonts and car images inlined,
so it opens from a single file on a phone/tablet (no assets folder needed)."""
import base64, pathlib, re, sys
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
html = (root / "overlay.html").read_text()
def b64(path, mime):
    return f"data:{mime};base64," + base64.b64encode((root / path).read_bytes()).decode()
html = re.sub(r"url\((assets/fonts/[^)]+\.woff2)\)", lambda m: f"url({b64(m.group(1), 'font/woff2')})", html)
html = re.sub(r'"(assets/cars/[a-z]+\.jpg)"', lambda m: f'"{b64(m.group(1), "image/jpeg")}"', html)
assert "assets/" not in html, "unresolved asset path"
(root / "overlay-satu-fail.html").write_text(html)
print("wrote", root / "overlay-satu-fail.html", len(html) // 1024, "KB")
