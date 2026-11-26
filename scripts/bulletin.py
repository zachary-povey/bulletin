#!/usr/bin/env python3
"""Bulletin tooling: topic selection, validation and static site build.

  python3 scripts/bulletin.py topics [due|all|<id> ...]   # JSON list of topics to update
  python3 scripts/bulletin.py check                       # validate topics/ and updates/
  python3 scripts/bulletin.py build [--out _site]         # render the static site
"""
import argparse
import datetime as dt
import html
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = ROOT / "topics"
UPDATES_DIR = ROOT / "updates"
SITE_DIR = ROOT / "site"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def read_doc(path):
    """Return (front matter dict, markdown body) for a file with YAML front matter."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path.relative_to(ROOT)}: missing YAML front matter")
    try:
        _, fm, body = text.split("---", 2)
    except ValueError:
        raise ValueError(f"{path.relative_to(ROOT)}: unterminated front matter")
    meta = yaml.safe_load(fm) or {}
    if not isinstance(meta, dict):
        raise ValueError(f"{path.relative_to(ROOT)}: front matter must be a mapping")
    return meta, body.strip()


def load_topics():
    topics = []
    for path in sorted(TOPICS_DIR.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        meta, body = read_doc(path)
        if not meta.get("title"):
            raise ValueError(f"{path.relative_to(ROOT)}: front matter needs a 'title'")
        topics.append({
            "id": path.stem,
            "title": str(meta["title"]),
            "cadence_days": int(meta.get("cadence_days", 1)),
            "order": meta.get("order", 100),
            "enabled": bool(meta.get("enabled", True)),
            "brief": body,
            "updates": load_updates(path.stem),
        })
    topics.sort(key=lambda t: (t["order"], t["title"]))
    return topics


def load_updates(topic_id):
    """Updates for a topic, newest first."""
    updates = []
    for path in sorted((UPDATES_DIR / topic_id).glob("*.md"), reverse=True):
        if not DATE_RE.match(path.stem):
            raise ValueError(f"{path.relative_to(ROOT)}: file name must be YYYY-MM-DD.md")
        meta, body = read_doc(path)
        if not body:
            raise ValueError(f"{path.relative_to(ROOT)}: empty update")
        updates.append({
            "date": dt.date.fromisoformat(path.stem),
            "headline": str(meta.get("headline", "")).strip(),
            "covers_from": str(meta.get("covers_from", "")).strip(),
            "body": body,
        })
    return updates


# ---------------------------------------------------------------- topics

def cmd_topics(args):
    topics = load_topics()
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    by_id = {t["id"]: t for t in topics}
    sel = args.selection or ["due"]
    if sel == ["all"]:
        chosen = [t for t in topics if t["enabled"]]
    elif sel == ["due"]:
        chosen = [
            t for t in topics if t["enabled"] and (
                not t["updates"]
                or (today - t["updates"][0]["date"]).days >= t["cadence_days"])
        ]
    else:
        unknown = [s for s in sel if s not in by_id]
        if unknown:
            sys.exit(f"Unknown topic(s): {', '.join(unknown)}. Known: {', '.join(by_id)}")
        chosen = [by_id[s] for s in sel]
    out = []
    for t in chosen:
        # Previous update before today (a same-day rerun replaces today's file).
        prev = next((u for u in t["updates"] if u["date"] < today), None)
        out.append({
            "id": t["id"],
            "title": t["title"],
            "topic_file": f"topics/{t['id']}.md",
            "output_file": f"updates/{t['id']}/{today.isoformat()}.md",
            "previous_update": f"updates/{t['id']}/{prev['date'].isoformat()}.md" if prev else None,
            # Window to research: from the previous update, or three days back on first run.
            "covers_from": (prev["date"] if prev else today - dt.timedelta(days=3)).isoformat(),
            "date": today.isoformat(),
        })
    print(json.dumps(out, indent=2))


def cmd_check(_args):
    topics = load_topics()
    ids = {t["id"] for t in topics}
    problems = []
    for d in UPDATES_DIR.iterdir() if UPDATES_DIR.exists() else []:
        if d.is_dir() and d.name not in ids:
            problems.append(f"updates/{d.name}/ has no matching topics/{d.name}.md")
    for t in topics:
        for u in t["updates"]:
            where = f"updates/{t['id']}/{u['date']}.md"
            if not u["headline"]:
                problems.append(f"{where}: missing 'headline' in front matter")
            if "](http" not in u["body"]:
                problems.append(f"{where}: no source links found")
    if problems:
        sys.exit("\n".join(problems))
    print(f"OK: {len(topics)} topics, {sum(len(t['updates']) for t in topics)} updates")


# ----------------------------------------------------------------- build

def render_md(text):
    import markdown
    return markdown.markdown(
        text, extensions=["extra", "sane_lists", "smarty"], output_format="html5")


def fmt_date(d):
    return f"{d.strftime('%A')} {d.day} {d.strftime('%B %Y')}"


def page(title, body, depth, generated):
    rel = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{rel}style.css">
</head>
<body>
<header class="site">
  <a class="brand" href="{rel}index.html">The Bulletin</a>
  <nav><a href="{rel}index.html">Latest</a><a href="{rel}archive/index.html">Archive</a><a href="{rel}topics/index.html">Topics</a></nav>
</header>
<main>
{body}
</main>
<footer>Compiled by Claude from public news sources. Summaries may contain errors &mdash; follow the source links. Built {generated}.</footer>
</body>
</html>
"""


def update_article(topic, update, rel, heading="h2", link_title=True):
    url = f"{rel}topics/{topic['id']}/{update['date']}.html"
    title = html.escape(topic["title"])
    if link_title:
        title = f'<a href="{url}">{title}</a>'
    covers = f" &middot; covering from {html.escape(update['covers_from'])}" if update["covers_from"] else ""
    headline = f'<p class="headline">{html.escape(update["headline"])}</p>' if update["headline"] else ""
    return f"""<article class="update" id="{topic['id']}">
<{heading} class="topic-title">{title}</{heading}>
<p class="meta">{fmt_date(update['date'])}{covers} &middot; <a href="{rel}topics/{topic['id']}/index.html">earlier updates</a></p>
{headline}
<div class="content">
{render_md(update['body'])}
</div>
</article>"""


def cmd_build(args):
    out = Path(args.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copy(SITE_DIR / "style.css", out / "style.css")
    (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    (out / ".nojekyll").write_text("")
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    topics = load_topics()
    live = [t for t in topics if t["updates"]]

    def write(relpath, title, body):
        dest = out / relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page(title, body, relpath.count("/"), generated), encoding="utf-8")

    # Home: the newest update of every topic.
    if live:
        newest = max(t["updates"][0]["date"] for t in live)
        toc = "".join(
            f'<li><a href="#{t["id"]}"><strong>{html.escape(t["title"])}</strong></a>'
            f'<span class="when">{t["updates"][0]["date"].strftime("%-d %b")}</span>'
            f'<span class="hl">{html.escape(t["updates"][0]["headline"])}</span></li>'
            for t in live)
        body = (f'<h1>Latest bulletin</h1><p class="meta">Most recent update: {fmt_date(newest)}</p>'
                f'<ul class="toc">{toc}</ul>'
                + "\n".join(update_article(t, t["updates"][0], "") for t in live))
    else:
        body = "<h1>Latest bulletin</h1><p>No updates published yet.</p>"
    write("index.html", "The Bulletin", body)

    # Archive: every update grouped by date.
    by_date = {}
    for t in live:
        for u in t["updates"]:
            by_date.setdefault(u["date"], []).append((t, u))
    body = "<h1>Archive</h1>"
    for d in sorted(by_date, reverse=True):
        items = "".join(
            f'<li><a href="../topics/{t["id"]}/{u["date"]}.html"><strong>{html.escape(t["title"])}</strong></a>'
            f'<span class="hl">{html.escape(u["headline"])}</span></li>' for t, u in by_date[d])
        body += f'<h2>{fmt_date(d)}</h2><ul class="toc">{items}</ul>'
    write("archive/index.html", "Archive · The Bulletin", body)

    # Topics: the briefs driving the research, plus per-topic history and update pages.
    body = "<h1>Topics</h1><p>These briefs are the configuration for the bulletin (<code>topics/*.md</code>).</p>"
    for t in topics:
        state = "" if t["enabled"] else " (disabled)"
        body += (f'<article class="update"><h2 class="topic-title"><a href="{t["id"]}/index.html">'
                 f'{html.escape(t["title"])}</a>{state}</h2>'
                 f'<p class="meta">Every {t["cadence_days"]} day(s) &middot; {len(t["updates"])} update(s)</p>'
                 f'<div class="content">{render_md(t["brief"])}</div></article>')
    write("topics/index.html", "Topics · The Bulletin", body)

    for t in topics:
        items = "".join(
            f'<li><a href="{u["date"]}.html"><strong>{fmt_date(u["date"])}</strong></a>'
            f'<span class="hl">{html.escape(u["headline"])}</span></li>' for u in t["updates"])
        body = (f'<h1>{html.escape(t["title"])}</h1>'
                + (f'<ul class="toc">{items}</ul>' if items else "<p>No updates yet.</p>"))
        write(f"topics/{t['id']}/index.html", f"{t['title']} · The Bulletin", body)
        for u in t["updates"]:
            write(f"topics/{t['id']}/{u['date']}.html", f"{t['title']} · {u['date']}",
                  update_article(t, u, "../../", heading="h1", link_title=False))
    print(f"Built {sum(1 for _ in out.rglob('*.html'))} pages in {out}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("topics")
    t.add_argument("selection", nargs="*", help="due (default), all, or topic ids")
    t.add_argument("--today", help="override today's date (YYYY-MM-DD)")
    t.set_defaults(fn=cmd_topics)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    b = sub.add_parser("build")
    b.add_argument("--out", default=str(ROOT / "_site"))
    b.set_defaults(fn=cmd_build)
    args = p.parse_args()
    try:
        args.fn(args)
    except ValueError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
