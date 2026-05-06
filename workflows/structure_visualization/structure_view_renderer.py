import os
import matplotlib.pyplot as plt
from pymatgen.core import Structure
from pymatgen.io.cif import CifParser
from pymatgen.io.ase import AseAtomsAdaptor
from ase.visualize.plot import plot_atoms
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pymatgen.io.cif")


class StructureViewRenderer:
    """
    使用 ASE 的 plot_atoms（与参考代码完全相同的方式）渲染 CIF 文件，
    生成指定视图的图像（俯视图、主视图、侧视图）。
    """

    def __init__(self, cif_path: str):
        parser = CifParser(cif_path)
        self.structure = parser.parse_structures(primitive=False)[0]
        # 与参考代码中 get_ase_atoms 方法完全一致
        self.ase_atoms = AseAtomsAdaptor().get_atoms(self.structure)

    def _plot_view(self, view: str, output_path: str, dpi: int = 300, figsize: tuple = (8, 6)):
        rotation_map = {
            'top':    '0x,0y,0z',   # 俯视图
            'front':  '270x,90y',        # 主视图（ac平面）
            'side':   '270x,180y'         # 侧视图（bc平面）
        }
        if view not in rotation_map:
            raise ValueError(f"无效视图: {view}，可选 'top', 'front', 'side'")
        rotation = rotation_map[view]

        # 创建单图，尺寸与参考代码中的子图一致（参考中单个子图约 3x3 英寸，此处可自定义）
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        # 核心调用：与参考代码中的 plot_atoms(ase_atoms, ax, rotation=...) 完全相同
        plot_atoms(self.ase_atoms, ax, rotation=rotation)
        #ax.set_axis_off()
        # 设置标题（与参考代码风格一致）
        title_map = {
            'top':    'Top View (along c)',
            'front':  'Front View (along a)',
            'side':   'Side View (along b)'
        }
        ax.set_title(title_map[view])

        # 参考代码中没有显式设置刻度，但 plot_atoms 内部已隐藏坐标轴
        # 为了完全一致，不额外调用 set_xticks([]) 等
        # 但参考代码中某些地方（如 plot_overview）有设置，为统一，这里保持与主要方法一致：不做额外处理

        plt.tight_layout()  # 参考代码中均有调用
        plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)

    def render_views(self, views: list, output_dir: str = ".", base_name: str = "structure",
                     dpi: int = 300, figsize: tuple = (8, 6)):
        os.makedirs(output_dir, exist_ok=True)
        for view in views:
            output_path = os.path.join(output_dir, f"{base_name}_{view}.png")
            self._plot_view(view, output_path, dpi, figsize)
            print(f"{view}视图已保存: {output_path}")