#!/usr/bin/env bash

# Description:
#   Create and submit RF calculations for structure subdirectories that do not
#   already contain an `RF/` folder.

set -euo pipefail

RF_BUILDER_BIN="${RF_BUILDER_BIN:-rfcalculation_nosubmit.sh}"
SBATCH_BIN="${SBATCH_BIN:-sbatch}"

usage() {
    cat <<'EOF'
Usage:
  mkrf.bash [base_dir]

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
LOG_FILE="$BASE_DIR/rf.log"
ERROR_FILE="$(mktemp)"
RF_LOG_FILE="$BASE_DIR/RFlog.txt"

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

run_or_log_error() {
    : > "$ERROR_FILE"
    "$@" > /dev/null 2> "$ERROR_FILE" || true
    if [[ -s "$ERROR_FILE" ]]; then
        log "warning: $(cat "$ERROR_FILE")"
    fi
}

: > "$LOG_FILE"

shopt -s nullglob
for dir in "$BASE_DIR"/*/; do
    struct_name="$(basename "$dir")"

    if [[ "$struct_name" == "CONTCAR" || "$struct_name" == "POSCAR" || "$struct_name" == .* ]]; then
        continue
    fi

    if [[ -d "$dir/RF" ]]; then
        log "$struct_name: RF directory already exists, skipped"
        continue
    fi

    pushd "$dir" > /dev/null
    log "$struct_name: creating RF calculation"
    run_or_log_error "$RF_BUILDER_BIN"

    if [[ ! -d "RF" ]]; then
        log "$struct_name: RF directory was not created"
        popd > /dev/null
        continue
    fi

    pushd "RF" > /dev/null
    job_id="$("$SBATCH_BIN" do.pbs 2> "$ERROR_FILE" | awk '{print $NF}' || true)"
    if [[ -s "$ERROR_FILE" ]]; then
        log "$struct_name: sbatch warning: $(cat "$ERROR_FILE")"
    fi

    if [[ "$job_id" =~ ^[0-9]+$ ]]; then
        printf "%s %s %s\n" "$(date +"%y%m%d%H%M")" "$struct_name" "$job_id" >> "$RF_LOG_FILE"
        log "$struct_name: submitted RF job $job_id"
    else
        log "$struct_name: failed to submit RF job"
    fi
    popd > /dev/null
    popd > /dev/null
done

echo "RF setup finished. Log file: $LOG_FILE"
