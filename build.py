#!/usr/bin/env python3
"""Build the website into _site/ from the files in documents/.

Each document is listed once, titled from its filename. A PDF and a Word
file with the same name are shown as one entry with two links.
"""
import html
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote

# --- Edit these two lines to change the page heading -----------------------
SITE_TITLE = "Foundational Ideas"
SITE_INTRO = "Warwick Zeamer, PhD (McGill University)"
# ---------------------------------------------------------------------------

SITE_URL = "https://foundationalideas.org/"

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "documents"
OUT = ROOT / "_site"
LINK_LABELS = {".pdf": "Read (PDF)", ".docx": "Word file", ".doc": "Word file"}


def title_from(stem: str) -> str:
    s = re.sub(r"[_-]+", " ", stem)
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)  # FoundationalStruggles -> Foundational Struggles
    return re.sub(r"\s+", " ", s).strip()


def last_updated(path: Path) -> str:
    """Date of the last commit that touched this file (empty if unknown)."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            cwd=ROOT, capture_output=True, text=True,
        )
        return result.stdout.strip()
    except OSError:
        return ""


def collect():
    groups = {}
    for f in sorted(DOCS.iterdir()):
        if f.name.startswith(".") or f.suffix.lower() not in LINK_LABELS:
            continue
        groups.setdefault(f.stem, []).append(f)
    entries = []
    for stem, files in groups.items():
        files.sort(key=lambda f: list(LINK_LABELS).index(f.suffix.lower()))  # PDF first
        dates = [d for d in (last_updated(f) for f in files) if d]
        entries.append({"title": title_from(stem), "files": files, "date": max(dates, default="")})
    # Most recently updated first; undated (not yet committed) at the end.
    entries.sort(key=lambda e: (e["date"] != "", e["date"], e["title"]), reverse=True)
    return entries


def render(entries) -> str:
    items = []
    for e in entries:
        href = lambda f: "documents/" + quote(f.name)
        links = " ".join(
            f'<a class="file" href="{href(f)}">{LINK_LABELS[f.suffix.lower()]}</a>' for f in e["files"]
        )
        items.append(
            f'<li><a class="title" href="{href(e["files"][0])}">{html.escape(e["title"])}</a>'
            f'<div class="meta">{links}</div></li>'
        )
    body = "\n".join(items) if items else '<li class="empty">No documents yet.</li>'
    return page(f"<ul>\n{body}\n</ul>")


def page(content: str, footer: str = "") -> str:
    return TEMPLATE.format(
        title=html.escape(SITE_TITLE), intro=html.escape(SITE_INTRO), url=SITE_URL,
        content=content, footer=f"<footer>{footer}</footer>" if footer else "",
    )


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{intro}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{intro}">
<meta property="og:url" content="{url}">
<meta name="theme-color" content="#fbfaf7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#161514" media="(prefers-color-scheme: dark)">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ctext x='16' y='25' text-anchor='middle' font-family='Georgia,serif' font-size='28' fill='%231f1d1a'%3EF%3C/text%3E%3C/svg%3E">
<style>
  :root {{ --bg: #fbfaf7; --text: #1f1d1a; --muted: #6b665e; --line: #e4e0d8; --link: #2f4f7f; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #161514; --text: #ebe7e0; --muted: #a29c92; --line: #33302c; --link: #9cb8e6; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text);
         font: 18px/1.6 Georgia, "Times New Roman", serif; }}
  main {{ max-width: 44rem; margin: 0 auto; padding: clamp(2rem, 8vw, 4.5rem) 16px 3rem; }}
  h1 {{ font-weight: normal; font-size: clamp(2rem, 6vw, 2.6rem); line-height: 1.15; margin: 0 0 .35rem;
        letter-spacing: .005em; }}
  h1 a {{ color: inherit; text-decoration: none; }}
  .intro {{ color: var(--muted); margin: 0 0 2.5rem; }}
  ul {{ list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--line); }}
  li {{ padding: 1rem 0; border-bottom: 1px solid var(--line); }}
  a {{ color: var(--link); text-underline-offset: .18em; text-decoration-thickness: 1px; }}
  a:focus-visible {{ outline: 2px solid var(--link); outline-offset: 3px; border-radius: 2px; }}
  .title {{ font-size: 1.3rem; line-height: 1.35; text-decoration: none; color: var(--text); }}
  .title:hover {{ color: var(--link); text-decoration: underline; }}
  .meta {{ margin-top: .3rem; font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           color: var(--muted); display: flex; flex-wrap: wrap; align-items: baseline; gap: .3rem 1.25rem; }}
  .empty {{ color: var(--muted); }}
  footer {{ margin-top: 2.5rem; font: 13px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--muted); }}
</style>
</head>
<body>
<main>
<header>
<h1><a href="/">{title}</a></h1>
<p class="intro">{intro}</p>
</header>
{content}
{footer}
</main>
</body>
</html>
"""


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(DOCS, OUT / "documents", ignore=shutil.ignore_patterns(".*"))
    (OUT / "index.html").write_text(render(collect()), encoding="utf-8")
    (OUT / "404.html").write_text(
        page("<p>Page not found.</p>", footer='<a href="/">All documents</a>'), encoding="utf-8")
    print(f"Built {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
