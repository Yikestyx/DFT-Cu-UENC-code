#!/usr/bin/env python3
"""
Description:
    Example entry-point script for running the structure-rendering pipeline with
    the Python plotting backend.
"""

from pipeline_main import build_structure_ppt


def main() -> None:
    report = build_structure_ppt(
        engine="python",
        save_both_views=True,
        auto_best_direction=False,
        cif_dir=r"D:\lyf\calculation\Cu-old\couple\Cu\CONTCAR",
        pair_capture_mode=False,
        ppt_output_path=r"D:\lyf\calculation\Cu-old\couple\Cu\structures.pptx",
        excel_path=r"D:\lyf\calculation\Cu-old\couple\Cu\energy_clean.xlsx",
        sheet_name="Sheet1",
        product_col="产物",
        image_output_dir=r"D:\lyf\calculation\Cu-old\couple\Cu\image",
        structures_per_slide=3,
        z_fractional_threshold=0.4,
        generate_ppt=False,
    )
    print(report["汇总"])


if __name__ == "__main__":
    main()
