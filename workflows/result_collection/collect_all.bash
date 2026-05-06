#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<'EOF'
Usage:
  collect_all.bash [base_dir] [summary_dir]

Arguments:
  base_dir     Directory containing structure subdirectories. Default: current directory.
  summary_dir  Output directory for collected results. Default: SummaryResults under base_dir.

Examples:
  bash collect_all.bash
  bash collect_all.bash /path/to/calculations
  bash collect_all.bash /path/to/calculations /path/to/output/SummaryResults
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

BASE_DIR_INPUT="${1:-$(pwd)}"
SUMMARY_DIR_INPUT="${2:-SummaryResults}"

BASE_DIR="$(cd "$BASE_DIR_INPUT" && pwd)"
if [[ "$SUMMARY_DIR_INPUT" = /* ]]; then
    SUMMARY_DIR="$SUMMARY_DIR_INPUT"
else
    SUMMARY_DIR="$BASE_DIR/$SUMMARY_DIR_INPUT"
fi

mkdir -p "$SUMMARY_DIR"
LOG_FILE="$SUMMARY_DIR/collect.log"
exec > >(tee -a "$LOG_FILE") 2>&1

WORKFUNC_DIR="$SUMMARY_DIR/workfunction"
DBAND_DIR="$SUMMARY_DIR/dbandcenter"
CHGDIFF_DIR="$SUMMARY_DIR/chargediff"
DOS_DIR="$SUMMARY_DIR/tdospdos"

mkdir -p "$WORKFUNC_DIR" "$DBAND_DIR" "$CHGDIFF_DIR" "$DOS_DIR"

echo "========================================="
echo "Collection started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Base directory: $BASE_DIR"
echo "Summary directory: $SUMMARY_DIR"
echo "========================================="

shopt -s nullglob
for struct_path in "$BASE_DIR"/*/; do
    struct_name="$(basename "$struct_path")"

    if [[ "$struct_name" == "$(basename "$SUMMARY_DIR")" || "$struct_name" == .* ]]; then
        continue
    fi

    if [[ ! -d "$struct_path/RF" ]]; then
        echo "[skip] $struct_name: RF directory not found"
        continue
    fi

    echo "-----------------------------------------"
    echo "Processing structure: $struct_name"
    echo "-----------------------------------------"

    if ! "$SCRIPT_DIR/collect_workfunction.bash" "$struct_name" "$WORKFUNC_DIR" "$BASE_DIR"; then
        echo "[warn] workfunction collection failed: $struct_name"
    fi

    if ! "$SCRIPT_DIR/collect_bandcenter.bash" "$struct_name" "$DBAND_DIR" "$BASE_DIR"; then
        echo "[warn] band-center collection failed: $struct_name"
    fi

    if ! "$SCRIPT_DIR/collect_chargediff.bash" "$struct_name" "$CHGDIFF_DIR" "$BASE_DIR"; then
        echo "[warn] charge-difference collection failed: $struct_name"
    fi

    if ! "$SCRIPT_DIR/collect_tdospdos.bash" "$struct_name" "$DOS_DIR" "$BASE_DIR"; then
        echo "[warn] TDOS/PDOS collection failed: $struct_name"
    fi
done

echo "========================================="
echo "Collection finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Log file: $LOG_FILE"
echo "========================================="
