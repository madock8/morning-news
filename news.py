import feedparser, datetime, html, os

FEEDS = [
    "https://hnrss.org/frontpage",
    "https://www.reddit.com/r/technology/.rss",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "http://www.benchmark.pl/rss/aktualnosci-pliki.xml",
    "http://www.benchmark.pl/rss/testy-recenzje-minirecenzje.xml",
]

sections = []
seen = set()

for url in FEEDS:
    feed = feedparser.parse(url)
    source = feed.feed.get("title", url)
    rows = []
    for e in feed.entries[:10]:
        if e.link in seen:
            continue
        seen.add(e.link)
        rows.append(f'<li><a href="{html.escape(e.link)}">{html.escape(e.title)}</a></li>')
    sections.append(f"<h2>{html.escape(source)}</h2><ul>{''.join(rows)}</ul>")

now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Morning news</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
  h2 {{ margin-top: 2rem; border-bottom: 1px solid #ccc; }}
  li {{ margin: .4rem 0; }}
</style>
</head>
<body>
<h1>Morning news</h1>
<p>Updated: {now}</p>
{''.join(sections)}
</body>
</html>"""

os.makedirs("public", exist_ok=True)
with open("public/index.html", "w", encoding="utf-8") as f:
    f.write(page)
