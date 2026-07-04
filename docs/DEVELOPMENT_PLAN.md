# Infinite-Genre-Instance-Dungeons 开发落地方案

> **文档版本**: v1.0  
> **创建日期**: 2026-07-05  
> **参考来源**: 互动电影创作台 (wbmnbwl.vercel.app)  
> **目标**: 构建生产可用的无限流副本记忆系统

---

## 目录

- [一、现状分析与差距评估](#一现状分析与差距评估)
- [二、核心架构设计](#二核心架构设计)
- [三、数据模型重构](#三数据模型重构)
- [四、功能模块开发计划](#四功能模块开发计划)
- [五、失效模式分析与防御](#五失效模式分析与防御)
- [六、生产部署方案](#六生产部署方案)
- [七、开发里程碑](#七开发里程碑)

---

## 一、现状分析与差距评估

### 1.1 当前系统能力矩阵

| 模块 | 现有能力 | 缺失能力 | 优先级 |
|------|---------|---------|--------|
| **核心记忆** | 概念、记忆、连接 | 场景、章节、周目 | 🔴 高 |
| **时间维度** | 历史今日、未闭合话题 | 跨周目记忆、时间线 | 🔴 高 |
| **人物印象** | 好感度追踪 | 属性面板、关系演化 | 🟡 中 |
| **存档系统** | 无 | 自动存档、导入导出 | 🔴 高 |
| **视觉资产** | 多模态基础 | 图片/视频/音乐管理 | 🟡 中 |
| **Web界面** | 基础CRUD | 副本工作流UI | 🔴 高 |

### 1.2 参考网站关键设计元素提取

```
┌─────────────────────────────────────────────────────────────┐
│                    互动电影创作台核心设计                       │
├─────────────────────────────────────────────────────────────┤
│  📋 场景时间线     │  按"夜/章节"分组，场景编号+名称+进度      │
│  📊 属性面板       │  周目、路线、碎片、信任度等状态追踪       │
│  🔮 回忆系统       │  已到达场景、已解锁结局、跨周目记忆       │
│  💾 存档系统       │  自动存档、导出、导入、重开               │
│  🎨 视觉资产       │  图片、视频、音乐设计                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 差距分析（神经网络结构）

```
                    ┌──────────────────┐
                    │   输入层差距      │
                    │  (当前系统)       │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  场景管理缺失  │   │  周目系统缺失  │   │  存档系统缺失  │
│  - 无场景概念  │   │  - 无周目概念  │   │  - 无存档功能  │
│  - 无章节分组  │   │  - 无线性推进  │   │  - 无导入导出  │
│  - 无进度追踪  │   │  - 无轮回机制  │   │  - 无版本管理  │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                    ┌──────────────────┐
                    │   输出层差距      │
                    │  (目标系统)       │
                    └──────────────────┘
```

---

## 二、核心架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Infinite-Genre-Instance-Dungeons                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │  输入层      │───▶│  核心处理    │───▶│  存储层      │                 │
│  │             │    │             │    │             │                 │
│  │ • 用户对话   │    │ • 话题分析   │    │ • SQLite    │                 │
│  │ • 场景图片   │    │ • 记忆形成   │    │ • LanceDB   │                 │
│  │ • 角色互动   │    │ • 关系图谱   │    │ • 图数据库   │                 │
│  │ • 剧情选择   │    │ • 人物印象   │    │ • 时间线     │                 │
│  └─────────────┘    │ • 时间记忆   │    └─────────────┘                 │
│                     └─────────────┘                                     │
│                            │                                            │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        输出层                                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │   │
│  │  │ 上下文注入 │ │ 角色演化  │ │ 剧情延续  │ │ 记忆召回  │          │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      副本工作流层                                 │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │   │
│  │  │ 场景时间线 │ │ 属性面板  │ │ 回忆系统  │ │ 存档系统  │          │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流设计

```
用户输入 ──▶ 话题分析 ──▶ 场景识别 ──▶ 记忆形成 ──▶ 属性更新
                │              │              │              │
                ▼              ▼              ▼              ▼
           主题检测        场景匹配        记忆存储        状态同步
                │              │              │              │
                ▼              ▼              ▼              ▼
           话题摘要        场景状态        关系图谱        属性面板
                │              │              │              │
                └──────────────┴──────────────┴──────────────┘
                                   │
                                   ▼
                           ┌──────────────┐
                           │  下一轮副本   │
                           │  上下文注入   │
                           └──────────────┘
```

---

## 三、数据模型重构

### 3.1 新增数据表

```sql
-- 场景表
CREATE TABLE scenes (
    id TEXT PRIMARY KEY,
    chapter TEXT NOT NULL,           -- 章节/夜 (如: "第一夜")
    scene_number TEXT NOT NULL,      -- 场景编号 (如: "1-3")
    name TEXT NOT NULL,              -- 场景名称 (如: "月光森林")
    description TEXT,                -- 场景描述
    status TEXT DEFAULT 'locked',   -- locked/active/completed
    progress INTEGER DEFAULT 0,     -- 进度 (0-100)
    created_at REAL,
    updated_at REAL
);

-- 周目表
CREATE TABLE playthroughs (
    id TEXT PRIMARY KEY,
    playthrough_number INTEGER NOT NULL,  -- 周目编号
    status TEXT DEFAULT 'active',         -- active/completed/abandoned
    route TEXT,                           -- 路线名称
    started_at REAL,
    completed_at REAL,
   结局 TEXT,                              -- 结局名称
    summary TEXT                          -- 周目摘要
);

-- 属性表
CREATE TABLE attributes (
    id TEXT PRIMARY KEY,
    playthrough_id TEXT NOT NULL,     -- 关联周目
    attribute_name TEXT NOT NULL,     -- 属性名 (如: "狐族信任")
    attribute_value REAL DEFAULT 0,   -- 属性值
    max_value REAL DEFAULT 100,       -- 最大值
    min_value REAL DEFAULT 0,         -- 最小值
    category TEXT,                    -- 属性分类
    created_at REAL,
    updated_at REAL,
    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id)
);

-- 存档表
CREATE TABLE saves (
    id TEXT PRIMARY KEY,
    playthrough_id TEXT NOT NULL,
    save_type TEXT DEFAULT 'auto',    -- auto/manual/export
    save_data TEXT NOT NULL,           -- JSON格式的完整存档数据
    created_at REAL,
    file_size INTEGER,
    version TEXT DEFAULT '1.0',
    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id)
);

-- 视觉资产表
CREATE TABLE visual_assets (
    id TEXT PRIMARY KEY,
    scene_id TEXT,
    asset_type TEXT NOT NULL,         -- image/video/audio
    file_path TEXT NOT NULL,
    thumbnail_path TEXT,
    metadata TEXT,                    -- JSON格式的元数据
    created_at REAL,
    FOREIGN KEY (scene_id) REFERENCES scenes(id)
);

-- 跨周目记忆表
CREATE TABLE cross_playthrough_memories (
    id TEXT PRIMARY KEY,
    memory_content TEXT NOT NULL,
    memory_type TEXT,                 -- memory/ending/achievement
    discovered_at REAL,
    playthrough_id TEXT,              -- 发现于哪个周目
    related_scene_id TEXT,
    FOREIGN KEY (playthrough_id) REFERENCES playthroughs(id),
    FOREIGN KEY (related_scene_id) REFERENCES scenes(id)
);
```

### 3.2 数据模型关系图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  playthroughs │────▶│   scenes    │────▶│ visual_assets│
│             │     │             │     │             │
│ • 周目编号   │     │ • 章节      │     │ • 图片      │
│ • 路线      │     │ • 场景编号   │     │ • 视频      │
│ • 状态      │     │ • 名称      │     │ • 音乐      │
│ • 结局      │     │ • 进度      │     │             │
└──────┬──────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  attributes │     │    saves    │     │cross_play-  │
│             │     │             │     │through_mem  │
│ • 属性名    │     │ • 存档类型   │     │             │
│ • 属性值    │     │ • 存档数据   │     │ • 记忆内容   │
│ • 最大值    │     │ • 版本      │     │ • 记忆类型   │
│ • 分类      │     │ • 文件大小   │     │ • 发现周目   │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## 四、功能模块开发计划

### 4.1 模块一：场景管理系统

**目标**: 实现按"夜/章节"分组的场景时间线

```python
# 核心接口设计
class SceneManager:
    def __init__(self, memory_system):
        self.memory_system = memory_system

    async def create_chapter(self, chapter_name: str) -> str:
        """创建章节/夜"""
        pass

    async def create_scene(self, chapter_id: str, scene_number: str, name: str) -> str:
        """创建场景"""
        pass

    async def update_scene_progress(self, scene_id: str, progress: int) -> None:
        """更新场景进度"""
        pass

    async def get_scene_timeline(self, playthrough_id: str) -> dict:
        """获取场景时间线"""
        pass

    async def complete_scene(self, scene_id: str) -> dict:
        """完成场景，返回解锁的下一场景"""
        pass
```

**实现要点**:
- 场景状态机: `locked` → `active` → `completed`
- 章节分组逻辑
- 进度追踪和统计

### 4.2 模块二：周目系统

**目标**: 实现多周目轮回机制

```python
class PlaythroughManager:
    def __init__(self, memory_system):
        self.memory_system = memory_system

    async def start_new_playthrough(self, route: str = None) -> str:
        """开始新周目"""
        pass

    async def get_current_playthrough(self) -> dict:
        """获取当前周目信息"""
        pass

    async def complete_playthrough(self, ending: str) -> dict:
        """完成周目"""
        pass

    async def get_playthrough_history(self) -> list:
        """获取周目历史"""
        pass

    async def get_cross_playthrough_memories(self) -> list:
        """获取跨周目记忆"""
        pass
```

**实现要点**:
- 周目编号自动递增
- 路线系统（不同选择导致不同路线）
- 跨周目记忆继承

### 4.3 模块三：属性面板系统

**目标**: 实现角色属性追踪

```python
class AttributeManager:
    def __init__(self, memory_system):
        self.memory_system = memory_system

    async def create_attribute(self, playthrough_id: str, name: str, 
                               initial_value: float = 0, max_value: float = 100) -> str:
        """创建属性"""
        pass

    async def update_attribute(self, attribute_id: str, delta: float) -> dict:
        """更新属性值（支持增减）"""
        pass

    async def get_attribute_panel(self, playthrough_id: str) -> dict:
        """获取属性面板数据"""
        pass

    async def get_attribute_history(self, attribute_id: str) -> list:
        """获取属性变化历史"""
        pass
```

**实现要点**:
- 属性值范围控制
- 属性变化日志
- 属性分类（信任类、侵蚀类、真相类等）

### 4.4 模块四：回忆系统

**目标**: 实现跨周目记忆和结局追踪

```python
class RecallSystem:
    def __init__(self, memory_system):
        self.memory_system = memory_system

    async def get_current_recall(self, playthrough_id: str) -> dict:
        """获取当前回忆面板数据"""
        pass

    async def discover_memory(self, memory_content: str, playthrough_id: str) -> str:
        """发现新记忆"""
        pass

    async def unlock_ending(self, playthrough_id: str, ending_name: str) -> str:
        """解锁结局"""
        pass

    async def get_destiny_map(self) -> dict:
        """获取命运地图（所有周目路线）"""
        pass
```

**实现要点**:
- 记忆发现机制
- 结局解锁条件
- 命运地图可视化

### 4.5 模块五：存档系统

**目标**: 实现完整的存档管理

```python
class SaveManager:
    def __init__(self, memory_system):
        self.memory_system = memory_system

    async def auto_save(self, playthrough_id: str) -> str:
        """自动存档"""
        pass

    async def manual_save(self, playthrough_id: str, slot_name: str) -> str:
        """手动存档"""
        pass

    async def load_save(self, save_id: str) -> dict:
        """加载存档"""
        pass

    async def export_save(self, save_id: str) -> bytes:
        """导出存档"""
        pass

    async def import_save(self, save_data: bytes) -> str:
        """导入存档"""
        pass

    async def delete_save(self, save_id: str) -> bool:
        """删除存档"""
        pass

    async def get_save_list(self, playthrough_id: str) -> list:
        """获取存档列表"""
        pass
```

**实现要点**:
- 自动存档触发时机
- 存档数据压缩
- 存档版本兼容

### 4.6 模块六：视觉资产管理

**目标**: 实现图片/视频/音乐管理

```python
class AssetManager:
    def __init__(self, memory_system):
        self.memory_system = memory_system

    async def upload_asset(self, scene_id: str, file_path: str, 
                           asset_type: str) -> str:
        """上传资产"""
        pass

    async def get_scene_assets(self, scene_id: str) -> dict:
        """获取场景资产"""
        pass

    async def generate_thumbnail(self, asset_id: str) -> str:
        """生成缩略图"""
        pass

    async def delete_asset(self, asset_id: str) -> bool:
        """删除资产"""
        pass
```

**实现要点**:
- 文件存储策略
- 缩略图生成
- 资产元数据管理

---

## 五、失效模式分析与防御

### 5.1 潜在失效模式

| 失效模式 | 影响 | 概率 | 防御措施 |
|---------|------|------|---------|
| **数据库损坏** | 数据丢失 | 中 | 自动备份+校验和 |
| **存档数据不一致** | 状态错乱 | 中 | 事务+版本控制 |
| **跨周目记忆泄露** | 信息污染 | 低 | 作用域隔离 |
| **属性值越界** | 逻辑错误 | 低 | 边界检查 |
| **资产文件丢失** | 资源缺失 | 中 | 引用计数+清理 |
| **并发写入冲突** | 数据覆盖 | 低 | 锁机制 |

### 5.2 防御性编程策略

```python
# 1. 数据库操作防御
class SafeDatabaseOperation:
    async def execute_with_retry(self, operation, max_retries=3):
        for attempt in range(max_retries):
            try:
                return await operation()
            except DatabaseError as e:
                if attempt == max_retries - 1:
                    raise
                await self.backup_and_recover()

# 2. 存档数据校验
class SaveDataValidator:
    def validate(self, save_data: dict) -> bool:
        required_fields = ['playthrough_id', 'scenes', 'attributes', 'timestamp']
        return all(field in save_data for field in required_fields)

# 3. 属性值边界控制
class AttributeBoundaryControl:
    def clamp_value(self, value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))
```

### 5.3 数据一致性保障

```
┌─────────────────────────────────────────────────────────────┐
│                    数据一致性保障机制                          │
├─────────────────────────────────────────────────────────────┤
│  1. 事务管理: 所有写操作使用事务                              │
│  2. 版本控制: 每次更新递增版本号                              │
│  3. 校验和: 存档数据包含校验和                                │
│  4. 备份策略: 自动备份+手动备份                              │
│  5. 恢复机制: 损坏数据自动恢复                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 六、生产部署方案

### 6.1 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                      生产环境架构                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Web服务器   │    │  应用服务器   │    │  数据库      │     │
│  │  (Nginx)    │───▶│  (Python)   │───▶│  (SQLite)   │     │
│  │             │    │             │    │             │     │
│  │ • 静态文件   │    │ • API接口   │    │ • 记忆数据   │     │
│  │ • 反向代理   │    │ • 业务逻辑   │    │ • 存档数据   │     │
│  │ • SSL终端    │    │ • 认证授权   │    │ • 资产索引   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                     │       │
│                                                     ▼       │
│                                           ┌─────────────┐   │
│                                           │  文件存储    │   │
│                                           │  (Local/S3) │   │
│                                           │             │   │
│                                           │ • 图片文件   │   │
│                                           │ • 视频文件   │   │
│                                           │ • 音频文件   │   │
│                                           └─────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 配置管理

```python
# 生产环境配置
PRODUCTION_CONFIG = {
    "database": {
        "path": "/data/memora/connect.db",
        "backup_path": "/data/backups/",
        "max_backups": 10,
        "auto_backup_interval": 3600,  # 1小时
    },
    "storage": {
        "assets_path": "/data/assets/",
        "max_file_size": 100 * 1024 * 1024,  # 100MB
        "allowed_types": ["image/*", "video/*", "audio/*"],
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8352,
        "workers": 4,
        "timeout": 30,
    },
    "security": {
        "access_token": "${ACCESS_TOKEN}",
        "rate_limit": 100,  # 请求/分钟
        "cors_origins": ["https://yourdomain.com"],
    }
}
```

### 6.3 监控与告警

```python
# 健康检查端点
@app.route("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database(),
        "storage": await check_storage(),
        "version": "1.0.0",
        "uptime": get_uptime(),
    }

# 关键指标监控
METRICS = {
    "memory_count": "记忆总数",
    "playthrough_count": "周目总数",
    "save_count": "存档总数",
    "asset_count": "资产总数",
    "api_latency": "API延迟",
    "error_rate": "错误率",
}
```

---

## 七、开发里程碑

### Phase 1: 基础框架 (2周)

| 任务 | 负责人 | 预计时间 | 产出物 |
|------|--------|---------|--------|
| 数据库Schema设计 | - | 3天 | SQL迁移脚本 |
| 核心数据模型 | - | 3天 | models.py更新 |
| 场景管理模块 | - | 4天 | scene_manager.py |
| 周目管理模块 | - | 4天 | playthrough_manager.py |

### Phase 2: 核心功能 (3周)

| 任务 | 负责人 | 预计时间 | 产出物 |
|------|--------|---------|--------|
| 属性面板系统 | - | 5天 | attribute_manager.py |
| 回忆系统 | - | 5天 | recall_system.py |
| 存档系统 | - | 5天 | save_manager.py |
| API端点开发 | - | 5天 | 新增API路由 |

### Phase 3: 前端界面 (3周)

| 任务 | 负责人 | 预计时间 | 产出物 |
|------|--------|---------|--------|
| 场景时间线UI | - | 5天 | 前端组件 |
| 属性面板UI | - | 5天 | 前端组件 |
| 回忆系统UI | - | 5天 | 前端组件 |
| 存档管理UI | - | 5天 | 前端组件 |

### Phase 4: 集成测试 (2周)

| 任务 | 负责人 | 预计时间 | 产出物 |
|------|--------|---------|--------|
| 单元测试 | - | 3天 | 测试用例 |
| 集成测试 | - | 3天 | 测试报告 |
| E2E测试 | - | 4天 | Playwright测试 |
| 性能测试 | - | 4天 | 性能报告 |

### Phase 5: 生产部署 (1周)

| 任务 | 负责人 | 预计时间 | 产出物 |
|------|--------|---------|--------|
| 环境配置 | - | 2天 | 配置文件 |
| 监控告警 | - | 2天 | 监控面板 |
| 文档编写 | - | 3天 | 用户文档 |

---

## 附录

### A. API端点设计

```
POST   /api/playthroughs              # 创建新周目
GET    /api/playthroughs              # 获取周目列表
GET    /api/playthroughs/:id          # 获取周目详情
PUT    /api/playthroughs/:id          # 更新周目
DELETE /api/playthroughs/:id          # 删除周目

POST   /api/scenes                    # 创建场景
GET    /api/scenes?playthrough_id=    # 获取场景列表
GET    /api/scenes/:id                # 获取场景详情
PUT    /api/scenes/:id                # 更新场景
PUT    /api/scenes/:id/progress       # 更新场景进度

POST   /api/attributes                # 创建属性
GET    /api/attributes?playthrough_id= # 获取属性列表
PUT    /api/attributes/:id            # 更新属性值

POST   /api/saves                     # 创建存档
GET    /api/saves?playthrough_id=     # 获取存档列表
GET    /api/saves/:id                 # 加载存档
POST   /api/saves/:id/export          # 导出存档
POST   /api/saves/import              # 导入存档

GET    /api/recall                    # 获取回忆数据
POST   /api/recall/memories           # 发现新记忆
POST   /api/recall/endings            # 解锁结局
GET    /api/recall/destiny-map        # 获取命运地图

POST   /api/assets                    # 上传资产
GET    /api/assets?scene_id=          # 获取场景资产
DELETE /api/assets/:id                # 删除资产
```

### B. 环境变量

```bash
# 数据库
DATABASE_PATH=/data/memora/connect.db
DATABASE_BACKUP_PATH=/data/backups/

# 存储
ASSETS_PATH=/data/assets/
MAX_FILE_SIZE=104857600

# 服务器
SERVER_HOST=0.0.0.0
SERVER_PORT=8352

# 安全
ACCESS_TOKEN=your-secret-token
CORS_ORIGINS=https://yourdomain.com

# 监控
ENABLE_METRICS=true
METRICS_PORT=9090
```

### C. 开发工具

```bash
# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 运行测试
pytest tests/ -v

# 运行E2E测试
pytest tests/test_e2e_web.py -v

# 启动开发服务器
python3 start_backend.py

# 代码格式化
black .
isort .

# 类型检查
mypy .
```

---

**文档维护者**: kaori-seasons  
**最后更新**: 2026-07-05
