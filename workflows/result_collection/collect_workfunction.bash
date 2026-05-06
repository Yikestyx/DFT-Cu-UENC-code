#!/usr/bin/env bash

set -euo pipefail

VASPKIT_BIN="${VASPKIT_BIN:-vaspkit}"

usage() {
    cat <<'EOF'
Usage:
  collect_workfunction.bash <structure_name> <output_dir> [base_dir]

Examples:
  bash collect_workfunction.bash Cu-001 SummaryResults/workfunction
  bash collect_workfunction.bash Cu-001 /tmp/workfunction /path/to/calculations
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if [[ $# -lt 2 || $# -gt 3 ]]; then
    usage >&2
    exit 1
fi

STRUCT_NAME="$1"
OUTPUT_DIR_INPUT="$2"
BASE_DIR_INPUT="${3:-$(pwd)}"

BASE_DIR="$(cd "$BASE_DIR_INPUT" && pwd)"
if [[ "$OUTPUT_DIR_INPUT" = /* ]]; then
    OUTPUT_DIR="$OUTPUT_DIR_INPUT"
else
    OUTPUT_DIR="$BASE_DIR/$OUTPUT_DIR_INPUT"
fi

STRUCT_PATH="$BASE_DIR/$STRUCT_NAME"
RF_DIR="$STRUCT_PATH/RF"
SUMMARY_FILE="$OUTPUT_DIR/summary_workfunction.txt"
TARGET_SUBDIR="$OUTPUT_DIR/$STRUCT_NAME"

[[ -d "$STRUCT_PATH" ]] || { echo "Structure directory not found: $STRUCT_PATH" >&2; exit 1; }
[[ -d "$RF_DIR" ]] || { echo "RF directory not found: $RF_DIR" >&2; exit 1; }

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

(cd "$RF_DIR" && printf "426\n3\n" | "$VASPKIT_BIN" > "$TMP_FILE" 2>&1)

VACUUM="$(grep -E '^[[:space:]]*Vacuum-Level' "$TMP_FILE" | sed -E 's/.*:[[:space:]]*([0-9.-]+).*/\1/' | head -1)"
WORKFUNC="$(grep -E '^[[:space:]]*Work Function' "$TMP_FILE" | sed -E 's/.*:[[:space:]]*([0-9.-]+).*/\1/' | head -1)"

if ! [[ "$VACUUM" =~ ^[0-9.-]+$ && "$WORKFUNC" =~ ^[0-9.-]+$ ]]; then
    echo "Failed to extract valid work-function data for $STRUCT_NAME" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
if [[ ! -f "$SUMMARY_FILE" ]]; then
    echo -e "Structure\tVacuum-Level (eV)\tWork Function (eV)" > "$SUMMARY_FILE"
fi

TMP_SUMMARY="$(mktemp)"
awk -F '\t' -v name="$STRUCT_NAME" 'NR == 1 || $1 != name' "$SUMMARY_FILE" > "$TMP_SUMMARY"
mv "$TMP_SUMMARY" "$SUMMARY_FILE"
echo -e "${STRUCT_NAME}\t${VACUUM}\t${WORKFUNC}" >> "$SUMMARY_FILE"

if [[ -f "$RF_DIR/PLANAR_AVERAGE.dat" ]]; then
    mkdir -p "$TARGET_SUBDIR"
    cp -f "$RF_DIR/PLANAR_AVERAGE.dat" "$TARGET_SUBDIR/"
fi

echo "Collected work function for $STRUCT_NAME"
