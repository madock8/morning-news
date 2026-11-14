import feedparser, datetime, html, os, calendar
from zoneinfo import ZoneInfo

FEEDS = [
    "https://hnrss.org/frontpage",
    "https://www.reddit.com/r/technology/.rss",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "http://www.benchmark.pl/rss/aktualnosci-pliki.xml",
    "https://www.purepc.pl/rss_all.xml",
]

HOURS = 24                 # how far back to look
MAX_PER_FEED = 30          # safety cap per source
LOCAL_TZ = ZoneInfo("Europe/Warsaw")

now_utc = datetime.datetime.now(datetime.timezone.utc)
cutoff = now_utc - datetime.timedelta(hours=HOURS)

def entry_time(e):
    """Return the entry's publish time as an aware UTC datetime, or None."""
    t = e.get("published_parsed") or e.get("updated_parsed")
    if not t:
        return None
    return datetime.datetime.fromtimestamp(calendar.timegm(t), tz=datetime.timezone.utc)

sections = []
seen = set()

for url in FEEDS:
    feed = feedparser.parse(url)
    source = feed.feed.get("title", url)

    fresh = []
    for e in feed.entries:
        link = e.get("link")
        if not link or link in seen:
            continue
        published = entry_time(e)
        if published is None or published < cutoff:
            continue  # skip undated or older than 24h
        seen.add(link)
        fresh.append((published, e.get("title", "(no title)"), link))

    fresh.sort(reverse=True)  # newest first
    fresh = fresh[:MAX_PER_FEED]

    if fresh:
        rows = "".join(
            f'<li><span class="time">{p.astimezone(LOCAL_TZ).strftime("%H:%M")}</span> '
            f'<a href="{html.escape(link)}">{html.escape(title)}</a></li>'
            for p, title, link in fresh
        )
    else:
        rows = '<li class="empty">No new items in the last 24 hours.</li>'

    sections.append(f"<h2>{html.escape(source)} ({len(fresh)})</h2><ul>{rows}</ul>")

updated = now_utc.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Morning news</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
  h2 {{ margin-top: 2rem; border-bottom: 1px solid #ccc; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ margin: .4rem 0; }}
  .time {{ color: #888; font-variant-numeric: tabular-nums; margin-right: .4rem; }}
  .empty {{ color: #888; }}
</style>
</head>
<body>
<h1>Morning news</h1>
<p>News from the last {HOURS} hours. Updated: {updated} (Poland time)</p>
{''.join(sections)}
</body>
</html>"""

os.makedirs("public", exist_ok=True)
with open("public/index.html", "w", encoding="utf-8") as f:
    f.write(page)
