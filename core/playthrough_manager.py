"""
周目管理系统
实现多周目轮回机制
"""

import json
import sqlite3
import time
import uuid
from typing import Optional

try:
    from astrbot.api import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .models import Playthrough, Attribute, CrossPlaythroughMemory


class PlaythroughManager:
    """
    周目管理系统
    管理周目的创建、完成、历史查询等操作
    """

    def __init__(self, db_path: str):
        """
        初始化周目管理系统

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

            # 周目表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playthroughs (
                    id TEXT PRIMARY KEY,
                    playthrough_number INTEGER NOT NULL,
                    status TEXT DEFAULT 'active',
                    route TEXT,
                    started_at REAL,
                    completed_at REAL,
                    ending TEXT,
                    summary TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """)

            # 属性表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attributes (
                    id TEXT PRIMARY KEY,
                    playthrough_id TEXT NOT NULL,
                    attribute_name TEXT NOT NULL,
                    attribute_value REAL DEFAULT 0,
                    max_value REAL DEFAULT 100,
                    min_value REAL DEFAULT 0,
                    category TEXT,
                    icon TEXT,
                    created_at REAL,
                    updated_at REAL,
                    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id)
                )
            """)

            # 跨周目记忆表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cross_playthrough_memories (
                    id TEXT PRIMARY KEY,
                    memory_content TEXT NOT NULL,
                    memory_type TEXT,
                    discovered_at REAL,
                    playthrough_id TEXT,
                    related_scene_id TEXT,
                    importance REAL DEFAULT 0.5,
                    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id),
                    FOREIGN KEY (related_scene_id) REFERENCES scenes(id)
                )
            """)

            # 属性变化历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attribute_history (
                    id TEXT PRIMARY KEY,
                    attribute_id TEXT NOT NULL,
                    old_value REAL,
                    new_value REAL,
                    change_reason TEXT,
                    changed_at REAL,
                    FOREIGN KEY (attribute_id) REFERENCES attributes(id)
                )
            """)

            # 索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attributes_playthrough ON attributes(playthrough_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cross_memories_playthrough ON cross_playthrough_memories(playthrough_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attribute_history_attribute ON attribute_history(attribute_id)")

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"初始化周目数据库失败: {e}")

    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"pt_{uuid.uuid4().hex[:12]}"

    def start_new_playthrough(self, route: str = None) -> Playthrough:
        """
        开始新周目

        Args:
            route: 路线名称

        Returns:
            创建的周目对象
        """
        # 获取当前最大周目编号
        playthrough_number = self._get_next_playthrough_number()
        playthrough_id = self._generate_id()
        now = time.time()

        playthrough = Playthrough(
            id=playthrough_id,
            playthrough_number=playthrough_number,
            status="active",
            route=route,
            started_at=now,
            created_at=now,
            updated_at=now,
        )

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO playthroughs (id, playthrough_number, status, route,
                                         started_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    playthrough.id,
                    playthrough.playthrough_number,
                    playthrough.status,
                    playthrough.route,
                    playthrough.started_at,
                    playthrough.created_at,
                    playthrough.updated_at,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"开始新周目: 第{playthrough_number}周目 (路线: {route or '默认'})")
            return playthrough

        except Exception as e:
            logger.error(f"创建周目失败: {e}")
            raise

    def _get_next_playthrough_number(self) -> int:
        """获取下一个周目编号"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT MAX(playthrough_number) FROM playthroughs")
            result = cursor.fetchone()

            conn.close()

            if result and result[0]:
                return result[0] + 1
            return 1

        except Exception as e:
            logger.error(f"获取周目编号失败: {e}")
            return 1

    def get_playthrough(self, playthrough_id: str) -> Optional[Playthrough]:
        """
        获取周目

        Args:
            playthrough_id: 周目ID

        Returns:
            周目对象，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM playthroughs WHERE id = ?", (playthrough_id,))
            row = cursor.fetchone()

            conn.close()

            if row:
                return Playthrough(
                    id=row[0],
                    playthrough_number=row[1],
                    status=row[2],
                    route=row[3],
                    started_at=row[4],
                    completed_at=row[5],
                    ending=row[6],
                    summary=row[7],
                    created_at=row[8],
                    updated_at=row[9],
                )
            return None

        except Exception as e:
            logger.error(f"获取周目失败: {e}")
            return None

    def get_current_playthrough(self) -> Optional[Playthrough]:
        """
        获取当前活跃的周目

        Returns:
            当前周目对象，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM playthroughs WHERE status = 'active' ORDER BY playthrough_number DESC LIMIT 1"
            )
            row = cursor.fetchone()

            conn.close()

            if row:
                return Playthrough(
                    id=row[0],
                    playthrough_number=row[1],
                    status=row[2],
                    route=row[3],
                    started_at=row[4],
                    completed_at=row[5],
                    ending=row[6],
                    summary=row[7],
                    created_at=row[8],
                    updated_at=row[9],
                )
            return None

        except Exception as e:
            logger.error(f"获取当前周目失败: {e}")
            return None

    def get_playthrough_history(self) -> list[Playthrough]:
        """
        获取周目历史

        Returns:
            周目列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM playthroughs ORDER BY playthrough_number DESC")
            rows = cursor.fetchall()

            conn.close()

            playthroughs = []
            for row in rows:
                playthroughs.append(
                    Playthrough(
                        id=row[0],
                        playthrough_number=row[1],
                        status=row[2],
                        route=row[3],
                        started_at=row[4],
                        completed_at=row[5],
                        ending=row[6],
                        summary=row[7],
                        created_at=row[8],
                        updated_at=row[9],
                    )
                )
            return playthroughs

        except Exception as e:
            logger.error(f"获取周目历史失败: {e}")
            return []

    def complete_playthrough(self, playthrough_id: str, ending: str, summary: str = "") -> Optional[Playthrough]:
        """
        完成周目

        Args:
            playthrough_id: 周目ID
            ending: 结局名称
            summary: 周目摘要

        Returns:
            完成后的周目对象
        """
        playthrough = self.get_playthrough(playthrough_id)
        if not playthrough:
            return None

        playthrough.complete(ending, summary)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE playthroughs
                SET status = ?, ending = ?, summary = ?, completed_at = ?, updated_at = ?
                WHERE id = ?
            """,
                (
                    playthrough.status,
                    playthrough.ending,
                    playthrough.summary,
                    playthrough.completed_at,
                    playthrough.updated_at,
                    playthrough_id,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"完成周目: 第{playthrough.playthrough_number}周目 (结局: {ending})")
            return playthrough

        except Exception as e:
            logger.error(f"完成周目失败: {e}")
            return None

    def abandon_playthrough(self, playthrough_id: str) -> Optional[Playthrough]:
        """
        放弃周目

        Args:
            playthrough_id: 周目ID

        Returns:
            放弃后的周目对象
        """
        playthrough = self.get_playthrough(playthrough_id)
        if not playthrough:
            return None

        playthrough.abandon()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE playthroughs
                SET status = ?, completed_at = ?, updated_at = ?
                WHERE id = ?
            """,
                (playthrough.status, playthrough.completed_at, playthrough.updated_at, playthrough_id),
            )

            conn.commit()
            conn.close()

            logger.info(f"放弃周目: 第{playthrough.playthrough_number}周目")
            return playthrough

        except Exception as e:
            logger.error(f"放弃周目失败: {e}")
            return None

    def delete_playthrough(self, playthrough_id: str) -> bool:
        """
        删除周目（仅允许删除已放弃的周目）

        Args:
            playthrough_id: 周目ID

        Returns:
            是否删除成功
        """
        playthrough = self.get_playthrough(playthrough_id)
        if not playthrough:
            return False

        if playthrough.status != "abandoned":
            logger.warning("只能删除已放弃的周目")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 删除关联数据
            cursor.execute("DELETE FROM scene_events WHERE scene_id IN (SELECT id FROM scenes WHERE playthrough_id = ?)", (playthrough_id,))
            cursor.execute("DELETE FROM scenes WHERE playthrough_id = ?", (playthrough_id,))
            cursor.execute("DELETE FROM attributes WHERE playthrough_id = ?", (playthrough_id,))
            cursor.execute("DELETE FROM saves WHERE playthrough_id = ?", (playthrough_id,))
            cursor.execute("DELETE FROM cross_playthrough_memories WHERE playthrough_id = ?", (playthrough_id,))
            cursor.execute("DELETE FROM playthroughs WHERE id = ?", (playthrough_id,))

            conn.commit()
            conn.close()

            logger.info(f"删除周目: {playthrough_id}")
            return True

        except Exception as e:
            logger.error(f"删除周目失败: {e}")
            return False

    # ============================================
    # 属性管理
    # ============================================

    def create_attribute(
        self,
        playthrough_id: str,
        attribute_name: str,
        initial_value: float = 0.0,
        max_value: float = 100.0,
        min_value: float = 0.0,
        category: str = "other",
        icon: str = None,
    ) -> Attribute:
        """
        创建属性

        Args:
            playthrough_id: 周目ID
            attribute_name: 属性名
            initial_value: 初始值
            max_value: 最大值
            min_value: 最小值
            category: 属性分类
            icon: 图标

        Returns:
            创建的属性对象
        """
        attribute_id = f"attr_{uuid.uuid4().hex[:12]}"
        now = time.time()

        attribute = Attribute(
            id=attribute_id,
            playthrough_id=playthrough_id,
            attribute_name=attribute_name,
            attribute_value=initial_value,
            max_value=max_value,
            min_value=min_value,
            category=category,
            icon=icon,
            created_at=now,
            updated_at=now,
        )

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO attributes (id, playthrough_id, attribute_name, attribute_value,
                                       max_value, min_value, category, icon, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    attribute.id,
                    attribute.playthrough_id,
                    attribute.attribute_name,
                    attribute.attribute_value,
                    attribute.max_value,
                    attribute.min_value,
                    attribute.category,
                    attribute.icon,
                    attribute.created_at,
                    attribute.updated_at,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"创建属性: {attribute_name} = {initial_value}")
            return attribute

        except Exception as e:
            logger.error(f"创建属性失败: {e}")
            raise

    def get_attribute(self, attribute_id: str) -> Optional[Attribute]:
        """
        获取属性

        Args:
            attribute_id: 属性ID

        Returns:
            属性对象，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM attributes WHERE id = ?", (attribute_id,))
            row = cursor.fetchone()

            conn.close()

            if row:
                return Attribute(
                    id=row[0],
                    playthrough_id=row[1],
                    attribute_name=row[2],
                    attribute_value=row[3],
                    max_value=row[4],
                    min_value=row[5],
                    category=row[6],
                    icon=row[7],
                    created_at=row[8],
                    updated_at=row[9],
                )
            return None

        except Exception as e:
            logger.error(f"获取属性失败: {e}")
            return None

    def get_attributes_by_playthrough(self, playthrough_id: str) -> list[Attribute]:
        """
        获取周目的所有属性

        Args:
            playthrough_id: 周目ID

        Returns:
            属性列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM attributes WHERE playthrough_id = ? ORDER BY category, attribute_name", (playthrough_id,))
            rows = cursor.fetchall()

            conn.close()

            attributes = []
            for row in rows:
                attributes.append(
                    Attribute(
                        id=row[0],
                        playthrough_id=row[1],
                        attribute_name=row[2],
                        attribute_value=row[3],
                        max_value=row[4],
                        min_value=row[5],
                        category=row[6],
                        icon=row[7],
                        created_at=row[8],
                        updated_at=row[9],
                    )
                )
            return attributes

        except Exception as e:
            logger.error(f"获取周目属性失败: {e}")
            return []

    def update_attribute_value(self, attribute_id: str, delta: float, reason: str = "") -> Optional[Attribute]:
        """
        更新属性值

        Args:
            attribute_id: 属性ID
            delta: 变化量（正数增加，负数减少）
            reason: 变化原因

        Returns:
            更新后的属性对象
        """
        attribute = self.get_attribute(attribute_id)
        if not attribute:
            return None

        old_value = attribute.attribute_value
        actual_change = attribute.update_value(delta)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 更新属性值
            cursor.execute(
                "UPDATE attributes SET attribute_value = ?, updated_at = ? WHERE id = ?",
                (attribute.attribute_value, attribute.updated_at, attribute_id),
            )

            # 记录变化历史
            history_id = f"hist_{uuid.uuid4().hex[:12]}"
            cursor.execute(
                """
                INSERT INTO attribute_history (id, attribute_id, old_value, new_value, change_reason, changed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (history_id, attribute_id, old_value, attribute.attribute_value, reason, time.time()),
            )

            conn.commit()
            conn.close()

            logger.info(f"更新属性: {attribute.attribute_name} {old_value} -> {attribute.attribute_value} ({reason})")
            return attribute

        except Exception as e:
            logger.error(f"更新属性失败: {e}")
            return None

    def get_attribute_panel(self, playthrough_id: str) -> dict:
        """
        获取属性面板数据

        Args:
            playthrough_id: 周目ID

        Returns:
            属性面板数据
        """
        attributes = self.get_attributes_by_playthrough(playthrough_id)

        # 按分类分组
        categories = {}
        for attr in attributes:
            cat = attr.category or "other"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(
                {
                    "id": attr.id,
                    "name": attr.attribute_name,
                    "value": attr.attribute_value,
                    "max_value": attr.max_value,
                    "min_value": attr.min_value,
                    "percentage": attr.percentage,
                    "icon": attr.icon,
                }
            )

        return {
            "playthrough_id": playthrough_id,
            "categories": categories,
            "total_attributes": len(attributes),
        }

    def get_attribute_history(self, attribute_id: str) -> list[dict]:
        """
        获取属性变化历史

        Args:
            attribute_id: 属性ID

        Returns:
            历史记录列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM attribute_history WHERE attribute_id = ? ORDER BY changed_at DESC",
                (attribute_id,),
            )
            rows = cursor.fetchall()

            conn.close()

            history = []
            for row in rows:
                history.append(
                    {
                        "id": row[0],
                        "attribute_id": row[1],
                        "old_value": row[2],
                        "new_value": row[3],
                        "change_reason": row[4],
                        "changed_at": row[5],
                    }
                )
            return history

        except Exception as e:
            logger.error(f"获取属性历史失败: {e}")
            return []

    # ============================================
    # 跨周目记忆
    # ============================================

    def discover_memory(
        self,
        memory_content: str,
        playthrough_id: str,
        memory_type: str = "memory",
        related_scene_id: str = None,
        importance: float = 0.5,
    ) -> CrossPlaythroughMemory:
        """
        发现跨周目记忆

        Args:
            memory_content: 记忆内容
            playthrough_id: 发现于哪个周目
            memory_type: 记忆类型
            related_scene_id: 相关场景ID
            importance: 重要性

        Returns:
            创建的记忆对象
        """
        memory_id = f"cpm_{uuid.uuid4().hex[:12]}"
        now = time.time()

        memory = CrossPlaythroughMemory(
            id=memory_id,
            memory_content=memory_content,
            memory_type=memory_type,
            discovered_at=now,
            playthrough_id=playthrough_id,
            related_scene_id=related_scene_id,
            importance=importance,
        )

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO cross_playthrough_memories (id, memory_content, memory_type,
                                                       discovered_at, playthrough_id, related_scene_id, importance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    memory.id,
                    memory.memory_content,
                    memory.memory_type,
                    memory.discovered_at,
                    memory.playthrough_id,
                    memory.related_scene_id,
                    memory.importance,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"发现跨周目记忆: {memory_content[:30]}...")
            return memory

        except Exception as e:
            logger.error(f"发现跨周目记忆失败: {e}")
            raise

    def get_cross_playthrough_memories(self, playthrough_id: str = None) -> list[CrossPlaythroughMemory]:
        """
        获取跨周目记忆

        Args:
            playthrough_id: 周目ID（如果为None则获取所有）

        Returns:
            记忆列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if playthrough_id:
                cursor.execute(
                    "SELECT * FROM cross_playthrough_memories WHERE playthrough_id = ? ORDER BY discovered_at DESC",
                    (playthrough_id,),
                )
            else:
                cursor.execute("SELECT * FROM cross_playthrough_memories ORDER BY discovered_at DESC")

            rows = cursor.fetchall()

            conn.close()

            memories = []
            for row in rows:
                memories.append(
                    CrossPlaythroughMemory(
                        id=row[0],
                        memory_content=row[1],
                        memory_type=row[2],
                        discovered_at=row[3],
                        playthrough_id=row[4],
                        related_scene_id=row[5],
                        importance=row[6],
                    )
                )
            return memories

        except Exception as e:
            logger.error(f"获取跨周目记忆失败: {e}")
            return []

    def get_recall_panel(self, playthrough_id: str) -> dict:
        """
        获取回忆面板数据

        Args:
            playthrough_id: 周目ID

        Returns:
            回忆面板数据
        """
        playthrough = self.get_playthrough(playthrough_id)
        if not playthrough:
            return {}

        # 获取所有跨周目记忆
        all_memories = self.get_cross_playthrough_memories()

        # 按类型分组
        memory_by_type = {}
        for memory in all_memories:
            mem_type = memory.memory_type or "memory"
            if mem_type not in memory_by_type:
                memory_by_type[mem_type] = []
            memory_by_type[mem_type].append(
                {
                    "id": memory.id,
                    "content": memory.memory_content,
                    "discovered_at": memory.discovered_at,
                    "playthrough_id": memory.playthrough_id,
                    "importance": memory.importance,
                }
            )

        return {
            "current_playthrough": {
                "id": playthrough.id,
                "number": playthrough.playthrough_number,
                "route": playthrough.route,
                "status": playthrough.status,
            },
            "memories": memory_by_type,
            "total_memories": len(all_memories),
        }
