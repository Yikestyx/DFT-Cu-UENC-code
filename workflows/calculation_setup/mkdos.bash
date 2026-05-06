#!/usr/bin/env bash

# Description:
#   Create and submit DOS calculations inside `RF/` directories when a `dos/`
#   subdirectory is not already present.

set -euo pipefail

DOS_BUILDER_BIN="${DOS_BUILDER_BIN:-dos_afterRFcalculation.sh}"
SBATCH_BIN="${SBATCH_BIN:-sbatch}"

usage() {
    cat <<'EOF'
Usage:
  mkdos.bash [base_dir]

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
LOG_FILE="$BASE_DIR/dos.log"
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

: > "$LOG_FILE"

shopt -s nullglob
for dir in "$BASE_DIR"/*/; do
    struct_name="$(basename "$dir")"

    if [[ "$struct_name" == "CONTCAR" || "$struct_name" == "POSCAR" || "$struct_name" == .* ]]; then
        continue
    fi

    if [[ ! -d "$dir/RF" ]]; then
        log "$struct_name: RF directory missing, skipped"
        continue
    fi

    if [[ -d "$dir/RF/dos" ]]; then
        log "$struct_name: dos directory already exists, skipped"
        continue
    fi

    pushd "$dir/RF" > /dev/null
    : > "$ERROR_FILE"
    "$DOS_BUILDER_BIN" > /dev/null 2> "$ERROR_FILE" || true
    if [[ -s "$ERROR_FILE" ]]; then
        log "$struct_name: dos builder warning: $(cat "$ERROR_FILE")"
    fi

    if [[ ! -d "dos" ]]; then
        log "$struct_name: dos directory was not created"
        popd > /dev/null
        continue
    fi

    pushd "dos" > /dev/null
    job_id="$("$SBATCH_BIN" do.pbs 2> "$ERROR_FILE" | awk '{print $NF}' || true)"
    if [[ -s "$ERROR_FILE" ]]; then
        log "$struct_name: sbatch warning: $(cat "$ERROR_FILE")"
    fi

    if [[ "$job_id" =~ ^[0-9]+$ ]]; then
        log "$struct_name: submitted DOS job $job_id"
    else
        log "$struct_name: failed to submit DOS job"
    fi
    popd > /dev/null
    popd > /dev/null
done

echo "DOS setup finished. Log file: $LOG_FILE"
