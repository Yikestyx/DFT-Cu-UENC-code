# Result Collection

Scripts in this directory collect finished calculation outputs into summary files or organized result folders.

- `collect_all.bash`: run all supported collection steps in batch.
- `collect_workfunction.bash`: extract work-function related outputs.
- `collect_bandcenter.bash`: collect W d-band and coordination-atom p-band centers.
- `collect_chargediff.bash`: gather charge-density-difference files.
- `collect_tdospdos.bash`: gather TDOS and PDOS outputs.
- `myenergy.bash`: summarize total energy and, when available, vibrational free-energy correction.
- `chk.bash`: quick status/convergence inspection helper.

## Usage

Run from a calculation root directory or pass that directory explicitly.

```bash
bash workflows/result_collection/collect_all.bash /path/to/calculations
bash workflows/result_collection/chk.bash /path/to/calculations
bash workflows/result_collection/myenergy.bash /path/to/calculations
```

## Assumptions

- Structure folders live directly under the calculation root.
- Post-processing outputs use directories such as `RF/`, `RF/dos/`, or `RF/CFDH/`.
- External commands such as `vaspkit`, `energy`, `check`, and `check-DAV` are available in `PATH`.

For portability, several scripts now also support environment-variable overrides such as `VASPKIT_BIN`, `ENERGY_BIN`, `CHECK_BIN`, and `CHECK_DAV_BIN`.
