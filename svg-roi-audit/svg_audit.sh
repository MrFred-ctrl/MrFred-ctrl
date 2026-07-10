#!/usr/bin/env bash
#
# svg_audit.sh — SVG inventory + categorization for Built For Them Design
#
# Scans your machine for .svg files, prints a review table, and writes
# svg_inventory.csv — which you then fill in with cost / uses / sale price
# and feed to svg_roi.py for the ROI report.
#
# Usage:
#   ./svg_audit.sh                 # scans your home folder
#   ./svg_audit.sh /path/one /path/two   # scans specific folders instead
#
# Works on macOS, Linux, and Windows (via Git Bash or WSL).

set -uo pipefail

OUT_CSV="svg_inventory.csv"

# --- Where to scan -----------------------------------------------------------
if [ "$#" -gt 0 ]; then
    ROOTS=("$@")
else
    ROOTS=("$HOME")
fi

# Folders that are never user content — skipped for speed and noise reduction.
PRUNE_DIRS=(node_modules .git .cache Library AppData venv .venv __pycache__)

# --- Categorization patterns (edit these to match YOUR folder/file naming) ---
# Case-insensitive substring matches against the full file path.
PURCHASED_PATTERNS=(purchase purchases bought licensed license invoice etsy
                    creativefabrica "creative fabrica" designbundles "design bundles"
                    sofontsy vendor downloads)
SELFMADE_PATTERNS=(designs originals "my-work" "my work" mywork bft "built for them"
                   inkscape drafts)

categorize() {
    local lower_path
    lower_path=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
    local p
    for p in "${PURCHASED_PATTERNS[@]}"; do
        [[ "$lower_path" == *"$p"* ]] && { echo "purchased"; return; }
    done
    for p in "${SELFMADE_PATTERNS[@]}"; do
        [[ "$lower_path" == *"$p"* ]] && { echo "self-made"; return; }
    done
    echo "unknown"
}

# --- Build the find prune expression -----------------------------------------
PRUNE_EXPR=()
for d in "${PRUNE_DIRS[@]}"; do
    PRUNE_EXPR+=(-name "$d" -prune -o)
done

# Portable file-size + mtime (GNU vs BSD stat)
if stat -c '%s' "$0" >/dev/null 2>&1; then
    file_size()  { stat -c '%s' "$1"; }
    file_mtime() { stat -c '%y' "$1" | cut -d. -f1; }
else
    file_size()  { stat -f '%z' "$1"; }
    file_mtime() { stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' "$1"; }
fi

human_size() {
    awk -v b="$1" 'BEGIN{ s="B KB MB GB"; split(s,u);
        i=1; while (b>=1024 && i<4) { b/=1024; i++ }
        printf (i==1 ? "%d %s" : "%.1f %s"), b, u[i] }'
}

csv_escape() { printf '"%s"' "${1//\"/\"\"}"; }

# --- Scan ---------------------------------------------------------------------
echo "Scanning: ${ROOTS[*]}"
echo

printf '%s\n' "filename,path,size_bytes,modified,category,cost,uses,avg_sale_price" > "$OUT_CSV"

count=0; n_purchased=0; n_selfmade=0; n_unknown=0

# Table header
printf '%-40s | %-9s | %-19s | %-9s | %s\n' "FILENAME" "SIZE" "MODIFIED" "CATEGORY" "PATH"
printf '%s\n' "$(printf '=%.0s' {1..140})"

while IFS= read -r -d '' f; do
    name=$(basename "$f")
    size=$(file_size "$f")
    mtime=$(file_mtime "$f")
    cat=$(categorize "$f")
    case "$cat" in
        purchased) n_purchased=$((n_purchased+1)) ;;
        self-made) n_selfmade=$((n_selfmade+1)) ;;
        *)         n_unknown=$((n_unknown+1)) ;;
    esac
    printf '%-40.40s | %-9s | %-19s | %-9s | %s\n' \
        "$name" "$(human_size "$size")" "$mtime" "$cat" "$f"
    printf '%s,%s,%s,%s,%s,,,\n' \
        "$(csv_escape "$name")" "$(csv_escape "$f")" "$size" \
        "$(csv_escape "$mtime")" "$cat" >> "$OUT_CSV"
    count=$((count+1))
done < <(find "${ROOTS[@]}" "${PRUNE_EXPR[@]}" -type f -iname '*.svg' -print0 2>/dev/null)

echo
echo "Found $count SVG file(s):  purchased=$n_purchased  self-made=$n_selfmade  unknown=$n_unknown"
echo
echo "Inventory written to: $OUT_CSV"
echo
echo "NEXT STEPS:"
echo "  1. Open $OUT_CSV in Excel/Sheets."
echo "  2. Fix any wrong 'category' values (purchased / self-made / unknown)."
echo "  3. For purchased files, fill in: cost, uses, avg_sale_price."
echo "     (For a batch buy, divide the bundle price by the number of files.)"
echo "  4. Run:  python3 svg_roi.py $OUT_CSV"
