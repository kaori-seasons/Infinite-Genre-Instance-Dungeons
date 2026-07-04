"""
副本工作流单元测试
测试场景管理、周目管理、属性面板、存档系统、回忆系统
"""

import os
import sqlite3
import tempfile
import time
import pytest
import importlib.util

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_module(name, path):
    """动态加载模块"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# 加载 models 模块
models = load_module("models", os.path.join(PROJECT_ROOT, "core", "models.py"))


# 创建一个简化的 SceneManager 用于测试
class SimpleSceneManager:
    """简化版场景管理器（用于测试）"""

    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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
                updated_at REAL
            )
        """)
        conn.commit()
        conn.close()

    def _generate_id(self):
        import uuid
        return f"scene_{uuid.uuid4().hex[:12]}"

    def create_scene(self, playthrough_id, chapter, scene_number, name, description="", sort_order=0):
        scene_id = self._generate_id()
        now = time.time()
        scene = models.Scene(
            id=scene_id,
            playthrough_id=playthrough_id,
            chapter=chapter,
            scene_number=scene_number,
            name=name,
            description=description,
            status="locked",
            progress=0,
            sort_order=sort_order,
            created_at=now,
            updated_at=now,
        )
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scenes (id, playthrough_id, chapter, scene_number, name, description, status, progress, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (scene.id, scene.playthrough_id, scene.chapter, scene.scene_number, scene.name, scene.description, scene.status, scene.progress, scene.sort_order, scene.created_at, scene.updated_at),
        )
        conn.commit()
        conn.close()
        return scene

    def get_scene(self, scene_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return models.Scene(
                id=row[0], playthrough_id=row[1], chapter=row[2], scene_number=row[3],
                name=row[4], description=row[5] or "", status=row[6], progress=row[7],
                sort_order=row[8], created_at=row[9], updated_at=row[10],
            )
        return None

    def get_scenes_by_playthrough(self, playthrough_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scenes WHERE playthrough_id = ? ORDER BY sort_order", (playthrough_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            models.Scene(
                id=r[0], playthrough_id=r[1], chapter=r[2], scene_number=r[3],
                name=r[4], description=r[5] or "", status=r[6], progress=r[7],
                sort_order=r[8], created_at=r[9], updated_at=r[10],
            )
            for r in rows
        ]

    def activate_scene(self, scene_id):
        scene = self.get_scene(scene_id)
        if scene:
            scene.activate()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE scenes SET status = ?, updated_at = ? WHERE id = ?", (scene.status, scene.updated_at, scene_id))
            conn.commit()
            conn.close()
        return scene

    def complete_scene(self, scene_id):
        scene = self.get_scene(scene_id)
        if scene:
            scene.complete()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE scenes SET status = ?, progress = ?, updated_at = ? WHERE id = ?", (scene.status, scene.progress, scene.updated_at, scene_id))
            conn.commit()
            conn.close()
        return scene

    def update_scene_progress(self, scene_id, progress):
        scene = self.get_scene(scene_id)
        if scene:
            scene.update_progress(progress)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE scenes SET progress = ?, status = ?, updated_at = ? WHERE id = ?", (scene.progress, scene.status, scene.updated_at, scene_id))
            conn.commit()
            conn.close()
        return scene

    def get_scene_timeline(self, playthrough_id):
        scenes = self.get_scenes_by_playthrough(playthrough_id)
        chapters = {}
        for scene in scenes:
            if scene.chapter not in chapters:
                chapters[scene.chapter] = {"chapter_name": scene.chapter, "scenes": [], "total_scenes": 0, "completed_scenes": 0}
            chapters[scene.chapter]["scenes"].append({"id": scene.id, "scene_number": scene.scene_number, "name": scene.name, "status": scene.status, "progress": scene.progress})
            chapters[scene.chapter]["total_scenes"] += 1
            if scene.status == "completed":
                chapters[scene.chapter]["completed_scenes"] += 1
        total = len(scenes)
        completed = sum(1 for s in scenes if s.status == "completed")
        return {
            "chapters": list(chapters.values()),
            "summary": {"total_scenes": total, "completed_scenes": completed, "active_scenes": total - completed, "progress": (completed / total * 100) if total > 0 else 0},
        }


# 创建一个简化的 PlaythroughManager 用于测试
class SimplePlaythroughManager:
    """简化版周目管理器（用于测试）"""

    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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
                updated_at REAL
            )
        """)
        conn.commit()
        conn.close()

    def _generate_id(self):
        import uuid
        return f"pt_{uuid.uuid4().hex[:12]}"

    def start_new_playthrough(self, route=None):
        playthrough_number = self._get_next_number()
        playthrough_id = self._generate_id()
        now = time.time()
        pt = models.Playthrough(id=playthrough_id, playthrough_number=playthrough_number, route=route, started_at=now, created_at=now, updated_at=now)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO playthroughs (id, playthrough_number, status, route, started_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (pt.id, pt.playthrough_number, pt.status, pt.route, pt.started_at, pt.created_at, pt.updated_at))
        conn.commit()
        conn.close()
        return pt

    def _get_next_number(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(playthrough_number) FROM playthroughs")
        result = cursor.fetchone()
        conn.close()
        return (result[0] or 0) + 1

    def get_current_playthrough(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM playthroughs WHERE status = 'active' ORDER BY playthrough_number DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return models.Playthrough(id=row[0], playthrough_number=row[1], status=row[2], route=row[3], started_at=row[4], completed_at=row[5], ending=row[6], summary=row[7], created_at=row[8], updated_at=row[9])
        return None

    def get_playthrough(self, playthrough_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM playthroughs WHERE id = ?", (playthrough_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return models.Playthrough(id=row[0], playthrough_number=row[1], status=row[2], route=row[3], started_at=row[4], completed_at=row[5], ending=row[6], summary=row[7], created_at=row[8], updated_at=row[9])
        return None

    def complete_playthrough(self, playthrough_id, ending, summary=""):
        pt = self.get_playthrough(playthrough_id)
        if pt:
            pt.complete(ending, summary)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE playthroughs SET status = ?, ending = ?, summary = ?, completed_at = ?, updated_at = ? WHERE id = ?",
                           (pt.status, pt.ending, pt.summary, pt.completed_at, pt.updated_at, playthrough_id))
            conn.commit()
            conn.close()
        return pt

    def get_playthrough_history(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM playthroughs ORDER BY playthrough_number DESC")
        rows = cursor.fetchall()
        conn.close()
        return [models.Playthrough(id=r[0], playthrough_number=r[1], status=r[2], route=r[3], started_at=r[4], completed_at=r[5], ending=r[6], summary=r[7], created_at=r[8], updated_at=r[9]) for r in rows]

    def create_attribute(self, playthrough_id, name, initial_value=0.0, max_value=100.0, min_value=0.0, category="other", icon=None):
        import uuid
        attr_id = f"attr_{uuid.uuid4().hex[:12]}"
        now = time.time()
        attr = models.Attribute(id=attr_id, playthrough_id=playthrough_id, attribute_name=name, attribute_value=initial_value, max_value=max_value, min_value=min_value, category=category, icon=icon, created_at=now, updated_at=now)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO attributes (id, playthrough_id, attribute_name, attribute_value, max_value, min_value, category, icon, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (attr.id, attr.playthrough_id, attr.attribute_name, attr.attribute_value, attr.max_value, attr.min_value, attr.category, attr.icon, attr.created_at, attr.updated_at))
        conn.commit()
        conn.close()
        return attr

    def get_attributes_by_playthrough(self, playthrough_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attributes WHERE playthrough_id = ?", (playthrough_id,))
        rows = cursor.fetchall()
        conn.close()
        return [models.Attribute(id=r[0], playthrough_id=r[1], attribute_name=r[2], attribute_value=r[3], max_value=r[4], min_value=r[5], category=r[6], icon=r[7], created_at=r[8], updated_at=r[9]) for r in rows]

    def update_attribute_value(self, attribute_id, delta, reason=""):
        attr = None
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attributes WHERE id = ?", (attribute_id,))
        row = cursor.fetchone()
        if row:
            attr = models.Attribute(id=row[0], playthrough_id=row[1], attribute_name=row[2], attribute_value=row[3], max_value=row[4], min_value=row[5], category=row[6], icon=row[7], created_at=row[8], updated_at=row[9])
            attr.update_value(delta)
            cursor.execute("UPDATE attributes SET attribute_value = ?, updated_at = ? WHERE id = ?", (attr.attribute_value, attr.updated_at, attribute_id))
            conn.commit()
        conn.close()
        return attr

    def get_attribute_panel(self, playthrough_id):
        attrs = self.get_attributes_by_playthrough(playthrough_id)
        categories = {}
        for a in attrs:
            cat = a.category or "other"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({"id": a.id, "name": a.attribute_name, "value": a.attribute_value, "percentage": a.percentage})
        return {"categories": categories}


# 简化的存档管理器
class SimpleSaveManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
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
                checksum TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _generate_id(self):
        import uuid
        return f"save_{uuid.uuid4().hex[:12]}"

    def create_save(self, playthrough_id, save_type="auto", save_name=None, save_data=None):
        import json, hashlib
        save_id = self._generate_id()
        now = time.time()
        data_str = json.dumps(save_data or {})
        checksum = hashlib.md5(data_str.encode()).hexdigest()
        save = models.Save(id=save_id, playthrough_id=playthrough_id, save_type=save_type, save_name=save_name or f"存档_{int(now)}", save_data=data_str, created_at=now, file_size=len(data_str), checksum=checksum)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO saves (id, playthrough_id, save_type, save_name, save_data, created_at, file_size, version, checksum) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (save.id, save.playthrough_id, save.save_type, save.save_name, save.save_data, save.created_at, save.file_size, save.version, save.checksum))
        conn.commit()
        conn.close()
        return save

    def load_save(self, save_id):
        import json
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT save_data FROM saves WHERE id = ?", (save_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return None

    def get_save(self, save_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM saves WHERE id = ?", (save_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return models.Save(id=row[0], playthrough_id=row[1], save_type=row[2], save_name=row[3], save_data=row[4], created_at=row[5], file_size=row[6], version=row[7], checksum=row[8])
        return None

    def auto_save(self, playthrough_id, save_data=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM saves WHERE playthrough_id = ? AND save_type = 'auto' ORDER BY created_at DESC LIMIT 1", (playthrough_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self.update_save(row[0], save_data)
        return self.create_save(playthrough_id, "auto", None, save_data)

    def update_save(self, save_id, save_data=None):
        import json, hashlib
        save = self.get_save(save_id)
        if save and save_data:
            data_str = json.dumps(save_data)
            save.save_data = data_str
            save.checksum = hashlib.md5(data_str.encode()).hexdigest()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE saves SET save_data = ?, checksum = ? WHERE id = ?", (save.save_data, save.checksum, save_id))
            conn.commit()
            conn.close()
        return save

    def export_save(self, save_id):
        import json, base64
        save = self.get_save(save_id)
        if save:
            export_data = {"version": save.version, "save_id": save.id, "save_name": save.save_name, "data": save.save_data}
            return base64.b64encode(json.dumps(export_data).encode()).decode('ascii')
        return None

    def import_save(self, export_data):
        import json, base64
        decoded = base64.b64decode(export_data).decode('ascii')
        import_data = json.loads(decoded)
        data_str = import_data.get("data", "{}")
        return self.create_save("imported", "import", f"导入_{import_data.get('save_name', '')}", json.loads(data_str))

    def get_save_list(self, playthrough_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, playthrough_id, save_type, save_name, created_at, file_size, version FROM saves WHERE playthrough_id = ?", (playthrough_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "playthrough_id": r[1], "save_type": r[2], "save_name": r[3], "created_at": r[4], "file_size": r[5], "version": r[6]} for r in rows]


# 简化的回忆系统
class SimpleRecallSystem:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cross_playthrough_memories (
                id TEXT PRIMARY KEY,
                memory_content TEXT NOT NULL,
                memory_type TEXT,
                discovered_at REAL,
                playthrough_id TEXT,
                related_scene_id TEXT,
                importance REAL DEFAULT 0.5
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unlocked_endings (
                id TEXT PRIMARY KEY,
                ending_name TEXT NOT NULL,
                ending_description TEXT,
                unlocked_at REAL,
                playthrough_id TEXT,
                ending_data TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _generate_id(self):
        import uuid
        return f"recall_{uuid.uuid4().hex[:12]}"

    def discover_memory(self, memory_content, playthrough_id, memory_type="memory", related_scene_id=None, importance=0.5):
        import uuid
        memory_id = self._generate_id()
        now = time.time()
        memory = models.CrossPlaythroughMemory(id=memory_id, memory_content=memory_content, memory_type=memory_type, discovered_at=now, playthrough_id=playthrough_id, related_scene_id=related_scene_id, importance=importance)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cross_playthrough_memories (id, memory_content, memory_type, discovered_at, playthrough_id, related_scene_id, importance) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (memory.id, memory.memory_content, memory.memory_type, memory.discovered_at, memory.playthrough_id, memory.related_scene_id, memory.importance))
        conn.commit()
        conn.close()
        return memory

    def unlock_ending(self, ending_name, playthrough_id, ending_description="", ending_data=None):
        import uuid, json
        ending_id = f"ending_{uuid.uuid4().hex[:12]}"
        now = time.time()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO unlocked_endings (id, ending_name, ending_description, unlocked_at, playthrough_id, ending_data) VALUES (?, ?, ?, ?, ?, ?)",
                       (ending_id, ending_name, ending_description, now, playthrough_id, json.dumps(ending_data) if ending_data else None))
        conn.commit()
        conn.close()
        return {"status": "unlocked", "ending_id": ending_id, "ending_name": ending_name}

    def is_ending_unlocked(self, ending_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM unlocked_endings WHERE ending_name = ?", (ending_name,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def get_unlocked_endings(self, playthrough_id=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if playthrough_id:
            cursor.execute("SELECT * FROM unlocked_endings WHERE playthrough_id = ?", (playthrough_id,))
        else:
            cursor.execute("SELECT * FROM unlocked_endings")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "ending_name": r[1], "ending_description": r[2], "unlocked_at": r[3], "playthrough_id": r[4]} for r in rows]

    def get_destiny_map(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM playthroughs ORDER BY playthrough_number")
        playthroughs = cursor.fetchall()
        cursor.execute("SELECT * FROM unlocked_endings")
        endings = cursor.fetchall()
        cursor.execute("SELECT * FROM cross_playthrough_memories")
        memories = cursor.fetchall()
        conn.close()
        return {
            "playthroughs": [{"id": p[0], "number": p[1], "status": p[2], "route": p[3]} for p in playthroughs],
            "endings": [{"id": e[0], "name": e[1], "description": e[2]} for e in endings],
            "memories": [{"id": m[0], "content": m[1], "type": m[2]} for m in memories],
            "summary": {"total_playthroughs": len(playthroughs), "unlocked_endings": len(endings), "total_memories": len(memories)},
        }

    def get_recall_panel(self, playthrough_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM playthroughs WHERE id = ?", (playthrough_id,))
        playthrough = cursor.fetchone()
        cursor.execute("SELECT * FROM cross_playthrough_memories WHERE playthrough_id = ?", (playthrough_id,))
        memories = cursor.fetchall()
        cursor.execute("SELECT * FROM unlocked_endings")
        endings = cursor.fetchall()
        conn.close()
        return {
            "current_playthrough": {"id": playthrough[0], "number": playthrough[1], "status": playthrough[2]} if playthrough else {},
            "memories": [{"content": m[1], "type": m[2]} for m in memories],
            "endings": [{"name": e[1]} for e in endings],
        }


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    yield db_path
    os.unlink(db_path)


@pytest.fixture
def scene_manager(temp_db):
    return SimpleSceneManager(temp_db)


@pytest.fixture
def playthrough_manager(temp_db):
    return SimplePlaythroughManager(temp_db)


@pytest.fixture
def save_manager(temp_db):
    return SimpleSaveManager(temp_db)


@pytest.fixture
def recall_system(temp_db):
    return SimpleRecallSystem(temp_db)


class TestSceneManager:
    """场景管理器测试"""

    def test_create_scene(self, scene_manager, playthrough_manager):
        """测试创建场景"""
        # 先创建周目
        playthrough = playthrough_manager.start_new_playthrough("测试路线")

        # 创建场景
        scene = scene_manager.create_scene(
            playthrough_id=playthrough.id,
            chapter="第一夜",
            scene_number="1-1",
            name="月光森林",
            description="测试场景"
        )

        assert scene is not None
        assert scene.chapter == "第一夜"
        assert scene.scene_number == "1-1"
        assert scene.name == "月光森林"
        assert scene.status == "locked"

    def test_get_scene_timeline(self, scene_manager, playthrough_manager):
        """测试获取场景时间线"""
        playthrough = playthrough_manager.start_new_playthrough()

        # 创建多个场景
        scene_manager.create_scene(playthrough.id, "第一夜", "1-1", "场景1")
        scene_manager.create_scene(playthrough.id, "第一夜", "1-2", "场景2")
        scene_manager.create_scene(playthrough.id, "第二夜", "2-1", "场景3")

        timeline = scene_manager.get_scene_timeline(playthrough.id)

        assert timeline is not None
        assert "chapters" in timeline
        assert len(timeline["chapters"]) == 2
        assert timeline["summary"]["total_scenes"] == 3

    def test_update_scene_progress(self, scene_manager, playthrough_manager):
        """测试更新场景进度"""
        playthrough = playthrough_manager.start_new_playthrough()
        scene = scene_manager.create_scene(playthrough.id, "第一夜", "1-1", "场景1")
        scene_manager.activate_scene(scene.id)

        updated_scene = scene_manager.update_scene_progress(scene.id, 50)

        assert updated_scene is not None
        assert updated_scene.progress == 50
        assert updated_scene.status == "active"

    def test_complete_scene(self, scene_manager, playthrough_manager):
        """测试完成场景"""
        playthrough = playthrough_manager.start_new_playthrough()
        scene = scene_manager.create_scene(playthrough.id, "第一夜", "1-1", "场景1")
        scene_manager.activate_scene(scene.id)

        completed_scene = scene_manager.complete_scene(scene.id)

        assert completed_scene is not None
        assert completed_scene.status == "completed"
        assert completed_scene.progress == 100


class TestPlaythroughManager:
    """周目管理器测试"""

    def test_start_new_playthrough(self, playthrough_manager):
        """测试开始新周目"""
        playthrough = playthrough_manager.start_new_playthrough("测试路线")

        assert playthrough is not None
        assert playthrough.playthrough_number == 1
        assert playthrough.status == "active"
        assert playthrough.route == "测试路线"

    def test_get_current_playthrough(self, playthrough_manager):
        """测试获取当前周目"""
        playthrough_manager.start_new_playthrough()
        current = playthrough_manager.get_current_playthrough()

        assert current is not None
        assert current.status == "active"

    def test_complete_playthrough(self, playthrough_manager):
        """测试完成周目"""
        playthrough = playthrough_manager.start_new_playthrough()
        completed = playthrough_manager.complete_playthrough(playthrough.id, "好结局", "测试完成")

        assert completed is not None
        assert completed.status == "completed"
        assert completed.ending == "好结局"

    def test_get_playthrough_history(self, playthrough_manager):
        """测试获取周目历史"""
        playthrough_manager.start_new_playthrough()
        playthrough_manager.start_new_playthrough()

        history = playthrough_manager.get_playthrough_history()

        assert len(history) == 2
        assert history[0].playthrough_number == 2
        assert history[1].playthrough_number == 1

    def test_create_attribute(self, playthrough_manager):
        """测试创建属性"""
        playthrough = playthrough_manager.start_new_playthrough()
        attribute = playthrough_manager.create_attribute(
            playthrough.id, "狐族信任", 30.0, 100.0, 0.0, "trust"
        )

        assert attribute is not None
        assert attribute.attribute_name == "狐族信任"
        assert attribute.attribute_value == 30.0

    def test_update_attribute_value(self, playthrough_manager):
        """测试更新属性值"""
        playthrough = playthrough_manager.start_new_playthrough()
        attribute = playthrough_manager.create_attribute(playthrough.id, "信任度", 50.0)

        updated = playthrough_manager.update_attribute_value(attribute.id, 10.0, "增加信任")

        assert updated is not None
        assert updated.attribute_value == 60.0

    def test_get_attribute_panel(self, playthrough_manager):
        """测试获取属性面板"""
        playthrough = playthrough_manager.start_new_playthrough()
        playthrough_manager.create_attribute(playthrough.id, "信任度", 50.0, category="trust")
        playthrough_manager.create_attribute(playthrough.id, "侵蚀度", 20.0, category="corruption")

        panel = playthrough_manager.get_attribute_panel(playthrough.id)

        assert panel is not None
        assert "categories" in panel
        assert len(panel["categories"]) == 2


class TestSaveManager:
    """存档管理器测试"""

    def test_create_save(self, save_manager, playthrough_manager):
        """测试创建存档"""
        playthrough = playthrough_manager.start_new_playthrough()
        save = save_manager.create_save(
            playthrough.id, "manual", "测试存档", {"test": "data"}
        )

        assert save is not None
        assert save.save_type == "manual"
        assert save.save_name == "测试存档"

    def test_load_save(self, save_manager, playthrough_manager):
        """测试加载存档"""
        playthrough = playthrough_manager.start_new_playthrough()
        test_data = {"score": 100, "level": 5}
        save = save_manager.create_save(playthrough.id, "manual", "测试", test_data)

        loaded_data = save_manager.load_save(save.id)

        assert loaded_data is not None
        assert loaded_data["score"] == 100
        assert loaded_data["level"] == 5

    def test_auto_save(self, save_manager, playthrough_manager):
        """测试自动存档"""
        playthrough = playthrough_manager.start_new_playthrough()
        save1 = save_manager.auto_save(playthrough.id, {"step": 1})
        save2 = save_manager.auto_save(playthrough.id, {"step": 2})

        # 自动存档应该更新同一个存档
        assert save1.id == save2.id

        loaded = save_manager.load_save(save2.id)
        assert loaded["step"] == 2

    def test_export_import_save(self, save_manager, playthrough_manager):
        """测试导出导入存档"""
        playthrough = playthrough_manager.start_new_playthrough()
        save = save_manager.create_save(playthrough.id, "manual", "导出测试", {"data": "test"})

        # 导出
        export_data = save_manager.export_save(save.id)
        assert export_data is not None

        # 导入
        imported = save_manager.import_save(export_data)
        assert imported is not None
        assert imported.save_type == "import"

    def test_get_save_list(self, save_manager, playthrough_manager):
        """测试获取存档列表"""
        playthrough = playthrough_manager.start_new_playthrough()
        save_manager.create_save(playthrough.id, "manual", "存档1")
        save_manager.create_save(playthrough.id, "manual", "存档2")

        saves = save_manager.get_save_list(playthrough.id)

        assert len(saves) == 2


class TestRecallSystem:
    """回忆系统测试"""

    def test_discover_memory(self, recall_system, playthrough_manager):
        """测试发现跨周目记忆"""
        playthrough = playthrough_manager.start_new_playthrough()
        memory = recall_system.discover_memory(
            "你在月光森林中醒来",
            playthrough.id,
            "memory",
            importance=0.8
        )

        assert memory is not None
        assert memory.memory_content == "你在月光森林中醒来"
        assert memory.importance == 0.8

    def test_unlock_ending(self, recall_system, playthrough_manager):
        """测试解锁结局"""
        playthrough = playthrough_manager.start_new_playthrough()
        result = recall_system.unlock_ending(
            "好结局",
            playthrough.id,
            "成功拯救了世界"
        )

        assert result is not None
        assert result["status"] == "unlocked"

    def test_is_ending_unlocked(self, recall_system, playthrough_manager):
        """测试检查结局解锁状态"""
        playthrough = playthrough_manager.start_new_playthrough()

        assert not recall_system.is_ending_unlocked("好结局")

        recall_system.unlock_ending("好结局", playthrough.id)

        assert recall_system.is_ending_unlocked("好结局")

    def test_get_destiny_map(self, recall_system, playthrough_manager):
        """测试获取命运地图"""
        playthrough = playthrough_manager.start_new_playthrough()
        recall_system.discover_memory("记忆1", playthrough.id)
        recall_system.unlock_ending("结局1", playthrough.id)

        destiny_map = recall_system.get_destiny_map()

        assert destiny_map is not None
        assert "playthroughs" in destiny_map
        assert "endings" in destiny_map
        assert "memories" in destiny_map

    def test_get_recall_panel(self, recall_system, playthrough_manager):
        """测试获取回忆面板"""
        playthrough = playthrough_manager.start_new_playthrough()
        recall_system.discover_memory("记忆1", playthrough.id)

        panel = recall_system.get_recall_panel(playthrough.id)

        assert panel is not None
        assert "current_playthrough" in panel
        assert "memories" in panel


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
