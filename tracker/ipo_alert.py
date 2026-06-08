"""IPO / SEC S-1 alert module for SpaceX and Starlink.

Checks two data sources:
1. SEC EDGAR full-text search API for S-1 / S-1/A filings.
2. Google News RSS feed (reused from news.py) filtered for IPO keywords.
"""

import feedparser
import requests
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEC_HEADERS = {"User-Agent": "SpaceX Tracker research@example.com"}
SEC_TIMEOUT = 10

SEC_QUERIES = [
    (
        "SpaceX",
        "https://efts.sec.gov/LATEST/search-index?q=%22SpaceX%22&forms=S-1,S-1%2FA",
    ),
    (
        "Starlink",
        "https://efts.sec.gov/LATEST/search-index?q=%22Starlink%22&forms=S-1,S-1%2FA",
    ),
]

NEWS_RSS_URL = (
    "https://news.google.com/rss/search"
    "?q=SpaceX+OR+Tesla+OR+%22Boring+Company%22&hl=en-US&gl=US&ceid=US:en"
)

IPO_KEYWORDS = ["ipo", "s-1", "goes public", "public offering", "initial public offering"]
SUBJECT_KEYWORDS = ["spacex", "starlink"]

MAX_NEWS = 20  # scan more than the normal 8 to catch IPO headlines


# ---------------------------------------------------------------------------
# SEC EDGAR helpers
# ---------------------------------------------------------------------------

def _parse_filing(hit: dict, label: str) -> dict:
    """Extract display fields from a single EDGAR hits.hits entry."""
    src = hit.get("_source", {})
    filing_id = hit.get("_id", "")
    form_type = src.get("form_type", "S-1")
    file_date = src.get("file_date", src.get("period_of_report", "Unknown"))
    display_names = src.get("display_names", [])
    if isinstance(display_names, list):
        filer = ", ".join(display_names) if display_names else "Unknown filer"
    else:
        filer = str(display_names)

    # Build a URL that lands on the EDGAR filing viewer
    if filing_id:
        # filing_id for EDGAR full-text is usually like "0001234567-24-001234"
        accession = filing_id.replace("-", "")
        url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcompany&filenum={filing_id}"
        )
    else:
        url = "https://efts.sec.gov/LATEST/search-index"

    return {
        "title": f"[{form_type}] {filer} — search term: {label}",
        "date": file_date,
        "url": url,
        "form_type": form_type,
        "filer": filer,
        "label": label,
    }


def get_sec_filings() -> list[dict]:
    """Query SEC EDGAR for S-1 / S-1/A filings mentioning SpaceX or Starlink.

    Returns a deduplicated list of filing dicts.
    """
    seen_ids: set[str] = set()
    results: list[dict] = []

    for label, url in SEC_QUERIES:
        try:
            resp = requests.get(url, headers=SEC_HEADERS, timeout=SEC_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            for hit in hits:
                filing_id = hit.get("_id", "")
                if filing_id in seen_ids:
                    continue
                seen_ids.add(filing_id)
                results.append(_parse_filing(hit, label))
        except Exception:
            # Network errors, rate-limits, etc. — silently continue
            pass

    return results


# ---------------------------------------------------------------------------
# News RSS IPO keyword filter
# ---------------------------------------------------------------------------

def get_ipo_news_headlines() -> list[dict]:
    """Return news headlines that match both a subject keyword and an IPO keyword."""
    try:
        feed = feedparser.parse(NEWS_RSS_URL)
        entries = feed.entries[:MAX_NEWS]
    except Exception:
        return []

    matches: list[dict] = []
    for entry in entries:
        raw_title = entry.get("title", "")
        title_lower = raw_title.lower()

        # Must mention SpaceX or Starlink
        if not any(kw in title_lower for kw in SUBJECT_KEYWORDS):
            continue

        # Must mention an IPO-related term
        if not any(kw in title_lower for kw in IPO_KEYWORDS):
            continue

        # Strip " - Source" suffix that Google News appends
        title = raw_title
        source = ""
        if " - " in raw_title:
            parts = raw_title.rsplit(" - ", 1)
            title = parts[0].strip()
            source = parts[1].strip()

        matches.append(
            {
                "title": title,
                "source": source,
                "link": entry.get("link", ""),
            }
        )

    return matches


# ---------------------------------------------------------------------------
# Combined public entry point
# ---------------------------------------------------------------------------

def get_ipo_alerts() -> dict:
    """Fetch all IPO alert data and return a summary dict.

    Returns:
        {
            "filings": [...],   # SEC S-1 filing dicts
            "headlines": [...], # IPO-related news headline dicts
            "checked_at": str,  # ISO timestamp
        }
    """
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    filings = get_sec_filings()
    headlines = get_ipo_news_headlines()
    return {
        "filings": filings,
        "headlines": headlines,
        "checked_at": checked_at,
    }
