"""
快捷窗口后端逻辑
处理快捷窗口的显示、隐藏和交互
"""

from PySide6.QtCore import QObject, Signal, Slot, QTimer, Qt, QPoint, QSize
from PySide6.QtGui import QPixmap, QGuiApplication, QScreen
from PySide6.QtWidgets import QWidget, QApplication
from core.app_manager import AppManager
from core.config_manager import ConfigManager, QuickWindowConfig
from core.window_algorithm import WindowAlgorithm
from dataclasses import asdict


class QuickWindowBackend(QObject):
    """快捷窗口后端逻辑"""

    # 信号定义
    apps_changed = Signal(list)
    config_updated = Signal(dict)
    position_changed = Signal(str)
    visibility_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.app_manager = AppManager()
        self.config_manager = ConfigManager()
        self.window_algorithm = WindowAlgorithm()

        # 应用列表缓存
        self._cached_apps = []
        self._load_apps()

        # 监听配置变化
        self.config_manager.quick_config_updated.connect(self._on_config_updated)

        # 性能优化：延迟加载
        self._initialized = False
        QTimer.singleShot(1000, self._delayed_init)

    def _delayed_init(self):
        """延迟初始化非关键组件"""
        if not self._initialized:
            self._initialized = True
            print("快捷窗口延迟初始化完成")

    def _on_config_updated(self):
        """配置更新时发出信号"""
        try:
            config = self.get_config()
            old_position = getattr(self, '_previous_position', config.get('position', 'bottom_center'))
            new_position = config.get('position', 'bottom_center')
            self._previous_position = new_position
            
            self.config_updated.emit(config)

            # 根据配置更新窗口位置
            if 'position' in config:
                self.position_changed.emit(config['position'])
                
            # 如果应用顺序更新，重新加载应用列表以确保顺序正确
            if 'app_order' in config:
                # 重新加载应用列表以确保快捷窗口应用顺序正确
                self._load_apps()
                
            # 如果背景颜色或透明度更新，发出配置更新信号以确保界面更新
            if 'background_color' in config or 'opacity' in config:
                self.config_updated.emit(config)
                
            # 如果行数或列数更新，发出配置更新信号以确保界面更新
            if 'rows' in config or 'cols' in config:
                self.config_updated.emit(config)
                
            # 如果位置发生变化，需要临时设置行数为1，然后恢复，以确保布局计算正确
            if old_position != new_position:
                print(f"位置从 {old_position} 变更为 {new_position}，正在重新计算布局")
                # 临时将行数设为1，然后恢复原始行数，以确保布局计算正确
                original_rows = config.get('rows', 1)
                self.config_manager.update_quick_config(rows=1)
                
                # 立即发出配置更新信号
                QTimer.singleShot(10, lambda: self.config_updated.emit(self.get_config()))
                
                # 恢复原始行数并重新计算
                QTimer.singleShot(50, lambda: self.config_manager.update_quick_config(rows=original_rows))
                QTimer.singleShot(100, lambda: self.config_updated.emit(self.get_config()))
            
            # 每次配置更新时，都要确保窗口尺寸根据新配置进行调整
            self.config_updated.emit(config)
        except Exception as e:
            print(f"配置更新处理失败: {e}")

    def _load_apps(self):
        """加载应用列表 - 按照快捷窗口配置的顺序"""
        try:
            # 获取所有应用
            all_apps = self.app_manager.get_applications()
            
            # 获取快捷窗口配置中的应用顺序
            quick_app_ids = self.config_manager.quick_config.app_order
            
            # 按照快捷窗口顺序排列的应用
            ordered_apps = []
            remaining_apps = []
            
            # 先按快捷窗口顺序排列
            for app_id in quick_app_ids:
                for app in all_apps:
                    if app.get('id') == app_id:
                        ordered_apps.append(app)
                        break
            
            # 添加不在快捷窗口中的其他应用
            for app in all_apps:
                if app.get('id') not in quick_app_ids:
                    remaining_apps.append(app)
            
            # 合并列表：快捷窗口应用在前，其他应用在后
            self._cached_apps = ordered_apps + remaining_apps
            self.apps_changed.emit(self._cached_apps)
        except Exception as e:
            print(f"加载应用列表失败: {e}")
            self._cached_apps = []
            self.apps_changed.emit([])

    @Slot(result='QVariantList')
    def get_apps(self) -> list:
        """获取应用列表"""
        return self._cached_apps

    @Slot(result='QVariantMap')
    def get_config(self) -> dict:
        """获取配置"""
        try:
            return asdict(self.config_manager.quick_config)
        except Exception as e:
            print(f"获取配置失败: {e}")
            return asdict(QuickWindowConfig())

    @Slot()
    def refresh_apps(self):
        """刷新应用列表"""
        self._load_apps()

    @Slot(str, result='QVariantMap')
    def get_app_by_index(self, index: int):
        """根据索引获取应用"""
        try:
            if 0 <= index < len(self._cached_apps):
                return self._cached_apps[index]
        except Exception as e:
            print(f"获取应用失败: {e}")
        return {}

    @Slot(str, result=bool)
    def launch_app_by_id(self, app_id: str) -> bool:
        """根据ID启动应用"""
        try:
            return self.app_manager.launch_application(app_id)
        except Exception as e:
            print(f"启动应用失败 {app_id}: {e}")
            return False

    @Slot(int, result=bool)
    def launch_app_by_index(self, index: int) -> bool:
        """根据索引启动应用"""
        try:
            if 0 <= index < len(self._cached_apps):
                app = self._cached_apps[index]
                if 'id' in app:
                    return self.app_manager.launch_application(app['id'])
        except Exception as e:
            print(f"启动应用失败: {e}")
        return False

    @Slot(str, result=dict)
    def get_app_position(self, position: str = None) -> dict:
        """获取应用窗口位置"""
        try:
            if not position:
                position = self.config_manager.quick_config.position

            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()

            config = self.get_config()
            icon_size = config.get('icon_size', 64)
            icon_spacing = config.get('icon_spacing', 10)
            rows = config.get('rows', 1)
            cols = config.get('cols', 5)
            show_labels = config.get('show_labels', False)

            # 获取快捷窗口中配置的应用数量
            quick_app_ids = self.config_manager.quick_config.app_order
            app_count = len(quick_app_ids)
            
            # 使用窗口算法计算布局信息
            layout_info = self.window_algorithm.calculate_layout(app_count, rows, cols, position)
            
            # 计算窗口尺寸
            window_width, window_height = self.window_algorithm.calculate_window_size(
                layout_info, icon_size, icon_spacing, show_labels
            )

            # 根据位置计算坐标
            if position == "top_center":
                x = screen_geometry.center().x() - window_width // 2
                y = screen_geometry.top() + 10  # 距离顶部10像素
            else:  # bottom_center
                x = screen_geometry.center().x() - window_width // 2
                y = screen_geometry.bottom() - window_height - 10  # 距离底部10像素

            return {
                'x': x,
                'y': y,
                'width': window_width,
                'height': window_height,
                'position': position
            }

        except Exception as e:
            print(f"获取窗口位置失败: {e}")
            return {'x': 100, 'y': 100, 'width': 800, 'height': 120, 'position': 'bottom_center'}

    @Slot('QVariantList', result=bool)
    def update_app_order(self, app_order: list) -> bool:
        """更新应用顺序"""
        try:
            # 处理可能的QJSValue对象
            from PySide6.QtQml import QJSValue
            def process_qjsvalue_in_list(lst):
                """处理列表中的QJSValue对象"""
                if isinstance(lst, list):
                    processed_list = []
                    for item in lst:
                        if isinstance(item, QJSValue):
                            if item.isString():
                                processed_list.append(str(item.toString()))
                            elif item.isNumber():
                                num_val = item.toNumber()
                                processed_list.append(int(num_val) if num_val.is_integer() else float(num_val))
                            elif item.isBool():
                                processed_list.append(bool(item.toBool()))
                            elif item.isNull() or item.isUndefined():
                                processed_list.append(None)
                            else:
                                try:
                                    processed_list.append(item.toVariant())
                                except:
                                    processed_list.append(str(item.toString()) if hasattr(item, 'toString') else None)
                        else:
                            processed_list.append(item)
                    return processed_list
                return lst

            processed_app_order = process_qjsvalue_in_list(app_order)

            if isinstance(processed_app_order, list):
                # 验证所有ID都存在
                valid_ids = [app.get('id', '') for app in self._cached_apps]
                filtered_order = [id for id in processed_app_order if id in valid_ids]

                # 更新配置
                self.config_manager.quick_config.app_order = filtered_order
                self.config_manager.save()

                # 重新排序缓存的应用列表
                # 现在确保快捷窗口中显示的应用按照正确的顺序排列在缓存列表的前面
                ordered_apps = []
                remaining_apps = []
                
                # 获取所有应用的副本
                all_apps = self._cached_apps.copy()
                
                # 按照快捷窗口顺序排列的应用
                for app_id in filtered_order:
                    for app in all_apps:
                        if app.get('id') == app_id:
                            ordered_apps.append(app)
                            break
                
                # 添加不在快捷窗口中的其他应用
                for app in all_apps:
                    if app.get('id') not in filtered_order:
                        remaining_apps.append(app)
                
                # 重新构建缓存列表：快捷应用在前，其他应用在后
                self._cached_apps = ordered_apps + remaining_apps

                # 发出信号
                self.apps_changed.emit(self._cached_apps)
                
                # 发出配置更新信号以确保窗口尺寸更新
                self.config_updated.emit(self.get_config())
                
                return True

        except Exception as e:
            print(f"更新应用顺序失败: {e}")

        return False

    @Slot(result=dict)
    def get_window_geometry(self) -> dict:
        """获取窗口几何信息"""
        try:
            position_config = self.get_app_position()

            return {
                'x': position_config['x'],
                'y': position_config['y'],
                'width': position_config['width'],
                'height': position_config['height'],
                'opacity': self.config_manager.quick_config.opacity,
                'background_color': self.config_manager.quick_config.background_color
            }

        except Exception as e:
            print(f"获取窗口几何信息失败: {e}")
            return {
                'x': 100,
                'y': 100,
                'width': 800,
                'height': 120,
                'opacity': 0.9,
                'background_color': '#FFFFFF'
            }

    @Slot(result=dict)
    def get_grid_layout_info(self) -> dict:
        """获取网格布局信息"""
        try:
            config = self.get_config()
            quick_app_ids = self.config_manager.quick_config.app_order
            app_count = len(quick_app_ids)
            rows = config.get('rows', 1)
            cols = config.get('cols', 5)
            position = config.get('position', 'bottom_center')
            
            # 使用窗口算法计算布局信息
            layout_info = self.window_algorithm.calculate_layout(app_count, rows, cols, position)
            
            # 获取特殊行信息
            special_row_info = self.window_algorithm.get_special_row_info(layout_info, position)
            
            # 计算应用分布
            app_distribution = self.window_algorithm.calculate_app_distribution(app_count, rows, cols, position)
            
            # 计算窗口尺寸
            icon_size = config.get('icon_size', 64)
            icon_spacing = config.get('icon_spacing', 10)
            show_labels = config.get('show_labels', False)
            window_width, window_height = self.window_algorithm.calculate_window_size(
                layout_info, icon_size, icon_spacing, show_labels
            )
            
            # 确保窗口尺寸基于实际应用数量，而不是配置的最大网格
            actual_rows = layout_info.rows
            actual_cols = min(cols, max([pos[1] for pos in layout_info.app_positions], default=-1) + 1) if layout_info.app_positions else 0
            
            return {
                'rows': actual_rows,
                'cols': actual_cols if actual_cols > 0 else layout_info.cols,
                'app_positions': [{'row': pos[0], 'col': pos[1]} for pos in layout_info.app_positions],
                'max_apps': layout_info.max_apps,
                'total_apps': layout_info.total_apps,
                'special_row_info': special_row_info,
                'app_distribution': app_distribution,
                'can_add_row': self.window_algorithm.can_add_row(app_count, rows, cols, position),
                'width': window_width,
                'height': window_height,
                'configured_rows': rows,
                'configured_cols': cols
            }
        except Exception as e:
            print(f"获取网格布局信息失败: {e}")
            return {
                'rows': 1,
                'cols': 5,
                'app_positions': [],
                'max_apps': 5,
                'total_apps': 0,
                'special_row_info': {},
                'app_distribution': {},
                'can_add_row': True,
                'width': 200,
                'height': 100,
                'configured_rows': 1,
                'configured_cols': 5
            }

    @Slot(str, int, result=bool)
    def update_window_config(self, key: str, value: int) -> bool:
        """更新窗口配置（如行数或列数）"""
        try:
            # 验证输入参数
            if key not in ['rows', 'cols']:
                return False
                
            if value <= 0 or value > 15:  # 限制最大为15
                return False
                
            # 获取当前配置
            current_config = self.get_config()
            
            # 检查是否与当前值相同
            if current_config.get(key) == value:
                return True
                
            # 更新配置
            update_data = {key: value}
            self.config_manager.update_quick_config(**update_data)
            
            # 发出配置更新信号，以便前端重新计算布局
            self.config_updated.emit(self.get_config())
            
            return True
        except Exception as e:
            print(f"更新窗口配置失败: {e}")
            return False

    @Slot(str, result=bool)
    def add_app_to_quick_window(self, app_id: str) -> bool:
        """向快捷窗口添加应用"""
        try:
            # 获取当前的快捷应用列表
            current_order = self.config_manager.quick_config.app_order.copy()
            
            # 检查应用ID是否已存在
            if app_id in current_order:
                return False  # 应用已在快捷窗口中
                
            # 检查是否达到最大限制
            rows = self.config_manager.quick_config.rows
            cols = self.config_manager.quick_config.cols
            max_apps = rows * cols
            
            if len(current_order) >= max_apps:
                return False  # 已达到最大应用数量限制
                
            # 添加应用到列表末尾
            current_order.append(app_id)
            
            # 更新配置
            self.config_manager.quick_config.app_order = current_order
            self.config_manager.save()
            
            # 重新加载应用列表
            self._load_apps()
            
            # 发出配置更新信号以触发窗口尺寸更新
            self.config_updated.emit(self.get_config())
            
            return True
        except Exception as e:
            print(f"向快捷窗口添加应用失败: {e}")
            return False

    @Slot(str, result=bool)
    def remove_app_from_quick_window(self, app_id: str) -> bool:
        """从快捷窗口移除应用"""
        try:
            # 获取当前的快捷应用列表
            current_order = self.config_manager.quick_config.app_order.copy()
            
            # 检查应用ID是否存在
            if app_id not in current_order:
                return False  # 应用不在快捷窗口中
                
            # 移除应用
            current_order.remove(app_id)
            
            # 更新配置
            self.config_manager.quick_config.app_order = current_order
            self.config_manager.save()
            
            # 重新加载应用列表
            self._load_apps()
            
            # 发出配置更新信号以触发窗口尺寸更新
            self.config_updated.emit(self.get_config())
            
            return True
        except Exception as e:
            print(f"从快捷窗口移除应用失败: {e}")
            return False

    @Slot()
    def show_window(self):
        """显示窗口"""
        self.visibility_changed.emit(True)

    @Slot()
    def hide_window(self):
        """隐藏窗口"""
        self.visibility_changed.emit(False)

    @Slot(result=int)
    def get_app_count(self) -> int:
        """获取应用数量"""
        return len(self._cached_apps)

    @Slot(result=dict)
    def get_performance_stats(self) -> dict:
        """获取性能统计"""
        try:
            # 这里可以添加更多的性能统计
            return {
                'app_count': len(self._cached_apps),
                'cache_initialized': self._initialized,
                'config_loaded': True
            }
        except Exception as e:
            print(f"获取性能统计失败: {e}")
            return {}

    @Slot(str, result=bool)
    def update_app_count(self, app_id: str) -> bool:
        """更新应用数量后自动调整窗口尺寸和布局"""
        try:
            # 重新计算布局信息
            config = self.get_config()
            quick_app_ids = self.config_manager.quick_config.app_order
            app_count = len(quick_app_ids)
            rows = config.get('rows', 1)
            cols = config.get('cols', 5)
            position = config.get('position', 'bottom_center')
            
            # 使用窗口算法重新计算布局
            layout_info = self.window_algorithm.calculate_layout(app_count, rows, cols, position)
            
            # 如果应用数量变化导致行数需要调整
            if app_count <= cols and rows != 1:
                # 如果应用数量少于等于列数，且当前行数不是1，则调整为1行
                self.config_manager.update_quick_config(rows=1)
            elif app_count > cols:
                # 如果应用数量大于列数，根据布局算法计算所需的行数
                k = app_count // cols  # 向下取整
                r = app_count % cols   # 余数
                required_rows = k if r == 0 else k + 1
                
                if required_rows != rows:
                    # 如果所需行数与当前配置不同，更新配置
                    self.config_manager.update_quick_config(rows=required_rows)
            
            # 发出配置更新信号以确保界面更新
            self.config_updated.emit(self.get_config())
            
            return True
        except Exception as e:
            print(f"更新应用数量失败: {e}")
            return False

    @Slot()
    def refresh_with_single_row(self):
        """刷新快捷窗口，先将行数变为一行然后恢复原来的行数"""
        try:
            # 获取当前配置
            config = self.get_config()
            original_rows = config.get('rows', 1)

            
            print(f"开始刷新快捷窗口，当前行数: {original_rows}")
            
            # 先将行数设为1
            self.config_manager.update_quick_config(rows=1)
            
            # 发出配置更新信号，让前端界面更新
            self.config_updated.emit(self.get_config())
            
            # 使用定时器在稍后恢复原来的行数
            from PySide6.QtCore import QTimer
            def restore_original_rows():
                print(f"恢复原始行数: {original_rows}")
                self.config_manager.update_quick_config(rows=original_rows)
                self.config_updated.emit(self.get_config())
            
            # 延迟50毫秒后恢复原始行数，给界面足够时间更新
            QTimer.singleShot(50, restore_original_rows)
            
            print("快捷窗口刷新流程已启动")
        except Exception as e:
            print(f"刷新快捷窗口失败: {e}")
