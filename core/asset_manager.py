"""
视觉资产管理模块
实现图片、视频、音频的上传、存储和管理
"""

import hashlib
import json
import os
import shutil
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Optional

try:
    from astrbot.api import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .models import VisualAsset


class AssetManager:
    """
    视觉资产管理系统
    管理图片、视频、音频等媒体文件
    """

    def __init__(self, db_path: str, assets_dir: str = "assets"):
        """
        初始化资产管理系统

        Args:
            db_path: 数据库路径
            assets_dir: 资产存储目录
        """
        self.db_path = db_path
        self.assets_dir = Path(assets_dir)
        self._ensure_directories()
        self._ensure_db_schema()

    def _ensure_directories(self):
        """确保资产目录存在"""
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        (self.assets_dir / "images").mkdir(exist_ok=True)
        (self.assets_dir / "videos").mkdir(exist_ok=True)
        (self.assets_dir / "audio").mkdir(exist_ok=True)
        (self.assets_dir / "thumbnails").mkdir(exist_ok=True)

    def _ensure_db_schema(self):
        """确保数据库表存在"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visual_assets (
                    id TEXT PRIMARY KEY,
                    scene_id TEXT,
                    asset_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT,
                    thumbnail_path TEXT,
                    file_size INTEGER,
                    mime_type TEXT,
                    metadata TEXT,
                    created_at REAL,
                    FOREIGN KEY (scene_id) REFERENCES scenes(id)
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_visual_assets_scene ON visual_assets(scene_id)")

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"初始化资产数据库失败: {e}")

    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"asset_{uuid.uuid4().hex[:12]}"

    def _get_mime_type(self, file_path: str) -> str:
        """获取文件MIME类型"""
        ext = Path(file_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg",
            ".flac": "audio/flac",
        }
        return mime_types.get(ext, "application/octet-stream")

    def _get_asset_type(self, mime_type: str) -> str:
        """根据MIME类型获取资产类型"""
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("audio/"):
            return "audio"
        return "other"

    def upload_asset(
        self,
        file_path: str,
        scene_id: str = None,
        metadata: dict = None,
    ) -> VisualAsset:
        """
        上传资产

        Args:
            file_path: 文件路径
            scene_id: 场景ID
            metadata: 元数据

        Returns:
            创建的资产对象
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        asset_id = self._generate_id()
        mime_type = self._get_mime_type(file_path)
        asset_type = self._get_asset_type(mime_type)
        file_name = Path(file_path).name
        file_size = os.path.getsize(file_path)

        # 生成存储路径
        ext = Path(file_path).suffix
        storage_name = f"{asset_id}{ext}"
        asset_dir = self.assets_dir / f"{asset_type}s"
        storage_path = asset_dir / storage_name

        # 复制文件
        shutil.copy2(file_path, storage_path)

        # 生成缩略图（仅图片）
        thumbnail_path = None
        if asset_type == "image":
            thumbnail_path = self._generate_thumbnail(str(storage_path), asset_id)

        now = time.time()
        asset = VisualAsset(
            id=asset_id,
            scene_id=scene_id,
            asset_type=asset_type,
            file_path=str(storage_path),
            file_name=file_name,
            thumbnail_path=thumbnail_path,
            file_size=file_size,
            mime_type=mime_type,
            metadata=json.dumps(metadata) if metadata else None,
            created_at=now,
        )

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO visual_assets (id, scene_id, asset_type, file_path, file_name,
                                          thumbnail_path, file_size, mime_type, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    asset.id,
                    asset.scene_id,
                    asset.asset_type,
                    asset.file_path,
                    asset.file_name,
                    asset.thumbnail_path,
                    asset.file_size,
                    asset.mime_type,
                    asset.metadata,
                    asset.created_at,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"上传资产: {file_name} (类型: {asset_type})")
            return asset

        except Exception as e:
            # 清理已上传的文件
            if os.path.exists(storage_path):
                os.remove(storage_path)
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            logger.error(f"上传资产失败: {e}")
            raise

    def _generate_thumbnail(self, image_path: str, asset_id: str) -> Optional[str]:
        """
        生成缩略图

        Args:
            image_path: 原图路径
            asset_id: 资产ID

        Returns:
            缩略图路径
        """
        try:
            from PIL import Image

            thumbnail_dir = self.assets_dir / "thumbnails"
            thumbnail_path = thumbnail_dir / f"{asset_id}_thumb.jpg"

            with Image.open(image_path) as img:
                # 保持比例，最大尺寸 200x200
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", quality=85)

            return str(thumbnail_path)

        except ImportError:
            logger.warning("Pillow未安装，跳过缩略图生成")
            return None
        except Exception as e:
            logger.warning(f"生成缩略图失败: {e}")
            return None

    def get_asset(self, asset_id: str) -> Optional[VisualAsset]:
        """
        获取资产

        Args:
            asset_id: 资产ID

        Returns:
            资产对象，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM visual_assets WHERE id = ?", (asset_id,))
            row = cursor.fetchone()

            conn.close()

            if row:
                return VisualAsset(
                    id=row[0],
                    scene_id=row[1],
                    asset_type=row[2],
                    file_path=row[3],
                    file_name=row[4],
                    thumbnail_path=row[5],
                    file_size=row[6],
                    mime_type=row[7],
                    metadata=row[8],
                    created_at=row[9],
                )
            return None

        except Exception as e:
            logger.error(f"获取资产失败: {e}")
            return None

    def get_scene_assets(self, scene_id: str) -> dict:
        """
        获取场景的所有资产

        Args:
            scene_id: 场景ID

        Returns:
            按类型分组的资产数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM visual_assets WHERE scene_id = ? ORDER BY created_at",
                (scene_id,),
            )
            rows = cursor.fetchall()

            conn.close()

            # 按类型分组
            assets_by_type = {"image": [], "video": [], "audio": []}
            for row in rows:
                asset = VisualAsset(
                    id=row[0],
                    scene_id=row[1],
                    asset_type=row[2],
                    file_path=row[3],
                    file_name=row[4],
                    thumbnail_path=row[5],
                    file_size=row[6],
                    mime_type=row[7],
                    metadata=row[8],
                    created_at=row[9],
                )

                asset_data = {
                    "id": asset.id,
                    "file_name": asset.file_name,
                    "file_path": asset.file_path,
                    "thumbnail_path": asset.thumbnail_path,
                    "file_size": asset.file_size,
                    "mime_type": asset.mime_type,
                    "created_at": asset.created_at,
                }

                if asset.asset_type in assets_by_type:
                    assets_by_type[asset.asset_type].append(asset_data)
                else:
                    if "other" not in assets_by_type:
                        assets_by_type["other"] = []
                    assets_by_type["other"].append(asset_data)

            return {
                "scene_id": scene_id,
                "assets": assets_by_type,
                "total_count": len(rows),
                "total_size": sum(row[6] for row in rows if row[6]),
            }

        except Exception as e:
            logger.error(f"获取场景资产失败: {e}")
            return {"scene_id": scene_id, "assets": {}, "total_count": 0, "total_size": 0}

    def delete_asset(self, asset_id: str) -> bool:
        """
        删除资产

        Args:
            asset_id: 资产ID

        Returns:
            是否删除成功
        """
        asset = self.get_asset(asset_id)
        if not asset:
            return False

        try:
            # 删除文件
            if os.path.exists(asset.file_path):
                os.remove(asset.file_path)

            if asset.thumbnail_path and os.path.exists(asset.thumbnail_path):
                os.remove(asset.thumbnail_path)

            # 删除数据库记录
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM visual_assets WHERE id = ?", (asset_id,))

            conn.commit()
            conn.close()

            logger.info(f"删除资产: {asset.file_name}")
            return True

        except Exception as e:
            logger.error(f"删除资产失败: {e}")
            return False

    def get_asset_stats(self, scene_id: str = None) -> dict:
        """
        获取资产统计信息

        Args:
            scene_id: 场景ID（可选）

        Returns:
            统计信息
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if scene_id:
                cursor.execute(
                    "SELECT asset_type, COUNT(*), SUM(file_size) FROM visual_assets WHERE scene_id = ? GROUP BY asset_type",
                    (scene_id,),
                )
            else:
                cursor.execute(
                    "SELECT asset_type, COUNT(*), SUM(file_size) FROM visual_assets GROUP BY asset_type"
                )

            rows = cursor.fetchall()

            conn.close()

            stats = {"image": {"count": 0, "size": 0}, "video": {"count": 0, "size": 0}, "audio": {"count": 0, "size": 0}}
            total_count = 0
            total_size = 0

            for row in rows:
                asset_type = row[0]
                count = row[1] or 0
                size = row[2] or 0

                if asset_type in stats:
                    stats[asset_type]["count"] = count
                    stats[asset_type]["size"] = size

                total_count += count
                total_size += size

            return {
                "by_type": stats,
                "total_count": total_count,
                "total_size": total_size,
            }

        except Exception as e:
            logger.error(f"获取资产统计失败: {e}")
            return {"by_type": {}, "total_count": 0, "total_size": 0}
