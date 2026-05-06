#!/usr/bin/env python3
"""
Description:
    Example entry-point script for running the structure-rendering pipeline with
    the xyzrender backend.
"""

from pipeline_main import build_structure_ppt


def main() -> None:
    report = build_structure_ppt(
        engine="xyzrender",
        save_both_views=False,
        auto_best_direction=False,
        pair_capture_mode=True,
        cif_dir=r"D:\lyf\calculation\couple\Cu\POSCAR\Cu5",
        contcar_dir=r"D:\lyf\calculation\couple\Cu\CONTCAR",
        ppt_output_path=r"D:\lyf\test\structures_vesta.pptx",
        excel_path=r"D:\lyf\test\test.xlsx",
        sheet_name="Sheet1",
        xyzrender_cmd="xyzrender",
        product_col="产物",
        structures_per_slide=1,
        image_output_dir=r"D:\lyf\test\image",
    )
    print(report["汇总"])


if __name__ == "__main__":
    main()
