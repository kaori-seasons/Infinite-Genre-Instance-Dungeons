"""
数据模型定义
包含记忆系统的核心数据结构：Concept, Memory, Connection
以及副本工作流系统：Scene, Playthrough, Attribute, Save
"""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Concept:
    """概念节点"""

    id: str
    name: str
    created_at: float = None
    last_accessed: float = None
    access_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.last_accessed is None:
            self.last_accessed = time.time()


@dataclass
class Memory:
    """记忆条目"""

    id: str
    concept_id: str
    content: str
    details: str = ""  # 详细描述
    participants: str = ""  # 参与者
    location: str = ""  # 地点
    emotion: str = ""  # 情感
    tags: str = ""  # 标签
    created_at: float = None
    last_accessed: float = None
    access_count: int = 0
    strength: float = 1.0
    allow_forget: bool = True
    group_id: str = ""  # 群组ID，用于群聊隔离

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.last_accessed is None:
            self.last_accessed = time.time()
        if self.allow_forget is None:
            self.allow_forget = True


@dataclass
class Connection:
    """概念之间的连接"""

    id: str
    from_concept: str
    to_concept: str
    strength: float = 1.0
    last_strengthened: float = None

    def __post_init__(self):
        if self.last_strengthened is None:
            self.last_strengthened = time.time()


# ============================================
# 副本工作流系统数据模型
# ============================================


@dataclass
class Playthrough:
    """周目"""

    id: str
    playthrough_number: int
    status: str = "active"  # active/completed/abandoned
    route: Optional[str] = None
    started_at: float = None
    completed_at: Optional[float] = None
    ending: Optional[str] = None
    summary: Optional[str] = None
    created_at: float = None
    updated_at: float = None

    def __post_init__(self):
        if self.started_at is None:
            self.started_at = time.time()
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()

    def complete(self, ending: str, summary: str = "") -> None:
        """完成周目"""
        self.status = "completed"
        self.ending = ending
        self.summary = summary
        self.completed_at = time.time()
        self.updated_at = time.time()

    def abandon(self) -> None:
        """放弃周目"""
        self.status = "abandoned"
        self.completed_at = time.time()
        self.updated_at = time.time()


@dataclass
class Scene:
    """场景"""

    id: str
    playthrough_id: str
    chapter: str  # 章节/夜 (如: "第一夜")
    scene_number: str  # 场景编号 (如: "1-3")
    name: str  # 场景名称 (如: "月光森林")
    description: str = ""
    status: str = "locked"  # locked/active/completed
    progress: int = 0  # 进度 (0-100)
    sort_order: int = 0
    created_at: float = None
    updated_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()

    def activate(self) -> None:
        """激活场景"""
        self.status = "active"
        self.updated_at = time.time()

    def complete(self) -> None:
        """完成场景"""
        self.status = "completed"
        self.progress = 100
        self.updated_at = time.time()

    def update_progress(self, progress: int) -> None:
        """更新进度"""
        self.progress = max(0, min(100, progress))
        self.updated_at = time.time()
        if self.progress >= 100:
            self.complete()

    @property
    def is_locked(self) -> bool:
        return self.status == "locked"

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"


@dataclass
class Attribute:
    """属性"""

    id: str
    playthrough_id: str
    attribute_name: str
    attribute_value: float = 0.0
    max_value: float = 100.0
    min_value: float = 0.0
    category: str = "other"  # trust/corruption/truth/other
    icon: Optional[str] = None
    created_at: float = None
    updated_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()

    def update_value(self, delta: float) -> float:
        """更新属性值，返回实际变化量"""
        old_value = self.attribute_value
        new_value = self.attribute_value + delta
        # 边界控制
        new_value = max(self.min_value, min(self.max_value, new_value))
        self.attribute_value = new_value
        self.updated_at = time.time()
        return new_value - old_value

    def set_value(self, value: float) -> None:
        """设置属性值"""
        self.attribute_value = max(self.min_value, min(self.max_value, value))
        self.updated_at = time.time()

    @property
    def percentage(self) -> float:
        """获取百分比"""
        if self.max_value == self.min_value:
            return 0.0
        return (self.attribute_value - self.min_value) / (self.max_value - self.min_value) * 100


@dataclass
class Save:
    """存档"""

    id: str
    playthrough_id: str
    save_type: str = "auto"  # auto/manual/export
    save_name: Optional[str] = None
    save_data: str = "{}"  # JSON格式的完整存档数据
    created_at: float = None
    file_size: int = 0
    version: str = "1.0"
    checksum: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class VisualAsset:
    """视觉资产"""

    id: str
    scene_id: Optional[str] = None
    asset_type: str = "image"  # image/video/audio
    file_path: str = ""
    file_name: Optional[str] = None
    thumbnail_path: Optional[str] = None
    file_size: int = 0
    mime_type: Optional[str] = None
    metadata: Optional[str] = None
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class CrossPlaythroughMemory:
    """跨周目记忆"""

    id: str
    memory_content: str
    memory_type: str = "memory"  # memory/ending/achievement
    discovered_at: float = None
    playthrough_id: Optional[str] = None
    related_scene_id: Optional[str] = None
    importance: float = 0.5  # 重要性 (0-1)

    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = time.time()


@dataclass
class AttributeHistory:
    """属性变化历史"""

    id: str
    attribute_id: str
    old_value: float
    new_value: float
    change_reason: str = ""
    changed_at: float = None

    def __post_init__(self):
        if self.changed_at is None:
            self.changed_at = time.time()


@dataclass
class SceneEvent:
    """场景事件"""

    id: str
    scene_id: str
    event_type: str = "dialogue"  # dialogue/choice/achievement/discovery
    event_content: str = ""
    event_data: Optional[str] = None  # JSON格式的额外数据
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
