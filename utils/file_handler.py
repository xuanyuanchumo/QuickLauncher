"""
文件处理工具类 - 包含文件上传、删除、更新等操作
带有日志记录功能

提供以下功能:
- 文件上传 (upload_file): 支持文件大小限制、扩展名验证和唯一文件名生成
- 文件删除 (delete_file): 安全删除指定文件
- 文件更新 (update_file): 支持文件大小限制和扩展名验证的文件更新
- 文件信息获取 (get_file_info): 获取文件的详细信息
- 目录确保 (ensure_directory_exists): 确保指定目录存在
- 路径安全验证 (is_safe_path): 防止路径遍历攻击
- 文件哈希计算 (get_file_hash): 计算文件的哈希值用于完整性验证
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import uuid4
import mimetypes

# 配置日志
logger = logging.getLogger(__name__)


class FileHandler:
    """文件处理工具类"""
    
    @staticmethod
    def upload_file(source_path: str, dest_dir: str, allowed_extensions: Optional[list] = None, max_size: Optional[int] = None) -> Dict[str, Any]:
        """
        上传文件到指定目录
        :param source_path: 源文件路径
        :param dest_dir: 目标目录
        :param allowed_extensions: 允许的文件扩展名列表
        :param max_size: 最大文件大小(字节)
        :return: 上传结果字典
        """
        try:
            logger.info(f"开始上传文件: {source_path} -> {dest_dir}")
            
            # 验证源文件是否存在
            if not os.path.exists(source_path):
                result = {"success": False, "message": "源文件不存在"}
                logger.error(f"上传失败: {result['message']}, 源路径: {source_path}")
                return result
            
            source_path_obj = Path(source_path)
            dest_dir_obj = Path(dest_dir)
            
            logger.debug(f"正在验证源文件: {source_path_obj}, 大小: {source_path_obj.stat().st_size} 字节")
            
            # 检查文件大小
            if max_size:
                file_size = source_path_obj.stat().st_size
                if file_size > max_size:
                    result = {"success": False, "message": f"文件大小超过限制: {file_size} > {max_size}"}
                    logger.error(f"上传失败: {result['message']}, 源路径: {source_path}")
                    return result
            
            # 验证文件扩展名
            if allowed_extensions:
                file_ext = source_path_obj.suffix.lower()
                if file_ext not in allowed_extensions:
                    result = {"success": False, "message": f"不支持的文件格式: {file_ext}"}
                    logger.error(f"上传失败: {result['message']}, 源路径: {source_path}")
                    return result
            
            # 尝试检测MIME类型
            mime_type, _ = mimetypes.guess_type(source_path)
            logger.debug(f"检测到的MIME类型: {mime_type}, 文件路径: {source_path}")
            
            # 创建目标目录
            dest_dir_obj.mkdir(parents=True, exist_ok=True)
            logger.debug(f"目标目录已准备: {dest_dir_obj}")
            
            # 生成唯一文件名
            filename = f"{uuid4()}{source_path_obj.suffix}"
            dest_path = dest_dir_obj / filename
            
            # 复制文件
            shutil.copy2(source_path, dest_path)
            logger.debug(f"文件已复制: {source_path} -> {dest_path}")
            
            # 计算相对路径
            relative_path = dest_path.relative_to(Path(__file__).parent.parent)
            
            result = {
                "success": True,
                "message": "文件上传成功",
                "path": str(relative_path),
                "full_path": str(dest_path),
                "size": source_path_obj.stat().st_size
            }
            logger.info(f"文件上传成功: {source_path} -> {dest_path}, 大小: {source_path_obj.stat().st_size} 字节")
            return result
            
        except Exception as e:
            result = {"success": False, "message": f"上传文件失败: {str(e)}"}
            logger.error(f"上传失败: {str(e)}, 源路径: {source_path}, 目标目录: {dest_dir}")
            return result

    @staticmethod
    def delete_file(file_path: str) -> Dict[str, Any]:
        """
        删除指定文件
        :param file_path: 文件路径
        :return: 删除结果字典
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                result = {"success": False, "message": "文件不存在"}
                logger.warning(f"删除失败: {result['message']}, 路径: {file_path}")
                return result
            
            file_path_obj.unlink()
            result = {"success": True, "message": "文件删除成功"}
            logger.info(f"文件删除成功: {file_path}")
            return result
            
        except Exception as e:
            result = {"success": False, "message": f"删除文件失败: {str(e)}"}
            logger.error(f"删除失败: {str(e)}, 路径: {file_path}")
            return result

    @staticmethod
    def update_file(source_path: str, target_path: str, allowed_extensions: Optional[list] = None, max_size: Optional[int] = None) -> Dict[str, Any]:
        """
        更新文件
        :param source_path: 源文件路径
        :param target_path: 目标文件路径
        :param allowed_extensions: 允许的文件扩展名列表
        :param max_size: 最大文件大小(字节)
        :return: 更新结果字典
        """
        try:
            # 验证源文件是否存在
            if not os.path.exists(source_path):
                result = {"success": False, "message": "源文件不存在"}
                logger.error(f"更新失败: {result['message']}, 源路径: {source_path}")
                return result
            
            source_path_obj = Path(source_path)
            target_path_obj = Path(target_path)
            
            logger.debug(f"正在验证源文件: {source_path_obj}, 大小: {source_path_obj.stat().st_size} 字节")
            
            # 检查文件大小
            if max_size:
                file_size = source_path_obj.stat().st_size
                if file_size > max_size:
                    result = {"success": False, "message": f"文件大小超过限制: {file_size} > {max_size}"}
                    logger.error(f"更新失败: {result['message']}, 源路径: {source_path}")
                    return result
            
            # 验证文件扩展名
            if allowed_extensions:
                file_ext = source_path_obj.suffix.lower()
                if file_ext not in allowed_extensions:
                    result = {"success": False, "message": f"不支持的文件格式: {file_ext}"}
                    logger.error(f"更新失败: {result['message']}, 源路径: {source_path}")
                    return result
            
            # 尝试检测MIME类型
            mime_type, _ = mimetypes.guess_type(source_path)
            logger.debug(f"检测到的MIME类型: {mime_type}, 文件路径: {source_path}")
            
            # 创建目标目录
            target_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(source_path, target_path)
            
            result = {
                "success": True,
                "message": "文件更新成功",
                "path": str(target_path),
                "size": source_path_obj.stat().st_size
            }
            logger.info(f"文件更新成功: {source_path} -> {target_path}, 大小: {source_path_obj.stat().st_size} 字节")
            return result
            
        except Exception as e:
            result = {"success": False, "message": f"更新文件失败: {str(e)}"}
            logger.error(f"更新失败: {str(e)}, 源路径: {source_path}, 目标路径: {target_path}")
            return result

    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        获取文件信息
        :param file_path: 文件路径
        :return: 文件信息字典
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                result = {"success": False, "message": "文件不存在"}
                logger.warning(f"获取文件信息失败: {result['message']}, 路径: {file_path}")
                return result
            
            stat = file_path_obj.stat()
            result = {
                "success": True,
                "path": str(file_path_obj),
                "size": stat.st_size,
                "modified_time": stat.st_mtime,
                "created_time": stat.st_ctime,
                "extension": file_path_obj.suffix.lower()
            }
            logger.debug(f"获取文件信息成功: {file_path}")
            return result
            
        except Exception as e:
            result = {"success": False, "message": f"获取文件信息失败: {str(e)}"}
            logger.error(f"获取文件信息失败: {str(e)}, 路径: {file_path}")
            return result

    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """
        确保目录存在，不存在则创建
        :param directory_path: 目录路径
        :return: 是否成功
        """
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            logger.debug(f"目录确保存在: {directory_path}")
            return True
        except Exception as e:
            logger.error(f"确保目录存在失败: {str(e)}, 路径: {directory_path}")
            return False

    @staticmethod
    def is_safe_path(file_path: str, base_path: str = None) -> bool:
        """
        验证文件路径是否安全，防止路径遍历攻击
        :param file_path: 待验证的文件路径
        :param base_path: 基础路径，如果不提供则使用当前工作目录
        :return: 路径是否安全
        """
        try:
            file_path_obj = Path(file_path).resolve()
            base_path_obj = Path(base_path).resolve() if base_path else Path.cwd().resolve()
            
            # 检查文件路径是否在基础路径内
            file_path_obj.relative_to(base_path_obj)
            logger.debug(f"路径验证通过: {file_path} 在 {base_path_obj} 内")
            return True
        except ValueError:
            logger.warning(f"路径验证失败: {file_path} 超出基础路径 {base_path if base_path else Path.cwd()}")
            return False

    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = 'sha256') -> Optional[str]:
        """
        计算文件哈希值
        :param file_path: 文件路径
        :param algorithm: 哈希算法类型
        :return: 哈希值字符串
        """
        import hashlib
        try:
            hash_func = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            hash_value = hash_func.hexdigest()
            logger.debug(f"计算文件哈希值成功: {file_path}, 算法: {algorithm}, 哈希: {hash_value[:16]}...")
            return hash_value
        except Exception as e:
            logger.error(f"计算文件哈希值失败: {str(e)}, 路径: {file_path}")
            return None