"""Stamp every browser-tab and installed-app icon URL with a version taken from the file's own bytes.

    python scripts/icon_versions.py          # rewrite site/index.html and site/manifest.webmanifest
    python scripts/icon_versions.py --check  # exit 1 if any icon URL is missing or out of date

Browsers keep a favicon for as long as its URL is unchanged, so an icon's URL carries ?v=<first 8 hex digits
of its SHA-256>: a changed icon is a new URL. The manifest lists icons too, so it is stamped the same way,
after its icon entries. scripts/ui_check.py asserts the stamps against the served bytes.
"""
import hashlib, re, sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
INDEX, MANIFEST = SITE / "index.html", SITE / "manifest.webmanifest"
LINK = re.compile(r'(<link rel="(?:icon|apple-touch-icon|mask-icon|manifest)"[^>]*?href=")([^"?]+)(?:\?v=[^"]*)?(")')
SRC = re.compile(r'("src":\s*")([^"?]+)(?:\?v=[^"]*)?(")')


def v8(path):
    return hashlib.sha256((SITE / path).read_bytes()).hexdigest()[:8]


def stamp_manifest(text):
    return SRC.sub(lambda m: f"{m.group(1)}{m.group(2)}?v={v8(m.group(2))}{m.group(3)}", text)


def stamp_index(text, manifest_version):
    def repl(m):
        name = m.group(2)
        v = manifest_version if name == "manifest.webmanifest" else v8(name)
        return f"{m.group(1)}{name}?v={v}{m.group(3)}"
    return LINK.sub(repl, text)


def main():
    check = "--check" in sys.argv
    old_manifest, old_index = MANIFEST.read_text(encoding="utf-8"), INDEX.read_text(encoding="utf-8")
    new_manifest = stamp_manifest(old_manifest)
    manifest_version = hashlib.sha256(new_manifest.encode("utf-8")).hexdigest()[:8]
    new_index = stamp_index(old_index, manifest_version)
    changed = [p.name for p, a, b in ((MANIFEST, old_manifest, new_manifest), (INDEX, old_index, new_index)) if a != b]
    if check:
        print("icon versions current" if not changed else "icon versions out of date in: " + ", ".join(changed))
        sys.exit(1 if changed else 0)
    for p, a, b in ((MANIFEST, old_manifest, new_manifest), (INDEX, old_index, new_index)):
        if a != b:
            p.write_text(b, encoding="utf-8")
    for m in LINK.finditer(new_index):
        print(m.group(2) + "?" + new_index[m.end(2):m.end(0) - 1].split("?", 1)[-1])
    print("updated: " + (", ".join(changed) or "nothing (already current)"))


if __name__ == "__main__":
    main()
