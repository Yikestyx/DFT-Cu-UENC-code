#!/usr/bin/env bash

set -euo pipefail

CHECK_BIN="${CHECK_BIN:-check}"
CHECK_DAV_BIN="${CHECK_DAV_BIN:-check-DAV}"

usage() {
    cat <<'EOF'
Usage:
  chk.bash [base_dir]

Outputs:
  cks.txt           Structure status summary
  unconverged.txt   Structure names that contain "not converged"
  error.txt         Captured command output for failed checks
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

BASE_DIR_INPUT="${1:-$(pwd)}"
BASE_DIR="$(cd "$BASE_DIR_INPUT" && pwd)"

CKS_FILE="$BASE_DIR/cks.txt"
UNCONVERGED_FILE="$BASE_DIR/unconverged.txt"
ERROR_FILE="$BASE_DIR/error.txt"

: > "$CKS_FILE"
: > "$UNCONVERGED_FILE"
: > "$ERROR_FILE"

shopt -s nullglob
for dir in "$BASE_DIR"/*/; do
    struct_name="$(basename "$dir")"

    if [[ "$struct_name" == "CONTCAR" || "$struct_name" == "POSCAR" || "$struct_name" == .* ]]; then
        continue
    fi

    output="$(cd "$dir" && "$CHECK_BIN" 2>&1 || true)"

    if grep -q "TypeError: int() argument must be a string or a number, not 'list'" <<< "$output"; then
        output="$(cd "$dir" && "$CHECK_DAV_BIN" 2>&1 || true)"
    fi

    calc_line="$(grep '^Calculation' <<< "$output" | head -1)"

    echo "$struct_name" >> "$CKS_FILE"
    echo "$calc_line" >> "$CKS_FILE"

    if grep -q "not converged" <<< "$output"; then
        echo "$struct_name" >> "$UNCONVERGED_FILE"
    fi

    if grep -Eq "Traceback|Error|Exception|IOError|IndexError" <<< "$output"; then
        {
            echo "=== $struct_name ==="
            echo "$output"
            echo
        } >> "$ERROR_FILE"
    fi
done

echo "Saved check summaries to:"
echo "  $CKS_FILE"
echo "  $UNCONVERGED_FILE"
echo "  $ERROR_FILE"
