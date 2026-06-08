"""News headlines via Google News RSS and feedparser."""

import feedparser
from datetime import datetime, timezone
import time


RSS_URL = (
    "https://news.google.com/rss/search"
    "?q=SpaceX+OR+Tesla+OR+%22Boring+Company%22&hl=en-US&gl=US&ceid=US:en"
)
MAX_HEADLINES = 8


def get_headlines():
    """Return a list of dicts with headline info."""
    try:
        feed = feedparser.parse(RSS_URL)
        entries = feed.entries[:MAX_HEADLINES]
        headlines = []
        for entry in entries:
            title = entry.get("title", "No title")
            # Google News titles often end with " - Source Name"
            source = ""
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0].strip()
                source = parts[1].strip()

            # Parse published time
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            time_ago = _time_ago(published)

            headlines.append(
                {
                    "title": title,
                    "source": source,
                    "time_ago": time_ago,
                    "link": entry.get("link", ""),
                }
            )
        return headlines
    except Exception:
        return []


def _time_ago(parsed_time):
    """Convert a time.struct_time to a 'X ago' string."""
    if not parsed_time:
        return "Unknown"
    try:
        pub_ts = time.mktime(parsed_time)
        now_ts = time.time()
        delta = int(now_ts - pub_ts)
        if delta < 60:
            return f"{delta}s ago"
        elif delta < 3600:
            return f"{delta // 60}m ago"
        elif delta < 86400:
            return f"{delta // 3600}h ago"
        else:
            return f"{delta // 86400}d ago"
    except Exception:
        return "Unknown"
