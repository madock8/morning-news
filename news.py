import feedparser, datetime, html, os, calendar
from zoneinfo import ZoneInfo

# ---- SETTINGS: edit categories and feeds here ----
CATEGORIES = {
    "Technologie": [
        "http://www.benchmark.pl/rss/aktualnosci-pliki.xml",
        "https://www.purepc.pl/rss_all.xml",
        "https://www.telepolis.pl/rss",
        "https://www.polsatnews.pl/rss/technologie.xml",
        #"https://www.theverge.com/rss/index.xml",
        #"https://feeds.arstechnica.com/arstechnica/index",
        #"https://techcrunch.com/feed/",
        #"https://hnrss.org/frontpage",
    ],
    "IT": [
        "https://www.bleepingcomputer.com/feed/",
        "https://krebsonsecurity.com/feed/",
        "https://www.theregister.com/headlines.atom",
        "https://www.reddit.com/r/sysadmin/.rss",
    ],
    "Świat": [        
        "https://www.polsatnews.pl/rss/swiat.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://feeds.bbci.co.uk/news/rss.xml",          
    ],
    "Finanse": [
        "http://www.money.pl/rss/main.xml",
        "https://www.bankier.pl/rss",        
    ],
}

HOURS = 24                 # how far back to look
MAX_PER_FEED = 30          # safety cap per source
LOCAL_TZ = ZoneInfo("Europe/Warsaw")
# --------------------------------------------------

feedparser.USER_AGENT = "MorningNewsBot/1.0 (+https://github.com)"

now_utc = datetime.datetime.now(datetime.timezone.utc)
cutoff = now_utc - datetime.timedelta(hours=HOURS)


def entry_time(e):
    t = e.get("published_parsed") or e.get("updated_parsed")
    if not t:
        return None
    return datetime.datetime.fromtimestamp(calendar.timegm(t), tz=datetime.timezone.utc)


def build_category(feeds):
    """Return (html, total_items) for one category."""
    seen = set()
    sections = []
    total = 0

    for url in feeds:
        feed = feedparser.parse(url)
        source = feed.feed.get("title", url)

        fresh = []
        for e in feed.entries:
            link = e.get("link")
            if not link or link in seen:
                continue
            published = entry_time(e)
            if published is None or published < cutoff:
                continue
            seen.add(link)
            fresh.append((published, e.get("title", "(no title)"), link))

        fresh.sort(reverse=True)
        fresh = fresh[:MAX_PER_FEED]
        total += len(fresh)

        if fresh:
            rows = "".join(
                f'<li><span class="time">{p.astimezone(LOCAL_TZ).strftime("%H:%M")}</span> '
                f'<a href="{html.escape(link)}" target="_blank" rel="noopener">{html.escape(title)}</a></li>'
                for p, title, link in fresh
            )
        else:
            rows = '<li class="empty">No new items in the last 24 hours.</li>'

        sections.append(f"<h2>{html.escape(source)} ({len(fresh)})</h2><ul>{rows}</ul>")

    return "".join(sections), total


buttons = []
panels = []
for i, (name, feeds) in enumerate(CATEGORIES.items()):
    body, total = build_category(feeds)
    tab_id = f"tab{i}"
    buttons.append(
        f'<button class="tab" data-tab="{tab_id}">{html.escape(name)} <span class="count">{total}</span></button>'
    )
    panels.append(f'<section class="panel" id="{tab_id}"><h1 class="print-title">{html.escape(name)}</h1>{body}</section>')

updated = now_utc.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Morning news</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
  h2 {{ margin-top: 2rem; border-bottom: 1px solid #ccc; font-size: 1.1rem; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ margin: .4rem 0; }}
  .time {{ color: #888; font-variant-numeric: tabular-nums; margin-right: .4rem; }}
  .empty {{ color: #888; }}
  .tabs {{ display: flex; flex-wrap: wrap; gap: .5rem; margin: 1rem 0; }}
  .tab {{ border: 1px solid #ccc; background: #f5f5f5; color: #222; padding: .5rem .9rem;
          border-radius: 999px; cursor: pointer; font-size: 1rem; }}
  .tab.active {{ background: #222; color: #fff; border-color: #222; }}
  .count {{ opacity: .7; font-size: .85em; }}
  .print-title {{ display: none; }}
  .js .panel {{ display: none; }}
  .js .panel.active {{ display: block; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #111; color: #eee; }}
    a {{ color: #8ab4f8; }}
    h2 {{ border-color: #444; }}
    .tab {{ background: #222; color: #eee; border-color: #444; }}
    .tab.active {{ background: #eee; color: #111; border-color: #eee; }}
  }}
</style>
</head>
<body>
<h1>Morning news</h1>
<p>News from the last {HOURS} hours. Updated: {updated} (Poland time)</p>
<nav class="tabs">{''.join(buttons)}</nav>
{''.join(panels)}
<script>
  document.documentElement.classList.add("js");
  var tabs = document.querySelectorAll(".tab");
  var panels = document.querySelectorAll(".panel");
  function show(id) {{
    tabs.forEach(function (t) {{ t.classList.toggle("active", t.dataset.tab === id); }});
    panels.forEach(function (p) {{ p.classList.toggle("active", p.id === id); }});
    history.replaceState(null, "", "#" + id);
  }}
  tabs.forEach(function (t) {{ t.addEventListener("click", function () {{ show(t.dataset.tab); }}); }});
  var start = location.hash.slice(1);
  show(document.getElementById(start) ? start : panels[0].id);
</script>
</body>
</html>"""

os.makedirs("public", exist_ok=True)
with open("public/index.html", "w", encoding="utf-8") as f:
    f.write(page)
