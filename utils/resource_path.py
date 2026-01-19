"""
资源路径处理模块
统一处理开发环境和PyInstaller打包后的资源路径差异
"""
import os
import sys
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径，兼容PyInstaller打包环境
    :param relative_path: 相对路径
    :return: 绝对路径字符串
    """
    try:
        # PyInstaller会将资源文件放在_temp目录下，并设置_MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境下使用当前文件的目录作为基础路径
        base_path = Path(__file__).parent.parent

    return str(Path(base_path) / relative_path)


def get_resource_path(sub_path: str) -> str:
    """
    获取资源路径
    :param sub_path: 子路径
    :return: 完整的资源路径
    """
    return resource_path(sub_path)


def get_data_path(sub_path: str = "") -> str:
    """
    获取数据存储路径
    :param sub_path: 子路径
    :return: 完整的数据路径
    """
    if getattr(sys, 'frozen', False):
        # 打包后使用用户数据目录
        import os
        if sys.platform == "win32":
            data_dir = os.environ.get('APPDATA', os.path.expanduser('~/.local/share'))
        else:
            data_dir = os.path.expanduser('~/.local/share')
        base_path = Path(data_dir) / "QuickLauncher"
    else:
        # 开发环境下使用项目根目录
        base_path = Path(__file__).parent.parent

    if sub_path:
        base_path = base_path / sub_path

    # 确保目录存在
    base_path.mkdir(parents=True, exist_ok=True)
    return str(base_path)


def get_assets_path(sub_path: str = "") -> str:
    """
    获取资源文件路径（图片、QML等）
    :param sub_path: 子路径
    :return: 完整的资源文件路径
    """
    if sub_path:
        return resource_path(f"assets/{sub_path}")
    else:
        return resource_path("assets")


def get_qml_path(qml_filename: str) -> str:
    """
    获取QML文件路径
    :param qml_filename: QML文件名
    :return: 完整的QML文件路径
    """
    if not qml_filename.endswith('.qml'):
        qml_filename += '.qml'
    
    return resource_path(f"ui/qml/{qml_filename}")


def get_ui_path(ui_subpath: str) -> str:
    """
    获取UI相关资源路径
    :param ui_subpath: UI子路径
    :return: 完整的UI资源路径
    """
    return resource_path(f"ui/{ui_subpath}")


def get_config_path(filename: str = "config.json") -> str:
    """
    获取配置文件路径
    :param filename: 配置文件名
    :return: 配置文件路径
    """
    return get_data_path(filename)


def get_cache_path(sub_path: str = "") -> str:
    """
    获取缓存路径
    :param sub_path: 缓存子路径
    :return: 完整的缓存路径
    """
    return get_data_path(f"cache/{sub_path}" if sub_path else "cache")


if __name__ == "__main__":
    print("Resource paths:")
    print(f"  Base resource: {resource_path('.')}")
    print(f"  QML path for MainWindow: {get_qml_path('MainWindow')}")
    print(f"  Assets path: {get_assets_path()}")
    print(f"  Data path: {get_data_path()}")
    print(f"  Cache path: {get_cache_path()}")
    print(f"  Config path: {get_config_path()}")