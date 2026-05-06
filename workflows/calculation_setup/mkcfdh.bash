#!/usr/bin/env bash

# Description:
#   Create and submit CFDH-style charge-density-difference calculations inside
#   `RF/CFDH/` for structures that do not already contain that workflow.

set -euo pipefail

VASPKIT_BIN="${VASPKIT_BIN:-vaspkit}"
MAGMOM_BIN="${MAGMOM_BIN:-MAGMOM.py}"
SBATCH_BIN="${SBATCH_BIN:-sbatch}"

usage() {
    cat <<'EOF'
Usage:
  mkcfdh.bash [base_dir]

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
LOG_FILE="$BASE_DIR/CFDH.log"
ERROR_FILE="$(mktemp)"

cleanup() {
    rm -f "$ERROR_FILE"
}
trap cleanup EXIT

timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

log() {
    printf "%s - %s\n" "$(timestamp)" "$1" >> "$LOG_FILE"
}

setup_cfdh_case() {
    local source_rf_dir="$1"
    local target_dir="$2"
    local remove_elements="$3"
    local job_name="$4"

    mkdir -p "$target_dir"
    pushd "$target_dir" > /dev/null

    cp "$source_rf_dir/INCAR" .
    cp "$source_rf_dir/do.pbs" .
    cp "$source_rf_dir/KPOINTS" .
    cp "$source_rf_dir/CONTCAR" POSCAR

    printf "404\n1\n%s\n" "$remove_elements" | "$VASPKIT_BIN" > /dev/null 2> "$ERROR_FILE" || true
    [[ -f "POSCAR_REV.vasp" ]] || { popd > /dev/null; return 1; }

    cp POSCAR_REV.vasp POSCAR
    "$MAGMOM_BIN" > /dev/null 2> "$ERROR_FILE" || true
    printf "103\n" | "$VASPKIT_BIN" > /dev/null 2> "$ERROR_FILE" || true
    sed -i "s/#SBATCH --job-name=/#SBATCH --job-name=${job_name}/" do.pbs

    local job_id
    job_id="$("$SBATCH_BIN" do.pbs 2> "$ERROR_FILE" | awk '{print $NF}' || true)"
    if [[ "$job_id" =~ ^[0-9]+$ ]]; then
        log "$job_name: submitted job $job_id"
    else
        log "$job_name: failed to submit job"
    fi

    if [[ -s "$ERROR_FILE" ]]; then
        log "$job_name warning: $(cat "$ERROR_FILE")"
    fi

    popd > /dev/null
}

: > "$LOG_FILE"

shopt -s nullglob
for dir in "$BASE_DIR"/*/; do
    struct_name="$(basename "$dir")"

    if [[ "$struct_name" == "CONTCAR" || "$struct_name" == "POSCAR" || "$struct_name" == .* ]]; then
        continue
    fi

    rf_dir="$dir/RF"
    cfdh_dir="$rf_dir/CFDH"

    if [[ ! -d "$rf_dir" ]]; then
        log "$struct_name: RF directory missing, skipped"
        continue
    fi

    if [[ -d "$cfdh_dir" ]]; then
        log "$struct_name: CFDH directory already exists, skipped"
        continue
    fi

    mkdir -p "$cfdh_dir"
    setup_cfdh_case "$rf_dir" "$cfdh_dir/W" "B C N O P S" "CFDH-W-$struct_name"
    setup_cfdh_case "$rf_dir" "$cfdh_dir/others" "W" "CFDH-o-$struct_name"
done

echo "CFDH setup finished. Log file: $LOG_FILE"
