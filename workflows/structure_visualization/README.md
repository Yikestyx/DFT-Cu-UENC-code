# Structure Visualization

This directory contains the CIF rendering and PPT generation workflow.

- `pipeline_main.py`: main programmable entry point.
- `projection_overlap.py`: select a better lateral projection direction.
- `structure_view_renderer.py`: render structures with Python plotting.
- `vesta_controller.py` and `vesta_double_capture.ps1`: automate VESTA-based capture.
- `pythonrender.py`, `vestarender.py`, `xyzrender.py`: example runner scripts for the three rendering backends.
- `structure_ppt_generator.py`: generate PowerPoint slides from rendered images.

Install the Python dependencies from `requirements-visualization.txt` before using this workflow on a new machine.
