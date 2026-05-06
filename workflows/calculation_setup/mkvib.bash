#!/usr/bin/env bash

# Description:
#   Create and submit vibration calculations for structures marked as converged
#   in a `cks.txt` file and that do not already contain a `vib/` subdirectory.

set -euo pipefail

VIB_BUILDER_BIN="${VIB_BUILDER_BIN:-vibrate_nosubmit.sh}"
VASPKIT_BIN="${VASPKIT_BIN:-vaspkit}"
SBATCH_BIN="${SBATCH_BIN:-sbatch}"
PBS_TEMPLATE="${PBS_TEMPLATE:-$HOME/do.pbs}"
CONVERGENCE_FILE_NAME="${CONVERGENCE_FILE_NAME:-cks.txt}"

SUBGROUP_ELEMENTS=("Sc" "Ti" "V" "Cr" "Mn" "Fe" "Co" "Ni" "Cu" "Zn" "Y" "Zr" "Nb" "Mo" "Tc" "Ru" "Rh" "Pd" "Ag" "Cd")

usage() {
    cat <<'EOF'
Usage:
  mkvib.bash [base_dir]

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
LOG_FILE="$BASE_DIR/vib_calculation.log"
VIB_LOG_FILE="$BASE_DIR/viblog.txt"
CONVERGENCE_FILE="$BASE_DIR/$CONVERGENCE_FILE_NAME"
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

load_convergence_status() {
    declare -n status_ref=$1

    shopt -s nullglob
    for dir in "$BASE_DIR"/*/; do
        status_ref["$(basename "$dir")"]="unknown"
    done

    if [[ ! -f "$CONVERGENCE_FILE" ]]; then
        log "convergence file not found: $CONVERGENCE_FILE"
        return
    fi

    local current_dir=""
    local line=""
    while IFS= read -r line; do
        line="$(echo "$line" | sed -e 's/^[ \t]*//' -e 's/[ \t]*$//')"
        [[ -z "$line" ]] && continue

        if [[ "$line" == Calculation\ is* ]]; then
            if [[ -n "$current_dir" ]]; then
                if grep -q "not converged" <<< "$line"; then
                    status_ref["$current_dir"]="not_converged"
                elif grep -q "converged and reached required accuracy" <<< "$line"; then
                    status_ref["$current_dir"]="converged"
                else
                    status_ref["$current_dir"]="unknown"
                fi
                current_dir=""
            fi
        else
            if [[ -n "$current_dir" ]]; then
                status_ref["$current_dir"]="unknown"
            fi
            current_dir="$line"
        fi
    done < "$CONVERGENCE_FILE"

    if [[ -n "$current_dir" ]]; then
        status_ref["$current_dir"]="unknown"
    fi
}

filter_target_elements() {
    local poscar_file="$1"
    local elements=""
    elements="$(awk 'NR==6 {print $0}' "$poscar_file" | tr -s ' ')"

    local filtered=""
    local element=""
    for element in $elements; do
        local subgroup=""
        for subgroup in "${SUBGROUP_ELEMENTS[@]}"; do
            if [[ "$element" == "$subgroup" ]]; then
                filtered+="${element} "
                break
            fi
        done
    done
    printf "%s" "$filtered"
}

: > "$LOG_FILE"

declare -A convergence_status
load_convergence_status convergence_status

shopt -s nullglob
for dir in "$BASE_DIR"/*/; do
    struct_name="$(basename "$dir")"

    if [[ "$struct_name" == "CONTCAR" || "$struct_name" == "POSCAR" || "$struct_name" == .* ]]; then
        continue
    fi

    status="${convergence_status[$struct_name]:-unknown}"
    if [[ "$status" != "converged" ]]; then
        log "$struct_name: convergence status is $status, skipped"
        continue
    fi

    if [[ -d "$dir/vib" ]]; then
        log "$struct_name: vib directory already exists, skipped"
        continue
    fi

    pushd "$dir" > /dev/null
    : > "$ERROR_FILE"
    "$VIB_BUILDER_BIN" > /dev/null 2> "$ERROR_FILE" || true
    if [[ -s "$ERROR_FILE" ]]; then
        log "$struct_name: vibration builder warning: $(cat "$ERROR_FILE")"
    fi

    if [[ ! -d "vib" ]]; then
        log "$struct_name: vib directory was not created"
        popd > /dev/null
        continue
    fi

    pushd "vib" > /dev/null
    filtered_elements="$(filter_target_elements POSCAR)"
    printf "402\n1\n1\n%s\nall\n" "$filtered_elements" | "$VASPKIT_BIN" > /dev/null 2> "$ERROR_FILE" || true
    if [[ -s "$ERROR_FILE" ]]; then
        log "$struct_name: vaspkit warning: $(cat "$ERROR_FILE")"
    fi

    if [[ ! -f "POSCAR_FIX.vasp" ]]; then
        log "$struct_name: POSCAR_FIX.vasp not generated"
        popd > /dev/null
        popd > /dev/null
        continue
    fi

    cp POSCAR_FIX.vasp POSCAR
    cp "$PBS_TEMPLATE" .
    sed -i "s/#SBATCH --job-name=/#SBATCH --job-name=vib-$struct_name/" do.pbs

    job_id="$("$SBATCH_BIN" do.pbs 2> "$ERROR_FILE" | awk '{print $NF}' || true)"
    if [[ -s "$ERROR_FILE" ]]; then
        log "$struct_name: sbatch warning: $(cat "$ERROR_FILE")"
    fi

    if [[ "$job_id" =~ ^[0-9]+$ ]]; then
        printf "%s %s FilteredElements:[%s] %s Converged:Yes\n" \
            "$(date +"%y%m%d%H%M")" "$struct_name" "$filtered_elements" "$job_id" >> "$VIB_LOG_FILE"
        log "$struct_name: submitted vibration job $job_id"
    else
        log "$struct_name: failed to submit vibration job"
    fi
    popd > /dev/null
    popd > /dev/null
done

echo "Vibration setup finished. Log file: $LOG_FILE"
