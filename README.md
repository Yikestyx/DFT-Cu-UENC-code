# DFT Workflow Toolkit

Personal scripts for day-to-day DFT work, organized by workflow stage instead of by language. The repository centers on VASP calculation setup, result collection, energy-table analysis, structure visualization, and a few standalone utilities for conversion or manual review.

This is still a personal research toolbox, but the layout and documentation are being cleaned up so individual parts are easier to understand, reuse, and adapt.

## Repository layout

### `workflows/calculation_setup/`
Scripts for preparing or submitting follow-up calculations from an existing structure directory.

- `mkcal.bash`: batch process CIF files into calculation folders and submit jobs.
- `mkrf.bash`: create and submit RF calculations for structures that do not yet have an `RF/` directory.
- `mkcon.bash`: collect `CONTCAR.cif` exports.
- `mkdos.bash`, `mkvib.bash`, `mkcfdh.bash`: prepare DOS, vibration, and charge-related workflows.

### `workflows/result_collection/`
Scripts for gathering completed calculation outputs into summary files or result folders.

- `collect_all.bash`: batch driver for all supported collection tasks.
- `collect_workfunction.bash`, `collect_bandcenter.bash`, `collect_chargediff.bash`, `collect_tdospdos.bash`: collect specific post-processing results.
- `myenergy.bash`: summarize total energy and optional vibrational correction.
- `chk.bash`: quick convergence and error-status helper.

Most scripts in this directory accept a calculation root directory as an argument, so they are less tied to a single working directory than before.

### `workflows/energy_processor/`
Python scripts for analyzing tabulated energy data.

- `energy_processor.py`: read an Excel table of structure names, energies, and vibrational corrections; compute corrected energies and `DeltaE`; then export multiple analysis sheets into one workbook.

### `workflows/structure_visualization/`
Python-based structure rendering and reporting workflow.

- `pipeline_main.py`: main programmable entry point for batch rendering.
- `projection_overlap.py`: select better projection directions.
- `structure_view_renderer.py`, `vesta_controller.py`, `xyzrender.py`: different rendering backends.
- `structure_ppt_generator.py`: assemble rendered images into PowerPoint slides.

At the moment, the `xyzrender` backend is included as an option but its visual output is still not as good as the other rendering routes, so it should be treated as experimental.

### `tools/conversion/` and `tools/review/`
Smaller standalone helpers.

- `tools/conversion/xsdtocif.py`: convert `.xsd` files to `.cif`.
- `tools/review/structure_check.py`: review structures with Excel and image previews.

## Typical workflow

1. Use `workflows/calculation_setup/` to generate or submit the next stage of VASP calculations.
2. Use `workflows/result_collection/` to gather finished outputs from many structure folders.
3. Use `workflows/energy_processor/` to analyze consolidated energy tables.
4. Use `workflows/structure_visualization/` to render CIF structures and generate presentation material.

## Quick start

This is not a packaged application. Most scripts assume an existing local research environment and a known directory layout. If you want to reuse this repository:

1. Start with one functional area rather than the whole repo.
2. Read the local `README.md` in that directory first.
3. Replace hard-coded paths or machine-specific settings before running anything important.
4. Test on a small sample directory before using real calculation results.

Examples:

```bash
bash workflows/result_collection/collect_all.bash /path/to/calculations
python workflows/energy_processor/energy_processor.py
pip install -r requirements-visualization.txt
python workflows/structure_visualization/pipeline_main.py
```

## External dependencies

Different parts of the repository depend on different tools.

- VASPKit
- VESTA
- Slurm `sbatch`
- Python packages listed in `requirements-visualization.txt`
- `pandas` and `openpyxl` for Excel-based energy analysis

Some calculation-setup scripts also rely on two local helper scripts, `Elementordering.py` and `MAGMOM.py`, for POSCAR element ordering and INCAR `MAGMOM` editing. They are not included in this repository for copyright reasons, so those workflows will need local replacements before they can run elsewhere.

## Current limitations

- Several scripts still contain hard-coded Windows paths or user-specific assumptions.
- Many shell scripts depend on a fixed VASP calculation directory layout.
- The repo does not yet provide sample datasets or a unified CLI.
- Not every workflow has been refactored to the same level of portability yet.
- The `xyzrender` backend currently produces weaker visual results than the other structure-visualization backends.

Even with those limits, the current structure makes it much clearer which scripts belong to which stage of the workflow and where to start if you want to adapt one part of the toolkit for your own use.
