"""Render site/AI-HANDOFF.md as site/ai-handoff.html, the page the site's "AI Handoff" links open.

build.py calls render() on every build, so the page cannot drift from the Markdown file, and anyone can read
the handoff on the site itself: no GitHub account, app or sign-in is involved. validate.py re-renders the file
and fails the build if the page is stale, if a section link misses, or if Markdown survived unrendered.

Standard library only, like the rest of the build. It follows GitHub's rendering of the Markdown the handoff
uses: ATX and setext headings (with GitHub's section anchors, so #34-... links keep working), paragraphs,
**strong**, *emphasis*, ~~strikethrough~~, `code`, [links](url), bare URLs and e-mail addresses, pipe tables,
nested bullet and numbered lists, fenced code blocks, block quotes and rules. A relative link resolves as it
would on GitHub: to the page on this site when the target is inside site/, otherwise to the file in the
repository. Text the renderer does not recognise is kept as plain text, never dropped, and reported as a
warning; validate.py turns every warning into a build failure.

    python scripts/handoff_page.py      # writes site/ai-handoff.html (build.py does this too)
"""
import hashlib, html, pathlib, posixpath, re, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SOURCE = SITE / "AI-HANDOFF.md"
OUT_NAME = "ai-handoff.html"
TITLE = "AI Handoff · APP Conference Runway"


def repo_url():
    """The repository named in site/assets/config.js (a fork names its own), without a trailing slash."""
    try:
        m = re.search(r'\brepo:\s*"([^"]*)"', (SITE / "assets" / "config.js").read_text(encoding="utf-8"))
    except OSError:
        return ""
    return m.group(1).rstrip("/") if m else ""


# ---------------------------------------------------------------- inline

CODE = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.S)
ESCAPE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])")
ANGLE = re.compile(r"<((?:https?|mailto):[^\s<>]+|[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+)>")
LINK = re.compile(r"(!?)\[((?:[^\[\]\\]|\\.|\[[^\[\]]*\])*)\]\(\s*(<[^<>\n]*>|[^\s()]*(?:\([^\s()]*\)[^\s()]*)*)"
                  r"(?:\s+(\"[^\"]*\"|'[^']*'))?\s*\)", re.S)
URL = re.compile(r"(?<![\w/@.\-])(?:https?://|www\.)[^\s<\x01]+")
EMAIL = re.compile(r"(?<![\w.+\-@/:])[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+")
HOLD = re.compile(r"\x00(\d+)\x00")
BREAK = "\x01"   # a hard line break inside a paragraph


class Inline:
    """One renderer per page, so that link resolution and warnings are shared by every paragraph."""

    def __init__(self, resolve, warnings):
        self.resolve = resolve
        self.warnings = warnings

    def __call__(self, text):
        slots = []

        def hold(s):
            slots.append(s)
            return f"\x00{len(slots) - 1}\x00"

        def code(m):
            body = m.group(2).replace("\n", " ")
            if body.startswith(" ") and body.endswith(" ") and body.strip():
                body = body[1:-1]
            return hold("<code>" + html.escape(body, quote=False) + "</code>")

        text = CODE.sub(code, text)
        text = ESCAPE.sub(lambda m: hold(html.escape(m.group(1), quote=False)), text)
        text = ANGLE.sub(lambda m: hold(self.anchor(m.group(1), html.escape(m.group(1), quote=False))), text)

        def link(m):
            label, target, title = m.group(2), m.group(3).strip("<>"), m.group(4)
            if m.group(1):   # an image: shown when it lives on this site, otherwise linked (no third-party request)
                href = self.resolve(target)
                if not re.match(r"^[a-z][a-z0-9+.-]*:|^//", href, re.I):
                    return hold(f'<img src="{html.escape(href)}" alt="{html.escape(label)}" loading="lazy">')
                return hold(self.anchor(target, html.escape(label, quote=False) or html.escape(target, quote=False)))
            return hold(self.anchor(target, self(label), title[1:-1] if title else None))

        text = LINK.sub(link, text)

        def url(m):
            u = m.group(0)
            while u and (u[-1] in "?!.,:*_~'\";" or (u[-1] == ")" and u.count(")") > u.count("("))):
                u = u[:-1]
            host = re.sub(r"^https?://", "", u).split("/")[0].split("?")[0].split("#")[0]
            if "." not in host or not re.fullmatch(r"[\w.\-]+(?::\d+)?", host):
                return m.group(0)
            full = u if u.startswith("http") else "http://" + u
            return hold(self.anchor(full, html.escape(u, quote=False))) + m.group(0)[len(u):]

        text = URL.sub(url, text)

        def email(m):
            e = m.group(0).rstrip(".")
            if e[-1] in "-_":
                return m.group(0)
            return hold(self.anchor("mailto:" + e, html.escape(e, quote=False))) + m.group(0)[len(e):]

        text = EMAIL.sub(email, text)
        for tag in re.findall(r"</?[A-Za-z][\w-]*(?:\s[^<>]*)?/?>", text):
            self.warnings.append(f"raw HTML is not rendered: {tag[:60]}")
        text = html.escape(text, quote=False)
        text = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", text, flags=re.S)
        text = re.sub(r"(?<![\w\\])__(?=\S)(.+?)(?<=\S)__(?!\w)", r"<strong>\1</strong>", text, flags=re.S)
        text = re.sub(r"(?<![*\\])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?!\*)", r"<em>\1</em>", text, flags=re.S)
        text = re.sub(r"(?<![\w\\])_(?=[^\s_])(.+?)(?<=[^\s_])_(?!\w)", r"<em>\1</em>", text, flags=re.S)
        text = re.sub(r"(?<!~)~~(?=\S)(.+?)(?<=\S)~~(?!~)", r"<del>\1</del>", text, flags=re.S)
        text = text.replace(BREAK + "\n", "<br>\n").replace(BREAK, "<br>\n")
        while HOLD.search(text):
            text = HOLD.sub(lambda m: slots[int(m.group(1))], text)
        return text

    def anchor(self, target, label_html, title=None):
        href = self.resolve(target)
        t = f' title="{html.escape(title)}"' if title else ""
        return f'<a href="{html.escape(href)}"{t}>{label_html}</a>'


def site_resolver(repo):
    """Resolve a link as GitHub would for a file in site/, but pointing at this site where the target is in it."""
    def resolve(target):
        if re.match(r"^[a-z][a-z0-9+.-]*:|^//|^#", target, re.I):
            return target
        path, _, frag = target.partition("#")
        full = posixpath.normpath(posixpath.join("site", path)) if path else "site/AI-HANDOFF.md"
        if full == "site/AI-HANDOFF.md":
            out = OUT_NAME
        elif full.startswith("site/"):
            out = full[len("site/"):]
        elif repo:
            out = f"{repo}/blob/main/{full}"
        else:
            out = target
        return out + ("#" + frag if frag else "")
    return resolve


# ---------------------------------------------------------------- blocks

ATX = re.compile(r"^ {0,3}(#{1,6})(?=[ \t]|$)(.*)$")
SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
HR = re.compile(r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$")
FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})[ \t]*([^`]*?)[ \t]*$")
QUOTE = re.compile(r"^ {0,3}> ?(.*)$")
ITEM = re.compile(r"^( {0,3})(?:([-+*])|(\d{1,9})([.)]))([ \t]+|$)(.*)$")
DELIM = re.compile(r"^ {0,3}\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")
REFDEF = re.compile(r"^ {0,3}\[[^\]]+\]:\s*\S")
HTMLBLOCK = re.compile(r"^ {0,3}<(?:!--|/?[A-Za-z][\w-]*(?:[\s/>]|$))")


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, i = [], "", 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur += "|"; i += 2; continue
        if s[i] == "|":
            cells.append(cur.strip()); cur = ""; i += 1; continue
        cur += s[i]; i += 1
    cells.append(cur.strip())
    return cells


def starts_block(line):
    return bool(ATX.match(line) or FENCE.match(line) or HR.match(line) or QUOTE.match(line) or ITEM.match(line))


def slugger():
    """GitHub's section anchors (github-slugger): lower case; keep letters, marks, numbers, connector
    punctuation, spaces and hyphens; spaces become hyphens; a repeated anchor gets -1, -2, ..."""
    seen = {}

    def slug(text):
        s = "".join(ch for ch in text.lower() if ch in " -" or unicodedata.category(ch)[0] in "LMN" or unicodedata.category(ch) == "Pc")
        base = result = s.replace(" ", "-")
        while result in seen:
            seen[base] += 1
            result = f"{base}-{seen[base]}"
        seen[result] = 0
        return result
    return slug


class Renderer:
    def __init__(self, repo):
        self.warnings = []
        self.inline = Inline(site_resolver(repo), self.warnings)
        self.slug = slugger()
        self.headings = []   # (level, id, text)

    def heading(self, level, raw):
        inner = self.inline(raw.strip())
        text = html.unescape(re.sub(r"<[^>]+>", "", inner))
        hid = self.slug(text)
        self.headings.append((level, hid, text))
        return ("h", f'<h{level} id="{html.escape(hid)}">{inner}'
                     f'<a class="anchor" href="#{html.escape(hid)}" aria-label="Link to this section">#</a></h{level}>')

    def paragraph(self, lines):
        parts = []
        for k, line in enumerate(lines):
            last = k == len(lines) - 1
            s = line.strip()
            if not last and (line.endswith("  ") or s.endswith("\\")):
                s = (s[:-1] if s.endswith("\\") else s) + BREAK
            parts.append(s)
        return ("p", self.inline("\n".join(parts)))

    def blocks(self, lines):
        """Render a list of lines into (kind, html) blocks; kind "p" lets a tight list drop the <p>."""
        out, para, i, n = [], [], 0, len(lines)

        def flush():
            if para:
                out.append(self.paragraph(para)); para.clear()

        while i < n:
            line = lines[i]
            if not line.strip():
                flush(); i += 1; continue
            m = FENCE.match(line)
            if m:
                flush()
                pad, fence, info = len(m.group(1)), m.group(2), m.group(3).split()
                body, i, closed = [], i + 1, False
                while i < n:
                    c = re.match(r"^ {0,3}(`{3,}|~{3,})[ \t]*$", lines[i])
                    if c and c.group(1)[0] == fence[0] and len(c.group(1)) >= len(fence):
                        closed = True; i += 1; break
                    body.append(re.sub(r"^ {0,%d}" % pad, "", lines[i])); i += 1
                if not closed:
                    self.warnings.append("a code fence is never closed")
                cls = f' class="language-{html.escape(info[0])}"' if info else ""
                out.append(("pre", f"<pre><code{cls}>{html.escape(chr(10).join(body), quote=False)}</code></pre>"))
                continue
            m = ATX.match(line)
            if m:
                flush()
                raw = re.sub(r"(?:^|[ \t]+)#+[ \t]*$", "", m.group(2).strip())
                out.append(self.heading(len(m.group(1)), raw)); i += 1; continue
            if para and SETEXT.match(line) and not ITEM.match(line):
                level = 1 if line.strip()[0] == "=" else 2
                raw = " ".join(l.strip() for l in para); para.clear()
                out.append(self.heading(level, raw)); i += 1; continue
            if HR.match(line):
                flush(); out.append(("hr", "<hr>")); i += 1; continue
            if QUOTE.match(line):
                flush()
                inner = []
                while i < n and lines[i].strip():
                    q = QUOTE.match(lines[i])
                    if q:
                        inner.append(q.group(1))
                    elif inner and inner[-1].strip() and not starts_block(lines[i]):
                        inner.append(lines[i])      # lazy continuation of a quoted paragraph
                    else:
                        break
                    i += 1
                body = "\n".join(h for _, h in self.blocks(inner) for h in [h if _ != "p" else f"<p>{h}</p>"])
                out.append(("quote", f"<blockquote>\n{body}\n</blockquote>"))
                continue
            m = ITEM.match(line)
            if m and (not para or (m.group(6).strip() and (m.group(2) or m.group(3) == "1"))):
                flush()
                html_list, i = self.list_block(lines, i)
                out.append(("list", html_list)); continue
            if "|" in line and i + 1 < n and DELIM.match(lines[i + 1]) and len(split_row(line)) == len(split_row(lines[i + 1])):
                flush()
                html_table, i = self.table(lines, i)
                out.append(("table", html_table)); continue
            if not para and REFDEF.match(line):
                self.warnings.append(f"reference-style link definitions are not supported: {line.strip()[:60]}")
            if not para and HTMLBLOCK.match(line):
                self.warnings.append(f"raw HTML is not rendered: {line.strip()[:60]}")
            para.append(line); i += 1
        flush()
        return out

    def table(self, lines, i):
        head = split_row(lines[i])
        aligns = []
        for c in split_row(lines[i + 1]):
            c = c.strip()
            aligns.append("center" if c.startswith(":") and c.endswith(":") else "right" if c.endswith(":") else "left" if c.startswith(":") else None)
        i += 2
        rows = []
        while i < len(lines) and lines[i].strip() and not starts_block(lines[i]):
            cells = split_row(lines[i])
            rows.append((cells + [""] * len(head))[:len(head)]); i += 1

        def cell(tag, text, k):
            a = f' style="text-align:{aligns[k]}"' if aligns[k] else ""
            return f"<{tag}{a}>{self.inline(text)}</{tag}>"

        thead = "<tr>" + "".join(cell("th", c, k) for k, c in enumerate(head)) + "</tr>"
        tbody = "".join("<tr>" + "".join(cell("td", c, k) for k, c in enumerate(r)) + "</tr>\n" for r in rows)
        return (f'<div class="table-wrap"><table>\n<thead>{thead}</thead>\n<tbody>\n{tbody}</tbody>\n</table></div>', i)

    def list_block(self, lines, i):
        first = ITEM.match(lines[i])
        ordered = first.group(3) is not None
        mark = first.group(4) if ordered else first.group(2)
        start = int(first.group(3)) if ordered else 1
        items, loose, n = [], False, len(lines)
        while i < n:
            m = ITEM.match(lines[i])
            if not m or (m.group(3) is not None) != ordered or (m.group(4) if ordered else m.group(2)) != mark:
                break
            gap = len(m.group(5).expandtabs(4))
            col = len(m.group(1)) + len(m.group(2) or m.group(3) + m.group(4)) + (gap if 1 <= gap <= 4 else 1)
            body, i, blank, inner_blank = [m.group(6)], i + 1, False, False
            while i < n:
                line = lines[i]
                if not line.strip():
                    blank = True; body.append(""); i += 1; continue
                indent = len(line) - len(line.lstrip(" "))
                if indent >= col:
                    inner_blank = inner_blank or blank
                    body.append(line[col:]); blank = False; i += 1; continue
                if blank or starts_block(line):
                    break
                body.append(line.strip()); i += 1       # lazy continuation of the item's paragraph
            while body and not body[-1].strip():
                body.pop()
            items.append(body)
            nxt = ITEM.match(lines[i]) if i < n else None
            same = nxt and (nxt.group(3) is not None) == ordered and (nxt.group(4) if ordered else nxt.group(2)) == mark
            if inner_blank or (blank and same):
                loose = True
        tag = "ol" if ordered else "ul"
        attr = f' start="{start}"' if ordered and start != 1 else ""
        parts = []
        for body in items:
            blocks = self.blocks(body)
            inner = "\n".join(h if (k != "p" or not loose) else f"<p>{h}</p>" for k, h in blocks)
            parts.append(f"<li>{inner}</li>")
        return f"<{tag}{attr}>\n" + "\n".join(parts) + f"\n</{tag}>", i


# ---------------------------------------------------------------- page

CSS = """
@font-face{font-family:"Source Sans 3";font-weight:400;font-display:swap;src:url(fonts/source-sans-3-latin-400-normal.woff2) format("woff2")}
@font-face{font-family:"Source Sans 3";font-weight:400;font-style:italic;font-display:swap;src:url(fonts/source-sans-3-latin-400-italic.woff2) format("woff2")}
@font-face{font-family:"Source Sans 3";font-weight:600;font-display:swap;src:url(fonts/source-sans-3-latin-600-normal.woff2) format("woff2")}
@font-face{font-family:"Source Sans 3";font-weight:700;font-display:swap;src:url(fonts/source-sans-3-latin-700-normal.woff2) format("woff2")}
:root{--ground:#F6F4F0;--surface:#FFFEFC;--sunk:#EEE9E3;--ink:#202329;--ink-2:#4C5358;--ink-3:#667075;--rule:#D5D1CB;--rule-soft:#E9E4DE;--scarlet:#CC0033;--link:#0B55A3;--focus:#1B62BD;color-scheme:light}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-padding-top:12px}
body{margin:0;background:var(--ground);color:var(--ink);font:16.5px/1.6 "Source Sans 3","Segoe UI",system-ui,-apple-system,sans-serif;border-top:3px solid var(--scarlet);-webkit-font-smoothing:antialiased}
a{color:var(--link);text-underline-offset:2px}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.skip{position:absolute;z-index:10;left:16px;top:-60px;background:var(--ink);color:#fff;padding:8px 12px;font-weight:700}
.skip:focus{top:0}
.wrap{max-width:880px;margin:0 auto;padding-inline:24px}
.top{background:var(--surface);border-bottom:1px solid var(--rule)}
.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-block:12px}
.home{display:block;min-width:0}
.home img{display:block;height:34px;width:auto;max-width:100%}
.back{flex:none;color:var(--ink-2);font-weight:600;text-decoration:none;border:1px solid var(--rule);padding:7px 11px;white-space:nowrap}
.back:hover{color:var(--ink);border-color:var(--ink-3)}
main{padding-block:28px 36px}
.doc{background:var(--surface);border:1px solid var(--rule);padding:34px 44px 30px;overflow-wrap:break-word}
.doc h1{font:400 clamp(30px,4.6vw,42px)/1.1 Georgia,"Times New Roman",serif;letter-spacing:-.02em;margin:0 0 18px}
.doc h2{font-size:23px;line-height:1.25;margin:38px 0 12px;padding-top:16px;border-top:1px solid var(--rule)}
.doc h3{font-size:18.5px;line-height:1.3;margin:28px 0 8px}
.doc h1,.doc h2,.doc h3,.doc h4{scroll-margin-top:12px}
.anchor{margin-left:.35em;color:var(--ink-3);text-decoration:none;font-weight:400;opacity:0}
h1:hover .anchor,h2:hover .anchor,h3:hover .anchor,h4:hover .anchor,.anchor:focus{opacity:1}
.doc p,.doc ul,.doc ol,.doc pre,.doc blockquote{margin:0 0 14px}
.doc ul,.doc ol{padding-left:1.45em}
.doc li{margin:5px 0}
.doc li>ul,.doc li>ol{margin:5px 0 0}
.doc li>p{margin:0 0 8px}
.doc a{overflow-wrap:anywhere}
.doc code{font:.87em/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;background:var(--sunk);padding:.08em .34em;border-radius:3px;overflow-wrap:anywhere}
.doc pre{background:#F8F6F2;border:1px solid var(--rule-soft);padding:12px 14px;overflow-x:auto}
.doc pre code{background:none;padding:0;font-size:14px;overflow-wrap:normal;white-space:pre}
.doc blockquote{margin-left:0;padding:2px 0 2px 16px;border-left:3px solid var(--rule);color:var(--ink-2)}
.doc hr{border:0;border-top:1px solid var(--rule);margin:28px 0}
.doc img{max-width:100%;height:auto}
.table-wrap{overflow-x:auto;margin:0 0 16px;border:1px solid var(--rule)}
.doc table{border-collapse:collapse;width:100%;font-size:15px;line-height:1.45}
.doc th,.doc td{padding:8px 11px;text-align:left;vertical-align:top;border-bottom:1px solid var(--rule-soft)}
.doc th{background:var(--sunk);font-weight:700;border-bottom-color:var(--rule)}
.doc tbody tr:last-child td{border-bottom:0}
.toc{margin:0 0 8px;padding:14px 18px;background:#F8F6F2;border:1px solid var(--rule-soft)}
.toc p{margin:0 0 6px;font-size:12px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-3)}
.toc ul{margin:0;padding:0;list-style:none;columns:2;column-gap:28px}
.toc li{margin:0;padding:3px 0;break-inside:avoid}
.toc a{text-decoration:none}
.toc a:hover{text-decoration:underline}
.foot{color:var(--ink-3);font-size:14px;line-height:1.5;padding-bottom:40px}
.foot p{margin:0 0 6px}
.foot a{color:inherit}
@media (max-width:640px){
  .wrap{padding-inline:16px}
  .top .wrap{padding-block:10px}
  .home img{height:26px}
  .back{padding:6px 9px;font-size:15px}
  main{padding-block:18px 26px}
  .doc{background:none;border:0;padding:0}
  .doc h2{font-size:21px;margin-top:32px}
  .toc{padding:12px 14px}
  .toc ul{columns:1}
  .doc table{font-size:14.5px}
  .doc th,.doc td{padding:7px 9px}
}
@media print{
  body{background:#fff;border:0}
  .top,.skip,.toc,.anchor{display:none}
  .doc{border:0;padding:0}
  .doc a{color:inherit}
}
"""


def icon_links():
    """The site's own icon and manifest links, copied from index.html so the tab looks the same."""
    try:
        index = (SITE / "index.html").read_text(encoding="utf-8")
    except OSError:
        return ""
    keep = re.findall(r'<link rel="(?:manifest|icon|apple-touch-icon|mask-icon)"[^>]*>', index)
    return "\n".join(keep)


def render(source=None):
    """Return (page_html, warnings) for the handoff; source defaults to site/AI-HANDOFF.md."""
    raw = SOURCE.read_bytes() if source is None else source.encode("utf-8")
    md = raw.decode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()   # of the file's bytes, as the site serves them
    repo = repo_url()
    r = Renderer(repo)
    lines = md.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4).split("\n")
    blocks = r.blocks(lines)
    body, toc_done = [], False
    sections = [(hid, text) for level, hid, text in r.headings if level == 2]
    for kind, h in blocks:
        if not toc_done and kind == "h" and h.startswith("<h2") and sections:
            items = "\n".join(f'<li><a href="#{html.escape(hid)}">{html.escape(text)}</a></li>' for hid, text in sections)
            body.append(f'<nav class="toc" aria-label="Contents">\n<p>Contents</p>\n<ul>\n{items}\n</ul>\n</nav>')
            toc_done = True
        body.append(h if kind != "p" else f"<p>{h}</p>")
    source_links = '<a href="AI-HANDOFF.md">on this site</a>'
    if repo:
        source_links += f' and <a href="{html.escape(repo)}/blob/main/site/AI-HANDOFF.md">in the repository</a>'
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; font-src 'self'; img-src 'self' data:; manifest-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'; upgrade-insecure-requests">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="color-scheme" content="light">
<meta name="robots" content="noindex, nofollow, noarchive"><!-- the Runway is circulated among APPs, not listed in search engines -->
<meta name="handoff-source-sha256" content="{digest}">
<title>{html.escape(TITLE)}</title>
<meta name="description" content="How the APP Conference Runway was built, where its data comes from, and how to reproduce or challenge it.">
<meta name="theme-color" content="#102F3B">
{icon_links()}
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#doc">Skip to the handoff</a>
<header class="top"><div class="wrap">
<a class="home" href="./" title="The APP Conference Runway"><img src="assets/app-conference-runway-logo.png" width="1870" height="355" alt="APP Conference Runway" decoding="async"></a>
<a class="back" href="./">Back to the Runway</a>
</div></header>
<main class="wrap"><article class="doc" id="doc">
{chr(10).join(body)}
</article></main>
<footer class="wrap foot">
<p>This page is generated from the Markdown file AI-HANDOFF.md (SHA-256 <code>{digest[:12]}</code>) every time the site is built. The file itself is {source_links}.</p>
</footer>
</body>
</html>
"""
    return page, list(dict.fromkeys(r.warnings))


def write():
    page, warnings = render()
    (SITE / OUT_NAME).write_text(page, encoding="utf-8", newline="\n")
    return warnings


if __name__ == "__main__":
    for w in write():
        print("warning:", w)
    print(f"wrote site/{OUT_NAME}")
