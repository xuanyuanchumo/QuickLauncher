"""
窗口算法模块
处理快捷窗口的网格布局算法、尺寸计算和位置定位逻辑
"""

from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, Slot


@dataclass
class WindowLayoutInfo:
    """窗口布局信息"""
    rows: int  # 实际行数
    cols: int  # 实际列数
    app_positions: List[Tuple[int, int]]  # 每个应用的位置 (row, col)
    max_apps: int  # 最大显示应用数量
    total_apps: int  # 实际应用数量


class WindowAlgorithm(QObject):
    """窗口算法处理器"""

    def __init__(self):
        super().__init__()

    def calculate_layout(self, app_count: int, rows: int, cols: int, position: str = "bottom_center") -> WindowLayoutInfo:
        """
        计算网格布局信息
        
        Args:
            app_count: 应用总数
            rows: 配置行数
            cols: 配置列数
            position: 窗口位置 ('top_center' 或 'bottom_center')
            
        Returns:
            WindowLayoutInfo: 包含布局详细信息的对象
        """
        max_apps = rows * cols
        
        # 实际显示的应用数量（不超过最大限制）
        actual_app_count = min(app_count, max_apps)
        
        # 计算实际需要的行数
        if actual_app_count == 0:
            actual_rows = 0
        else:
            actual_rows = (actual_app_count + cols - 1) // cols  # 向上取整

        # 计算每行的列数
        app_positions = []
        
        if actual_app_count > 0:
            if actual_app_count <= cols:
                # 如果 x <= m：只显示1行，该行包含x列（即x个应用）
                # 如果n != 1要设置n=1
                for col in range(actual_app_count):
                    app_positions.append((0, col))
                actual_rows = 1
            elif actual_app_count <= max_apps:
                # 多行情况，根据位置计算布局
                if position == "top_center":
                    # 顶部居中：如果x > m
                    # 计算 k = ⌊x/m⌋（向下取整），r = x % m（余数）
                    k = actual_app_count // cols
                    r = actual_app_count % cols
                    
                    # 如果 n >= k+1，设置 n=k+1并且前端不允许在快捷窗口设置行操作添加行数
                    required_rows = k if r == 0 else k + 1
                    actual_rows = min(required_rows, rows)
                    
                    # 前k行每行显示m个应用，第k+1行显示r个应用
                    # 应用按从上到下的顺序填充(填满一行再填下一行)
                    for row_idx in range(actual_rows):
                        apps_in_this_row = cols if row_idx < k else r
                        if row_idx == k and r == 0:  # 最后一行没有余数应用
                            apps_in_this_row = cols
                            
                        for col_idx in range(apps_in_this_row):
                            app_idx = row_idx * cols + col_idx
                            if app_idx < actual_app_count:
                                app_positions.append((row_idx, col_idx))
                else:  # bottom_center
                    # 底部居中：如果x > m
                    # 计算 k = ⌊x/m⌋，r = x % m
                    k = actual_app_count // cols
                    r = actual_app_count % cols
                    
                    # 如果 n >= k+1，设置 n=k+1并且前端不允许在快捷窗口设置行操作添加行数
                    required_rows = k if r == 0 else k + 1
                    actual_rows = min(required_rows, rows)
                    
                    # 第1行显示r个应用，后k行（底部）每行显示m个应用
                    # 应用按从下到上的顺序填充(填满一行再填上一行)
                    if r > 0 and actual_rows > 0:
                        # 第一行显示r个应用
                        for col_idx in range(r):
                            app_idx = col_idx
                            if app_idx < actual_app_count:
                                app_positions.append((0, col_idx))
                        
                        # 后续行（从下往上）显示m个应用
                        for row_idx in range(1, actual_rows):
                            # 从底部开始填充，即倒序行号
                            display_row = row_idx  # 从上往下排列，但第一行是余数行
                            for col_idx in range(cols):
                                app_idx = r + (row_idx - 1) * cols + col_idx
                                if app_idx < actual_app_count:
                                    app_positions.append((display_row, col_idx))
                    else:
                        # 没有余数，每行都显示m个应用
                        for row_idx in range(actual_rows):
                            for col_idx in range(cols):
                                app_idx = row_idx * cols + col_idx
                                if app_idx < actual_app_count:
                                    app_positions.append((row_idx, col_idx))
            else:
                # 如果 x > n * m：只显示前n * m个应用，以完整的n行m列网格显示
                for idx in range(max_apps):
                    row = idx // cols
                    col = idx % cols
                    app_positions.append((row, col))
                actual_rows = rows  # 使用配置的行数
        
        # 确保窗口尺寸正确，只计算实际使用的行列数
        if actual_app_count > 0:
            # 根据实际应用数量重新计算行数，以确保不会预留多余空间
            required_rows = (actual_app_count + cols - 1) // cols  # 向上取整
            actual_rows = min(required_rows, actual_rows)
        
        return WindowLayoutInfo(
            rows=actual_rows,
            cols=cols,
            app_positions=app_positions,
            max_apps=max_apps,
            total_apps=actual_app_count
        )

    def calculate_window_size(self, layout_info: WindowLayoutInfo, icon_size: int, icon_spacing: int, show_labels: bool) -> Tuple[int, int]:
        """
        计算窗口尺寸
        
        Args:
            layout_info: 布局信息
            icon_size: 图标大小
            icon_spacing: 图标间距（间隙）
            show_labels: 是否显示标签
            
        Returns:
            Tuple[int, int]: (width, height)
        """
        if layout_info.total_apps == 0:
            return 200, 100  # 默认最小尺寸

        # 计算应用名高度
        label_height = 20 if show_labels else 0
        
        # 根据要求，窗口尺寸计算：
        # 宽度 = 左边距+图标+（间隙+图标）*(m-1)+右边距
        # 高度 = 上边距+图标+应用名+（间隙+图标+应用名）*(n-1)+下边距
        # 边距长度10，间隙5
        margin = icon_spacing  # 边距长度
        gap = 5  # 间隙
        
        # 宽度 = margin + icon_size + (gap + icon_size) * (layout_info.cols - 1) + margin
        width = margin + icon_size + (gap + icon_size) * (layout_info.cols - 1) + margin
        
        # 高度 = margin + (icon_size + label_height) + (gap + (icon_size + label_height)) * (layout_info.rows - 1) + margin
        height = margin + (icon_size + label_height) + (gap + (icon_size + label_height)) * (layout_info.rows - 1) + margin
        
        return width, height

    def can_add_row(self, app_count: int, rows: int, cols: int, position: str = "bottom_center") -> bool:
        """
        判断是否可以添加行数（根据特定条件）
        
        Args:
            app_count: 应用总数
            rows: 当前行数
            cols: 当前列数
            position: 窗口位置
            
        Returns:
            bool: 是否可以添加行
        """
        max_apps = rows * cols
        
        # 检查当前应用数量是否超过限制
        actual_app_count = min(app_count, max_apps)
        
        # 计算理论行数
        if app_count > 0:
            k = app_count // cols  # 向下取整
            r = app_count % cols   # 余数
            required_rows = k if r == 0 else k + 1
        else:
            required_rows = 0
            
        # 如果当前已经是15行或15列，不允许添加
        if rows >= 15 or cols >= 15:
            return False
        
        # 当窗口位于顶部时，如果最后一行不是满列，则不允许添加行
        if position == "top_center":
            if actual_app_count % cols != 0 and actual_app_count < max_apps and required_rows > rows:
                return False
        # 当窗口位于底部时，如果第一行不是满列，则不允许添加行
        elif position == "bottom_center":
            if actual_app_count > cols:  # 多行情况
                k = actual_app_count // cols
                r = actual_app_count % cols
                # 如果第一行（余数行）不是满列
                if r != 0 and required_rows > rows:
                    return False
            else:  # 单行情况
                if actual_app_count < cols and required_rows > rows:
                    return False
            
        return True

    def calculate_app_distribution(self, app_count: int, rows: int, cols: int, position: str = "bottom_center") -> Dict[str, Any]:
        """
        计算应用在网格中的分布
        
        Args:
            app_count: 应用总数
            rows: 配置行数
            cols: 配置列数
            position: 窗口位置
            
        Returns:
            Dict: 包含应用分布信息的字典
        """
        max_apps = rows * cols
        actual_app_count = min(app_count, max_apps)
        
        if actual_app_count <= cols:
            # 如果 x <= m：只显示1行，该行包含x列（即x个应用），且该行位于窗口顶部
            # 如果n!=1要设置n=1
            distribution = {
                'display_rows': 1,
                'apps_in_each_row': [actual_app_count],
                'first_row_apps': actual_app_count
            }
        else:
            # 多行情况
            if actual_app_count <= max_apps:
                if position == "top_center":
                    # 顶部居中：如果x > m
                    # 计算 k = ⌊x/m⌋（向下取整），r = x % m（余数）
                    k = actual_app_count // cols  # 向下取整
                    r = actual_app_count % cols  # 余数
                    # 如果 n >= k+1，设置 n=k+1并且前端不允许在快捷窗口设置行操作添加行数
                    required_rows = k if r == 0 else k + 1
                    actual_display_rows = min(required_rows, rows)
                    
                    apps_in_each_row = []
                    for i in range(actual_display_rows):
                        if i < k:  # 前k行
                            apps_in_each_row.append(cols)
                        elif r > 0 and i == k:  # 第k+1行（如果有余数）
                            apps_in_each_row.append(r)
                    
                    distribution = {
                        'display_rows': actual_display_rows,
                        'apps_in_each_row': apps_in_each_row,
                        'k_value': k,
                        'remainder': r,
                        'required_rows': required_rows,
                        'can_add_row': rows < required_rows  # 当前设置的行数不够
                    }
                else:  # bottom_center
                    # 底部居中：如果x > m
                    # 计算 k = ⌊x/m⌋，r = x % m
                    k = actual_app_count // cols
                    r = actual_app_count % cols
                    # 如果 n >= k+1，设置 n=k+1并且前端不允许在快捷窗口设置行操作添加行数
                    required_rows = k if r == 0 else k + 1
                    actual_display_rows = min(required_rows, rows)
                    
                    apps_in_each_row = []
                    if r > 0 and actual_display_rows > 0:
                        # 第1行显示r个应用
                        apps_in_first_row = r
                        apps_in_each_row.append(apps_in_first_row)
                        # 后k行（底部）每行显示m个应用
                        for i in range(actual_display_rows - 1):
                            apps_in_each_row.append(cols)
                    else:
                        # 如果没有余数，所有行都显示m个应用
                        apps_in_each_row = [cols] * actual_display_rows
                    
                    distribution = {
                        'display_rows': actual_display_rows,
                        'apps_in_each_row': apps_in_each_row,
                        'k_value': k,
                        'remainder': r,
                        'required_rows': required_rows,
                        'can_add_row': rows < required_rows  # 当前设置的行数不够
                    }
            else:
                # 如果 x > n * m：只显示前n * m个应用，以完整的n行m列网格显示
                distribution = {
                    'display_rows': rows,
                    'apps_in_each_row': [cols] * rows,
                    'full_grid': True
                }
        
        return distribution

    def get_special_row_info(self, layout_info: WindowLayoutInfo, position: str = "bottom_center") -> Dict[str, Any]:
        """
        获取特殊行信息（用于居中显示）
        
        Args:
            layout_info: 布局信息
            position: 窗口位置
            
        Returns:
            Dict: 特殊行相关信息
        """
        if layout_info.total_apps == 0 or layout_info.rows == 0:
            return {}

        special_row_info = {}
        
        if position == "top_center":
            # 顶部居中：最后一行为特殊行，需要居中
            last_row = layout_info.rows - 1
            apps_in_last_row = sum(1 for pos in layout_info.app_positions if pos[0] == last_row)
            special_row_info = {
                'special_row': last_row,
                'apps_in_special_row': apps_in_last_row,
                'items_per_row': layout_info.cols,
                'is_last_row': True
            }
        else:  # bottom_center
            # 底部居中：第一行为特殊行，需要居中
            first_row = 0
            apps_in_first_row = sum(1 for pos in layout_info.app_positions if pos[0] == first_row)
            special_row_info = {
                'special_row': first_row,
                'apps_in_special_row': apps_in_first_row,
                'items_per_row': layout_info.cols,
                'is_first_row': True
            }
        
        return special_row_info