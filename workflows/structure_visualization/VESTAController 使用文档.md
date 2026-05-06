VESTAController 使用文档
================================================================================

一、概述

VESTAController 是一个 Python 类，通过模拟鼠标点击自动控制 VESTA 软件打开 CIF 文件、切换视图（俯视图、主视图、侧视图）并截图。

主要功能：

俯视图始终截取。

可选择截取主视图和/或侧视图。

支持自动判断主/侧视图中哪个方向遮挡更少（需配合 ProjectionOverlapAnalyzer）。

支持在截图前执行额外次数的旋转点击（用于调整视角）。

二、安装依赖

需要安装以下 Python 库：
pip install pyautogui pillow pygetwindow ase

如果使用自动遮挡判断功能，还需安装 mendeleev（可选）并确保 projection_overlap.py 文件可导入。

三、类初始化参数

class VESTAController(cif_path, vesta_path="VESTA", views_mode="both", auto_select_best=False, direction_to_view=None)

参数说明：

cif_path : CIF 文件的完整路径（字符串）

vesta_path : VESTA 可执行文件路径，若已加入环境变量可只写 "VESTA"（字符串）

views_mode : 需要截取的视图模式，可选：
"both" : 截取俯视图 + 主视图 + 侧视图
"front_only" : 截取俯视图 + 主视图
"side_only" : 截取俯视图 + 侧视图

auto_select_best: 布尔值，仅在 views_mode 为 "front_only" 或 "side_only" 时有效。
若为 True，会调用 ProjectionOverlapAnalyzer 自动选择遮挡更少的方向，
并覆盖用户指定的 only 方向。

direction_to_view: 字典，将遮挡分析返回的 'a'/'b' 映射到 VESTA 视图名称。
默认 {"a": "front", "b": "side"}。

四、主要方法

set_view_click(view, position, click_count=1)
设置某个视图切换所需的点击参数。

view : 视图名称，可选 "top", "front", "side"

position : 屏幕坐标元组 (x, y)

click_count: 需要点击的次数（例如侧视图可能需要点两次）

set_rotation_click(position)
设置旋转视角的点击位置（用于截图前的额外旋转）。

position: 屏幕坐标元组 (x, y)

set_extra_rotation_clicks(front=0, side=0)
设置主视图和侧视图在截图前需要额外旋转点击的次数。

front: 主视图截图前的旋转次数

side : 侧视图截图前的旋转次数

set_screenshot_region(region)
设置截图区域。

region: 元组，支持两种格式：
(left, top, width, height)
(left, top, right, bottom) （自动转换）

run()
执行完整的自动截图流程：启动 VESTA，截取俯视图，然后根据配置截取其他视图并保存。

五、输出文件命名

截图自动保存为：
{样本名}_top.png
{样本名}_front.png （如果截取主视图）
{样本名}_side.png （如果截取侧视图）
其中“样本名”为 CIF 文件名去掉 .cif 后缀。

六、使用示例

示例1：同时截取俯视图、主视图、侧视图，无额外旋转

controller = VESTAController(
cif_path="C:/data/sample1.cif",
vesta_path="C:/Program Files/VESTA/VESTA.exe",
views_mode="both"
)

设置切换点击位置（坐标需提前用 pyautogui.mouseInfo() 获取）
controller.set_view_click("top", (0,0), 1) # 占位，实际不会点击
controller.set_view_click("front", (1200,150), 1)
controller.set_view_click("side", (1300,150), 2)

设置截图区域（可选）
controller.set_screenshot_region((100, 200, 800, 600))
controller.run()

示例2：只截取一个视图，自动选择遮挡更少的方向，并在截图前旋转2次

controller = VESTAController(
cif_path="C:/data/sample2.cif",
views_mode="side_only", # 名义上只想要侧视图
auto_select_best=True # 实际会根据遮挡选择 front 或 side
)
controller.set_view_click("top", (0,0), 1)
controller.set_view_click("front", (1200,150), 1)
controller.set_view_click("side", (1300,150), 2)

设置旋转点击位置
controller.set_rotation_click((1250, 200))

主视图截图前不旋转，侧视图截图前旋转2次
controller.set_extra_rotation_clicks(front=0, side=2)
controller.set_screenshot_region((100, 200, 800, 600))
controller.run()

七、注意事项

屏幕坐标获取：运行 python -c "import pyautogui; pyautogui.mouseInfo()" 打开坐标工具。

切换视图的点击次数和位置需要根据实际 VESTA 界面确定（例如主视图按钮点1次，侧视图可能需要点2次）。

等待时间（如启动等待、点击后等待）已在类内部硬编码，如果计算机较慢可修改源码中的 time.sleep 值。

自动遮挡判断需要安装 ase 库，并将 ProjectionOverlapAnalyzer 类所在的 projection_overlap.py 文件放在 Python 可导入路径下。

旋转点击功能需要指定旋转按钮的屏幕坐标，且旋转次数和方向由用户自行控制（类只负责点击指定次数）。