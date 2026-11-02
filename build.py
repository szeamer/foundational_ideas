#!/usr/bin/env python3
"""Build the website into _site/ from the files in documents/.

Each document is listed once, titled from its filename. A PDF and a Word
file with the same name are shown as one entry with two links.
"""
import datetime
import html
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote

# --- Edit these two lines to change the page heading -----------------------
SITE_TITLE = "Foundational Ideas"
SITE_INTRO = "Papers and notes."
# ---------------------------------------------------------------------------

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


def nice_date(iso: str) -> str:
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


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
        date = f'<span class="date">Updated {nice_date(e["date"])}</span>' if e["date"] else ""
        items.append(
            f'<li><a class="title" href="{href(e["files"][0])}">{html.escape(e["title"])}</a>'
            f'<div class="meta">{links}{date}</div></li>'
        )
    body = "\n".join(items) if items else '<li class="empty">No documents yet.</li>'
    return TEMPLATE.format(title=html.escape(SITE_TITLE), intro=html.escape(SITE_INTRO), items=body)


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --bg: #fbfaf7; --text: #1f1d1a; --muted: #6b665e; --line: #e4e0d8; --link: #2f4f7f; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #161514; --text: #ebe7e0; --muted: #a29c92; --line: #33302c; --link: #9cb8e6; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text);
         font: 18px/1.6 Georgia, "Times New Roman", serif; }}
  main {{ max-width: 44rem; margin: 0 auto; padding: 2rem 16px 3rem; }}
  h1 {{ font-weight: normal; font-size: 2rem; margin: 0 0 .1rem; letter-spacing: .01em; }}
  .intro {{ color: var(--muted); margin: 0 0 1.25rem; }}
  ul {{ list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--line); }}
  li {{ padding: .6rem 0; border-bottom: 1px solid var(--line); }}
  a {{ color: var(--link); }}
  .title {{ font-size: 1.25rem; text-decoration: none; color: var(--text); }}
  .title:hover {{ text-decoration: underline; }}
  .meta {{ margin-top: .1rem; font: 14px/1.5 -apple-system, "Segoe UI", sans-serif; color: var(--muted);
           display: flex; flex-wrap: wrap; gap: .4rem 1.1rem; }}
  .empty {{ color: var(--muted); }}
</style>
</head>
<body>
<main>
<h1>{title}</h1>
<p class="intro">{intro}</p>
<ul>
{items}
</ul>
</main>
</body>
</html>
"""


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(DOCS, OUT / "documents", ignore=shutil.ignore_patterns(".*"))
    (OUT / "index.html").write_text(render(collect()), encoding="utf-8")
    print(f"Built {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
