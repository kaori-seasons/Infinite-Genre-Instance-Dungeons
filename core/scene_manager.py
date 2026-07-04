"""
场景管理系统
实现按"夜/章节"分组的场景时间线
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

from .models import Scene, SceneEvent


class SceneManager:
    """
    场景管理系统
    管理场景的创建、更新、完成等操作
    """

    def __init__(self, db_path: str):
        """
        初始化场景管理系统

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

            # 场景表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scenes (
                    id TEXT PRIMARY KEY,
                    playthrough_id TEXT NOT NULL,
                    chapter TEXT NOT NULL,
                    scene_number TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'locked',
                    progress INTEGER DEFAULT 0,
                    sort_order INTEGER DEFAULT 0,
                    created_at REAL,
                    updated_at REAL,
                    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id)
                )
            """)

            # 场景事件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scene_events (
                    id TEXT PRIMARY KEY,
                    scene_id TEXT NOT NULL,
                    event_type TEXT,
                    event_content TEXT NOT NULL,
                    event_data TEXT,
                    created_at REAL,
                    FOREIGN KEY (scene_id) REFERENCES scenes(id)
                )
            """)

            # 索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scenes_playthrough ON scenes(playthrough_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scenes_chapter ON scenes(playthrough_id, chapter)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scenes_status ON scenes(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scene_events_scene ON scene_events(scene_id)")

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"初始化场景数据库失败: {e}")

    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"scene_{uuid.uuid4().hex[:12]}"

    def create_scene(
        self,
        playthrough_id: str,
        chapter: str,
        scene_number: str,
        name: str,
        description: str = "",
        sort_order: int = 0,
        auto_activate: bool = False,
    ) -> Scene:
        """
        创建场景

        Args:
            playthrough_id: 周目ID
            chapter: 章节/夜
            scene_number: 场景编号
            name: 场景名称
            description: 场景描述
            sort_order: 排序顺序
            auto_activate: 是否自动激活（如果是第一个场景）

        Returns:
            创建的场景对象
        """
        scene_id = self._generate_id()
        now = time.time()

        # 如果是自动激活，检查是否是该章节的第一个场景
        if auto_activate:
            existing_scenes = self.get_scenes_by_chapter(playthrough_id, chapter)
            if not existing_scenes:
                status = "active"
            else:
                status = "locked"
        else:
            status = "locked"

        scene = Scene(
            id=scene_id,
            playthrough_id=playthrough_id,
            chapter=chapter,
            scene_number=scene_number,
            name=name,
            description=description,
            status=status,
            progress=0,
            sort_order=sort_order,
            created_at=now,
            updated_at=now,
        )

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO scenes (id, playthrough_id, chapter, scene_number, name,
                                   description, status, progress, sort_order, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    scene.id,
                    scene.playthrough_id,
                    scene.chapter,
                    scene.scene_number,
                    scene.name,
                    scene.description,
                    scene.status,
                    scene.progress,
                    scene.sort_order,
                    scene.created_at,
                    scene.updated_at,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(f"创建场景: {scene.chapter} {scene.scene_number} - {scene.name}")
            return scene

        except Exception as e:
            logger.error(f"创建场景失败: {e}")
            raise

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """
        获取场景

        Args:
            scene_id: 场景ID

        Returns:
            场景对象，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,))
            row = cursor.fetchone()

            conn.close()

            if row:
                return Scene(
                    id=row[0],
                    playthrough_id=row[1],
                    chapter=row[2],
                    scene_number=row[3],
                    name=row[4],
                    description=row[5] or "",
                    status=row[6],
                    progress=row[7],
                    sort_order=row[8],
                    created_at=row[9],
                    updated_at=row[10],
                )
            return None

        except Exception as e:
            logger.error(f"获取场景失败: {e}")
            return None

    def get_scenes_by_playthrough(self, playthrough_id: str) -> list[Scene]:
        """
        获取周目的所有场景

        Args:
            playthrough_id: 周目ID

        Returns:
            场景列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM scenes WHERE playthrough_id = ? ORDER BY sort_order, chapter, scene_number",
                (playthrough_id,),
            )
            rows = cursor.fetchall()

            conn.close()

            scenes = []
            for row in rows:
                scenes.append(
                    Scene(
                        id=row[0],
                        playthrough_id=row[1],
                        chapter=row[2],
                        scene_number=row[3],
                        name=row[4],
                        description=row[5] or "",
                        status=row[6],
                        progress=row[7],
                        sort_order=row[8],
                        created_at=row[9],
                        updated_at=row[10],
                    )
                )
            return scenes

        except Exception as e:
            logger.error(f"获取周目场景失败: {e}")
            return []

    def get_scenes_by_chapter(self, playthrough_id: str, chapter: str) -> list[Scene]:
        """
        获取章节的所有场景

        Args:
            playthrough_id: 周目ID
            chapter: 章节名称

        Returns:
            场景列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM scenes WHERE playthrough_id = ? AND chapter = ? ORDER BY sort_order, scene_number",
                (playthrough_id, chapter),
            )
            rows = cursor.fetchall()

            conn.close()

            scenes = []
            for row in rows:
                scenes.append(
                    Scene(
                        id=row[0],
                        playthrough_id=row[1],
                        chapter=row[2],
                        scene_number=row[3],
                        name=row[4],
                        description=row[5] or "",
                        status=row[6],
                        progress=row[7],
                        sort_order=row[8],
                        created_at=row[9],
                        updated_at=row[10],
                    )
                )
            return scenes

        except Exception as e:
            logger.error(f"获取章节场景失败: {e}")
            return []

    def get_scene_timeline(self, playthrough_id: str) -> dict:
        """
        获取场景时间线（按章节分组）

        Args:
            playthrough_id: 周目ID

        Returns:
            时间线数据
        """
        scenes = self.get_scenes_by_playthrough(playthrough_id)

        # 按章节分组
        chapters = {}
        for scene in scenes:
            if scene.chapter not in chapters:
                chapters[scene.chapter] = {
                    "chapter_name": scene.chapter,
                    "scenes": [],
                    "total_scenes": 0,
                    "completed_scenes": 0,
                    "active_scenes": 0,
                }

            chapters[scene.chapter]["scenes"].append(
                {
                    "id": scene.id,
                    "scene_number": scene.scene_number,
                    "name": scene.name,
                    "status": scene.status,
                    "progress": scene.progress,
                }
            )
            chapters[scene.chapter]["total_scenes"] += 1

            if scene.status == "completed":
                chapters[scene.chapter]["completed_scenes"] += 1
            elif scene.status == "active":
                chapters[scene.chapter]["active_scenes"] += 1

        # 计算总体进度
        total_scenes = len(scenes)
        completed_scenes = sum(1 for s in scenes if s.status == "completed")
        active_scenes = sum(1 for s in scenes if s.status == "active")

        return {
            "playthrough_id": playthrough_id,
            "chapters": list(chapters.values()),
            "summary": {
                "total_scenes": total_scenes,
                "completed_scenes": completed_scenes,
                "active_scenes": active_scenes,
                "locked_scenes": total_scenes - completed_scenes - active_scenes,
                "progress": (completed_scenes / total_scenes * 100) if total_scenes > 0 else 0,
            },
        }

    def update_scene_progress(self, scene_id: str, progress: int) -> Optional[Scene]:
        """
        更新场景进度

        Args:
            scene_id: 场景ID
            progress: 进度 (0-100)

        Returns:
            更新后的场景对象
        """
        scene = self.get_scene(scene_id)
        if not scene:
            return None

        scene.update_progress(progress)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE scenes SET progress = ?, status = ?, updated_at = ? WHERE id = ?",
                (scene.progress, scene.status, scene.updated_at, scene_id),
            )

            conn.commit()
            conn.close()

            logger.info(f"更新场景进度: {scene.name} -> {scene.progress}%")
            return scene

        except Exception as e:
            logger.error(f"更新场景进度失败: {e}")
            return None

    def activate_scene(self, scene_id: str) -> Optional[Scene]:
        """
        激活场景

        Args:
            scene_id: 场景ID

        Returns:
            激活后的场景对象
        """
        scene = self.get_scene(scene_id)
        if not scene:
            return None

        scene.activate()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE scenes SET status = ?, updated_at = ? WHERE id = ?",
                (scene.status, scene.updated_at, scene_id),
            )

            conn.commit()
            conn.close()

            logger.info(f"激活场景: {scene.chapter} {scene.scene_number} - {scene.name}")
            return scene

        except Exception as e:
            logger.error(f"激活场景失败: {e}")
            return None

    def complete_scene(self, scene_id: str) -> Optional[Scene]:
        """
        完成场景

        Args:
            scene_id: 场景ID

        Returns:
            完成后的场景对象
        """
        scene = self.get_scene(scene_id)
        if not scene:
            return None

        scene.complete()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE scenes SET status = ?, progress = ?, updated_at = ? WHERE id = ?",
                (scene.status, scene.progress, scene.updated_at, scene_id),
            )

            conn.commit()
            conn.close()

            logger.info(f"完成场景: {scene.chapter} {scene.scene_number} - {scene.name}")

            # 自动激活下一个场景
            self._activate_next_scene(scene.playthrough_id, scene.chapter, scene.scene_number)

            return scene

        except Exception as e:
            logger.error(f"完成场景失败: {e}")
            return None

    def _activate_next_scene(self, playthrough_id: str, current_chapter: str, current_scene_number: str):
        """自动激活下一个场景"""
        try:
            # 获取当前章节的所有场景
            chapter_scenes = self.get_scenes_by_chapter(playthrough_id, current_chapter)

            # 找到当前场景的下一个
            current_index = None
            for i, scene in enumerate(chapter_scenes):
                if scene.scene_number == current_scene_number:
                    current_index = i
                    break

            if current_index is not None and current_index + 1 < len(chapter_scenes):
                next_scene = chapter_scenes[current_index + 1]
                if next_scene.status == "locked":
                    self.activate_scene(next_scene.id)
            else:
                # 当前章节已完成，尝试激活下一章节的第一个场景
                all_scenes = self.get_scenes_by_playthrough(playthrough_id)
                chapters = list(set(s.chapter for s in all_scenes))
                chapters.sort()

                current_chapter_index = None
                for i, chapter in enumerate(chapters):
                    if chapter == current_chapter:
                        current_chapter_index = i
                        break

                if current_chapter_index is not None and current_chapter_index + 1 < len(chapters):
                    next_chapter = chapters[current_chapter_index + 1]
                    next_chapter_scenes = self.get_scenes_by_chapter(playthrough_id, next_chapter)
                    if next_chapter_scenes and next_chapter_scenes[0].status == "locked":
                        self.activate_scene(next_chapter_scenes[0].id)

        except Exception as e:
            logger.error(f"激活下一个场景失败: {e}")

    def add_scene_event(
        self,
        scene_id: str,
        event_type: str,
        event_content: str,
        event_data: dict = None,
    ) -> SceneEvent:
        """
        添加场景事件

        Args:
            scene_id: 场景ID
            event_type: 事件类型
            event_content: 事件内容
            event_data: 事件数据

        Returns:
            创建的事件对象
        """
        event_id = f"event_{uuid.uuid4().hex[:12]}"
        now = time.time()

        event = SceneEvent(
            id=event_id,
            scene_id=scene_id,
            event_type=event_type,
            event_content=event_content,
            event_data=json.dumps(event_data) if event_data else None,
            created_at=now,
        )

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO scene_events (id, scene_id, event_type, event_content, event_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (event.id, event.scene_id, event.event_type, event.event_content, event.event_data, event.created_at),
            )

            conn.commit()
            conn.close()

            return event

        except Exception as e:
            logger.error(f"添加场景事件失败: {e}")
            raise

    def get_scene_events(self, scene_id: str) -> list[SceneEvent]:
        """
        获取场景事件

        Args:
            scene_id: 场景ID

        Returns:
            事件列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM scene_events WHERE scene_id = ? ORDER BY created_at",
                (scene_id,),
            )
            rows = cursor.fetchall()

            conn.close()

            events = []
            for row in rows:
                events.append(
                    SceneEvent(
                        id=row[0],
                        scene_id=row[1],
                        event_type=row[2],
                        event_content=row[3],
                        event_data=row[4],
                        created_at=row[5],
                    )
                )
            return events

        except Exception as e:
            logger.error(f"获取场景事件失败: {e}")
            return []

    def delete_scene(self, scene_id: str) -> bool:
        """
        删除场景

        Args:
            scene_id: 场景ID

        Returns:
            是否删除成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 删除关联的事件
            cursor.execute("DELETE FROM scene_events WHERE scene_id = ?", (scene_id,))

            # 删除场景
            cursor.execute("DELETE FROM scenes WHERE id = ?", (scene_id,))

            conn.commit()
            conn.close()

            logger.info(f"删除场景: {scene_id}")
            return True

        except Exception as e:
            logger.error(f"删除场景失败: {e}")
            return False
