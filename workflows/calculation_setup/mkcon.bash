#!/usr/bin/env bash

# Description:
#   Export `CONTCAR.cif` files from structure subdirectories into a single
#   `CONTCAR/` folder under the chosen calculation root.

set -euo pipefail

VASPKIT_BIN="${VASPKIT_BIN:-vaspkit}"

usage() {
    cat <<'EOF'
Usage:
  mkcon.bash [base_dir]

Arguments:
  base_dir   Calculation root containing structure subdirectories.
             Default: current directory.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

BASE_DIR_INPUT="${1:-$(pwd)}"
BASE_DIR="$(cd "$BASE_DIR_INPUT" && pwd)"
OUTPUT_DIR="$BASE_DIR/CONTCAR"

mkdir -p "$OUTPUT_DIR"

shopt -s nullglob
for dir in "$BASE_DIR"/*/; do
    struct_name="$(basename "$dir")"

    if [[ "$struct_name" == "CONTCAR" || "$struct_name" == "POSCAR" || "$struct_name" == .* ]]; then
        continue
    fi

    pushd "$dir" > /dev/null
    if [[ ! -f "CONTCAR.cif" ]]; then
        printf "413\n2\n" | "$VASPKIT_BIN" > /dev/null 2>&1
    fi

    if [[ -f "CONTCAR.cif" ]]; then
        cp -f "CONTCAR.cif" "$OUTPUT_DIR/${struct_name}.cif"
        echo "Exported CONTCAR.cif for $struct_name"
    else
        echo "Skipped $struct_name: CONTCAR.cif was not generated" >&2
    fi
    popd > /dev/null
done
