-- Infinite-Genre-Instance-Dungeons 数据库Schema
-- 版本: 1.0.0
-- 创建日期: 2026-07-05

-- ============================================
-- 1. 原有表（保持兼容）
-- ============================================

-- 概念表
CREATE TABLE IF NOT EXISTS concepts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at REAL,
    last_accessed REAL,
    access_count INTEGER DEFAULT 0
);

-- 记忆表
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    concept_id TEXT NOT NULL,
    content TEXT NOT NULL,
    details TEXT DEFAULT '',
    participants TEXT DEFAULT '',
    location TEXT DEFAULT '',
    emotion TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    created_at REAL,
    last_accessed REAL,
    access_count INTEGER DEFAULT 0,
    strength REAL DEFAULT 1.0,
    group_id TEXT DEFAULT '',
    FOREIGN KEY (concept_id) REFERENCES concepts (id)
);

-- 连接表
CREATE TABLE IF NOT EXISTS connections (
    id TEXT PRIMARY KEY,
    from_concept TEXT NOT NULL,
    to_concept TEXT NOT NULL,
    strength REAL DEFAULT 1.0,
    last_strengthened REAL,
    FOREIGN KEY (from_concept) REFERENCES concepts (id),
    FOREIGN KEY (to_concept) REFERENCES concepts (id)
);

-- 印象表
CREATE TABLE IF NOT EXISTS impressions (
    id TEXT PRIMARY KEY,
    person_name TEXT NOT NULL,
    score REAL DEFAULT 50.0,
    tags TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at REAL,
    updated_at REAL
);

-- ============================================
-- 2. 新增表：副本工作流系统
-- ============================================

-- 周目表
CREATE TABLE IF NOT EXISTS playthroughs (
    id TEXT PRIMARY KEY,
    playthrough_number INTEGER NOT NULL,
    status TEXT DEFAULT 'active',          -- active/completed/abandoned
    route TEXT,                            -- 路线名称
    started_at REAL,
    completed_at REAL,
    ending TEXT,                           -- 结局名称
    summary TEXT,                          -- 周目摘要
    created_at REAL,
    updated_at REAL
);

-- 场景表
CREATE TABLE IF NOT EXISTS scenes (
    id TEXT PRIMARY KEY,
    playthrough_id TEXT NOT NULL,
    chapter TEXT NOT NULL,                 -- 章节/夜 (如: "第一夜")
    scene_number TEXT NOT NULL,            -- 场景编号 (如: "1-3")
    name TEXT NOT NULL,                    -- 场景名称 (如: "月光森林")
    description TEXT,                      -- 场景描述
    status TEXT DEFAULT 'locked',          -- locked/active/completed
    progress INTEGER DEFAULT 0,            -- 进度 (0-100)
    sort_order INTEGER DEFAULT 0,          -- 排序顺序
    created_at REAL,
    updated_at REAL,
    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id)
);

-- 属性表
CREATE TABLE IF NOT EXISTS attributes (
    id TEXT PRIMARY KEY,
    playthrough_id TEXT NOT NULL,
    attribute_name TEXT NOT NULL,          -- 属性名 (如: "狐族信任")
    attribute_value REAL DEFAULT 0,        -- 属性值
    max_value REAL DEFAULT 100,            -- 最大值
    min_value REAL DEFAULT 0,              -- 最小值
    category TEXT,                         -- 属性分类 (trust/corruption/truth/other)
    icon TEXT,                             -- 图标
    created_at REAL,
    updated_at REAL,
    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id)
);

-- 存档表
CREATE TABLE IF NOT EXISTS saves (
    id TEXT PRIMARY KEY,
    playthrough_id TEXT NOT NULL,
    save_type TEXT DEFAULT 'auto',         -- auto/manual/export
    save_name TEXT,                        -- 存档名称
    save_data TEXT NOT NULL,               -- JSON格式的完整存档数据
    created_at REAL,
    file_size INTEGER,
    version TEXT DEFAULT '1.0',
    checksum TEXT,                         -- 校验和
    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id)
);

-- 视觉资产表
CREATE TABLE IF NOT EXISTS visual_assets (
    id TEXT PRIMARY KEY,
    scene_id TEXT,
    asset_type TEXT NOT NULL,              -- image/video/audio
    file_path TEXT NOT NULL,
    file_name TEXT,
    thumbnail_path TEXT,
    file_size INTEGER,
    mime_type TEXT,
    metadata TEXT,                         -- JSON格式的元数据
    created_at REAL,
    FOREIGN KEY (scene_id) REFERENCES scenes(id)
);

-- 跨周目记忆表
CREATE TABLE IF NOT EXISTS cross_playthrough_memories (
    id TEXT PRIMARY KEY,
    memory_content TEXT NOT NULL,
    memory_type TEXT,                      -- memory/ending/achievement
    discovered_at REAL,
    playthrough_id TEXT,                   -- 发现于哪个周目
    related_scene_id TEXT,
    importance REAL DEFAULT 0.5,           -- 重要性 (0-1)
    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id),
    FOREIGN KEY (related_scene_id) REFERENCES scenes(id)
);

-- 属性变化历史表
CREATE TABLE IF NOT EXISTS attribute_history (
    id TEXT PRIMARY KEY,
    attribute_id TEXT NOT NULL,
    old_value REAL,
    new_value REAL,
    change_reason TEXT,
    changed_at REAL,
    FOREIGN KEY (attribute_id) REFERENCES attributes(id)
);

-- 场景事件表（记录场景中发生的关键事件）
CREATE TABLE IF NOT EXISTS scene_events (
    id TEXT PRIMARY KEY,
    scene_id TEXT NOT NULL,
    event_type TEXT,                       -- dialogue/choice/achievement/discovery
    event_content TEXT NOT NULL,
    event_data TEXT,                       -- JSON格式的额外数据
    created_at REAL,
    FOREIGN KEY (scene_id) REFERENCES scenes(id)
);

-- ============================================
-- 3. 索引优化
-- ============================================

-- 原有索引
CREATE INDEX IF NOT EXISTS idx_memories_group_id ON memories(group_id);
CREATE INDEX IF NOT EXISTS idx_memories_concept_group ON memories(concept_id, group_id);
CREATE INDEX IF NOT EXISTS idx_memories_created_group ON memories(created_at, group_id);

-- 新增索引
CREATE INDEX IF NOT EXISTS idx_scenes_playthrough ON scenes(playthrough_id);
CREATE INDEX IF NOT EXISTS idx_scenes_chapter ON scenes(playthrough_id, chapter);
CREATE INDEX IF NOT EXISTS idx_scenes_status ON scenes(status);
CREATE INDEX IF NOT EXISTS idx_attributes_playthrough ON attributes(playthrough_id);
CREATE INDEX IF NOT EXISTS idx_saves_playthrough ON saves(playthrough_id);
CREATE INDEX IF NOT EXISTS idx_saves_type ON saves(save_type);
CREATE INDEX IF NOT EXISTS idx_visual_assets_scene ON visual_assets(scene_id);
CREATE INDEX IF NOT EXISTS idx_cross_memories_playthrough ON cross_playthrough_memories(playthrough_id);
CREATE INDEX IF NOT EXISTS idx_attribute_history_attribute ON attribute_history(attribute_id);
CREATE INDEX IF NOT EXISTS idx_scene_events_scene ON scene_events(scene_id);

-- ============================================
-- 4. 触发器（自动更新时间戳）
-- ============================================

-- 场景更新触发器
CREATE TRIGGER IF NOT EXISTS update_scene_timestamp
AFTER UPDATE ON scenes
BEGIN
    UPDATE scenes SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;

-- 属性更新触发器
CREATE TRIGGER IF NOT EXISTS update_attribute_timestamp
AFTER UPDATE ON attributes
BEGIN
    UPDATE attributes SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;

-- 周目更新触发器
CREATE TRIGGER IF NOT EXISTS update_playthrough_timestamp
AFTER UPDATE ON playthroughs
BEGIN
    UPDATE playthroughs SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;
