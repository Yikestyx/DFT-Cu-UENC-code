# Energy Processor

This directory contains Python scripts for post-processing tabulated energy data and exporting derived analysis tables.

- `energy_processor.py`: read an Excel file with structure names, energies, and vibrational corrections; compute corrected energies and reaction `DeltaE`; then export multiple analysis sheets to a single Excel workbook.

## Input Assumptions

- The input Excel file contains three columns without a header row:
  1. structure name
  2. raw energy
  3. vibrational correction
- The catalyst name and reaction mapping are configured inside the script.

## Usage

Run the script directly and pass input/output files as arguments:

```bash
python workflows/energy_processor/energy_processor.py --input energy_data.xlsx --output energy_analysis.xlsx
```

## Dependencies

- `pandas`
- `openpyxl`
