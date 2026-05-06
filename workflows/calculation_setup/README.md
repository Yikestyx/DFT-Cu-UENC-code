# Calculation Setup

Scripts in this directory prepare or submit routine VASP calculations from an existing working folder.

- `mkcal.bash`: organize CIF files, generate inputs, and submit jobs.
- `mkrf.bash`: create and submit RF calculations for structures that do not already contain an `RF/` subdirectory.
- `mkcon.bash`: export `CONTCAR.cif` files into a central folder.
- `mkdos.bash`: create and submit DOS calculations after RF calculations.
- `mkvib.bash`: create and submit vibration calculations for converged structures.
- `mkcfdh.bash`: prepare charge-density-difference style workflows.

These scripts assume tools such as VASPKit, Slurm `sbatch`, and local templates already exist in the environment.

Some workflows also call two local helper scripts, `Elementordering.py` and `MAGMOM.py`, when generating POSCAR files and updating INCAR `MAGMOM` settings. Those files are intentionally not included in this repository for copyright reasons.

## Usage

Run from a calculation root directory or pass that directory explicitly:

```bash
bash workflows/calculation_setup/mkrf.bash /path/to/calculations
bash workflows/calculation_setup/mkdos.bash /path/to/calculations
bash workflows/calculation_setup/mkvib.bash /path/to/calculations
```

Several scripts also support environment-variable overrides for external commands such as `VASPKIT_BIN`, `SBATCH_BIN`, `PBS_TEMPLATE`, `RF_BUILDER_BIN`, `DOS_BUILDER_BIN`, and `VIB_BUILDER_BIN`.
