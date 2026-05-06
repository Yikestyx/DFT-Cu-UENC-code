ProjectionOverlapAnalyzer 使用文档

概述
ProjectionOverlapAnalyzer 是一个用于分析晶体结构（CIF 格式）在 a 方向与 b 方向投影下原子间遮挡程度的 Python 类。
通过计算投影平面上原子（视为圆形）的交叠面积，量化视觉遮挡程度，并返回遮挡更小的方向，便于决定结构可视化时的最佳截图视角。

核心功能：
读取 CIF 文件，提取原子坐标与晶胞信息。
支持通过分数坐标 c 分量阈值排除衬底原子（如催化剂本体）。
计算沿 a 轴和沿 b 轴投影的总原子遮挡面积。
比较两个方向，返回遮挡更少的方向及相关数值。
可选考虑周期性边界条件（通过构建超胞）。

---
依赖环境
Python ≥ 3.7
必需：numpy, ase（Atomic Simulation Environment）
可选：mendeleev（如需使用范德华半径）

安装命令：
pip install numpy ase

---
类定义与文件位置
类名：ProjectionOverlapAnalyzer
所在文件建议命名：projection_overlap.py

使用前需将包含该类的文件置于 Python 可导入的路径下。

---
初始化参数
ProjectionOverlapAnalyzer(
    cif_path,
    z_fractional_threshold=0.0,
    overlap_threshold=0.0,
    use_periodic=True,
    supercell=(3,3,3),
    radius_source='covalent'
)

参数说明：
cif_path：字符串类型，必填，CIF 文件的路径（相对或绝对）。
z_fractional_threshold：浮点数类型，默认值0.0，分数坐标 c 分量的下限阈值。仅 c 大于该值的原子参与遮挡计算，用于排除本体原子。取值范围通常0~1。
overlap_threshold：浮点数类型，默认值0.0，最小重叠面积阈值（Å²）。重叠小于该值的原子对被忽略，可过滤微小接触。
use_periodic：布尔类型，默认值True，是否考虑周期性边界条件。若为True，通过构建超胞近似跨晶胞原子间的遮挡。
supercell：三个整数组成的元组，默认值(3,3,3)，超胞在 a、b、c 方向的重复数。推荐奇数，中心为原胞。增大可提高精度但增加计算量。
radius_source：字符串类型，默认值'covalent'，原子半径来源。可选'covalent'（ASE 共价半径）或'vdw'（mendeleev 范德华半径）。

---
主要方法
1. get_overlap_areas()
计算并返回 a 方向和 b 方向的遮挡总面积。

返回值：两个浮点数组成的元组
第一个元素：沿 a 方向投影的遮挡面积（Å²）
第二个元素：沿 b 方向投影的遮挡面积（Å²）

示例：
area_a, area_b = analyzer.get_overlap_areas()
print(f"a方向遮挡面积: {area_a:.3f} Å²")
print(f"b方向遮挡面积: {area_b:.3f} Å²")

2. get_best_direction()
比较两个方向的遮挡面积，返回遮挡较小的方向及详细信息。

返回值：字典
包含以下键：
'best_direction'：字符串类型，'a'或'b'，表示遮挡更少的方向。
'area_a'：浮点数类型，a 方向遮挡面积（Å²）。
'area_b'：浮点数类型，b 方向遮挡面积（Å²）。
'difference'：浮点数类型，两个方向遮挡面积的差值（较大值减去较小值）。

示例：
result = analyzer.get_best_direction()
if result['best_direction'] == 'a':
    print("推荐沿 a 轴方向截图。")
else:
    print("推荐沿 b 轴方向截图。")
print(f"遮挡面积差: {result['difference']:.3f} Å²")

3. analyze()
在控制台打印详细分析报告，包括原子筛选数量、各方向遮挡面积及最佳方向。

返回值：无

示例：
analyzer.analyze()

输出示例：
分析文件: example.cif
分数坐标 c > 0.5 的原子数: 12/48
沿 a 方向投影总遮挡面积: 23.456 Å²
沿 b 方向投影总遮挡面积: 15.789 Å²
遮挡更少的方向: b (相差 7.667 Å²)

---
使用示例
示例 1：基础用法
from projection_overlap import ProjectionOverlapAnalyzer

analyzer = ProjectionOverlapAnalyzer(
    cif_path="structure.cif",
    z_fractional_threshold=0.5,   # 仅分析表面吸附原子
    overlap_threshold=0.01
)

# 获取最佳截图方向
best = analyzer.get_best_direction()
print(f"最佳方向: {best['best_direction']}")

示例 2：完整配置
analyzer = ProjectionOverlapAnalyzer(
    cif_path="MOF.cif",
    z_fractional_threshold=0.0,        # 分析全部原子
    overlap_threshold=0.1,
    use_periodic=True,
    supercell=(5,5,3),                 # 较大超胞以精确处理周期性
    radius_source='vdw'                # 使用范德华半径
)

analyzer.analyze()

示例 3：仅获取数值用于自定义逻辑
analyzer = ProjectionOverlapAnalyzer("crystal.cif")
area_a, area_b = analyzer.get_overlap_areas()

if area_a < area_b:
    view_direction = "a"
else:
    view_direction = "b"

# 将 view_direction 传递给可视化工具（如 VESTA、ASE GUI）

---
原子半径说明
covalent（默认）：使用 ASE 内置的共价半径表。缺失元素回退为 1.5 Å。
vdw：使用 mendeleev 库的范德华半径。需安装 pip install mendeleev。缺失元素回退为 1.8 Å。
如需自定义半径，可继承类并重写 _get_atomic_radii() 方法。

---
注意事项
投影方向定义：
“a 方向投影”指视线沿晶胞 a 轴，原子投影到 bc 平面（仅保留 b、c 坐标）。
“b 方向投影”指视线沿晶胞 b 轴，原子投影到 ac 平面（仅保留 a、c 坐标）。
不计算 c 方向投影。

高度筛选：
z_fractional_threshold 使用分数坐标（0~1）。若 CIF 中表面位于 c 轴顶部，可将阈值设为略低于表面原子分数坐标的值（如 0.5）以排除本体。

周期性处理：
启用 use_periodic=True 时，超胞大小直接影响计算精度。对于分子晶体或小晶胞，(3,3,3) 通常足够；对于大晶胞可适当减小以节约时间。

计算复杂度：
总计算量与原子数平方成正比。若原子数过多（如超胞导致大于500原子），建议关闭周期性或减小超胞。

兼容性：
依赖 ASE 读取 CIF 文件，若 CIF 包含对称操作，ASE 会自动展开为 P1 对称性。