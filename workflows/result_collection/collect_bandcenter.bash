#!/usr/bin/env bash

set -euo pipefail

VASPKIT_BIN="${VASPKIT_BIN:-vaspkit}"

usage() {
    cat <<'EOF'
Usage:
  collect_bandcenter.bash <structure_name> <output_dir> [base_dir]

Notes:
  The script expects the structure name suffix after the last '-' to be a 4-character
  coordination string built from B, C, N, O, P, or S.
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
N_COORD=4

BASE_DIR="$(cd "$BASE_DIR_INPUT" && pwd)"
if [[ "$OUTPUT_DIR_INPUT" = /* ]]; then
    OUTPUT_DIR="$OUTPUT_DIR_INPUT"
else
    OUTPUT_DIR="$BASE_DIR/$OUTPUT_DIR_INPUT"
fi

STRUCT_PATH="$BASE_DIR/$STRUCT_NAME"
DOS_DIR="$STRUCT_PATH/RF/dos"
SUMMARY_FILE="$OUTPUT_DIR/summary_dband_pband.txt"

[[ -d "$STRUCT_PATH" ]] || { echo "Structure directory not found: $STRUCT_PATH" >&2; exit 1; }
[[ -d "$DOS_DIR" ]] || { echo "DOS directory not found: $DOS_DIR" >&2; exit 1; }

pushd "$DOS_DIR" > /dev/null

POSCAR_FILE="POSCAR"
[[ -f "$POSCAR_FILE" ]] || { echo "POSCAR not found in $DOS_DIR" >&2; popd > /dev/null; exit 1; }

read -r -a elements <<< "$(sed -n '6p' "$POSCAR_FILE")"
read -r -a counts <<< "$(sed -n '7p' "$POSCAR_FILE")"

declare -A elem_indices_list
idx=1
for ((i = 0; i < ${#elements[@]}; i++)); do
    elem="${elements[$i]}"
    cnt="${counts[$i]}"
    indices=""
    for ((j = 0; j < cnt; j++)); do
        indices+="$idx "
        ((idx++))
    done
    elem_indices_list["$elem"]="${indices% }"
done

coord_part="${STRUCT_NAME##*-}"
if [[ -z "$coord_part" || ! "$coord_part" =~ ^[BCNOPS]{4}$ ]]; then
    echo "Invalid coordination suffix for $STRUCT_NAME: $coord_part" >&2
    popd > /dev/null
    exit 1
fi

coord_chars=()
for ((i = 0; i < ${#coord_part}; i++)); do
    coord_chars+=("${coord_part:$i:1}")
done

declare -A front_taken
declare -A back_taken
coord_ids=()
coord_indices=()

for ch in "${coord_chars[@]}"; do
    read -r -a all <<< "${elem_indices_list[$ch]:-}"
    total="${#all[@]}"
    if (( total == 0 )); then
        echo "Element $ch not found in POSCAR for $STRUCT_NAME" >&2
        popd > /dev/null
        exit 1
    fi

    case "$ch" in
        C)
            taken="${back_taken[$ch]:-0}"
            (( taken < total )) || { echo "Not enough $ch atoms in $STRUCT_NAME" >&2; popd > /dev/null; exit 1; }
            sel_idx="${all[$((total - taken - 1))]}"
            back_taken["$ch"]=$((taken + 1))
            ;;
        S|B|N|O|P)
            taken="${front_taken[$ch]:-0}"
            (( taken < total )) || { echo "Not enough $ch atoms in $STRUCT_NAME" >&2; popd > /dev/null; exit 1; }
            sel_idx="${all[$taken]}"
            front_taken["$ch"]=$((taken + 1))
            ;;
        *)
            echo "Unsupported coordination element: $ch" >&2
            popd > /dev/null
            exit 1
            ;;
    esac

    coord_indices+=("$sel_idx")
    coord_ids+=("${ch}-${sel_idx}")
done

if (( ${#coord_indices[@]} != N_COORD )); then
    echo "Expected $N_COORD coordination atoms for $STRUCT_NAME" >&2
    popd > /dev/null
    exit 1
fi

printf "503\n2\nN\n1\nW\n" | "$VASPKIT_BIN" > /dev/null 2>&1
[[ -f "BAND_CENTER" ]] || { echo "BAND_CENTER was not generated for $STRUCT_NAME" >&2; popd > /dev/null; exit 1; }

w_d_center="$(awk '/^#Average/ {getline; print $3; exit}' BAND_CENTER)"
[[ -n "$w_d_center" ]] || { echo "Failed to extract W d-band center for $STRUCT_NAME" >&2; popd > /dev/null; exit 1; }

mkdir -p "$OUTPUT_DIR"
if [[ ! -f "$SUMMARY_FILE" ]]; then
    header="Structure\tW-d-band-center"
    for ((i = 1; i <= N_COORD; i++)); do
        header+="\tcoord${i}_id\tp${i}"
    done
    echo -e "$header" > "$SUMMARY_FILE"
fi

data_line="$STRUCT_NAME\t$w_d_center"
for ((i = 0; i < ${#coord_indices[@]}; i++)); do
    atom_index="${coord_indices[$i]}"
    atom_id="${coord_ids[$i]}"
    printf "503\n2\nN\n1\n%s\n" "$atom_index" | "$VASPKIT_BIN" > /dev/null 2>&1
    p_center="$(awk '/^#Average/ {getline; print $2; exit}' BAND_CENTER)"
    [[ -n "$p_center" ]] || { echo "Failed to extract p-band center for atom $atom_index in $STRUCT_NAME" >&2; popd > /dev/null; exit 1; }
    data_line+="\t${atom_id}\t${p_center}"
done

popd > /dev/null

TMP_SUMMARY="$(mktemp)"
awk -F '\t' -v name="$STRUCT_NAME" 'NR == 1 || $1 != name' "$SUMMARY_FILE" > "$TMP_SUMMARY"
mv "$TMP_SUMMARY" "$SUMMARY_FILE"
echo -e "$data_line" >> "$SUMMARY_FILE"

echo "Collected band centers for $STRUCT_NAME"
