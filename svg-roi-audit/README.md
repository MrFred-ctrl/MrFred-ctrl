# SVG ROI Audit Toolkit — Built For Them Design

Two small tools to inventory every SVG on your machine and calculate
return-on-investment for purchased designs.

## Requirements

- **Windows:** [Git Bash](https://git-scm.com/downloads) (or WSL) and Python 3
- **macOS / Linux:** nothing extra — bash and python3 are built in

## Step 1 — Scan for SVGs

```bash
./svg_audit.sh                          # scans your whole home folder
./svg_audit.sh ~/Downloads ~/Documents  # or just specific folders
```

This prints a review table (filename, size, date modified, category, path)
and writes **`svg_inventory.csv`**.

Files are auto-categorized by path/name:

| Category  | Matched when the path contains…                                          |
|-----------|--------------------------------------------------------------------------|
| purchased | `purchases`, `bought`, `licensed`, `invoice`, `etsy`, `creativefabrica`, `designbundles`, `sofontsy`, `downloads`, … |
| self-made | `designs`, `originals`, `my-work`, `bft`, `built for them`, `drafts`, …   |
| unknown   | anything else                                                             |

The pattern lists live at the top of `svg_audit.sh` — edit them to match your
own folder names and vendors.

## Step 2 — Fill in your numbers

Open `svg_inventory.csv` in Excel or Google Sheets:

1. Correct any `category` values the auto-detection got wrong.
2. For each **purchased** file, fill in:
   - `cost` — what you paid for that file (for a bundle: bundle price ÷ number of files)
   - `uses` — how many products you've made/sold with it
   - `avg_sale_price` — average sale price of those products

## Step 3 — Run the ROI report

```bash
python3 svg_roi.py svg_inventory.csv
```

You get:

- Per-file table: name | cost | uses | revenue | **ROI** | break-even
  (ROI = uses × avg sale price − cost; break-even = sales needed to cover cost)
- Total spent vs. total revenue across all purchased designs
- Top 3 highest-ROI files
- Bottom 3 worst performers
- **Dead investments** — purchased files with zero uses
