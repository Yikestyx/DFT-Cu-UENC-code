import subprocess
import time
from pathlib import Path

import pyautogui


class VESTAController:
    """
    通过模拟鼠标点击控制 VESTA 打开 CIF、切换视图并截图。

    支持：
    - 截取 top/front/side 视图
    - 按需仅截取 front 或 side
    - 自动选择遮挡更少方向（依赖 ProjectionOverlapAnalyzer）
    - 截图前执行额外旋转点击
    - 全局截图区域、以及按视图独立截图区域
    """
    # ==================== 停留时间配置区（秒） ====================
    VESTA_LAUNCH_WAIT = 2.0          # 启动 VESTA 后等待窗口加载
    VESTA_ACTIVATE_WAIT = 0.3        # 激活 VESTA 窗口后等待
    VIEW_REFRESH_WAIT = 0.5          # 点击切换视图后等待刷新
    EXTRA_ROTATION_WAIT = 0.3        # 额外旋转每次点击后的等待
    BETWEEN_STRUCTURES_WAIT = 1.0    # 关闭当前结构后，切换到下个结构前等待
    # ===========================================================

    def __init__(
        self,
        cif_path: str,
        vesta_path: str = "VESTA",
        views_mode: str = "both",
        auto_select_best: bool = False,
        direction_to_view: dict = None,
    ):
        self.cif_path = Path(cif_path).resolve()
        if not self.cif_path.exists():
            raise FileNotFoundError(f"CIF file not found: {self.cif_path}")

        self.vesta_path = vesta_path
        self.sample_name = self.cif_path.stem
        self.views_mode = views_mode
        self.auto_select_best = auto_select_best
        self.direction_to_view = direction_to_view or {"a": "front", "b": "side"}

        # {'top': {'pos': (x,y), 'count': n}, 'front': ..., 'side': ...}
        self.click_config = {}
        self.rotation_click_pos = None
        self.extra_rotation_clicks = {"front": 0, "side": 0}

        # 全局截图区域
        self.screenshot_region = None
        # 分视图截图区域：{'top': region, 'front': region, 'side': region}
        self.view_screenshot_regions = {}

    def set_view_click(self, view: str, position: tuple, click_count: int = 1):
        if view not in ("top", "front", "side"):
            raise ValueError("view must be one of 'top', 'front', 'side'")
        self.click_config[view] = {"pos": position, "count": click_count}

    def set_rotation_click(self, position: tuple):
        self.rotation_click_pos = position

    def set_extra_rotation_clicks(self, front: int = 0, side: int = 0):
        self.extra_rotation_clicks["front"] = front
        self.extra_rotation_clicks["side"] = side

    def set_screenshot_region(self, region: tuple):
        """设置全局截图区域，支持 (left, top, width, height) 或 (left, top, right, bottom)。"""
        self.screenshot_region = self._normalize_region(region)

    def set_view_screenshot_region(self, view: str, region: tuple):
        """为单个视图设置独立截图区域，覆盖全局截图区域。"""
        if view not in ("top", "front", "side"):
            raise ValueError("view must be one of 'top', 'front', 'side'")
        self.view_screenshot_regions[view] = self._normalize_region(region)

    def _normalize_region(self, region: tuple):
        if len(region) != 4:
            raise ValueError("region must have 4 elements")
        # 自动兼容 (left, top, right, bottom)
        if region[2] > region[0] and region[3] > region[1] and region[2] < 5000:
            left, top, right, bottom = region
            return (left, top, right - left, bottom - top)
        return region

    def _launch_vesta(self):
        print(f"Launching VESTA with {self.cif_path} ...")
        self.process = subprocess.Popen([self.vesta_path, str(self.cif_path)])
        time.sleep(self.VESTA_LAUNCH_WAIT)
        try:
            import pygetwindow as gw

            windows = gw.getWindowsWithTitle("VESTA")
            if windows:
                windows[0].activate()
                time.sleep(self.VESTA_ACTIVATE_WAIT)
        except ImportError:
            pass

    def _click_at(self, position: tuple, count: int = 1):
        x, y = position
        pyautogui.click(x, y, clicks=count, interval=0.2)
        time.sleep(self.VIEW_REFRESH_WAIT)

    def _capture(self, output_path: str, region: tuple = None):
        if region:
            img = pyautogui.screenshot(region=region)
        elif self.screenshot_region:
            img = pyautogui.screenshot(region=self.screenshot_region)
        else:
            img = pyautogui.screenshot()
        img.save(output_path)
        print(f"Screenshot saved: {output_path}")

    def close_vesta(self):
        """关闭当前 VESTA 进程，并在切换到下一个结构前等待。"""
        proc = getattr(self, "process", None)
        if proc is None:
            return
        try:
            if proc.poll() is None:
                proc.terminate()
        except Exception:
            pass
        time.sleep(self.BETWEEN_STRUCTURES_WAIT)

    def _perform_extra_rotations(self, count: int):
        if count <= 0 or self.rotation_click_pos is None:
            return
        print(f"Performing {count} extra rotation click(s)...")
        for _ in range(count):
            self._click_at(self.rotation_click_pos, 1)
            time.sleep(self.EXTRA_ROTATION_WAIT)

    def _get_best_direction(self) -> str:
        try:
            from projection_overlap import ProjectionOverlapAnalyzer
        except ImportError:
            raise ImportError(
                "ProjectionOverlapAnalyzer not found. "
                "Please install ase and place projection_overlap.py in the Python path."
            )

        analyzer = ProjectionOverlapAnalyzer(str(self.cif_path))
        result = analyzer.get_best_direction()
        best = result["best_direction"]
        view = self.direction_to_view.get(best)
        if view not in ("front", "side"):
            raise ValueError(
                f"Direction '{best}' mapped to invalid view '{view}'. "
                f"Check direction_to_view mapping."
            )
        print(f"ProjectionOverlapAnalyzer suggests direction '{best}' -> view '{view}'")
        return view

    def run(self):
        required_views = ["top"]
        if self.views_mode == "both":
            required_views.extend(["front", "side"])
        elif self.views_mode == "front_only":
            required_views.append("front")
        elif self.views_mode == "side_only":
            required_views.append("side")
        else:
            raise ValueError("views_mode must be 'both', 'front_only', or 'side_only'")

        for view in required_views:
            if view not in self.click_config:
                raise RuntimeError(
                    f"Click configuration for '{view}' view is missing. "
                    f"Call set_view_click() first."
                )

        if self.auto_select_best and self.views_mode in ("front_only", "side_only"):
            best_view = self._get_best_direction()
            print(f"Auto-select best view: {best_view}")
            views_to_capture = [best_view]
        else:
            if self.views_mode == "both":
                views_to_capture = ["front", "side"]
            elif self.views_mode == "front_only":
                views_to_capture = ["front"]
            elif self.views_mode == "side_only":
                views_to_capture = ["side"]
            else:
                views_to_capture = []

        self._launch_vesta()
        top_region = self.view_screenshot_regions.get("top", self.screenshot_region)
        self._capture(f"{self.sample_name}_top.png", region=top_region)

        for view in views_to_capture:
            cfg = self.click_config[view]
            print(f"Switching to {view} view (click {cfg['pos']} x{cfg['count']})...")
            self._click_at(cfg["pos"], cfg["count"])

            extra = self.extra_rotation_clicks.get(view, 0)
            if extra > 0:
                self._perform_extra_rotations(extra)

            view_region = self.view_screenshot_regions.get(view, self.screenshot_region)
            self._capture(f"{self.sample_name}_{view}.png", region=view_region)

        print("All requested screenshots captured successfully.")
