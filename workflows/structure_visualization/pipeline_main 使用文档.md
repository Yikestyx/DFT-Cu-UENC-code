# pipeline_main 使用文档

## 1. 功能说明

`pipeline_main.py` 提供统一主函数 `build_structure_ppt(...)`，用于：

1. 从 Excel 指定 Sheet 的“产物”列读取结构名称。
2. 按 `{结构名}.cif` 在 CIF 目录中精确匹配文件。
3. 选择截图引擎（`python` 或 `vesta`）生成结构图。
4. 按参数决定是否同时保存主视图/侧视图，是否自动选择最佳方向。
5. 将所有生成图片汇总为 PPT。

## 2. 主函数签名

```python
build_structure_ppt(
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
) -> Dict[str, Any]
```

## 3. 参数说明

- `engine`
  - `"python"`：使用 `StructureViewRenderer` 绘图。
  - `"vesta"`：使用 `VESTAController` 自动化截图。
  - `"xyzrender"`：使用 `xyzrender` 命令行渲染（不改动 VESTA 流程）。
- `save_both_views`
  - `True`：保存 `top + front + side`。
  - `False`：保存 `top + 单个侧向视图`。
- `auto_best_direction`
  - `False`：单侧向模式下默认保存 `front`。
  - `True`：单侧向模式下自动在 `front/side` 中选遮挡更小的视图。
  - 当 `save_both_views=True` 时，此参数仅做分析记录，不影响输出数量。
- `cif_dir`：CIF 文件目录。
- `ppt_output_path`：PPT 输出路径。
- `excel_path`：Excel 文件路径。
- `sheet_name`：读取的工作表名。
- `vesta_path`：VESTA 程序路径（仅 `engine="vesta"` 必填）。
- `product_col`：结构名列名，默认 `"产物"`。
- `direction_to_view`：方向映射，默认 `{"a": "side", "b": "front"}`。
- `vesta_clicks`：VESTA 点击配置（仅 `engine="vesta"` 必填）。
  - 基础字段：
    - `top/front/side`: `{"position": (x, y), "click_count": n}`，视图按钮坐标和点击次数。
    - `rotation`: `{"position": (x, y)}`，旋转按钮坐标（可选）。
    - `extra_rotation_clicks`: `{"front": n1, "side": n2}`，截图前额外旋转次数（可选）。
  - 截图区域字段：
    - `screenshot_region`: 全局截图区域（可选）。
    - `view_screenshot_regions`: 分视图截图区域（可选，优先级高于 `screenshot_region`）。
      - 示例：`{"top": (...), "front": (...), "side": (...)}`。
      - 这样可分别给俯视图/主视图/侧视图设置不同截图区域。
- `structures_per_slide`：每页结构数，必须为 1/2/3。
- `xyzrender_cmd`：`xyzrender` 可执行命令名或绝对路径（可选）。
- `image_output_dir`：图片输出目录；为空时默认使用 `{ppt文件名}_images`。
- `pair_capture_mode`：是否启用 POSCAR/CONTCAR 成对截图模式。
- `contcar_dir`：CONTCAR 对应 CIF 目录（`pair_capture_mode=True` 时必填）。
- `pair_labels`：成对截图命名标签，默认 `("POSCAR", "CONTCAR")`。
- `generate_ppt`：是否自动生成 PPT；若只需出图可设为 `False`。
- `ppt_generator`：选择使用哪个代码生成 PPT：
  - `"structure"`：调用 `StructurePPTGenerator`（支持一页多个结构）
  - `"selected"`：调用 `create_ppt_from_selected.py` 的生成逻辑

## 4. Excel 和 CIF 命名要求

- Excel 中必须存在结构名列，默认列头：`产物`。
- 每个结构按 `{结构名}.cif` 精确匹配。
- 找不到 CIF 的结构会被跳过，并记录到返回报告中。

## 4.1 路径粘贴说明（Windows）

- 现在支持直接粘贴 Windows 复制的路径（包含首尾引号也可以）。
- 例如以下写法都可用：
  - `"D:\data\input\结构列表.xlsx"`
  - `'D:\data\cifs'`
  - `D:\data\output\structures.pptx`
- 代码内部会自动做路径清洗与规范化。
- 仍建议优先使用原始字符串写法（`r"..."`）或正斜杠路径，以避免 Python 字符串转义带来的歧义。

## 5. 使用示例（Python 引擎）

```python
from pipeline_main import build_structure_ppt

report = build_structure_ppt(
    engine="python",
    save_both_views=True,
    auto_best_direction=True,
    cif_dir=r"D:\\data\\cifs",
    ppt_output_path=r"D:\\data\\output\\structures.pptx",
    excel_path=r"D:\\data\\input\\结构列表.xlsx",
    sheet_name="Sheet1",
    product_col="产物",
    structures_per_slide=2,
    image_output_dir=r"D:\\data\\output\\screenshots",
)

print(report["汇总"])
```

## 5.2 使用 xyzrender 出图（不改 VESTA 流程）

```python
from pipeline_main import build_structure_ppt

report = build_structure_ppt(
    engine="xyzrender",
    save_both_views=False,
    auto_best_direction=False,
    cif_dir=r"D:\\data\\cifs",
    ppt_output_path=r"D:\\data\\output\\structures_xyzrender.pptx",
    excel_path=r"D:\\data\\input\\结构列表.xlsx",
    sheet_name="Sheet1",
    product_col="产物",
    xyzrender_cmd="xyzrender",  # 或 r"D:\\Python\\Scripts\\xyzrender.exe"
    structures_per_slide=2,
    image_output_dir=r"D:\\data\\output\\screenshots_xyzrender",
)

print(report["汇总"])
```

## 5.1 不使用智能选取面（auto_best_direction=False）

- 关闭智能选取面只需要设置：`auto_best_direction=False`。
- 此时行为：
  - `save_both_views=True`：保存 `top + front + side`
  - `save_both_views=False`：保存 `top + front`（固定主视图，不自动比较 side）

示例（Python 引擎，固定保存 top+front）：

```python
from pipeline_main import build_structure_ppt

report = build_structure_ppt(
    engine="python",
    save_both_views=False,
    auto_best_direction=False,  # 关闭智能选取面
    cif_dir=r"D:\\data\\cifs",
    ppt_output_path=r"D:\\data\\output\\structures_no_smart.pptx",
    excel_path=r"D:\\data\\input\\结构列表.xlsx",
    sheet_name="Sheet1",
    product_col="产物",
    structures_per_slide=2,
    image_output_dir=r"D:\\data\\output\\screenshots_no_smart",
)

print(report["汇总"])
```

## 6. 使用示例（VESTA 引擎）

```python
from pipeline_main import build_structure_ppt

vesta_clicks = {
    "top": {"position": (1000, 120), "click_count": 1},
    "front": {"position": (1100, 120), "click_count": 1},
    "side": {"position": (1200, 120), "click_count": 2},
    "rotation": {"position": (900, 300)},
    "extra_rotation_clicks": {"front": 0, "side": 2},
    "screenshot_region": (100, 100, 1200, 800),  # 全局兜底区域（可选）
    "view_screenshot_regions": {
        "top": (120, 120, 1000, 700),   # 俯视图区域
        "front": (80, 150, 980, 680),   # 主视图区域
        "side": (100, 160, 960, 660),   # 侧视图区域
    },
}

report = build_structure_ppt(
    engine="vesta",
    save_both_views=False,
    auto_best_direction=True,
    cif_dir=r"D:\\data\\cifs",
    ppt_output_path=r"D:\\data\\output\\structures_vesta.pptx",
    excel_path=r"D:\\data\\input\\结构列表.xlsx",
    sheet_name="Sheet1",
    vesta_path=r"C:\\Program Files\\VESTA\\VESTA.exe",
    product_col="产物",
    vesta_clicks=vesta_clicks,
    structures_per_slide=2,
    image_output_dir=r"D:\\data\\output\\screenshots_vesta",
)

print(report["汇总"])
```

## 6.1 同时获取 POSCAR 和 CONTCAR 图像

说明：
- 打开 `pair_capture_mode=True`
- 提供 `cif_dir`（POSCAR目录）和 `contcar_dir`（CONTCAR目录）
- 图片命名会自动变为：`{结构名}_POSCAR_top.png`、`{结构名}_CONTCAR_front.png` 等
- 若你后续用 `create_ppt_from_selected.py` 生成对比PPT，建议 `generate_ppt=False`，只出图

```python
from pipeline_main import build_structure_ppt

report = build_structure_ppt(
    engine="python",  # 或 "vesta"
    save_both_views=False,
    auto_best_direction=False,
    cif_dir=r"D:\\lyf\\calculation\\couple\\Cu\\POSCAR",
    contcar_dir=r"D:\\lyf\\calculation\\couple\\Cu\\CONTCAR",
    pair_capture_mode=True,
    pair_labels=("POSCAR", "CONTCAR"),
    generate_ppt=True,
    ppt_generator="structure",  # 或 "selected"
    ppt_output_path=r"D:\\lyf\\test\\unused_when_generate_false.pptx",
    excel_path=r"D:\\lyf\\test\\test.xlsx",
    sheet_name="Selected",
    product_col="产物",
    image_output_dir=r"D:\\lyf\\test\\Structure_Screenshots",
)

print(report["汇总"])
```

当你希望明确调用 `create_ppt_from_selected.py` 的排版逻辑时：

```python
report = build_structure_ppt(
    engine="python",
    save_both_views=False,
    auto_best_direction=False,
    cif_dir=r"D:\\lyf\\calculation\\couple\\Cu\\POSCAR",
    contcar_dir=r"D:\\lyf\\calculation\\couple\\Cu\\CONTCAR",
    pair_capture_mode=True,
    ppt_output_path=r"D:\\lyf\\test\\Selected_Structures.pptx",
    excel_path=r"D:\\lyf\\test\\energy_analysis.xlsx",
    sheet_name="Selected",
    product_col="产物",
    image_output_dir=r"D:\\lyf\\test\\Structure_Screenshots",
    generate_ppt=True,
    ppt_generator="selected",
)
```

示例（VESTA 引擎，关闭智能选取面，固定保存 top+front）：

```python
from pipeline_main import build_structure_ppt

vesta_clicks = {
    "top": {"position": (1000, 120), "click_count": 1},
    "front": {"position": (1100, 120), "click_count": 1},
    "side": {"position": (1200, 120), "click_count": 2},  # 可保留，当前模式不会使用 side 截图
    "screenshot_region": (100, 100, 1200, 800),
}

report = build_structure_ppt(
    engine="vesta",
    save_both_views=False,
    auto_best_direction=False,  # 关闭智能选取面
    cif_dir=r"D:\\data\\cifs",
    ppt_output_path=r"D:\\data\\output\\structures_vesta_no_smart.pptx",
    excel_path=r"D:\\data\\input\\结构列表.xlsx",
    sheet_name="Sheet1",
    vesta_path=r"C:\\Program Files\\VESTA\\VESTA.exe",
    product_col="产物",
    vesta_clicks=vesta_clicks,
    structures_per_slide=2,
    image_output_dir=r"D:\\data\\output\\screenshots_vesta_no_smart",
)

print(report["汇总"])
```

## 7. 返回值说明

函数返回字典，主要字段：

- `渲染引擎`
- `结构总数`
- `处理成功列表`
- `缺失CIF跳过列表`
- `失败列表`
- `汇总`

其中 `汇总` 包含：`成功数量`、`跳过数量`、`失败数量`、`图片输出目录`、`PPT输出路径`。

## 8. 常见报错

- `engine 参数必须是 'python' 或 'vesta'`
- `当 engine='vesta' 时，vesta_path 必填`
- `工作表 '<sheet>' 中未找到列 '<产物列>'`
- `cif_dir 不存在` / `excel_path 不存在`
- `vesta_clicks 缺少 'top/front/side' 配置`
