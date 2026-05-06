# projection_overlap.py
import numpy as np
from math import acos, sqrt, pi
from ase.io import read
from ase.data import covalent_radii, atomic_numbers

class ProjectionOverlapAnalyzer:
    """
    读取 CIF 文件，计算 a 方向与 b 方向投影中原子间的遮挡总面积。

    参数
    ----------
    cif_path : str
        CIF 文件路径。
    z_fractional_threshold : float, 可选
        分数坐标 c 分量的最小阈值。仅当原子的分数坐标 c 值大于此阈值时才参与遮挡计算。
        用于排除催化剂本体原子。默认 0.0 表示包含全部原子。
    overlap_threshold : float, 可选
        最小重叠面积阈值 (Å²)，重叠小于该值的原子对被忽略。默认 0.0。
    use_periodic : bool, 可选
        是否考虑周期性边界条件（通过构建超胞近似）。默认 True。
    supercell : tuple, 可选
        超胞重复数 (na, nb, nc)，推荐奇数以保证中心为原胞。默认 (3, 3, 3)。
    radius_source : str, 可选
        原子半径来源，支持 'covalent'（共价半径，默认）或 'vdw'（范德华半径，需 mendeleev 库）。

    方法
    -------
    get_overlap_areas()
        返回 (area_a, area_b) 元组，单位为 Å²。
    get_best_direction()
        返回字典，包含 'best_direction', 'area_a', 'area_b', 'difference'。
    analyze()
        在控制台打印详细报告。
    """

    def __init__(self, cif_path, z_fractional_threshold=0.0,
                 overlap_threshold=0.0, use_periodic=True,
                 supercell=(3,3,3), radius_source='covalent'):
        self.cif_path = cif_path
        self.z_frac_threshold = z_fractional_threshold
        self.overlap_threshold = overlap_threshold
        self.use_periodic = use_periodic
        self.supercell = supercell
        self.radius_source = radius_source

        # 读取结构
        self.atoms = read(cif_path)
        self.positions = self.atoms.get_positions()
        self.symbols = self.atoms.get_chemical_symbols()
        self.cell = self.atoms.cell.array
        self.frac_coords = self.atoms.get_scaled_positions()

        # 原子半径
        self.radii = self._get_atomic_radii()

        # 高度筛选
        self.mask = self.frac_coords[:, 2] > self.z_frac_threshold
        self.filtered_positions = self.positions[self.mask]
        self.filtered_radii = self.radii[self.mask]

    def _get_atomic_radii(self):
        if self.radius_source.lower() == 'covalent':
            radii = []
            for sym in self.symbols:
                try:
                    radii.append(covalent_radii[atomic_numbers[sym]])
                except:
                    radii.append(1.5)
            return np.array(radii)
        elif self.radius_source.lower() == 'vdw':
            try:
                from mendeleev import element
                radii = [element(sym).vdw_radius for sym in self.symbols]
                radii = [r if r is not None else 1.8 for r in radii]
                return np.array(radii)
            except ImportError:
                raise ImportError("使用范德华半径需要安装 mendeleev 库。")
        else:
            raise ValueError("radius_source 必须为 'covalent' 或 'vdw'")

    @staticmethod
    def _circle_overlap_area(r1, r2, d):
        if d >= r1 + r2:
            return 0.0
        if d <= abs(r1 - r2):
            return pi * min(r1, r2)**2
        term1 = r1**2 * acos((d**2 + r1**2 - r2**2) / (2 * d * r1))
        term2 = r2**2 * acos((d**2 + r2**2 - r1**2) / (2 * d * r2))
        term3 = 0.5 * sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))
        return term1 + term2 - term3

    def _project_to_plane(self, positions, drop_axis):
        if drop_axis == 0:      # 沿 a 方向 -> bc 平面
            return positions[:, 1:]
        elif drop_axis == 1:    # 沿 b 方向 -> ac 平面
            return positions[:, [0, 2]]
        else:
            raise ValueError("drop_axis 只能为 0 (a方向) 或 1 (b方向)")

    def _total_overlap_for_direction(self, drop_axis):
        if len(self.filtered_positions) < 2:
            return 0.0

        positions = self.filtered_positions
        radii = self.filtered_radii

        if self.use_periodic:
            na, nb, nc = self.supercell
            offsets = np.array([[i, j, k]
                                for i in range(-(na//2), na//2 + 1)
                                for j in range(-(nb//2), nb//2 + 1)
                                for k in range(-(nc//2), nc//2 + 1)])
            all_positions = []
            all_radii = []
            for offset in offsets:
                if np.all(offset == 0):
                    all_positions.append(positions)
                    all_radii.append(radii)
                else:
                    shift = offset @ self.cell
                    all_positions.append(positions + shift)
                    all_radii.append(radii)
            positions = np.vstack(all_positions)
            radii = np.hstack(all_radii)

        proj = self._project_to_plane(positions, drop_axis)
        n = len(positions)
        total = 0.0

        for i in range(n):
            for j in range(i+1, n):
                d = np.linalg.norm(proj[i] - proj[j])
                overlap = self._circle_overlap_area(radii[i], radii[j], d)
                if overlap > self.overlap_threshold:
                    total += overlap

        return total

    def get_overlap_areas(self):
        """返回 (area_a, area_b) 遮挡面积元组（Å²）。"""
        area_a = self._total_overlap_for_direction(drop_axis=0)
        area_b = self._total_overlap_for_direction(drop_axis=1)
        return area_a, area_b

    def get_best_direction(self):
        """
        比较 a 与 b 方向的遮挡面积，返回遮挡较小的方向及详细信息。

        返回
        -------
        dict
            {
                'best_direction': 'a' 或 'b',
                'area_a': float,
                'area_b': float,
                'difference': float
            }
        """
        area_a, area_b = self.get_overlap_areas()
        if area_a <= area_b:
            best = 'a'
            diff = area_b - area_a
        else:
            best = 'b'
            diff = area_a - area_b
        return {
            'best_direction': best,
            'area_a': area_a,
            'area_b': area_b,
            'difference': diff
        }

    def analyze(self):
        """在控制台打印分析报告。"""
        result = self.get_best_direction()
        print(f"分析文件: {self.cif_path}")
        print(f"分数坐标 c > {self.z_frac_threshold} 的原子数: {np.sum(self.mask)}/{len(self.atoms)}")
        print(f"沿 a 方向投影总遮挡面积: {result['area_a']:.3f} Å²")
        print(f"沿 b 方向投影总遮挡面积: {result['area_b']:.3f} Å²")
        print(f"遮挡更少的方向: {result['best_direction']} (相差 {result['difference']:.3f} Å²)")