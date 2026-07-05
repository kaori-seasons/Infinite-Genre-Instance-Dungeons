/**
 * 副本工作流前端模块
 * 实现场景时间线、属性面板、回忆系统、存档管理
 */

/* ============================================
 * 副本工作流状态管理
 * ============================================ */
const DungeonStore = {
  currentPlaythrough: null,
  playthroughs: [],
  scenes: [],
  attributes: [],
  saves: [],
  recallData: null,
  destinyMap: null,

  async init() {
    await this.loadCurrentPlaythrough();
    await this.loadPlaythroughs();
  },

  async loadCurrentPlaythrough() {
    try {
      this.currentPlaythrough = await API.get('/api/playthroughs/current');
    } catch (e) {
      this.currentPlaythrough = null;
    }
  },

  async loadPlaythroughs() {
    try {
      const data = await API.get('/api/playthroughs');
      this.playthroughs = data.playthroughs || [];
    } catch (e) {
      this.playthroughs = [];
    }
  },

  async loadScenes(playthroughId) {
    try {
      const data = await API.get(`/api/scenes?playthrough_id=${playthroughId}`);
      this.scenes = data.scenes || [];
    } catch (e) {
      this.scenes = [];
    }
  },

  async loadAttributes(playthroughId) {
    try {
      const data = await API.get(`/api/attributes?playthrough_id=${playthroughId}`);
      // 映射字段名以匹配前端期望
      this.attributes = (data.attributes || []).map(attr => ({
        id: attr.id,
        name: attr.attribute_name,
        value: attr.attribute_value,
        max_value: attr.max_value,
        min_value: attr.min_value,
        category: attr.category,
        icon: attr.icon,
        percentage: attr.max_value > attr.min_value
          ? ((attr.attribute_value - attr.min_value) / (attr.max_value - attr.min_value)) * 100
          : 0
      }));
    } catch (e) {
      this.attributes = [];
    }
  },

  async loadSaves(playthroughId) {
    try {
      const data = await API.get(`/api/saves?playthrough_id=${playthroughId}`);
      this.saves = data.saves || [];
    } catch (e) {
      this.saves = [];
    }
  },

  async loadRecall(playthroughId) {
    try {
      this.recallData = await API.get(`/api/recall?playthrough_id=${playthroughId}`);
    } catch (e) {
      this.recallData = null;
    }
  },

  async loadDestinyMap() {
    try {
      this.destinyMap = await API.get('/api/recall/destiny-map');
    } catch (e) {
      this.destinyMap = null;
    }
  }
};

/* ============================================
 * 场景时间线组件
 * ============================================ */
const SceneTimeline = {
  container: null,

  init() {
    this.container = document.getElementById('sceneTimeline');
  },

  async render() {
    if (!this.container) return;

    if (!DungeonStore.currentPlaythrough) {
      this.container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📋</div>
          <div class="empty-state-text">没有活跃的周目</div>
        </div>
      `;
      return;
    }

    await DungeonStore.loadScenes(DungeonStore.currentPlaythrough.id);

    const timeline = await API.get(`/api/scenes/timeline/${DungeonStore.currentPlaythrough.id}`);

    let html = `
      <div class="timeline-header">
        <h3>场景时间线</h3>
        <div class="timeline-stats">
          <span class="stat">
            <span class="stat-label">总场景</span>
            <span class="stat-value">${timeline.summary.total_scenes}</span>
          </span>
          <span class="stat completed">
            <span class="stat-label">已完成</span>
            <span class="stat-value">${timeline.summary.completed_scenes}</span>
          </span>
          <span class="stat active">
            <span class="stat-label">进行中</span>
            <span class="stat-value">${timeline.summary.active_scenes}</span>
          </span>
        </div>
      </div>
      <div class="timeline-progress">
        <div class="progress-fill" style="width: ${timeline.summary.progress}%"></div>
      </div>
      <div class="timeline-chapters">
    `;

    for (const chapter of timeline.chapters) {
      const progress = chapter.total_scenes > 0
        ? Math.round((chapter.completed_scenes / chapter.total_scenes) * 100)
        : 0;

      html += `
        <div class="chapter-group">
          <div class="chapter-header">
            <div class="chapter-header-left">
              <span class="chapter-icon">📖</span>
              <span class="chapter-name">${chapter.chapter_name}</span>
            </div>
            <div class="chapter-header-right">
              <span class="chapter-progress-text">${chapter.completed_scenes}/${chapter.total_scenes}</span>
              <span class="chapter-arrow">▼</span>
            </div>
          </div>
          <div class="chapter-scenes">
      `;

      for (const scene of chapter.scenes) {
        const statusClass = scene.status === 'completed' ? 'completed' :
                           scene.status === 'active' ? 'active' : 'locked';

        const statusIcon = scene.status === 'completed' ? '✓' :
                          scene.status === 'active' ? '◐' : '○';

        html += `
          <div class="scene-item ${statusClass}" data-scene-id="${scene.id}">
            <div class="scene-icon ${statusClass}">${statusIcon}</div>
            <div class="scene-number">${scene.scene_number}</div>
            <div class="scene-info">
              <div class="scene-name">${scene.name}</div>
            </div>
            <div class="scene-progress">
              <div class="progress-bar">
                <div class="progress-fill ${scene.status === 'completed' ? 'success' : ''}"
                     style="width: ${scene.progress}%"></div>
              </div>
              <span class="scene-progress-text">${scene.progress}%</span>
            </div>
          </div>
        `;
      }

      html += `
          </div>
        </div>
      `;
    }

    html += '</div>';
    this.container.innerHTML = html;

    // 绑定事件
    this.bindEvents();
  },

  bindEvents() {
    const sceneItems = this.container.querySelectorAll('.scene-item');
    sceneItems.forEach(item => {
      item.addEventListener('click', () => {
        const sceneId = item.dataset.sceneId;
        if (sceneId) {
          this.showSceneDetail(sceneId);
        }
      });
    });
  },

  async showSceneDetail(sceneId) {
    try {
      const scene = await API.get(`/api/scenes/${sceneId}`);

      const statusText = this.getStatusText(scene.status);
      const statusIcon = scene.status === 'completed' ? '✓' :
                        scene.status === 'active' ? '◐' : '○';

      const content = `
        <div class="scene-detail">
          <div class="scene-detail-header">
            <span class="scene-detail-icon ${scene.status}">${statusIcon}</span>
            <div class="scene-detail-title">
              <h4>${scene.name}</h4>
              <span class="scene-detail-subtitle">${scene.chapter} · ${scene.scene_number}</span>
            </div>
          </div>

          <div class="scene-detail-status">
            <span class="badge badge-${scene.status === 'completed' ? 'success' : scene.status === 'active' ? 'info' : 'gray'}">
              ${statusText}
            </span>
          </div>

          ${scene.description ? `
            <div class="scene-detail-section">
              <label>场景描述</label>
              <p>${scene.description}</p>
            </div>
          ` : ''}

          <div class="scene-detail-section">
            <label>进度</label>
            <div class="scene-detail-progress">
              <div class="progress-bar">
                <div class="progress-fill ${scene.status === 'completed' ? 'success' : ''}"
                     style="width: ${scene.progress}%"></div>
              </div>
              <span class="scene-detail-progress-text">${scene.progress}%</span>
            </div>
          </div>

          <div class="scene-detail-section">
            <label>更新进度</label>
            <div class="scene-detail-slider">
              <input type="range" id="sceneProgressSlider" min="0" max="100" value="${scene.progress}"
                     oninput="document.getElementById('sceneProgressValue').textContent = this.value + '%'">
              <span id="sceneProgressValue">${scene.progress}%</span>
            </div>
          </div>
        </div>
      `;

      const footer = scene.status === 'completed' ? '' : `
        <button class="btn-secondary" onclick="SceneTimeline.updateProgress('${sceneId}')">更新进度</button>
        ${scene.status !== 'completed' ? `<button class="btn-primary" onclick="SceneTimeline.completeScene('${sceneId}')">完成场景</button>` : ''}
      `;

      DungeonUI.showPanel(`场景详情`, content, footer);
    } catch (e) {
      console.error('获取场景详情失败:', e);
    }
  },

  getStatusText(status) {
    const statusMap = {
      'locked': '🔒 未解锁',
      'active': '▶ 进行中',
      'completed': '✓ 已完成'
    };
    return statusMap[status] || status;
  },

  async completeScene(sceneId) {
    try {
      await API.put(`/api/scenes/${sceneId}/progress`, { progress: 100 });
      DungeonUI.hidePanel();
      this.render();
    } catch (e) {
      console.error('完成场景失败:', e);
    }
  },

  async updateProgress(sceneId) {
    try {
      const slider = document.getElementById('sceneProgressSlider');
      const progress = parseInt(slider.value);
      await API.put(`/api/scenes/${sceneId}/progress`, { progress });
      DungeonUI.hidePanel();
      this.render();
    } catch (e) {
      console.error('更新进度失败:', e);
    }
  }
};

/* ============================================
 * 属性面板组件
 * ============================================ */
const AttributePanel = {
  container: null,

  init() {
    this.container = document.getElementById('attributePanel');
  },

  async render() {
    if (!this.container) return;

    if (!DungeonStore.currentPlaythrough) {
      this.container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📊</div>
          <div class="empty-state-text">没有活跃的周目</div>
        </div>
      `;
      return;
    }

    await DungeonStore.loadAttributes(DungeonStore.currentPlaythrough.id);

    let html = `
      <div class="panel-header">
        <h3>属性面板</h3>
        <button class="btn-add" onclick="AttributePanel.showAddAttribute()">
          <span>+</span> 添加
        </button>
      </div>
      <div class="attributes-grid">
    `;

    if (DungeonStore.attributes.length === 0) {
      html += `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-text">暂无属性</div>
        </div>
      `;
    } else {
      for (const attr of DungeonStore.attributes) {
        const percentage = attr.percentage || 0;
        html += `
          <div class="attribute-card" data-attr-id="${attr.id}">
            <div class="attr-header">
              <span class="attr-icon">${attr.icon || '📊'}</span>
              <span class="attr-name">${attr.name}</span>
            </div>
            <div class="attr-value">${Math.round(attr.value)}</div>
            <div class="attr-bar">
              <div class="attr-fill" style="width: ${percentage}%"></div>
            </div>
            <div class="attr-range">
              <span>${attr.min_value}</span>
              <span>${attr.max_value}</span>
            </div>
            <div class="attr-actions">
              <button class="btn-icon btn-minus" onclick="AttributePanel.adjustValue('${attr.id}', -10)">-</button>
              <button class="btn-icon btn-plus" onclick="AttributePanel.adjustValue('${attr.id}', 10)">+</button>
            </div>
          </div>
        `;
      }
    }

    html += '</div>';
    this.container.innerHTML = html;

    // 绑定事件
    this.bindEvents();
  },

  bindEvents() {
    const attrCards = this.container.querySelectorAll('.attribute-card');
    attrCards.forEach(card => {
      card.addEventListener('click', (e) => {
        if (!e.target.classList.contains('btn-small')) {
          const attrId = card.dataset.attrId;
          this.showAttributeHistory(attrId);
        }
      });
    });
  },

  async adjustValue(attrId, delta) {
    try {
      const reason = delta > 0 ? '增加' : '减少';
      await API.put(`/api/attributes/${attrId}`, { delta, reason });
      this.render();
    } catch (e) {
      console.error('调整属性值失败:', e);
    }
  },

  async showAttributeHistory(attrId) {
    try {
      const data = await API.get(`/api/attributes/${attrId}/history`);
      const attr = DungeonStore.attributes.find(a => a.id === attrId);

      const content = `
        <div class="attr-history">
          <h4>${attr.name} 变化历史</h4>
          <div class="history-list">
            ${(data.history || []).map(h => `
              <div class="history-item">
                <span class="history-time">${new Date(h.changed_at * 1000).toLocaleString()}</span>
                <span class="history-change">${h.old_value} → ${h.new_value}</span>
                <span class="history-reason">${h.change_reason || ''}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;

      DungeonUI.showPanel(`${attr.name} 历史`, content, '');
    } catch (e) {
      console.error('获取属性历史失败:', e);
    }
  },

  showAddAttribute() {
    const content = `
      <div class="add-attribute-form">
        <div class="form-group">
          <label>属性名称</label>
          <input type="text" id="newAttrName" placeholder="如: 狐族信任">
        </div>
        <div class="form-group">
          <label>初始值</label>
          <input type="number" id="newAttrValue" value="0">
        </div>
        <div class="form-group">
          <label>最大值</label>
          <input type="number" id="newAttrMax" value="100">
        </div>
        <div class="form-group">
          <label>分类</label>
          <select id="newAttrCategory">
            <option value="trust">信任类</option>
            <option value="corruption">侵蚀类</option>
            <option value="truth">真相类</option>
            <option value="other">其他</option>
          </select>
        </div>
      </div>
    `;

    DungeonUI.showPanel('添加属性', content, `
      <button onclick="AttributePanel.createAttribute()">创建</button>
    `);
  },

  async createAttribute() {
    const name = document.getElementById('newAttrName').value;
    const value = parseFloat(document.getElementById('newAttrValue').value);
    const maxValue = parseFloat(document.getElementById('newAttrMax').value);
    const category = document.getElementById('newAttrCategory').value;

    if (!name) {
      alert('请输入属性名称');
      return;
    }

    try {
      await API.post('/api/attributes', {
        playthrough_id: DungeonStore.currentPlaythrough.id,
        name,
        initial_value: value,
        max_value: maxValue,
        category
      });
      DungeonUI.hidePanel();
      this.render();
    } catch (e) {
      console.error('创建属性失败:', e);
    }
  }
};

/* ============================================
 * 回忆系统组件
 * ============================================ */
const RecallSystem = {
  container: null,

  init() {
    this.container = document.getElementById('recallPanel');
  },

  async render() {
    if (!this.container) return;

    if (!DungeonStore.currentPlaythrough) {
      this.container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">🔮</div>
          <div class="empty-state-text">没有活跃的周目</div>
        </div>
      `;
      return;
    }

    await DungeonStore.loadRecall(DungeonStore.currentPlaythrough.id);
    await DungeonStore.loadDestinyMap();

    const recall = DungeonStore.recallData;
    const destiny = DungeonStore.destinyMap;

    let html = `
      <div class="recall-header">
        <h3>回忆系统</h3>
        <div class="recall-tabs">
          <button class="tab-btn active" data-tab="memories" onclick="RecallSystem.switchTab('memories')">记忆</button>
          <button class="tab-btn" data-tab="endings" onclick="RecallSystem.switchTab('endings')">结局</button>
          <button class="tab-btn" data-tab="destiny" onclick="RecallSystem.switchTab('destiny')">命运</button>
        </div>
      </div>
      <div class="recall-content">
        <div id="recall-memories" class="recall-tab active">
          ${this.renderMemories(recall)}
        </div>
        <div id="recall-endings" class="recall-tab">
          ${this.renderEndings(recall)}
        </div>
        <div id="recall-destiny" class="recall-tab">
          ${this.renderDestinyMap(destiny)}
        </div>
      </div>
    `;

    this.container.innerHTML = html;
  },

  renderMemories(recall) {
    if (!recall || !recall.memories) {
      return '<div class="empty-state">暂无记忆</div>';
    }

    let html = '<div class="memories-list">';

    for (const [type, memories] of Object.entries(recall.memories)) {
      html += `
        <div class="memory-group">
          <h4>${this.getMemoryTypeName(type)}</h4>
          ${memories.map(m => `
            <div class="memory-item">
              <div class="memory-content">${m.content}</div>
              <div class="memory-meta">
                <span class="memory-importance">重要性: ${(m.importance * 100).toFixed(0)}%</span>
                <span class="memory-time">${new Date(m.discovered_at * 1000).toLocaleDateString()}</span>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    html += '</div>';
    return html;
  },

  renderEndings(recall) {
    if (!recall || !recall.endings || recall.endings.length === 0) {
      return '<div class="empty-state">暂无已解锁结局</div>';
    }

    let html = '<div class="endings-list">';

    for (const ending of recall.endings) {
      html += `
        <div class="ending-item">
          <div class="ending-name">${ending.name}</div>
          <div class="ending-description">${ending.description || '暂无描述'}</div>
          <div class="ending-time">解锁于: ${new Date(ending.unlocked_at * 1000).toLocaleDateString()}</div>
        </div>
      `;
    }

    html += '</div>';
    return html;
  },

  renderDestinyMap(destiny) {
    if (!destiny) {
      return '<div class="empty-state">无法加载命运地图</div>';
    }

    let html = `
      <div class="destiny-map">
        <div class="destiny-summary">
          <div class="stat">总周目: ${destiny.summary.total_playthroughs}</div>
          <div class="stat">已完成: ${destiny.summary.completed_playthroughs}</div>
          <div class="stat">已解锁结局: ${destiny.summary.unlocked_endings}</div>
          <div class="stat">总记忆: ${destiny.summary.total_memories}</div>
        </div>
        <div class="destiny-playthroughs">
          <h4>周目历史</h4>
          ${destiny.playthroughs.map(pt => `
            <div class="playthrough-item ${pt.status}">
              <span class="pt-number">第${pt.number}周目</span>
              <span class="pt-route">${pt.route || '默认路线'}</span>
              <span class="pt-status">${pt.status === 'completed' ? '已完成' : pt.status === 'active' ? '进行中' : '已放弃'}</span>
              ${pt.ending ? `<span class="pt-ending">结局: ${pt.ending}</span>` : ''}
            </div>
          `).join('')}
        </div>
      </div>
    `;

    return html;
  },

  getMemoryTypeName(type) {
    const typeMap = {
      'memory': '📝 记忆',
      'ending': '🎬 结局',
      'achievement': '🏆 成就',
      'discovery': '🔍 发现'
    };
    return typeMap[type] || type;
  },

  switchTab(tabName) {
    // 更新标签状态
    this.container.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // 切换内容
    this.container.querySelectorAll('.recall-tab').forEach(tab => {
      tab.style.display = 'none';
    });
    document.getElementById(`recall-${tabName}`).style.display = 'block';
  }
};

/* ============================================
 * 存档管理组件
 * ============================================ */
const SaveManager = {
  container: null,

  init() {
    this.container = document.getElementById('savePanel');
  },

  async render() {
    if (!this.container) return;

    if (!DungeonStore.currentPlaythrough) {
      this.container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">💾</div>
          <div class="empty-state-text">没有活跃的周目</div>
        </div>
      `;
      return;
    }

    await DungeonStore.loadSaves(DungeonStore.currentPlaythrough.id);

    let html = `
      <div class="save-header">
        <h3>存档管理</h3>
      </div>
      <div class="save-actions-bar">
        <button class="btn-primary" onclick="SaveManager.createManualSave()">
          <span>💾</span> 手动存档
        </button>
        <button class="btn-secondary" onclick="SaveManager.exportAllSaves()">
          <span>📤</span> 导出
        </button>
      </div>
      <div class="save-list">
    `;

    if (DungeonStore.saves.length === 0) {
      html += `
        <div class="empty-state">
          <div class="empty-state-text">暂无存档</div>
        </div>
      `;
    } else {
      for (const save of DungeonStore.saves) {
        const isAuto = save.save_type === 'auto';
        const icon = isAuto ? '📁' : '💾';
        const typeName = isAuto ? '自动存档' : '手动存档';
        const time = new Date(save.created_at * 1000).toLocaleString('zh-CN', {
          month: 'numeric',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });

        html += `
          <div class="save-item" data-save-id="${save.id}">
            <div class="save-icon">${icon}</div>
            <div class="save-info">
              <div class="save-name">${save.save_name || typeName}</div>
              <div class="save-meta">
                <span>${time}</span>
              </div>
            </div>
            <div class="save-item-actions">
              <button class="btn-small btn-secondary" onclick="SaveManager.loadSave('${save.id}')">加载</button>
              <button class="btn-small btn-danger" onclick="SaveManager.deleteSave('${save.id}')">删除</button>
            </div>
          </div>
        `;
      }
    }

    html += '</div>';
    this.container.innerHTML = html;
  },

  formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  },

  async createManualSave() {
    const name = prompt('请输入存档名称:');
    if (!name) return;

    try {
      // 收集当前游戏状态
      const saveData = {
        playthrough: DungeonStore.currentPlaythrough,
        scenes: DungeonStore.scenes,
        attributes: DungeonStore.attributes,
        timestamp: Date.now()
      };

      await API.post('/api/saves', {
        playthrough_id: DungeonStore.currentPlaythrough.id,
        save_type: 'manual',
        save_name: name,
        save_data: saveData
      });

      this.render();
    } catch (e) {
      console.error('创建存档失败:', e);
    }
  },

  async loadSave(saveId) {
    if (!confirm('确定要加载此存档吗？当前进度将被覆盖。')) {
      return;
    }

    try {
      const saveData = await API.get(`/api/saves/${saveId}`);
      console.log('加载存档:', saveData);
      // TODO: 实现存档加载逻辑
      alert('存档加载功能开发中');
    } catch (e) {
      console.error('加载存档失败:', e);
    }
  },

  async deleteSave(saveId) {
    if (!confirm('确定要删除此存档吗？')) {
      return;
    }

    try {
      await API.delete(`/api/saves/${saveId}`);
      this.render();
    } catch (e) {
      console.error('删除存档失败:', e);
    }
  },

  async exportAllSaves() {
    try {
      const saves = DungeonStore.saves;
      const exportData = {
        version: '1.0',
        export_time: Date.now(),
        saves: []
      };

      for (const save of saves) {
        const exportResult = await API.post(`/api/saves/${save.id}/export`);
        exportData.saves.push({
          name: save.save_name,
          data: exportResult.export_data
        });
      }

      // 下载文件
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `saves_export_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('导出存档失败:', e);
    }
  }
};

/* ============================================
 * 周目管理组件
 * ============================================ */
const PlaythroughManager = {
  container: null,

  init() {
    this.container = document.getElementById('playthroughPanel');
  },

  async render() {
    if (!this.container) return;

    await DungeonStore.loadPlaythroughs();

    let html = `
      <div class="playthrough-header">
        <h3>周目管理</h3>
        <button class="btn-primary" onclick="PlaythroughManager.createNew()">新周目</button>
      </div>
      <div class="playthrough-list">
    `;

    if (DungeonStore.playthroughs.length === 0) {
      html += '<div class="empty-state">暂无周目记录</div>';
    } else {
      for (const pt of DungeonStore.playthroughs) {
        const isActive = DungeonStore.currentPlaythrough && DungeonStore.currentPlaythrough.id === pt.id;
        html += `
          <div class="playthrough-item ${isActive ? 'active' : ''}" data-pt-id="${pt.id}">
            <div class="pt-number">第${pt.playthrough_number || pt.number}周目</div>
            <div class="pt-info">
              <span class="pt-route">${pt.route || '默认路线'}</span>
              <span class="pt-status ${pt.status}">${this.getStatusText(pt.status)}</span>
              ${pt.ending ? `<span class="pt-ending">结局: ${pt.ending}</span>` : ''}
            </div>
            <div class="pt-time">${new Date(pt.started_at * 1000).toLocaleDateString()}</div>
          </div>
        `;
      }
    }

    html += '</div>';
    this.container.innerHTML = html;

    // 绑定事件
    this.bindEvents();
  },

  getStatusText(status) {
    const statusMap = {
      'active': '进行中',
      'completed': '已完成',
      'abandoned': '已放弃'
    };
    return statusMap[status] || status;
  },

  bindEvents() {
    const items = this.container.querySelectorAll('.playthrough-item');
    items.forEach(item => {
      item.addEventListener('click', () => {
        const ptId = item.dataset.ptId;
        this.switchPlaythrough(ptId);
      });
    });
  },

  async createNew() {
    const route = prompt('请输入路线名称（可选）:');
    try {
      const result = await API.post('/api/playthroughs', { route: route || null });
      await DungeonStore.loadCurrentPlaythrough();
      this.render();
      SceneTimeline.render();
      AttributePanel.render();
    } catch (e) {
      console.error('创建周目失败:', e);
    }
  },

  async switchPlaythrough(ptId) {
    // 切换当前周目
    DungeonStore.currentPlaythrough = DungeonStore.playthroughs.find(pt => pt.id === ptId);
    this.render();
    SceneTimeline.render();
    AttributePanel.render();
    RecallSystem.render();
    SaveManager.render();
  }
};

/* ============================================
 * UI工具函数
 * ============================================ */
const DungeonUI = {
  showPanel(title, content, footer) {
    const panel = document.getElementById('sidePanel');
    const panelTitle = document.getElementById('panelTitle');
    const panelContent = document.getElementById('panelContent');
    const panelFooter = document.getElementById('panelFooter');

    panelTitle.textContent = title;
    panelContent.innerHTML = content;
    panelFooter.innerHTML = footer;
    panel.classList.add('visible');
  },

  hidePanel() {
    const panel = document.getElementById('sidePanel');
    panel.classList.remove('visible');
  }
};

/* ============================================
 * 标签页切换管理
 * ============================================ */
const TabManager = {
  currentTab: 'workflows',

  init() {
    // 监听标签页切换
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
      tab.addEventListener('click', (e) => {
        const tabName = e.target.dataset.tab;
        this.switchTab(tabName);
      });
    });
  },

  async switchTab(tabName) {
    this.currentTab = tabName;

    // 更新标签状态
    document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');

    // 切换内容显示
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    document.getElementById(`tab-${tabName}`)?.classList.remove('hidden');

    // 如果切换到副本标签，触发数据加载和渲染
    if (tabName === 'workflows') {
      await this.loadWorkflowData();
    }
  },

  async loadWorkflowData() {
    // 加载周目数据
    await DungeonStore.loadPlaythroughs();
    await DungeonStore.loadCurrentPlaythrough();

    // 渲染所有组件
    PlaythroughManager.render();
    SceneTimeline.render();
    AttributePanel.render();
    RecallSystem.render();
    SaveManager.render();
  }
};

/* ============================================
 * 初始化
 * ============================================ */
document.addEventListener('DOMContentLoaded', async () => {
  // 初始化标签页管理
  TabManager.init();

  // 初始化副本工作流模块
  await DungeonStore.init();

  // 初始化各个组件
  PlaythroughManager.init();
  SceneTimeline.init();
  AttributePanel.init();
  RecallSystem.init();
  SaveManager.init();

  // 如果当前是副本标签，加载数据
  if (TabManager.currentTab === 'workflows') {
    await TabManager.loadWorkflowData();
  }
});
