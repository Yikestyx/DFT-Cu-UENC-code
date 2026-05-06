#!/usr/bin/env python3
"""
Description:
    Example entry-point script for running the structure-rendering pipeline with
    the VESTA automation backend.
"""

from pipeline_main import build_structure_ppt


VESTA_CLICKS = {
    "top": {"position": (110, 90), "click_count": 1},
    "front": {"position": (20, 90), "click_count": 1},
    "side": {"position": (20, 90), "click_count": 1},
    "rotation": {"position": (440, 90)},
    "extra_rotation_clicks": {"front": 0, "side": 1},
    "screenshot_region": (100, 100, 1200, 800),
    "view_screenshot_regions": {
        "top": (1441, 510, 2465, 1281),
        "front": (1570, 272, 2341, 1520),
        "side": (1441, 272, 2465, 1520),
    },
}


def main() -> None:
    report = build_structure_ppt(
        engine="vesta",
        save_both_views=False,
        auto_best_direction=False,
        pair_capture_mode=True,
        vesta_clicks=VESTA_CLICKS,
        cif_dir=r"D:\lyf\calculation\couple\Cu\POSCAR\Cu5",
        contcar_dir=r"D:\lyf\calculation\couple\Cu\CONTCAR",
        ppt_output_path=r"D:\lyf\test\structures_vesta.pptx",
        excel_path=r"D:\lyf\test\test.xlsx",
        sheet_name="Sheet1",
        vesta_path=r"C:\Users\logic\Desktop\VESTA-win64\VESTA.exe",
        product_col="产物",
        structures_per_slide=2,
        image_output_dir=r"D:\lyf\test\image",
        z_fractional_threshold=0.4,
    )
    print(report["汇总"])


if __name__ == "__main__":
    main()
