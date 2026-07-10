#!/usr/bin/env python3
"""
svg_roi.py — ROI report for purchased SVG designs (Built For Them Design).

Reads the CSV produced by svg_audit.sh (after you fill in cost, uses, and
avg_sale_price for purchased files) and prints:

  * per-file table: name | purchased? | cost | uses | revenue | ROI
  * total spent on purchased SVGs
  * total revenue attributed to purchased SVGs
  * break-even threshold per file (sales needed to cover its cost)
  * top 3 highest-ROI files
  * bottom 3 worst performers, and any zero-use "dead investments"

Usage:  python3 svg_roi.py svg_inventory.csv
"""

import csv
import sys


def to_float(value, default=0.0):
    value = (value or "").strip().replace("$", "").replace(",", "")
    try:
        return float(value)
    except ValueError:
        return default


def money(x):
    return f"${x:,.2f}"


def main(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        sys.exit(f"No rows found in {path} — run svg_audit.sh first.")

    purchased = []
    for row in rows:
        if (row.get("category") or "").strip().lower() != "purchased":
            continue
        cost = to_float(row.get("cost"))
        uses = int(to_float(row.get("uses")))
        price = to_float(row.get("avg_sale_price"))
        revenue = uses * price
        purchased.append({
            "name": row.get("filename", "?"),
            "cost": cost,
            "uses": uses,
            "price": price,
            "revenue": revenue,
            "roi": revenue - cost,
            # sales needed for the design to pay for itself
            "break_even": (cost / price) if price > 0 else None,
        })

    print(f"\nSVG ROI REPORT — {len(rows)} files scanned, "
          f"{len(purchased)} marked as purchased\n")

    if not purchased:
        print("No files are categorized as 'purchased' in the CSV.")
        print("Edit the 'category' column and rerun.")
        return

    missing = [f["name"] for f in purchased if f["cost"] == 0 and f["price"] == 0]
    if missing:
        print(f"NOTE: {len(missing)} purchased file(s) have no cost/price data "
              f"yet: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}\n")

    # ---- Per-file table -----------------------------------------------------
    header = (f"{'SVG NAME':<40} {'COST':>10} {'USES':>6} "
              f"{'REVENUE':>12} {'ROI':>12} {'BREAK-EVEN':>11}")
    print(header)
    print("-" * len(header))
    for f in sorted(purchased, key=lambda f: f["roi"], reverse=True):
        be = f"{f['break_even']:.1f} sales" if f["break_even"] is not None else "n/a"
        flag = "  << DEAD (0 uses)" if f["uses"] == 0 else ""
        print(f"{f['name']:<40.40} {money(f['cost']):>10} {f['uses']:>6} "
              f"{money(f['revenue']):>12} {money(f['roi']):>12} {be:>11}{flag}")

    # ---- Totals ---------------------------------------------------------------
    total_cost = sum(f["cost"] for f in purchased)
    total_revenue = sum(f["revenue"] for f in purchased)
    print("-" * len(header))
    print(f"{'TOTAL':<40} {money(total_cost):>10} "
          f"{sum(f['uses'] for f in purchased):>6} {money(total_revenue):>12} "
          f"{money(total_revenue - total_cost):>12}")

    # ---- Highlights -----------------------------------------------------------
    ranked = sorted(purchased, key=lambda f: f["roi"], reverse=True)
    dead = [f for f in purchased if f["uses"] == 0]

    print("\nTOP 3 BY ROI:")
    for f in ranked[:3]:
        print(f"  {f['name']}: {money(f['roi'])} "
              f"({f['uses']} uses at {money(f['price'])})")

    bottom = ranked[3:][-3:]
    if bottom:
        print("\nBOTTOM 3:")
        for f in bottom[::-1]:
            print(f"  {f['name']}: {money(f['roi'])} ({f['uses']} uses)")

    if dead:
        print(f"\nDEAD INVESTMENTS ({len(dead)} file(s), "
              f"{money(sum(f['cost'] for f in dead))} spent, never used):")
        for f in dead:
            print(f"  {f['name']}: {money(f['cost'])}")
    else:
        print("\nNo dead investments — every purchased design has been used.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
