import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from projection_overlap import ProjectionOverlapAnalyzer
from structure_ppt_generator import StructurePPTGenerator
from structure_view_renderer import StructureViewRenderer

METAL_ELEMENTS = ['Pt', 'Pd', 'Au', 'Ag', 'Cu', 'Ni', 'Co', 'Fe']

def _validate_engine(engine: str) -> str:
    """校验渲染引擎参数。"""
    engine_norm = str(engine).strip().lower()
    if engine_norm not in ("python", "vesta", "xyzrender"):
        raise ValueError("engine 参数必须是 'python'、'vesta' 或 'xyzrender'")
    return engine_norm


def _validate_ppt_generator(ppt_generator: str) -> str:
    """校验 PPT 生成器类型。"""
    gen = str(ppt_generator).strip().lower()
    if gen not in ("structure", "selected"):
        raise ValueError("ppt_generator 必须是 'structure' 或 'selected'")
    return gen


def _validate_direction_mapping(direction_to_view: Dict[str, str]) -> Dict[str, str]:
    """校验最佳方向到视图的映射。"""
    if not isinstance(direction_to_view, dict):
        raise ValueError("direction_to_view 必须是字典，例如 {'a': 'side', 'b': 'front'}")
    if "a" not in direction_to_view or "b" not in direction_to_view:
        raise ValueError("direction_to_view 必须包含键 'a' 和 'b'")
    if direction_to_view["a"] not in ("front", "side") or direction_to_view["b"] not in ("front", "side"):
        raise ValueError("direction_to_view 的值必须是 'front' 或 'side'")
    return direction_to_view


def _normalize_path_input(path_value: Optional[str]) -> Optional[str]:
    """
    规范化路径输入，尽量兼容直接粘贴的 Windows 路径：
    - 去除首尾空白与包裹引号
    - 修复被 Python 转义后的控制字符（如 \t、\n 被解释成制表/换行）
    - 统一分隔符为反斜杠
    """
    if path_value is None:
        return None

    s = str(path_value).strip().strip('"').strip("'")
    if not s:
        return s

    escaped_ctrl = {
        "\t": "\\t",
        "\n": "\\n",
        "\r": "\\r",
        "\b": "\\b",
        "\f": "\\f",
        "\v": "\\v",
        "\a": "\\a",
    }
    if any(ch in s for ch in escaped_ctrl):
        s = "".join(escaped_ctrl.get(ch, ch) for ch in s)

    s = s.replace("/", "\\")
    return s


def _read_products_from_excel(excel_path: str, sheet_name: str, product_col: str) -> List[str]:
    """从 Excel 指定工作表读取结构名列表。"""
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    if product_col not in df.columns:
        raise ValueError(f"工作表 '{sheet_name}' 中未找到列 '{product_col}'")

    values: List[str] = []
    for raw in df[product_col].tolist():
        if pd.isna(raw):
            continue
        name = str(raw).strip()
        if name:
            values.append(name)
    return values


def _resolve_cif_path(cif_root: Path, product: str) -> Tuple[Optional[Path], str]:
    """
    在目录中解析 CIF 路径。
    优先尝试原名，再尝试去掉开头 '*' 的名称。
    返回 (路径或None, 用于输出命名的基础名)。
    """
    candidates = [product]
    if product.startswith("*"):
        candidates.append(product[1:])

    for name in candidates:
        p = cif_root / f"{name}.cif"
        if p.exists():
            base_name = product[1:] if product.startswith("*") else product
            return p, base_name

    base_name = product[1:] if product.startswith("*") else product
    return None, base_name


def _choose_views(
    cif_path: Path,
    save_both_views: bool,
    auto_best_direction: bool,
    direction_to_view: Dict[str, str],
    z_fractional_threshold: float,
    manual_side_view: Optional[str] = None,
) -> Tuple[List[str], Optional[Dict[str, Any]]]:
    """
    根据参数决定要保存的视图。

    规则：
    - save_both_views=True: 保存 top/front/side。
    - save_both_views=False 且 auto_best_direction=True: 保存 top + (front/side 其一)。
    - save_both_views=False 且 auto_best_direction=False: 保存 top + front。
    """
    if save_both_views:
        if auto_best_direction:
            best = ProjectionOverlapAnalyzer(str(cif_path)).get_best_direction()
            return ["top", "front", "side"], best
        return ["top", "front", "side"], None

    if auto_best_direction:
        best = ProjectionOverlapAnalyzer(str(cif_path)).get_best_direction()
        best_view = direction_to_view[best["best_direction"]]
        return ["top", best_view], best

    chosen_view = manual_side_view if manual_side_view is not None else "front"
    return ["top", chosen_view], None


def _render_python_views(cif_path: Path, views: List[str], output_dir: Path, base_name: str) -> None:
    """使用 Python 渲染器生成结构图。"""
    renderer = StructureViewRenderer(str(cif_path))
    renderer.render_views(views=views, output_dir=str(output_dir), base_name=base_name)


def _render_xyzrender_views(
    cif_path: Path,
    views: List[str],
    output_dir: Path,
    base_name: str,
    xyzrender_cmd: Optional[str] = None,
) -> None:
    """
    使用 xyzrender 渲染结构图。

    视图映射：
    - top:   axis=001（沿 c 轴观察）
    - front: axis=010（沿 b 轴观察）
    - side:  axis=100（沿 a 轴观察）
    """
    axis_map = {"top": "001", "front": "110", "side": "100"}
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd_name = xyzrender_cmd or shutil.which("xyzrender") or "xyzrender"
    for view in views:
        if view not in axis_map:
            raise ValueError(f"xyzrender 不支持视图: {view}")

        out_file = output_dir / f"{base_name}_{view}.png"
        cmd = [
            cmd_name,
            str(cif_path),
            "-o",
            str(out_file),
            "--axis",
            axis_map[view],
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "未找到 xyzrender 命令。请先安装：pip install 'xyzrender[cif]'，并确认命令已加入 PATH。"
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            raise RuntimeError(f"xyzrender 渲染失败: {stderr or exc}") from exc


def _validate_vesta_click_config(vesta_clicks: Optional[Dict[str, Any]], require_both_side_front: bool) -> Dict[str, Any]:
    """校验 VESTA 点击配置。"""
    if not isinstance(vesta_clicks, dict):
        raise ValueError("当 engine='vesta' 时，vesta_clicks 必须提供为字典")

    required = ["top", "front", "side"] if require_both_side_front else ["top", "front"]
    for view in required:
        if view not in vesta_clicks:
            raise ValueError(f"vesta_clicks 缺少 '{view}' 配置")
        cfg = vesta_clicks[view]
        if "position" not in cfg:
            raise ValueError(f"vesta_clicks['{view}'] 必须包含 'position'，例如 (x, y)")

    if "view_screenshot_regions" in vesta_clicks and vesta_clicks["view_screenshot_regions"] is not None:
        if not isinstance(vesta_clicks["view_screenshot_regions"], dict):
            raise ValueError("vesta_clicks['view_screenshot_regions'] 必须是字典")

    return vesta_clicks


def _render_vesta_views(
    cif_path: Path,
    views: List[str],
    output_dir: Path,
    vesta_path: str,
    direction_to_view: Dict[str, str],
    save_both_views: bool,
    auto_best_direction: bool,
    vesta_clicks: Dict[str, Any],
) -> None:
    """使用 VESTA 自动化截图。"""
    from vesta_controller import VESTAController

    require_both = save_both_views or auto_best_direction
    cfg = _validate_vesta_click_config(vesta_clicks, require_both_side_front=require_both)

    if save_both_views:
        views_mode = "both"
        auto_select_best = False
    elif auto_best_direction:
        views_mode = "front_only"
        auto_select_best = True
    else:
        views_mode = "front_only"
        auto_select_best = False

    controller = VESTAController(
        cif_path=str(cif_path),
        vesta_path=vesta_path,
        views_mode=views_mode,
        auto_select_best=auto_select_best,
        direction_to_view=direction_to_view,
    )

    for view in ("top", "front", "side"):
        if view in cfg:
            view_pos = tuple(cfg[view]["position"])
            click_count = int(cfg[view].get("click_count", 1))
            controller.set_view_click(view, view_pos, click_count)

    if "rotation" in cfg and cfg["rotation"] and "position" in cfg["rotation"]:
        controller.set_rotation_click(tuple(cfg["rotation"]["position"]))

    if "extra_rotation_clicks" in cfg and cfg["extra_rotation_clicks"]:
        front_rot = int(cfg["extra_rotation_clicks"].get("front", 0))
        side_rot = int(cfg["extra_rotation_clicks"].get("side", 0))
        controller.set_extra_rotation_clicks(front=front_rot, side=side_rot)

    if "screenshot_region" in cfg and cfg["screenshot_region"]:
        controller.set_screenshot_region(tuple(cfg["screenshot_region"]))

    if "view_screenshot_regions" in cfg and cfg["view_screenshot_regions"]:
        for view, region in cfg["view_screenshot_regions"].items():
            controller.set_view_screenshot_region(view, tuple(region))

    old_cwd = os.getcwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(str(output_dir))
    try:
        controller.run()
    finally:
        os.chdir(old_cwd)
        controller.close_vesta()

    suffix_to_keep = {f"_{v}.png" for v in views}
    for p in output_dir.glob(f"{cif_path.stem}_*.png"):
        if not any(p.name.endswith(sfx) for sfx in suffix_to_keep):
            try:
                p.unlink()
            except Exception:
                pass


def build_structure_ppt(
    engine: str,
    save_both_views: bool,
    auto_best_direction: bool,
    cif_dir: str,
    ppt_output_path: str,
    excel_path: str,
    sheet_name: str,
    vesta_path: Optional[str] = None,
    product_col: str = "产物",
    direction_to_view: Optional[Dict[str, str]] = None,
    vesta_clicks: Optional[Dict[str, Any]] = None,
    xyzrender_cmd: Optional[str] = None,
    structures_per_slide: int = 2,
    image_output_dir: Optional[str] = None,
    pair_capture_mode: bool = False,
    contcar_dir: Optional[str] = None,
    pair_labels: Tuple[str, str] = ("POSCAR", "CONTCAR"),
    generate_ppt: bool = True,
    ppt_generator: str = "structure",
    z_fractional_threshold: float = 0.0,manual_side_view: Optional[str] = None,
) -> Dict[str, Any]:
    """
    统一主函数：从 Excel 读取结构名，批量生成结构图并导出 PPT。

    参数
    ----------
    engine : str
        渲染引擎，`'python'`、`'vesta'` 或 `'xyzrender'`。
    save_both_views : bool
        是否同时保存主视图和侧视图。
    auto_best_direction : bool
        是否自动计算最佳侧向视图。
    cif_dir : str
        CIF 存放目录。按精确规则匹配：`{结构名}.cif`。
    ppt_output_path : str
        PPT 输出路径。
    excel_path : str
        Excel 文件路径。
    sheet_name : str
        读取的工作表名称。
    vesta_path : Optional[str]
        VESTA 可执行文件路径，仅 `engine='vesta'` 时必填。
    product_col : str
        结构名列名，默认值为 `"产物"`。
    direction_to_view : Optional[Dict[str, str]]
        最佳方向映射，默认 `{"a": "side", "b": "front"}`。
    vesta_clicks : Optional[Dict[str, Any]]
        VESTA 点击配置，仅 `engine='vesta'` 时必填。
    xyzrender_cmd : Optional[str]
        xyzrender 可执行命令名或绝对路径，仅 `engine='xyzrender'` 时可选。
    structures_per_slide : int
        每页 PPT 放置结构数（1/2/3）。
    image_output_dir : Optional[str]
        图片输出目录；未传时默认在 PPT 同级目录创建 `{ppt文件名}_images`。
    pair_capture_mode : bool
        是否启用 POSCAR/CONTCAR 成对截图模式。
    contcar_dir : Optional[str]
        CONTCAR 对应 CIF 目录，仅在 `pair_capture_mode=True` 时必填。
    pair_labels : Tuple[str, str]
        成对截图命名标签，默认 `(POSCAR, CONTCAR)`。
    generate_ppt : bool
        是否在截图完成后自动生成 PPT。
    ppt_generator : str
        使用哪个代码生成 PPT：
        - `structure`: 调用 StructurePPTGenerator
        - `selected`: 调用 create_ppt_from_selected.py
    """
    engine_norm = _validate_engine(engine)
    direction_map = _validate_direction_mapping(direction_to_view or {"a": "side", "b": "front"})
    ppt_generator_norm = _validate_ppt_generator(ppt_generator)

    if manual_side_view is not None and manual_side_view not in ('front', 'side'):
        raise ValueError("manual_side_view 必须是 'front' 或 'side'")

    cif_root = Path(_normalize_path_input(cif_dir)).expanduser().resolve()
    if not cif_root.is_dir():
        raise ValueError(f"cif_dir 不存在：{cif_root}")

    excel_abs = Path(_normalize_path_input(excel_path)).expanduser().resolve()
    if not excel_abs.is_file():
        raise ValueError(f"excel_path 不存在：{excel_abs}")

    ppt_abs = Path(_normalize_path_input(ppt_output_path)).expanduser().resolve()
    if image_output_dir:
        out_dir = Path(_normalize_path_input(image_output_dir)).expanduser().resolve()
    else:
        out_dir = ppt_abs.parent / f"{ppt_abs.stem}_images"
    out_dir.mkdir(parents=True, exist_ok=True)

    vesta_path_norm = _normalize_path_input(vesta_path) if vesta_path is not None else None
    if engine_norm == "vesta" and not vesta_path_norm:
        raise ValueError("当 engine='vesta' 时，vesta_path 必填")

    xyzrender_cmd_norm = _normalize_path_input(xyzrender_cmd) if xyzrender_cmd is not None else None

    contcar_root: Optional[Path] = None
    if pair_capture_mode:
        if not contcar_dir:
            raise ValueError("当 pair_capture_mode=True 时，contcar_dir 必填")
        contcar_root = Path(_normalize_path_input(contcar_dir)).expanduser().resolve()
        if not contcar_root.is_dir():
            raise ValueError(f"contcar_dir 不存在：{contcar_root}")
        if not isinstance(pair_labels, (tuple, list)) or len(pair_labels) != 2:
            raise ValueError("pair_labels 必须是长度为2的元组/列表，例如 ('POSCAR','CONTCAR')")

    products = _read_products_from_excel(str(excel_abs), sheet_name, product_col)

    report: Dict[str, Any] = {
        "渲染引擎": engine_norm,
        "结构总数": len(products),
        "处理成功列表": [],
        "缺失CIF跳过列表": [],
        "失败列表": [],
        "成对截图模式": pair_capture_mode,
    }

    for product in products:
        if pair_capture_mode:
            poscar_path, base_name = _resolve_cif_path(cif_root, product)
            contcar_path, _ = _resolve_cif_path(contcar_root, product)

            missing: List[str] = []
            if poscar_path is None:
                missing.append("POSCAR")
            if contcar_path is None:
                missing.append("CONTCAR")
            if missing:
                msg = f"结构 {product} 缺少: {', '.join(missing)}"
                print(f"[警告] {msg}")
                report["缺失CIF跳过列表"].append({"结构名": product, "原因": msg})
                continue

            capture_tasks = [(pair_labels[0], poscar_path), (pair_labels[1], contcar_path)]
        else:
            cif_path, base_name = _resolve_cif_path(cif_root, product)
            if cif_path is None:
                msg = f"未找到 CIF 文件：{(cif_root / f'{product}.cif')}"
                print(f"[警告] {msg}")
                report["缺失CIF跳过列表"].append({"结构名": product, "原因": msg})
                continue
            capture_tasks = [("", cif_path)]

        try:
            per_product_results = []
            for label, path_item in capture_tasks:
                views, best_info = _choose_views(
                    cif_path=path_item,
                    save_both_views=save_both_views,
                    auto_best_direction=auto_best_direction,
                    direction_to_view=direction_map,
                    z_fractional_threshold=z_fractional_threshold,
                    manual_side_view=manual_side_view,
                )

                output_name = f"{base_name}_{label}" if label else base_name
                if engine_norm == "python":
                    _render_python_views(path_item, views, out_dir, output_name)
                elif engine_norm == "xyzrender":
                    _render_xyzrender_views(path_item, views, out_dir, output_name, xyzrender_cmd=xyzrender_cmd_norm)
                else:
                    _render_vesta_views(
                        cif_path=path_item,
                        views=views,
                        output_dir=out_dir,
                        vesta_path=vesta_path_norm,
                        direction_to_view=direction_map,
                        save_both_views=save_both_views,
                        auto_best_direction=auto_best_direction,
                        vesta_clicks=vesta_clicks or {},
                    )
                    src_prefix = path_item.stem
                    for view in views:
                        src = out_dir / f"{src_prefix}_{view}.png"
                        dst = out_dir / f"{output_name}_{view}.png"
                        if src.exists() and src != dst:
                            if dst.exists():
                                dst.unlink()
                            src.rename(dst)

                per_product_results.append(
                    {
                        "标签": label if label else "SINGLE",
                        "CIF路径": str(path_item),
                        "输出前缀": output_name,
                        "保存视图": views,
                        "最佳方向分析": best_info,
                    }
                )

            report["处理成功列表"].append({"结构名": product, "结果": per_product_results})
            print(f"[完成] {product}，已输出 {len(per_product_results)} 组图像")
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            print(f"[错误] {product}：{msg}")
            report["失败列表"].append({"结构名": product, "原因": msg})

    if not report["处理成功列表"]:
        raise RuntimeError("没有可用于生成 PPT 的成功结构，已终止")

    if generate_ppt:
        generator = StructurePPTGenerator(str(out_dir), save_both_views=save_both_views)
        generator.generate_ppt(output_path=str(ppt_abs), structures_per_slide=structures_per_slide)

    report["汇总"] = {
        "成功数量": len(report["处理成功列表"]),
        "跳过数量": len(report["缺失CIF跳过列表"]),
        "失败数量": len(report["失败列表"]),
        "图片输出目录": str(out_dir),
        "PPT输出路径": str(ppt_abs) if generate_ppt else None,
        "已生成PPT": generate_ppt,
        "PPT生成器": ppt_generator_norm if generate_ppt else None,
    }
    print(f"[全部完成] {report['汇总']}")
    return report
