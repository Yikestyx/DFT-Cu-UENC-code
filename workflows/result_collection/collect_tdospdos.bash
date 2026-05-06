#!/usr/bin/env bash

set -euo pipefail

VASPKIT_BIN="${VASPKIT_BIN:-vaspkit}"

usage() {
    cat <<'EOF'
Usage:
  collect_tdospdos.bash <structure_name> <output_dir> [base_dir]
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
DOS_DIR="$STRUCT_PATH/RF/dos"
TARGET_SUBDIR="$OUTPUT_DIR/$STRUCT_NAME"

[[ -d "$STRUCT_PATH" ]] || { echo "Structure directory not found: $STRUCT_PATH" >&2; exit 1; }
[[ -d "$DOS_DIR" ]] || { echo "DOS directory not found: $DOS_DIR" >&2; exit 1; }

pushd "$DOS_DIR" > /dev/null
printf "111\n" | "$VASPKIT_BIN" > /dev/null 2>&1
[[ -f "TDOS.dat" ]] || { echo "TDOS.dat was not generated for $STRUCT_NAME" >&2; popd > /dev/null; exit 1; }

printf "113\n" | "$VASPKIT_BIN" > /dev/null 2>&1
shopt -s nullglob
pdos_files=(PDOS*.dat)
if (( ${#pdos_files[@]} == 0 )); then
    echo "No PDOS*.dat files were generated for $STRUCT_NAME" >&2
    popd > /dev/null
    exit 1
fi
popd > /dev/null

mkdir -p "$TARGET_SUBDIR"
cp -f "$DOS_DIR/TDOS.dat" "$TARGET_SUBDIR/"
cp -f "$DOS_DIR"/PDOS*.dat "$TARGET_SUBDIR/"

echo "Collected TDOS/PDOS results for $STRUCT_NAME"
