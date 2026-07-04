"""
副本工作流 E2E 测试
使用 Playwright 进行端到端测试
"""

import os
import sys
import pytest
from playwright.sync_api import Page, expect

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def browser_context_args():
    """浏览器上下文配置"""
    return {
        "viewport": {"width": 1400, "height": 900},
        "ignore_https_errors": True,
    }


class TestDungeonWorkflowE2E:
    """副本工作流 E2E 测试"""

    def test_page_loads(self, page: Page):
        """测试页面加载"""
        page.goto("http://localhost:8352")
        expect(page).to_have_title("Memora Connect - 副本工作流")

    def test_header_visible(self, page: Page):
        """测试头部区域可见"""
        page.goto("http://localhost:8352")
        header = page.locator(".app-header")
        expect(header).to_be_visible()

    def test_sidebar_tabs_visible(self, page: Page):
        """测试侧边栏标签可见"""
        page.goto("http://localhost:8352")
        tabs = page.locator(".tab-btn")
        expect(tabs.first).to_be_visible()

    def test_workflow_tab_click(self, page: Page):
        """测试点击副本标签"""
        page.goto("http://localhost:8352")
        page.wait_for_selector('[data-tab="workflows"]', timeout=5000)
        page.click('[data-tab="workflows"]')
        workflow_tab = page.locator("#tab-workflows")
        expect(workflow_tab).to_be_visible()

    def test_create_new_playthrough(self, page: Page):
        """测试创建新周目"""
        page.goto("http://localhost:8352")
        page.wait_for_selector('#playthroughPanel', timeout=5000)

        # 点击新周目按钮
        create_btn = page.locator('button:has-text("新周目")')
        if create_btn.is_visible():
            # 处理对话框
            page.on("dialog", lambda dialog: dialog.accept("测试路线"))
            create_btn.click()
            page.wait_for_timeout(1000)

    def test_scene_timeline_visible(self, page: Page):
        """测试场景时间线可见"""
        page.goto("http://localhost:8352")
        page.wait_for_selector('#sceneTimeline', timeout=5000)
        timeline = page.locator("#sceneTimeline")
        expect(timeline).to_be_visible()

    def test_attribute_panel_visible(self, page: Page):
        """测试属性面板可见"""
        page.goto("http://localhost:8352")
        page.wait_for_selector('#attributePanel', timeout=5000)
        panel = page.locator("#attributePanel")
        expect(panel).to_be_visible()

    def test_recall_panel_visible(self, page: Page):
        """测试回忆面板可见"""
        page.goto("http://localhost:8352")
        page.wait_for_selector('#recallPanel', timeout=5000)
        panel = page.locator("#recallPanel")
        expect(panel).to_be_visible()

    def test_save_panel_visible(self, page: Page):
        """测试存档面板可见"""
        page.goto("http://localhost:8352")
        page.wait_for_selector('#savePanel', timeout=5000)
        panel = page.locator("#savePanel")
        expect(panel).to_be_visible()

    def test_concept_tab_click(self, page: Page):
        """测试点击概念标签"""
        page.goto("http://localhost:8352")
        page.wait_for_selector('[data-tab="concepts"]', timeout=5000)
        page.click('[data-tab="concepts"]')
        concept_tab = page.locator("#tab-concepts")
        expect(concept_tab).to_be_visible()

    def test_memory_tab_click(self, page: Page):
        """测试点击记忆标签"""
        page.goto("http://localhost:8352")
        page.wait_for_selector('[data-tab="memories"]', timeout=5000)
        page.click('[data-tab="memories"]')
        memory_tab = page.locator("#tab-memories")
        expect(memory_tab).to_be_visible()

    def test_impression_tab_click(self, page: Page):
        """测试点击印象标签"""
        page.goto("http://localhost:8352")
        page.wait_for_selector('[data-tab="impressions"]', timeout=5000)
        page.click('[data-tab="impressions"]')
        impression_tab = page.locator("#tab-impressions")
        expect(impression_tab).to_be_visible()

    def test_search_input_visible(self, page: Page):
        """测试搜索框可见"""
        page.goto("http://localhost:8352")
        search = page.locator("#globalSearch")
        expect(search).to_be_visible()

    def test_graph_visible(self, page: Page):
        """测试图谱区域可见"""
        page.goto("http://localhost:8352")
        page.wait_for_selector("#graph", timeout=5000)
        graph = page.locator("#graph")
        expect(graph).to_be_visible()

    def test_group_select_visible(self, page: Page):
        """测试分组选择器可见"""
        page.goto("http://localhost:8352")
        group_select = page.locator("#groupSelect")
        expect(group_select).to_be_visible()

    def test_full_page_screenshot(self, page: Page):
        """测试全页面截图"""
        page.goto("http://localhost:8352")
        page.wait_for_timeout(2000)

        screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        page.screenshot(
            path=os.path.join(screenshot_dir, "e2e_dungeon_workflow.png"),
            full_page=True
        )


class TestDungeonWorkflowAPI:
    """副本工作流 API 测试"""

    def test_api_status(self, page: Page):
        """测试API状态"""
        response = page.request.get("http://localhost:8352/api/status")
        assert response.ok
        data = response.json()
        assert "memory_enabled" in data

    def test_api_playthroughs(self, page: Page):
        """测试周目API"""
        response = page.request.get("http://localhost:8352/api/playthroughs")
        assert response.ok
        data = response.json()
        assert "playthroughs" in data

    def test_api_create_playthrough(self, page: Page):
        """测试创建周目API"""
        response = page.request.post(
            "http://localhost:8352/api/playthroughs",
            data={"route": "API测试路线"}
        )
        assert response.ok
        data = response.json()
        assert "id" in data
        assert data["route"] == "API测试路线"

    def test_api_scenes(self, page: Page):
        """测试场景API"""
        # 先创建周目
        pt_response = page.request.post(
            "http://localhost:8352/api/playthroughs",
            data={"route": "场景测试"}
        )
        pt_data = pt_response.json()

        # 获取场景
        response = page.request.get(
            f"http://localhost:8352/api/scenes?playthrough_id={pt_data['id']}"
        )
        assert response.ok
        data = response.json()
        assert "scenes" in data

    def test_api_attributes(self, page: Page):
        """测试属性API"""
        # 先创建周目
        pt_response = page.request.post(
            "http://localhost:8352/api/playthroughs",
            data={"route": "属性测试"}
        )
        pt_data = pt_response.json()

        # 获取属性
        response = page.request.get(
            f"http://localhost:8352/api/attributes?playthrough_id={pt_data['id']}"
        )
        assert response.ok
        data = response.json()
        assert "attributes" in data

    def test_api_saves(self, page: Page):
        """测试存档API"""
        # 先创建周目
        pt_response = page.request.post(
            "http://localhost:8352/api/playthroughs",
            data={"route": "存档测试"}
        )
        pt_data = pt_response.json()

        # 获取存档
        response = page.request.get(
            f"http://localhost:8352/api/saves?playthrough_id={pt_data['id']}"
        )
        assert response.ok
        data = response.json()
        assert "saves" in data

    def test_api_recall(self, page: Page):
        """测试回忆API"""
        # 先创建周目
        pt_response = page.request.post(
            "http://localhost:8352/api/playthroughs",
            data={"route": "回忆测试"}
        )
        pt_data = pt_response.json()

        # 获取回忆
        response = page.request.get(
            f"http://localhost:8352/api/recall?playthrough_id={pt_data['id']}"
        )
        assert response.ok
        data = response.json()
        assert "current_playthrough" in data

    def test_api_destiny_map(self, page: Page):
        """测试命运地图API"""
        response = page.request.get("http://localhost:8352/api/recall/destiny-map")
        assert response.ok
        data = response.json()
        assert "playthroughs" in data
        assert "endings" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
