#!/usr/bin/env python3
"""
Description:
    Read an Excel table of structure energies and vibrational corrections,
    compute corrected energies and reaction DeltaE values, and export multiple
    analysis sheets into a single Excel workbook.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import pandas as pd

DEFAULT_INPUT_FILE = "energy_data.xlsx"
DEFAULT_OUTPUT_FILE = "energy_analysis.xlsx"
CATALYST = "*"

N_REACTANTS = ["*N", "*NH", "*NH2", "*NHO", "*NOH", "*NO", "*NO2", "*NOOH", "*NO3", "*NO3H", "*NHOH", "*NH3"]
C_REACTANTS = ["*C", "*CO", "*CO2", "*COOH", "*CHOO", "*CHO", "*COH"]

PRODUCT_MAPPING = {
    "NC": ("*N", "*C"), "NCO": ("*N", "*CO"), "NCO2": ("*N", "*CO2"), "NCOOH": ("*N", "*COOH"),
    "NHC": ("*NH", "*C"), "NHCO": ("*NH", "*CO"), "NHCO2": ("*NH", "*CO2"), "NHCOOH": ("*NH", "*COOH"),
    "NH2C": ("*NH2", "*C"), "NH2CO": ("*NH2", "*CO"), "NH2CO2": ("*NH2", "*CO2"), "NH2COOH": ("*NH2", "*COOH"),
    "NHOC": ("*NHO", "*C"), "NHOCO": ("*NHO", "*CO"), "NHOCO2": ("*NHO", "*CO2"), "NHOCOOH": ("*NHO", "*COOH"),
    "NOHC": ("*NOH", "*C"), "NOHCO": ("*NOH", "*CO"), "NOHCO2": ("*NOH", "*CO2"), "NOHCOOH": ("*NOH", "*COOH"),
    "NOC": ("*NO", "*C"), "NOCO": ("*NO", "*CO"), "NOCO2": ("*NO", "*CO2"), "NOCOOH": ("*NO", "*COOH"),
    "NO2C": ("*NO2", "*C"), "NO2CO": ("*NO2", "*CO"), "NO2CO2": ("*NO2", "*CO2"), "NO2COOH": ("*NO2", "*COOH"),
    "NOOHC": ("*NOOH", "*C"), "NOOHCO": ("*NOOH", "*CO"), "NOOHCO2": ("*NOOH", "*CO2"), "NOOHCOOH": ("*NOOH", "*COOH"),
    "NO3C": ("*NO3", "*C"), "NO3CO": ("*NO3", "*CO"), "NO3CO2": ("*NO3", "*CO2"), "NO3COOH": ("*NO3", "*COOH"),
    "NO3HC": ("*NO3H", "*C"), "NO3HCO": ("*NO3H", "*CO"), "NO3HCO2": ("*NO3H", "*CO2"), "NO3HCOOH": ("*NO3H", "*COOH"),
    "NHOHC": ("*NHOH", "*C"), "NHOHCO": ("*NHOH", "*CO"), "NHOHCO2": ("*NHOH", "*CO2"), "NHOHCOOH": ("*NHOH", "*COOH"),
    "NH3C": ("*NH3", "*C"), "NH3CO": ("*NH3", "*CO"), "NH3CO2": ("*NH3", "*CO2"), "NH3COOH": ("*NH3", "*COOH"),
    "NCHOO": ("*N", "*CHOO"), "NHCHOO": ("*NH", "*CHOO"), "NH2CHOO": ("*NH2", "*CHOO"),
    "NCHO": ("*N", "*CHO"), "NHCHO": ("*NH", "*CHO"), "NH2CHO": ("*NH2", "*CHO"),
    "NCOH": ("*N", "*COH"), "NHCOH": ("*NH", "*COH"), "NH2COH": ("*NH2", "*COH"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process an Excel energy table and export DeltaE analysis sheets."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT_FILE, help="Input Excel file without header row")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FILE, help="Output Excel workbook path")
    return parser.parse_args()


def load_and_filter_energy(filepath: Path) -> Dict[str, float]:
    df = pd.read_excel(filepath, header=None)
    print(f"Loaded {len(df)} rows from {filepath}")

    energy_dict: Dict[str, float] = {}
    skipped = []
    duplicate_count = 0

    for _, row in df.iterrows():
        name = str(row.iloc[0]).strip()
        e_val = row.iloc[1]
        zpe_val = row.iloc[2] if len(row) > 2 else None

        is_catalyst = name == CATALYST
        is_valid = True
        reason = ""

        try:
            if pd.isna(e_val):
                is_valid = False
                reason = "energy is NaN"
            else:
                e_float = float(e_val)
                if e_float == 0:
                    is_valid = False
                    reason = "energy is 0"
        except Exception:
            is_valid = False
            reason = f"invalid energy value: {e_val}"

        if is_valid:
            try:
                if pd.isna(zpe_val):
                    is_valid = False
                    reason = "vibrational correction is NaN"
                else:
                    zpe_float = float(zpe_val)
                    if zpe_float == 0 and not is_catalyst:
                        is_valid = False
                        reason = "vibrational correction is 0 for a non-catalyst entry"
            except Exception:
                is_valid = False
                reason = f"invalid vibrational correction: {zpe_val}"

        if not is_valid:
            print(f"Skipped {name}: {reason}")
            skipped.append(name)
            continue

        total_energy = e_float + zpe_float
        if name in energy_dict:
            duplicate_count += 1
            previous_energy = energy_dict[name]
            if total_energy < previous_energy:
                energy_dict[name] = total_energy
                print(f"Updated duplicate {name}: {previous_energy:.6f} -> {total_energy:.6f}")
            else:
                print(f"Kept lower duplicate for {name}: {previous_energy:.6f} <= {total_energy:.6f}")
        else:
            energy_dict[name] = total_energy

    print(
        f"Retained {len(energy_dict)} valid structures, skipped {len(skipped)}, "
        f"handled {duplicate_count} duplicate rows"
    )
    return energy_dict


def parse_product(name: str) -> Tuple[Optional[str], Optional[int]]:
    if not name.startswith("*"):
        return None, None

    inner = name[1:]
    parts = inner.split("-")
    base = parts[0]

    if len(parts) > 1:
        try:
            index = int(parts[-1])
        except Exception:
            index = 1
    else:
        index = 1

    return base, index


def calculate_delta_e(energy_dict: Dict[str, float]) -> pd.DataFrame:
    if CATALYST not in energy_dict:
        print("Catalyst energy is missing")
        return pd.DataFrame()

    catalyst_energy = energy_dict[CATALYST]
    print(f"Catalyst energy E({CATALYST}) = {catalyst_energy:.6f}")

    results = []
    for name, product_energy in energy_dict.items():
        if name == CATALYST or name in N_REACTANTS + C_REACTANTS:
            continue

        base, _ = parse_product(name)
        if base not in PRODUCT_MAPPING:
            continue

        n_reactant, c_reactant = PRODUCT_MAPPING[base]
        if n_reactant not in energy_dict or c_reactant not in energy_dict:
            print(f"Warning: {name} is missing reactant data for {n_reactant} or {c_reactant}")
            continue

        n_energy = energy_dict[n_reactant]
        c_energy = energy_dict[c_reactant]
        delta_e = product_energy + catalyst_energy - n_energy - c_energy

        results.append(
            {
                "product": name,
                "n_reactant": n_reactant,
                "c_reactant": c_reactant,
                "E_product": product_energy,
                "E_n_reactant": n_energy,
                "E_c_reactant": c_energy,
                "E_catalyst": catalyst_energy,
                "DeltaE": delta_e,
            }
        )

    if not results:
        print("No valid products were found")
        return pd.DataFrame()

    return pd.DataFrame(results).sort_values("product")


def generate_structure_analysis(energy_dict: Dict[str, float]) -> pd.DataFrame:
    rows = []
    for name, energy in energy_dict.items():
        if name == CATALYST:
            rows.append({"structure": name, "energy": energy, "type": "catalyst", "type_index": "-"})
        elif name in N_REACTANTS:
            rows.append({"structure": name, "energy": energy, "type": "n_reactant", "type_index": "-"})
        elif name in C_REACTANTS:
            rows.append({"structure": name, "energy": energy, "type": "c_reactant", "type_index": "-"})
        else:
            base, index = parse_product(name)
            if base in PRODUCT_MAPPING:
                n_reactant, c_reactant = PRODUCT_MAPPING[base]
                rows.append(
                    {
                        "structure": name,
                        "energy": energy,
                        "type": "product",
                        "type_index": index,
                        "reaction": f"{n_reactant}+{c_reactant}->{name}",
                    }
                )
            else:
                rows.append({"structure": name, "energy": energy, "type": "unknown", "type_index": "-"})

    return pd.DataFrame(rows)


def save_analysis(output_path: Path, df_delta: pd.DataFrame, df_analysis: pd.DataFrame) -> None:
    df_negative = df_delta[df_delta["DeltaE"] < 0].copy()
    df_sorted = df_delta.sort_values("DeltaE")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_delta.to_excel(writer, sheet_name="DeltaE_Results", index=False)
        if not df_negative.empty:
            df_negative.to_excel(writer, sheet_name="Exothermic", index=False)
        df_sorted.to_excel(writer, sheet_name="Sorted_by_DeltaE", index=False)
        df_analysis.to_excel(writer, sheet_name="Structure_Analysis", index=False)

    print(f"Saved analysis workbook to: {output_path}")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    energy_dict = load_and_filter_energy(input_path)
    if not energy_dict:
        raise SystemExit("No valid input data was found")

    df_delta = calculate_delta_e(energy_dict)
    if df_delta.empty:
        raise SystemExit("No DeltaE results were generated")

    df_analysis = generate_structure_analysis(energy_dict)

    print("\nDeltaE summary:")
    print(f"  min: {df_delta['DeltaE'].min():.6f}")
    print(f"  max: {df_delta['DeltaE'].max():.6f}")
    print(f"  mean: {df_delta['DeltaE'].mean():.6f}")
    print(f"  median: {df_delta['DeltaE'].median():.6f}")

    negative_count = (df_delta["DeltaE"] < 0).sum()
    print(f"  exothermic count: {negative_count} ({negative_count / len(df_delta) * 100:.1f}%)")

    save_analysis(output_path, df_delta, df_analysis)


if __name__ == "__main__":
    main()
