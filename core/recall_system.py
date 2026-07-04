"""
回忆系统
实现跨周目记忆、结局追踪和命运地图
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

from .models import CrossPlaythroughMemory


class RecallSystem:
    """
    回忆系统
    管理跨周目记忆、结局解锁和命运地图
    """

    def __init__(self, db_path: str):
        """
        初始化回忆系统

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

            # 结局解锁表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unlocked_endings (
                    id TEXT PRIMARY KEY,
                    ending_name TEXT NOT NULL,
                    ending_description TEXT,
                    unlocked_at REAL,
                    playthrough_id TEXT,
                    ending_data TEXT,
                    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id)
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cross_memories_playthrough ON cross_playthrough_memories(playthrough_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_unlocked_endings_playthrough ON unlocked_endings(playthrough_id)")

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"初始化回忆系统数据库失败: {e}")

    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"recall_{uuid.uuid4().hex[:12]}"

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
            memory_type: 记忆类型 (memory/ending/achievement/discovery)
            related_scene_id: 相关场景ID
            importance: 重要性 (0-1)

        Returns:
            创建的记忆对象
        """
        memory_id = self._generate_id()
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

            logger.info(f"发现跨周目记忆: {memory_content[:50]}...")
            return memory

        except Exception as e:
            logger.error(f"发现跨周目记忆失败: {e}")
            raise

    def get_memories(
        self,
        playthrough_id: str = None,
        memory_type: str = None,
        limit: int = 50,
    ) -> list[CrossPlaythroughMemory]:
        """
        获取跨周目记忆

        Args:
            playthrough_id: 周目ID（可选）
            memory_type: 记忆类型（可选）
            limit: 返回数量限制

        Returns:
            记忆列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT * FROM cross_playthrough_memories WHERE 1=1"
            params = []

            if playthrough_id:
                query += " AND playthrough_id = ?"
                params.append(playthrough_id)

            if memory_type:
                query += " AND memory_type = ?"
                params.append(memory_type)

            query += " ORDER BY importance DESC, discovered_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
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

    def delete_memory(self, memory_id: str) -> bool:
        """
        删除跨周目记忆

        Args:
            memory_id: 记忆ID

        Returns:
            是否删除成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM cross_playthrough_memories WHERE id = ?", (memory_id,))

            conn.commit()
            conn.close()

            logger.info(f"删除跨周目记忆: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"删除跨周目记忆失败: {e}")
            return False

    # ============================================
    # 结局解锁
    # ============================================

    def unlock_ending(
        self,
        ending_name: str,
        playthrough_id: str,
        ending_description: str = "",
        ending_data: dict = None,
    ) -> dict:
        """
        解锁结局

        Args:
            ending_name: 结局名称
            playthrough_id: 解锁于哪个周目
            ending_description: 结局描述
            ending_data: 结局数据

        Returns:
            解锁的结局信息
        """
        # 检查是否已解锁
        if self.is_ending_unlocked(ending_name):
            logger.info(f"结局已解锁: {ending_name}")
            return {"status": "already_unlocked", "ending_name": ending_name}

        ending_id = f"ending_{uuid.uuid4().hex[:12]}"
        now = time.time()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO unlocked_endings (id, ending_name, ending_description,
                                             unlocked_at, playthrough_id, ending_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    ending_id,
                    ending_name,
                    ending_description,
                    now,
                    playthrough_id,
                    json.dumps(ending_data) if ending_data else None,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"解锁结局: {ending_name}")
            return {
                "status": "unlocked",
                "ending_id": ending_id,
                "ending_name": ending_name,
                "unlocked_at": now,
            }

        except Exception as e:
            logger.error(f"解锁结局失败: {e}")
            raise

    def is_ending_unlocked(self, ending_name: str) -> bool:
        """
        检查结局是否已解锁

        Args:
            ending_name: 结局名称

        Returns:
            是否已解锁
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM unlocked_endings WHERE ending_name = ?", (ending_name,))
            count = cursor.fetchone()[0]

            conn.close()

            return count > 0

        except Exception as e:
            logger.error(f"检查结局解锁状态失败: {e}")
            return False

    def get_unlocked_endings(self, playthrough_id: str = None) -> list[dict]:
        """
        获取已解锁的结局

        Args:
            playthrough_id: 周目ID（可选）

        Returns:
            已解锁结局列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if playthrough_id:
                cursor.execute(
                    "SELECT * FROM unlocked_endings WHERE playthrough_id = ? ORDER BY unlocked_at DESC",
                    (playthrough_id,),
                )
            else:
                cursor.execute("SELECT * FROM unlocked_endings ORDER BY unlocked_at DESC")

            rows = cursor.fetchall()

            conn.close()

            endings = []
            for row in rows:
                endings.append(
                    {
                        "id": row[0],
                        "ending_name": row[1],
                        "ending_description": row[2],
                        "unlocked_at": row[3],
                        "playthrough_id": row[4],
                        "ending_data": json.loads(row[5]) if row[5] else None,
                    }
                )
            return endings

        except Exception as e:
            logger.error(f"获取已解锁结局失败: {e}")
            return []

    # ============================================
    # 命运地图
    # ============================================

    def get_destiny_map(self) -> dict:
        """
        获取命运地图（所有周目路线）

        Returns:
            命运地图数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取所有周目
            cursor.execute("SELECT * FROM playthroughs ORDER BY playthrough_number")
            playthroughs = cursor.fetchall()

            # 获取所有结局
            cursor.execute("SELECT * FROM unlocked_endings ORDER BY unlocked_at")
            endings = cursor.fetchall()

            # 获取所有跨周目记忆
            cursor.execute(
                "SELECT * FROM cross_playthrough_memories ORDER BY discovered_at"
            )
            memories = cursor.fetchall()

            conn.close()

            # 构建命运地图
            destiny_map = {
                "playthroughs": [],
                "endings": [],
                "memories": [],
                "summary": {
                    "total_playthroughs": len(playthroughs),
                    "completed_playthroughs": 0,
                    "unlocked_endings": len(endings),
                    "total_memories": len(memories),
                },
            }

            # 周目数据
            for pt in playthroughs:
                pt_data = {
                    "id": pt[0],
                    "number": pt[1],
                    "status": pt[2],
                    "route": pt[3],
                    "started_at": pt[4],
                    "completed_at": pt[5],
                    "ending": pt[6],
                }
                destiny_map["playthroughs"].append(pt_data)

                if pt[2] == "completed":
                    destiny_map["summary"]["completed_playthroughs"] += 1

            # 结局数据
            for ending in endings:
                destiny_map["endings"].append(
                    {
                        "id": ending[0],
                        "name": ending[1],
                        "description": ending[2],
                        "unlocked_at": ending[3],
                        "playthrough_id": ending[4],
                    }
                )

            # 记忆数据
            for memory in memories:
                destiny_map["memories"].append(
                    {
                        "id": memory[0],
                        "content": memory[1],
                        "type": memory[2],
                        "discovered_at": memory[3],
                        "playthrough_id": memory[4],
                        "importance": memory[6],
                    }
                )

            return destiny_map

        except Exception as e:
            logger.error(f"获取命运地图失败: {e}")
            return {}

    def get_recall_panel(self, playthrough_id: str) -> dict:
        """
        获取回忆面板数据

        Args:
            playthrough_id: 周目ID

        Returns:
            回忆面板数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取当前周目
            cursor.execute("SELECT * FROM playthroughs WHERE id = ?", (playthrough_id,))
            playthrough = cursor.fetchone()

            if not playthrough:
                return {}

            # 获取该周目发现的记忆
            cursor.execute(
                "SELECT * FROM cross_playthrough_memories WHERE playthrough_id = ? ORDER BY discovered_at DESC",
                (playthrough_id,),
            )
            memories = cursor.fetchall()

            # 获取已解锁的结局
            cursor.execute(
                "SELECT * FROM unlocked_endings ORDER BY unlocked_at DESC"
            )
            endings = cursor.fetchall()

            # 获取场景历史
            cursor.execute(
                "SELECT * FROM scenes WHERE playthrough_id = ? AND status = 'completed' ORDER BY updated_at",
                (playthrough_id,),
            )
            completed_scenes = cursor.fetchall()

            conn.close()

            return {
                "current_playthrough": {
                    "id": playthrough[0],
                    "number": playthrough[1],
                    "status": playthrough[2],
                    "route": playthrough[3],
                    "started_at": playthrough[4],
                    "ending": playthrough[6],
                },
                "memories": [
                    {
                        "id": m[0],
                        "content": m[1],
                        "type": m[2],
                        "discovered_at": m[3],
                        "importance": m[6],
                    }
                    for m in memories
                ],
                "endings": [
                    {
                        "id": e[0],
                        "name": e[1],
                        "description": e[2],
                        "unlocked_at": e[3],
                    }
                    for e in endings
                ],
                "completed_scenes": [
                    {
                        "id": s[0],
                        "chapter": s[2],
                        "scene_number": s[3],
                        "name": s[4],
                        "completed_at": s[10],
                    }
                    for s in completed_scenes
                ],
                "summary": {
                    "total_memories": len(memories),
                    "total_endings": len(endings),
                    "completed_scenes": len(completed_scenes),
                },
            }

        except Exception as e:
            logger.error(f"获取回忆面板失败: {e}")
            return {}
