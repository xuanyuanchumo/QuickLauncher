"""
图标工具模块 - 生成和管理应用程序图标
"""

import os
from pathlib import Path
from utils.resource_path import get_assets_path


def create_default_app_icon(size=64, text="QL", qapplication=None):
    """
    创建默认应用程序图标
    :param size: 图标尺寸
    :param text: 图标上的文字，默认为"QL"
    :param qapplication: QApplication实例，如果为None则创建临时实例
    :return: QPixmap类型的图标
    """
    from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
    from PySide6.QtCore import Qt
    
    # 确保在创建QPixmap前有QApplication实例
    if qapplication is None:
        from PySide6.QtWidgets import QApplication
        import sys
        if not QApplication.instance():
            # 创建一个临时的QApplication实例用于创建图标
            qapplication = QApplication.instance() or QApplication(sys.argv)
    
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 创建蓝色渐变背景
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0, QColor(66, 133, 244))  # Google Blue
    gradient.setColorAt(1, QColor(26, 115, 232))  # Darker blue

    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    
    # 绘制圆角矩形
    painter.drawRoundedRect(0, 0, size, size, 10, 10)

    # 绘制文字
    font = QFont()
    font.setPointSize(size // 4)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255))  # 白色文字
    
    # 居中绘制文字
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
    
    painter.end()
    return pixmap


def ensure_app_icon_exists(icon_path=None, app_instance=None):
    """
    确保应用程序图标存在，如果不存在则创建默认图标
    :param icon_path: 图标路径，如果为None则使用默认路径
    :param app_instance: QApplication实例，如果为None则在函数内部处理
    :return: 图标文件路径
    """
    if icon_path is None:
        # 使用资源路径处理工具
        icon_path = get_assets_path("icons/app_icon.png")
    
    icon_path = Path(icon_path)
    
    # 确保目录存在
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 如果图标不存在，创建默认图标
    if not icon_path.exists():
        print(f"图标文件不存在，正在创建默认图标: {icon_path}")
        icon = create_default_app_icon(64, "QL", app_instance)
        success = icon.save(str(icon_path), "PNG")
        if success:
            print(f"默认图标已创建: {icon_path}")
        else:
            print(f"创建默认图标失败: {icon_path}")
            raise Exception(f"无法创建默认图标: {icon_path}")
    
    return str(icon_path)


def get_app_icon_path():
    """
    获取应用程序图标的路径
    :return: 图标文件路径
    """
    return get_assets_path("icons/app_icon.png")


if __name__ == "__main__":
    # 测试创建默认图标
    icon_path = ensure_app_icon_exists()
    print(f"应用程序图标路径: {icon_path}")