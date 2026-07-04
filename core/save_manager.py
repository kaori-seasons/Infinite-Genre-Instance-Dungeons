"""
存档管理系统
实现自动存档、手动存档、导入导出功能
"""

import base64
import hashlib
import json
import sqlite3
import time
import uuid
import zlib
from typing import Optional

try:
    from astrbot.api import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .models import Save


class SaveManager:
    """
    存档管理系统
    管理存档的创建、加载、导出、导入等操作
    """

    def __init__(self, db_path: str):
        """
        初始化存档管理系统

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self._ensure_db_schema()

    def _ensure_db_schema(self):
        """确保数据库表存在"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saves (
                    id TEXT PRIMARY KEY,
                    playthrough_id TEXT NOT NULL,
                    save_type TEXT DEFAULT 'auto',
                    save_name TEXT,
                    save_data TEXT NOT NULL,
                    created_at REAL,
                    file_size INTEGER,
                    version TEXT DEFAULT '1.0',
                    checksum TEXT,
                    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id)
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_saves_playthrough ON saves(playthrough_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_saves_type ON saves(save_type)")

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"初始化存档数据库失败: {e}")

    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"save_{uuid.uuid4().hex[:12]}"

    def _calculate_checksum(self, data: str) -> str:
        """计算校验和"""
        return hashlib.md5(data.encode()).hexdigest()

    def _compress_data(self, data: str) -> str:
        """压缩数据"""
        try:
            compressed = zlib.compress(data.encode('utf-8'))
            return base64.b64encode(compressed).decode('ascii')
        except Exception as e:
            logger.warning(f"压缩数据失败: {e}")
            return data

    def _decompress_data(self, data: str) -> str:
        """解压数据"""
        try:
            decoded = base64.b64decode(data)
            return zlib.decompress(decoded).decode('utf-8')
        except Exception as e:
            # 如果解压失败，返回原始数据
            return data

    def create_save(
        self,
        playthrough_id: str,
        save_type: str = "auto",
        save_name: str = None,
        save_data: dict = None,
    ) -> Save:
        """
        创建存档

        Args:
            playthrough_id: 周目ID
            save_type: 存档类型 (auto/manual/export)
            save_name: 存档名称
            save_data: 存档数据

        Returns:
            创建的存档对象
        """
        save_id = self._generate_id()
        now = time.time()

        # 序列化存档数据
        data_str = json.dumps(save_data or {}, ensure_ascii=False)
        compressed_data = self._compress_data(data_str)
        checksum = self._calculate_checksum(data_str)

        save = Save(
            id=save_id,
            playthrough_id=playthrough_id,
            save_type=save_type,
            save_name=save_name or f"存档_{time.strftime('%Y%m%d_%H%M%S', time.localtime(now))}",
            save_data=compressed_data,
            created_at=now,
            file_size=len(compressed_data),
            version="1.0",
            checksum=checksum,
        )

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO saves (id, playthrough_id, save_type, save_name, save_data,
                                  created_at, file_size, version, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    save.id,
                    save.playthrough_id,
                    save.save_type,
                    save.save_name,
                    save.save_data,
                    save.created_at,
                    save.file_size,
                    save.version,
                    save.checksum,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"创建存档: {save.save_name} (类型: {save_type})")
            return save

        except Exception as e:
            logger.error(f"创建存档失败: {e}")
            raise

    def auto_save(self, playthrough_id: str, save_data: dict = None) -> Save:
        """
        自动存档

        Args:
            playthrough_id: 周目ID
            save_data: 存档数据

        Returns:
            创建的存档对象
        """
        # 检查是否已有自动存档，如果有则更新
        existing_save = self.get_latest_auto_save(playthrough_id)
        if existing_save:
            return self.update_save(existing_save.id, save_data)
        return self.create_save(playthrough_id, "auto", None, save_data)

    def manual_save(self, playthrough_id: str, save_name: str, save_data: dict = None) -> Save:
        """
        手动存档

        Args:
            playthrough_id: 周目ID
            save_name: 存档名称
            save_data: 存档数据

        Returns:
            创建的存档对象
        """
        return self.create_save(playthrough_id, "manual", save_name, save_data)

    def get_save(self, save_id: str) -> Optional[Save]:
        """
        获取存档

        Args:
            save_id: 存档ID

        Returns:
            存档对象，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM saves WHERE id = ?", (save_id,))
            row = cursor.fetchone()

            conn.close()

            if row:
                return Save(
                    id=row[0],
                    playthrough_id=row[1],
                    save_type=row[2],
                    save_name=row[3],
                    save_data=row[4],
                    created_at=row[5],
                    file_size=row[6],
                    version=row[7],
                    checksum=row[8],
                )
            return None

        except Exception as e:
            logger.error(f"获取存档失败: {e}")
            return None

    def load_save(self, save_id: str) -> Optional[dict]:
        """
        加载存档数据

        Args:
            save_id: 存档ID

        Returns:
            存档数据，如果不存在或校验失败则返回None
        """
        save = self.get_save(save_id)
        if not save:
            return None

        try:
            # 解压数据
            data_str = self._decompress_data(save.save_data)

            # 验证校验和
            checksum = self._calculate_checksum(data_str)
            if checksum != save.checksum:
                logger.warning(f"存档校验和不匹配: {save_id}")
                # 仍然尝试加载，但记录警告

            # 解析JSON
            save_data = json.loads(data_str)
            return save_data

        except Exception as e:
            logger.error(f"加载存档数据失败: {e}")
            return None

    def update_save(self, save_id: str, save_data: dict = None) -> Optional[Save]:
        """
        更新存档

        Args:
            save_id: 存档ID
            save_data: 新的存档数据

        Returns:
            更新后的存档对象
        """
        save = self.get_save(save_id)
        if not save:
            return None

        if save_data is not None:
            data_str = json.dumps(save_data, ensure_ascii=False)
            save.save_data = self._compress_data(data_str)
            save.checksum = self._calculate_checksum(data_str)
            save.file_size = len(save.save_data)

        save.updated_at = time.time()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE saves
                SET save_data = ?, file_size = ?, checksum = ?
                WHERE id = ?
            """,
                (save.save_data, save.file_size, save.checksum, save_id),
            )

            conn.commit()
            conn.close()

            logger.info(f"更新存档: {save.save_name}")
            return save

        except Exception as e:
            logger.error(f"更新存档失败: {e}")
            return None

    def delete_save(self, save_id: str) -> bool:
        """
        删除存档

        Args:
            save_id: 存档ID

        Returns:
            是否删除成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM saves WHERE id = ?", (save_id,))

            conn.commit()
            conn.close()

            logger.info(f"删除存档: {save_id}")
            return True

        except Exception as e:
            logger.error(f"删除存档失败: {e}")
            return False

    def get_save_list(self, playthrough_id: str) -> list[dict]:
        """
        获取存档列表

        Args:
            playthrough_id: 周目ID

        Returns:
            存档列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, playthrough_id, save_type, save_name, created_at, file_size, version FROM saves WHERE playthrough_id = ? ORDER BY created_at DESC",
                (playthrough_id,),
            )
            rows = cursor.fetchall()

            conn.close()

            saves = []
            for row in rows:
                saves.append(
                    {
                        "id": row[0],
                        "playthrough_id": row[1],
                        "save_type": row[2],
                        "save_name": row[3],
                        "created_at": row[4],
                        "file_size": row[5],
                        "version": row[6],
                    }
                )
            return saves

        except Exception as e:
            logger.error(f"获取存档列表失败: {e}")
            return []

    def get_latest_auto_save(self, playthrough_id: str) -> Optional[Save]:
        """
        获取最新的自动存档

        Args:
            playthrough_id: 周目ID

        Returns:
            最新的自动存档对象
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM saves WHERE playthrough_id = ? AND save_type = 'auto' ORDER BY created_at DESC LIMIT 1",
                (playthrough_id,),
            )
            row = cursor.fetchone()

            conn.close()

            if row:
                return Save(
                    id=row[0],
                    playthrough_id=row[1],
                    save_type=row[2],
                    save_name=row[3],
                    save_data=row[4],
                    created_at=row[5],
                    file_size=row[6],
                    version=row[7],
                    checksum=row[8],
                )
            return None

        except Exception as e:
            logger.error(f"获取最新自动存档失败: {e}")
            return None

    def export_save(self, save_id: str) -> Optional[str]:
        """
        导出存档（Base64编码）

        Args:
            save_id: 存档ID

        Returns:
            Base64编码的存档数据
        """
        save = self.get_save(save_id)
        if not save:
            return None

        try:
            # 创建导出数据
            export_data = {
                "version": save.version,
                "save_id": save.id,
                "playthrough_id": save.playthrough_id,
                "save_name": save.save_name,
                "created_at": save.created_at,
                "checksum": save.checksum,
                "data": save.save_data,
            }

            # 序列化并编码
            export_str = json.dumps(export_data, ensure_ascii=False)
            return base64.b64encode(export_str.encode()).decode('ascii')

        except Exception as e:
            logger.error(f"导出存档失败: {e}")
            return None

    def import_save(self, export_data: str) -> Optional[Save]:
        """
        导入存档

        Args:
            export_data: Base64编码的存档数据

        Returns:
            导入的存档对象
        """
        try:
            # 解码
            decoded = base64.b64decode(export_data).decode('ascii')
            import_data = json.loads(decoded)

            # 验证版本
            if "version" not in import_data:
                logger.error("导入数据缺少版本信息")
                return None

            # 验证校验和
            data_str = self._decompress_data(import_data.get("data", ""))
            checksum = self._calculate_checksum(data_str)
            if checksum != import_data.get("checksum"):
                logger.warning("导入数据校验和不匹配，继续导入")

            # 创建存档
            save = self.create_save(
                playthrough_id=import_data.get("playthrough_id", "unknown"),
                save_type="import",
                save_name=f"导入_{import_data.get('save_name', '未命名')}",
                save_data=json.loads(data_str),
            )

            return save

        except Exception as e:
            logger.error(f"导入存档失败: {e}")
            return None

    def cleanup_old_saves(self, playthrough_id: str, keep_count: int = 10) -> int:
        """
        清理旧的自动存档

        Args:
            playthrough_id: 周目ID
            keep_count: 保留的自动存档数量

        Returns:
            删除的存档数量
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取所有自动存档
            cursor.execute(
                "SELECT id FROM saves WHERE playthrough_id = ? AND save_type = 'auto' ORDER BY created_at DESC",
                (playthrough_id,),
            )
            rows = cursor.fetchall()

            # 删除多余的存档
            deleted_count = 0
            for i, row in enumerate(rows):
                if i >= keep_count:
                    cursor.execute("DELETE FROM saves WHERE id = ?", (row[0],))
                    deleted_count += 1

            conn.commit()
            conn.close()

            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 个旧的自动存档")

            return deleted_count

        except Exception as e:
            logger.error(f"清理旧存档失败: {e}")
            return 0
