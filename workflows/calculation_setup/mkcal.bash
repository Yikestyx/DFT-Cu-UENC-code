#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/cif_process_log.txt"
PBS_SOURCE="${HOME}/do.pbs"
INCAR_SOURCE="${SCRIPT_DIR}/INCAR"

now() {
    date +"%Y-%m-%d %H:%M:%S"
}

log() {
    printf "%s - %s\n" "$(now)" "$1" >> "$LOG_FILE"
}

run_cmd() {
    # Usage:
    #   run_cmd "<cwd>" "<stdin_text_or_empty>" cmd arg1 arg2 ...
    local cwd="$1"
    local stdin_text="$2"
    shift 2

    local out_file err_file
    out_file="$(mktemp)"
    err_file="$(mktemp)"

    if [[ -n "$stdin_text" ]]; then
        printf "%b" "$stdin_text" | (cd "$cwd" && "$@") >"$out_file" 2>"$err_file"
    else
        (cd "$cwd" && "$@") >"$out_file" 2>"$err_file"
    fi
    local ret=$?

    RUN_OUT="$(cat "$out_file")"
    RUN_ERR="$(cat "$err_file")"
    rm -f "$out_file" "$err_file"
    return $ret
}

parse_element() {
    local cif_name="$1"
    if [[ "$cif_name" != *-* ]]; then
        echo ""
        return 1
    fi
    echo "${cif_name%%-*}"
    return 0
}

get_sorted_elements() {
    local workdir="$1"
    run_cmd "$workdir" "" Elementordering.py
    local ret=$?
    if [[ $ret -ne 0 ]]; then
        return $ret
    fi

    local last_nonempty
    last_nonempty="$(printf "%s\n" "$RUN_OUT" | awk 'NF{line=$0} END{print line}')"
    if [[ -z "$last_nonempty" ]]; then
        return 2
    fi
    printf "%s" "$last_nonempty"
    return 0
}

update_job_name() {
    local do_pbs="$1"
    local job_name="$2"
    sed -i "s|#SBATCH --job-name=|#SBATCH --job-name=${job_name}|" "$do_pbs"
}

process_one_cif() {
    local base_dir="$1"
    local cif_name="$2"

    local cif_path="${base_dir}/${cif_name}"
    local structure_name="${cif_name%.cif}"

    local element
    element="$(parse_element "$cif_name")"
    if [[ -z "$element" ]]; then
        log "${cif_name}: FAILED - cannot parse element"
        return 1
    fi

    local element_dir="${base_dir}/${element}"
    local structure_dir="${element_dir}/${structure_name}"
    mkdir -p "$structure_dir"

    local target_cif="${structure_dir}/${cif_name}"
    mv "$cif_path" "$target_cif" || {
        log "${cif_name}: FAILED - move cif failed"
        return 1
    }
    log "${cif_name}: moved to ${structure_dir}"

    local sorted_elements
    sorted_elements="$(get_sorted_elements "$structure_dir")"
    local ret=$?
    if [[ $ret -ne 0 ]]; then
        log "${cif_name}: FAILED - Elementordering.py failed: ${RUN_ERR}"
        return 1
    fi

    run_cmd "$structure_dir" "105\n${cif_name}\n${sorted_elements}\n" vaspkit
    ret=$?
    if [[ $ret -ne 0 ]]; then
        log "${cif_name}: FAILED - vaspkit(105) failed: ${RUN_ERR}"
        return 1
    fi

    cp "$INCAR_SOURCE" "${structure_dir}/INCAR" || {
        log "${cif_name}: FAILED - copy INCAR failed"
        return 1
    }
    log "${cif_name}: INCAR copied before MAGMOM.py"

    run_cmd "$structure_dir" "" MAGMOM.py
    ret=$?
    if [[ $ret -ne 0 ]]; then
        log "${cif_name}: FAILED - MAGMOM.py failed: ${RUN_ERR}"
        return 1
    fi

    cp "$PBS_SOURCE" "${structure_dir}/do.pbs" || {
        log "${cif_name}: FAILED - copy do.pbs failed"
        return 1
    }
    local job_name="${structure_name}"
    update_job_name "${structure_dir}/do.pbs" "$job_name"

    run_cmd "$structure_dir" "102\n2\n0.04\n" vaspkit
    ret=$?
    if [[ $ret -ne 0 ]]; then
        log "${cif_name}: FAILED - vaspkit(102) failed: ${RUN_ERR}"
        return 1
    fi

    run_cmd "$structure_dir" "402\n1\n3\n0.08 0.25\n1\nall\n" vaspkit
    ret=$?
    if [[ $ret -ne 0 ]]; then
        log "${cif_name}: FAILED - vaspkit(402) failed: ${RUN_ERR}"
        return 1
    fi

    if [[ ! -f "${structure_dir}/POSCAR_FIX.vasp" ]]; then
        log "${cif_name}: FAILED - POSCAR_FIX.vasp not generated"
        return 1
    fi
    cp "${structure_dir}/POSCAR_FIX.vasp" "${structure_dir}/POSCAR" || {
        log "${cif_name}: FAILED - copy POSCAR_FIX.vasp to POSCAR failed"
        return 1
    }

    run_cmd "$structure_dir" "" sbatch do.pbs
    ret=$?
    if [[ $ret -ne 0 ]]; then
        log "${cif_name}: FAILED - sbatch failed: ${RUN_ERR}"
        return 1
    fi

    local job_id
    job_id="$(printf "%s\n" "$RUN_OUT" | awk 'NF{last=$NF} END{print last}')"
    if [[ "$job_id" =~ ^[0-9]+$ ]]; then
        log "${cif_name}: submitted, job_name=${job_name}, job_id=${job_id}"
    else
        log "${cif_name}: submitted, job_name=${job_name}, job_id=UNKNOWN, sbatch_out=${RUN_OUT}"
    fi
    return 0
}

main() {
    : > "$LOG_FILE"

    if [[ ! -f "$PBS_SOURCE" ]]; then
        echo "PBS template not found: $PBS_SOURCE" >&2
        exit 1
    fi
    if [[ ! -f "$INCAR_SOURCE" ]]; then
        echo "INCAR not found in script directory: $INCAR_SOURCE" >&2
        exit 1
    fi

    local cif_files=()
    while IFS= read -r -d '' f; do
        cif_files+=("$f")
    done < <(find "$SCRIPT_DIR" -maxdepth 1 -type f -name "*.cif" -print0 | sort -z)

    if [[ ${#cif_files[@]} -eq 0 ]]; then
        echo "No .cif files found in current directory."
        exit 0
    fi

    log "===== mkcal start ====="
    log "base_dir: ${SCRIPT_DIR}"
    log "cif_count: ${#cif_files[@]}"

    local ok=0
    local fail=0
    local cif_path cif_name
    for cif_path in "${cif_files[@]}"; do
        cif_name="$(basename "$cif_path")"
        log "processing: ${cif_name}"
        if process_one_cif "$SCRIPT_DIR" "$cif_name"; then
            ok=$((ok + 1))
        else
            fail=$((fail + 1))
        fi
    done

    log "===== mkcal end: success=${ok}, failed=${fail} ====="
    echo "All calculation submitted. success=${ok}, failed=${fail}"
}

main "$@"
