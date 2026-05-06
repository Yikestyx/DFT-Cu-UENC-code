#!/usr/bin/env bash

set -euo pipefail

VASPKIT_BIN="${VASPKIT_BIN:-vaspkit}"

usage() {
    cat <<'EOF'
Usage:
  collect_chargediff.bash <structure_name> <output_dir> [base_dir]
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
CFDH_DIR="$STRUCT_PATH/RF/CFDH"
TARGET_SUBDIR="$OUTPUT_DIR/$STRUCT_NAME"

[[ -d "$STRUCT_PATH" ]] || { echo "Structure directory not found: $STRUCT_PATH" >&2; exit 1; }
[[ -d "$CFDH_DIR" ]] || { echo "CFDH directory not found: $CFDH_DIR" >&2; exit 1; }

(cd "$CFDH_DIR" && printf "314\n../CHGCAR W/CHGCAR others/CHGCAR\n" | "$VASPKIT_BIN" > /dev/null 2>&1)

[[ -f "$CFDH_DIR/CHGDIFF.vasp" ]] || { echo "CHGDIFF.vasp was not generated for $STRUCT_NAME" >&2; exit 1; }

mkdir -p "$TARGET_SUBDIR"
cp -f "$CFDH_DIR/CHGDIFF.vasp" "$TARGET_SUBDIR/"

echo "Collected charge-difference result for $STRUCT_NAME"
