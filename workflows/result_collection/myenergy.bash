#!/usr/bin/env bash

set -euo pipefail

ENERGY_BIN="${ENERGY_BIN:-energy}"
VASPKIT_BIN="${VASPKIT_BIN:-vaspkit}"

usage() {
    cat <<'EOF'
Usage:
  myenergy.bash [base_dir] [output_file]

Arguments:
  base_dir      Directory containing structure subdirectories. Default: current directory.
  output_file   Summary file path. Default: E.txt under base_dir.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

BASE_DIR_INPUT="${1:-$(pwd)}"
OUTPUT_FILE_INPUT="${2:-E.txt}"

BASE_DIR="$(cd "$BASE_DIR_INPUT" && pwd)"
if [[ "$OUTPUT_FILE_INPUT" = /* ]]; then
    OUTPUT_FILE="$OUTPUT_FILE_INPUT"
else
    OUTPUT_FILE="$BASE_DIR/$OUTPUT_FILE_INPUT"
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"
: > "$OUTPUT_FILE"

shopt -s nullglob
for dir in "$BASE_DIR"/*/; do
    struct_name="$(basename "$dir")"

    if [[ "$struct_name" == .* ]]; then
        continue
    fi

    energy_output="$(cd "$dir" && "$ENERGY_BIN")"
    total_energy="$(echo "$energy_output" | awk '{print $7}' | head -1)"

    if [[ -d "$dir/vib" ]]; then
        vib_output="$(cd "$dir/vib" && printf "501\n298.15\n" | "$VASPKIT_BIN")"
        g_energy="$(echo "$vib_output" | awk '/Thermal correction to G\(T\):/ {print $7; exit}')"
        echo "${struct_name} ${total_energy} ${g_energy}" >> "$OUTPUT_FILE"
    else
        echo "${struct_name} ${total_energy}" >> "$OUTPUT_FILE"
    fi
done

echo "Saved energy summary to $OUTPUT_FILE"
