#!/usr/bin/env python3
"""Build a self-contained private HTML preview with no network requests."""
import base64
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "site"
out = pathlib.Path(sys.argv[1])

css = (ROOT / "assets/app.css").read_text(encoding="utf-8")
def inline_font(match):
    font = ROOT / "fonts" / match.group(1)
    return "url(data:font/woff2;base64," + base64.b64encode(font.read_bytes()).decode("ascii") + ")"
css = re.sub(r"url\(\.\./fonts/([^)]+)\)", inline_font, css)

html = (ROOT / "index.html").read_text(encoding="utf-8")
html = re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>\n?', "", html)
html = re.sub(r'<link rel="(?:manifest|icon|apple-touch-icon)"[^>]*>\n?', "", html)
html = html.replace('<link rel="stylesheet" href="assets/app.css">', f"<style>{css}</style>")

data = (ROOT / "data/runway.json").read_text(encoding="utf-8").replace("</", "<\\/")
zips = {}
for file in sorted((ROOT / "geo/zip").glob("*.json")):
    zips.update(json.loads(file.read_text(encoding="utf-8")))
cities = (ROOT / "geo/cities.json").read_text(encoding="utf-8").replace("</", "<\\/")
embedded = "<script>window.RUNWAY_DATA=" + data + ";window.RUNWAY_ZIP=" + json.dumps(zips, separators=(",", ":")) + ";window.RUNWAY_CITIES=" + cities + ";</script>"
for name in ("config", "footer", "app"):
    script = (ROOT / f"assets/{name}.js").read_text(encoding="utf-8")
    if name == "app":
        script = embedded + "\n<script>" + script + "</script>"
    else:
        script = "<script>" + script + "</script>"
    html = html.replace(f'<script src="assets/{name}.js"></script>', script)

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8")
print(out, len(html.encode("utf-8")) // 1024, "KB")
