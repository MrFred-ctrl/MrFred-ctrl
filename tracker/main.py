"""
SpaceX / Tesla / Boring Company Terminal Dashboard
Run: python main.py
     python main.py --refresh 30
"""

import argparse
import time
from datetime import datetime, timezone

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from spacex import get_upcoming_launch, get_latest_launch, get_launch_info
from tesla import get_stock_data
from news import get_headlines
from ipo_alert import get_ipo_alerts


console = Console()


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_spacex_panel():
    """Build the SpaceX info panel."""
    upcoming_raw = get_upcoming_launch()
    latest_raw = get_latest_launch()

    upcoming = get_launch_info(upcoming_raw)
    latest = get_launch_info(latest_raw)

    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Field", style="bold cyan", width=22)
    table.add_column("Value", style="white")

    # Next launch
    table.add_row("[bold yellow]-- NEXT LAUNCH --[/bold yellow]", "")
    if upcoming:
        table.add_row("Mission", upcoming.get("name", "Unknown"))
        table.add_row("Date", upcoming.get("date_utc", "Unknown"))
        table.add_row("Countdown", f"[bold green]{upcoming.get('countdown', 'Unknown')}[/bold green]")
        details = upcoming.get("details", "No details available.")
        if details and len(details) > 120:
            details = details[:117] + "..."
        table.add_row("Details", details or "No details available.")
    else:
        table.add_row("Status", "[red]Unavailable[/red]")

    table.add_row("", "")

    # Latest launch
    table.add_row("[bold yellow]-- LATEST LAUNCH --[/bold yellow]", "")
    if latest:
        success = latest.get("success")
        if success is True:
            success_str = "[bold green]SUCCESS[/bold green]"
        elif success is False:
            success_str = "[bold red]FAILURE[/bold red]"
        else:
            success_str = "[dim]Unknown[/dim]"

        table.add_row("Mission", latest.get("name", "Unknown"))
        table.add_row("Date", latest.get("date_utc", "Unknown"))
        table.add_row("Outcome", success_str)
        details = latest.get("details", "No details available.")
        if details and len(details) > 120:
            details = details[:117] + "..."
        table.add_row("Details", details or "No details available.")
    else:
        table.add_row("Status", "[red]Unavailable[/red]")

    return Panel(
        table,
        title="[bold white on blue] SPACEX [/bold white on blue]",
        border_style="blue",
        expand=True,
    )


def build_tesla_panel():
    """Build the Tesla stock panel."""
    data = get_stock_data()

    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Field", style="bold cyan", width=18)
    table.add_column("Value", style="white")

    if not data.get("available"):
        table.add_row("Status", "[red]Unavailable — market may be closed or network error[/red]")
    else:
        price = data["price"]
        change = data["change"]
        pct = data["pct_change"]

        # Color based on direction
        color = "green" if change >= 0 else "red"
        arrow = "▲" if change >= 0 else "▼"
        sign = "+" if change >= 0 else ""

        table.add_row("Ticker", "[bold white]TSLA[/bold white]")
        table.add_row(
            "Price",
            f"[bold {color}]${price:,.2f}[/bold {color}]",
        )
        table.add_row(
            "Change",
            f"[{color}]{arrow} {sign}{change:,.2f}  ({sign}{pct:.2f}%)[/{color}]",
        )
        if data["day_high"]:
            table.add_row("Day High", f"${data['day_high']:,.2f}")
        if data["day_low"]:
            table.add_row("Day Low", f"${data['day_low']:,.2f}")
        if data["volume"]:
            table.add_row("Volume", f"{data['volume']:,}")

    return Panel(
        table,
        title="[bold white on red] TESLA (TSLA) [/bold white on red]",
        border_style="red",
        expand=True,
    )


def build_news_panel():
    """Build the news headlines panel."""
    headlines = get_headlines()

    table = Table(
        box=box.SIMPLE_HEAVY,
        expand=True,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Headline", style="white", max_width=80, no_wrap=True)
    table.add_column("Source", style="dim cyan", width=22, no_wrap=True)
    table.add_column("When", style="dim", width=10, no_wrap=True)

    if not headlines:
        table.add_row("[red]No headlines available[/red]", "", "")
    else:
        for h in headlines:
            title = h["title"]
            if len(title) > 80:
                title = title[:77] + "..."
            table.add_row(title, h["source"], h["time_ago"])

    return Panel(
        table,
        title="[bold white on dark_green] NEWS — SpaceX / Tesla / Boring Company [/bold white on dark_green]",
        border_style="green",
        expand=True,
    )


def build_ipo_panel():
    """Build the IPO / SEC S-1 alert panel."""
    alerts = get_ipo_alerts()
    filings = alerts["filings"]
    headlines = alerts["headlines"]
    checked_at = alerts["checked_at"]

    from rich.console import Group as RichGroup

    renderables = []

    # ---- SEC filings block ------------------------------------------------
    if filings:
        filing_table = Table(
            box=box.SIMPLE_HEAVY,
            expand=True,
            show_header=True,
            header_style="bold bright_red",
        )
        filing_table.add_column("Form", style="bold bright_yellow", width=8, no_wrap=True)
        filing_table.add_column("Filer", style="bold white", max_width=40, no_wrap=True)
        filing_table.add_column("Date", style="bright_yellow", width=12, no_wrap=True)
        filing_table.add_column("Search Term", style="dim", width=12, no_wrap=True)

        for f in filings:
            filing_table.add_row(
                f.get("form_type", "S-1"),
                f.get("filer", "Unknown"),
                f.get("date", "Unknown"),
                f.get("label", ""),
            )
        renderables.append(
            Panel(
                filing_table,
                title="[bold bright_red] *** SEC S-1 FILINGS DETECTED *** [/bold bright_red]",
                border_style="bright_red",
                expand=True,
            )
        )

    # ---- IPO news headlines block -----------------------------------------
    if headlines:
        news_table = Table(
            box=box.SIMPLE,
            expand=True,
            show_header=True,
            header_style="bold yellow",
        )
        news_table.add_column("Headline", style="yellow", max_width=80, no_wrap=True)
        news_table.add_column("Source", style="dim cyan", width=22, no_wrap=True)

        for h in headlines:
            title = h["title"]
            if len(title) > 80:
                title = title[:77] + "..."
            news_table.add_row(title, h.get("source", ""))
        renderables.append(
            Panel(
                news_table,
                title="[bold yellow] IPO-Related News [/bold yellow]",
                border_style="yellow",
                expand=True,
            )
        )

    # ---- All-clear status -------------------------------------------------
    if not filings and not headlines:
        clear_text = Text(
            f"No IPO filings or news detected.  Last checked: {checked_at}",
            style="bold green",
            justify="center",
        )
        return Panel(
            clear_text,
            title="[bold white on dark_green] IPO ALERT — SpaceX / Starlink [/bold white on dark_green]",
            border_style="green",
            expand=True,
        )

    # Determine outer border color based on severity
    outer_border = "bright_red" if filings else "yellow"
    return Panel(
        RichGroup(*renderables),
        title="[bold white on dark_red] IPO ALERT — SpaceX / Starlink [/bold white on dark_red]"
        if filings
        else "[bold white on dark_orange] IPO ALERT — SpaceX / Starlink [/bold white on dark_orange]",
        border_style=outer_border,
        expand=True,
    )


def build_footer():
    """Build a footer with the last updated timestamp."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return Panel(
        Text(f"Last updated: {now}", style="dim", justify="center"),
        border_style="dim",
        expand=True,
    )


def build_title():
    """Build a title bar."""
    title_text = Text(
        "SpaceX / Tesla / Boring Company Tracker",
        style="bold white",
        justify="center",
    )
    return Panel(title_text, style="bold blue", expand=True)


# ---------------------------------------------------------------------------
# Dashboard renderer
# ---------------------------------------------------------------------------

def render_dashboard():
    """Assemble and return a renderable dashboard."""
    layout = Layout()
    layout.split_column(
        Layout(name="title", size=3),
        Layout(name="top_row", size=20),
        Layout(name="news", size=14),
        Layout(name="ipo", size=7),
        Layout(name="footer", size=3),
    )
    layout["top_row"].split_row(
        Layout(name="spacex"),
        Layout(name="tesla"),
    )

    layout["title"].update(build_title())
    layout["spacex"].update(build_spacex_panel())
    layout["tesla"].update(build_tesla_panel())
    layout["news"].update(build_news_panel())
    layout["ipo"].update(build_ipo_panel())
    layout["footer"].update(build_footer())

    return layout


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="SpaceX / Tesla / Boring Company terminal dashboard"
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=0,
        metavar="N",
        help="Refresh interval in seconds (0 = run once and exit)",
    )
    args = parser.parse_args()

    if args.refresh > 0:
        with Live(render_dashboard(), console=console, screen=True, refresh_per_second=1) as live:
            while True:
                time.sleep(args.refresh)
                live.update(render_dashboard())
    else:
        console.print(render_dashboard())


if __name__ == "__main__":
    main()
