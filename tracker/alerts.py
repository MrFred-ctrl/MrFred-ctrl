"""Email alert module for new SEC filings and IPO headlines.

Sends Gmail SMTP alerts when new filings or headlines are detected.
Credentials are read from environment variables:
  ALERT_EMAIL    — sender Gmail address
  ALERT_PASSWORD — Gmail app password (myaccount.google.com/apppasswords)
  ALERT_TO       — recipient address (defaults to ALERT_EMAIL)
"""

import json
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from pathlib import Path

SEEN_HEADLINES_FILE = Path("seen_headlines.json")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


# ---------------------------------------------------------------------------
# Persistence helpers for headlines
# ---------------------------------------------------------------------------

def _load_seen_headlines() -> set:
    """Return a set of seen headline strings from disk (empty set if missing)."""
    if not SEEN_HEADLINES_FILE.exists():
        return set()
    try:
        with SEEN_HEADLINES_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return set(data)
    except Exception:
        pass
    return set()


def _save_seen_headlines(seen: set) -> None:
    """Persist the set of seen headline strings to disk."""
    try:
        with SEEN_HEADLINES_FILE.open("w", encoding="utf-8") as fh:
            json.dump(sorted(seen), fh, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Email sender
# ---------------------------------------------------------------------------

def send_email_alert(subject: str, body: str, to_email: str) -> None:
    """Send an email via Gmail SMTP (port 465, SSL).

    Silently skips if ALERT_EMAIL or ALERT_PASSWORD env vars are not set.
    """
    sender = os.environ.get("ALERT_EMAIL", "")
    password = os.environ.get("ALERT_PASSWORD", "")

    if not sender or not password:
        return  # credentials not configured — skip silently

    recipient = to_email or os.environ.get("ALERT_TO", "") or sender

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
    except Exception:
        pass  # network errors, auth failures — silently skip


# ---------------------------------------------------------------------------
# High-level alert checker
# ---------------------------------------------------------------------------

def check_and_alert(alerts: dict) -> None:
    """Examine alert data and fire email alerts for new filings or headlines.

    Args:
        alerts: dict returned by ``get_ipo_alerts()`` — must contain keys
                ``"filings"`` and ``"headlines"``.
    """
    to_email = os.environ.get("ALERT_TO", "") or os.environ.get("ALERT_EMAIL", "")

    # ---- New SEC filings ----------------------------------------------------
    new_filings = [f for f in alerts.get("filings", []) if f.get("is_new")]
    if new_filings:
        lines = []
        for f in new_filings:
            lines.append(
                f"  Form: {f.get('form_type', 'S-1')}\n"
                f"  Filer: {f.get('filer', 'Unknown')}\n"
                f"  Date: {f.get('date', 'Unknown')}\n"
                f"  URL: {f.get('url', '')}\n"
            )
        body = "New SEC S-1 filing(s) detected:\n\n" + "\n".join(lines)
        send_email_alert(
            subject="SpaceX/Starlink S-1 Filing Detected!",
            body=body,
            to_email=to_email,
        )

    # ---- New IPO headlines --------------------------------------------------
    seen_headlines = _load_seen_headlines()
    all_headlines = alerts.get("headlines", [])

    new_headlines = []
    for h in all_headlines:
        key = h.get("title", "")
        if key and key not in seen_headlines:
            new_headlines.append(h)
            seen_headlines.add(key)

    _save_seen_headlines(seen_headlines)

    if new_headlines:
        lines = []
        for h in new_headlines:
            source = h.get("source", "")
            lines.append(
                f"  {h.get('title', '')}"
                + (f" ({source})" if source else "")
            )
        body = "New IPO-related headlines:\n\n" + "\n".join(lines)
        send_email_alert(
            subject="SpaceX IPO News Alert",
            body=body,
            to_email=to_email,
        )
