import feedparser, datetime, html, os, calendar
from zoneinfo import ZoneInfo

# ---- SETTINGS: edit categories and feeds here ----
CATEGORIES = {
    "Technologie": [
        "http://www.benchmark.pl/rss/aktualnosci-pliki.xml",
        "https://www.purepc.pl/rss_all.xml",
        "https://www.telepolis.pl/rss",
        "https://www.gry-online.pl/rss/tech.xml",
        "https://www.polsatnews.pl/rss/technologie.xml",
        #"https://www.theverge.com/rss/index.xml",
        #"https://feeds.arstechnica.com/arstechnica/index",
        #"https://techcrunch.com/feed/",
        #"https://hnrss.org/frontpage",
    ],
    "Gry": [
        "https://www.gram.pl/rss/content.xml",
        "https://www.gry-online.pl/rss/gry.xml",
        "https://www.eurogamer.pl/feed",
        "https://www.ppe.pl/rss.html",
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
<title>mNews</title>
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="site.webmanifest">
<meta name="theme-color" content="#0f172a">
<script>
  (function () {{
    var t = null;
    try {{ t = localStorage.getItem("theme"); }} catch (e) {{}}
    if (t !== "dark" && t !== "light") {{
      t = "dark";
      // t = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }}
    document.documentElement.setAttribute("data-theme", t);
  }})();
</script>
<style>
  :root {{
    --bg: #ffffff; --text: #222222; --link: #1a56c4; --muted: #888888;
    --line: #cccccc; --chip-bg: #f5f5f5; --chip-border: #cccccc;
    --active-bg: #222222; --active-text: #ffffff;
    color-scheme: light;
  }}
  :root[data-theme="dark"] {{
    --bg: #111418; --text: #e6e6e6; --link: #8ab4f8; --muted: #8b929a;
    --line: #333a42; --chip-bg: #1d2229; --chip-border: #333a42;
    --active-bg: #e6e6e6; --active-text: #111418;
    color-scheme: dark;
  }}
  body {{ font-family: system-ui, sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem;
          line-height: 1.5; background: var(--bg); color: var(--text); }}
  a {{ color: var(--link); }}
  h2 {{ margin-top: 2rem; border-bottom: 1px solid var(--line); font-size: 1.1rem; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ margin: .4rem 0; }}
  .time {{ color: var(--muted); font-variant-numeric: tabular-nums; margin-right: .4rem; }}
  .empty {{ color: var(--muted); }}
  .header {{ display: flex; justify-content: space-between; align-items: center; }}
  .header h1 {{ margin: 0; }}
  .theme-btn {{ border: 1px solid var(--chip-border); background: var(--chip-bg); color: var(--text);
                width: 2.4rem; height: 2.4rem; border-radius: 50%; cursor: pointer; font-size: 1.1rem; }}
  .tabs {{ display: flex; flex-wrap: wrap; gap: .5rem; margin: 1rem 0; }}
  .tab {{ border: 1px solid var(--chip-border); background: var(--chip-bg); color: var(--text);
          padding: .5rem .9rem; border-radius: 999px; cursor: pointer; font-size: 1rem; }}
  .tab.active {{ background: var(--active-bg); color: var(--active-text); border-color: var(--active-bg); }}
  .count {{ opacity: .7; font-size: .85em; }}
  .print-title {{ display: none; }}
  .js .panel {{ display: none; }}
  .js .panel.active {{ display: block; }}
</style>
</head>
<body>
<div class="header">
  <h1>mNews</h1>
  <button id="theme-toggle" class="theme-btn" type="button" aria-label="Switch light or dark theme"></button>
</div>
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

  var toggle = document.getElementById("theme-toggle");
  function current() {{ return document.documentElement.getAttribute("data-theme"); }}
  function icon() {{ toggle.textContent = current() === "dark" ? "☀️" : "🌙"; }}
  toggle.addEventListener("click", function () {{
    var next = current() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try {{ localStorage.setItem("theme", next); }} catch (e) {{}}
    icon();
  }});
  icon();
</script>
</body>
</html>"""

os.makedirs("public", exist_ok=True)
with open("public/index.html", "w", encoding="utf-8") as f:
    f.write(page)
