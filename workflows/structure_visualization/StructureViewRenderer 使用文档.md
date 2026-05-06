StructureViewRenderer 使用文档
=====================================

概述

StructureViewRenderer 是一个基于 pymatgen 和 matplotlib 的 Python 类，用于从 CIF 文件生成晶体结构的投影视图图像：俯视图（沿c轴）、主视图（沿b轴）、侧视图（沿a轴）。它支持两种输出模式：

全部保存：同时保存主视图和侧视图。

智能保存：结合 ProjectionOverlapAnalyzer 分析原子沿a轴和b轴投影的遮挡面积，仅保存遮挡更小的一个视图（主视图或侧视图）。这有助于自动选择视觉上更清晰的截图方向。

所有图像均以文件形式保存，不会弹出显示窗口，适合批量处理或集成到自动化流程中。

依赖环境

Python >= 3.7

必需库：

pymatgen (>=2023.0.0) 用于读取CIF文件，获取原子坐标和半径

matplotlib 用于绘制投影图

numpy 用于数值计算

智能模式额外依赖：

ase ProjectionOverlapAnalyzer 内部使用

projection_overlap 模块（需要您已实现 ProjectionOverlapAnalyzer 类）

安装命令：
pip install pymatgen matplotlib numpy ase

文件位置

将 StructureViewRenderer 类代码保存为 structure_view_renderer.py，并放置在 Python 可导入的路径下（例如当前工作目录或 site-packages）。同时确保 projection_overlap.py（包含 ProjectionOverlapAnalyzer）也在可导入路径中。

类初始化参数

init(self, cif_path, views_config="all", overlap_threshold=0.0, z_fractional_threshold=0.0, use_periodic=True, supercell=(3,3,3), radius_source="covalent", **analyzer_kwargs)

参数说明：

cif_path (str) : 必需，CIF文件的路径。

views_config (str) : 可选，默认 "all"。决定主视图和侧视图的保存策略。

"all" : 同时保存主视图和侧视图。

"best_one" : 仅保存遮挡面积较小的一个视图（主或侧）。

overlap_threshold (float) : 可选，默认0.0。传递给 ProjectionOverlapAnalyzer 的最小重叠面积阈值（埃^2）。

z_fractional_threshold (float) : 可选，默认0.0。传递给 ProjectionOverlapAnalyzer 的分数坐标c分量下限阈值，用于排除衬底原子。

use_periodic (bool) : 可选，默认True。是否考虑周期性边界条件（传递给 ProjectionOverlapAnalyzer）。

supercell (tuple of three ints) : 可选，默认(3,3,3)。超胞尺寸 (nx, ny, nz)，仅在 use_periodic=True 时生效。

radius_source (str) : 可选，默认 "covalent"。原子半径来源，"covalent" 或 "vdw"。

**analyzer_kwargs : 其他传递给 ProjectionOverlapAnalyzer 的关键字参数。

注意：当 views_config="best_one" 时，必须能够成功导入 ProjectionOverlapAnalyzer 并传入有效参数。

主要方法

render_views(self, output_dir=".", base_name="structure", dpi=300, figsize=(8,6))
生成并保存视图图像。

参数：

output_dir (str) : 输出目录，默认当前目录 "."。若目录不存在会自动创建。

base_name (str) : 输出文件的基础名，例如 "crystal" 会生成 crystal_top.png, crystal_front.png, crystal_side.png 等。

dpi (int) : 图像分辨率，默认300。

figsize (tuple of two floats) : 图像尺寸 (宽, 高)，单位为英寸，默认(8,6)。

返回值：无。但会在控制台打印保存的文件路径和遮挡分析信息（如果使用智能模式）。

内部辅助方法（通常无需直接调用）：

_get_atom_radius(self, element: str) -> float : 根据元素符号返回共价半径（埃），用于绘图时圆的大小。

_plot_projection(self, plane: str, output_path: str, dpi=300, figsize=(8,6)) : 绘制指定平面的投影并保存。

使用示例

示例1：基础用法 - 保存所有视图

from structure_view_renderer import StructureViewRenderer

初始化，使用默认配置保存全部视图
renderer = StructureViewRenderer(
cif_path="material.cif",
views_config="all"
)

生成图像，保存在 ./images 目录下，文件名以 "sample" 开头
renderer.render_views(output_dir="./images", base_name="sample", dpi=200)

输出文件：
./images/sample_top.png (俯视图)
./images/sample_front.png (主视图)
./images/sample_side.png (侧视图)

示例2：智能模式 - 根据遮挡分析仅保存一个视图

from structure_view_renderer import StructureViewRenderer

使用智能模式，并设置阈值以排除衬底原子（c分数坐标 > 0.5 的表面原子）
renderer = StructureViewRenderer(
cif_path="surface_adsorbate.cif",
views_config="best_one",
z_fractional_threshold=0.5, # 只分析表面原子
overlap_threshold=0.01,
use_periodic=True,
supercell=(3,3,3),
radius_source="covalent"
)

渲染，程序会自动计算a方向和b方向的遮挡面积，并保存遮挡更少的那个视图
renderer.render_views(output_dir="./best_view", base_name="optimized")

控制台输出示例：
a 方向遮挡面积: 23.456 Å²
b 方向遮挡面积: 15.789 Å²
推荐方向: b
主视图（遮挡更少）已保存: ./best_view/optimized_front.png

示例3：仅获取数值（不使用渲染）

如果您只想获得最佳方向而不实际生成图像，可以直接使用 ProjectionOverlapAnalyzer：
from projection_overlap import ProjectionOverlapAnalyzer

analyzer = ProjectionOverlapAnalyzer("crystal.cif")
best = analyzer.get_best_direction()
print(best['best_direction']) # 输出 'a' 或 'b'

但本类的主要目的是生成图像。

视图与投影方向的对应关系

俯视图 (Top View) : 沿 c 轴投影，显示 ab 平面。对应图像文件后缀 "_top.png"。

主视图 (Front View) : 沿 b 轴投影，显示 ac 平面。对应图像文件后缀 "_front.png"。

侧视图 (Side View) : 沿 a 轴投影，显示 bc 平面。对应图像文件后缀 "_side.png"。

遮挡分析的方向映射：

ProjectionOverlapAnalyzer 返回的 'a' 方向（视线沿 a 轴）对应本类的侧视图 (bc平面)。

返回的 'b' 方向（视线沿 b 轴）对应本类的主视图 (ac平面)。

因此，当智能模式选择 'a' 时，会保存侧视图；选择 'b' 时，会保存主视图。

注意事项

原子半径处理：

绘图时使用 pymatgen 提供的共价半径（单位埃），并乘以 0.3 的缩放因子，以避免圆点过大重叠严重。您可以根据需要修改 _plot_projection 方法中的 "radius * 0.3" 部分。

若某元素的共价半径在 pymatgen 中缺失，会回退为 0.5 埃。

周期性边界：

智能模式下的遮挡分析（ProjectionOverlapAnalyzer）支持超胞近似，但绘图本身始终使用原始晶胞（不扩展）。这符合通常的可视化需求：分析时考虑周期性以精确计算遮挡，绘制时展示原始晶胞即可。

图像不显示：

所有绘图均通过 plt.savefig 保存后立即关闭，不会弹出 matplotlib 窗口。如需调试，可以注释掉 plt.close(fig) 并添加 plt.show()。

性能考虑：

对于包含大量原子的结构（例如超胞后 >500 原子），遮挡分析的计算量较大。可通过减小 supercell 或设置 use_periodic=False 来加速。绘制图像本身通常很快。

颜色方案：

原子颜色使用 pymatgen 的默认配色（通过 StructurePlot.get_colorscheme()）。您可以在 _plot_projection 中修改 color_dict 来自定义。

文件覆盖：

如果输出目录中已存在同名文件，render_views 会直接覆盖，不会发出警告。请注意提前备份或使用不同的 base_name。

错误处理：

若 views_config="best_one" 但 ProjectionOverlapAnalyzer 未正确导入或初始化失败，会抛出异常。请确保 projection_overlap 模块可用。