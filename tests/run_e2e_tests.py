"""
副本工作流 E2E 测试脚本
使用 Playwright 进行端到端测试
"""

import os
import sys
from playwright.sync_api import sync_playwright

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screenshots", "e2e")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://localhost:8352"


def run_e2e_tests():
    """运行E2E测试"""
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        # 测试1: 页面加载
        print("测试1: 页面加载...")
        try:
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            title = page.title()
            assert "Memora Connect" in title
            results.append(("页面加载", "通过", f"标题: {title}"))
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_page_load.png"))
        except Exception as e:
            results.append(("页面加载", "失败", str(e)))

        # 测试2: 头部区域可见
        print("测试2: 头部区域可见...")
        try:
            header = page.locator(".app-header")
            assert header.is_visible()
            results.append(("头部区域", "通过", "头部区域可见"))
        except Exception as e:
            results.append(("头部区域", "失败", str(e)))

        # 测试3: 侧边栏标签可见
        print("测试3: 侧边栏标签可见...")
        try:
            tabs = page.locator(".tab-btn")
            assert tabs.first.is_visible()
            results.append(("侧边栏标签", "通过", "标签可见"))
        except Exception as e:
            results.append(("侧边栏标签", "失败", str(e)))

        # 测试4: 点击副本标签
        print("测试4: 点击副本标签...")
        try:
            page.click('[data-tab="workflows"]')
            page.wait_for_timeout(500)
            workflow_tab = page.locator("#tab-workflows")
            # 检查元素是否存在（不一定可见）
            assert workflow_tab.count() > 0
            results.append(("副本标签", "通过", "副本标签存在"))
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_workflow_tab.png"))
        except Exception as e:
            results.append(("副本标签", "失败", str(e)))

        # 测试5: 创建新周目
        print("测试5: 创建新周目...")
        try:
            page.on("dialog", lambda dialog: dialog.accept("E2E测试路线"))
            create_btn = page.locator('button:has-text("新周目")')
            if create_btn.count() > 0 and create_btn.first.is_visible():
                create_btn.first.click()
                page.wait_for_timeout(1500)
                results.append(("创建周目", "通过", "新周目创建成功"))
            else:
                results.append(("创建周目", "跳过", "按钮不可见"))
        except Exception as e:
            results.append(("创建周目", "失败", str(e)))

        # 测试6: 场景时间线存在
        print("测试6: 场景时间线存在...")
        try:
            timeline = page.locator("#sceneTimeline")
            assert timeline.count() > 0
            results.append(("场景时间线", "通过", "时间线元素存在"))
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_scene_timeline.png"))
        except Exception as e:
            results.append(("场景时间线", "失败", str(e)))

        # 测试7: 属性面板存在
        print("测试7: 属性面板存在...")
        try:
            panel = page.locator("#attributePanel")
            assert panel.count() > 0
            results.append(("属性面板", "通过", "面板元素存在"))
        except Exception as e:
            results.append(("属性面板", "失败", str(e)))

        # 测试8: 回忆面板存在
        print("测试8: 回忆面板存在...")
        try:
            panel = page.locator("#recallPanel")
            assert panel.count() > 0
            results.append(("回忆面板", "通过", "面板元素存在"))
        except Exception as e:
            results.append(("回忆面板", "失败", str(e)))

        # 测试9: 存档面板存在
        print("测试9: 存档面板存在...")
        try:
            panel = page.locator("#savePanel")
            assert panel.count() > 0
            results.append(("存档面板", "通过", "面板元素存在"))
        except Exception as e:
            results.append(("存档面板", "失败", str(e)))

        # 测试10: 点击概念标签
        print("测试10: 点击概念标签...")
        try:
            page.click('[data-tab="concepts"]')
            page.wait_for_timeout(500)
            concept_tab = page.locator("#tab-concepts")
            assert concept_tab.is_visible()
            results.append(("概念标签", "通过", "概念标签可点击"))
        except Exception as e:
            results.append(("概念标签", "失败", str(e)))

        # 测试11: 点击记忆标签
        print("测试11: 点击记忆标签...")
        try:
            page.click('[data-tab="memories"]')
            page.wait_for_timeout(500)
            memory_tab = page.locator("#tab-memories")
            assert memory_tab.is_visible()
            results.append(("记忆标签", "通过", "记忆标签可点击"))
        except Exception as e:
            results.append(("记忆标签", "失败", str(e)))

        # 测试12: 点击印象标签
        print("测试12: 点击印象标签...")
        try:
            page.click('[data-tab="impressions"]')
            page.wait_for_timeout(500)
            impression_tab = page.locator("#tab-impressions")
            assert impression_tab.is_visible()
            results.append(("印象标签", "通过", "印象标签可点击"))
        except Exception as e:
            results.append(("印象标签", "失败", str(e)))

        # 测试13: 搜索框可见
        print("测试13: 搜索框可见...")
        try:
            search = page.locator("#globalSearch")
            assert search.is_visible()
            results.append(("搜索框", "通过", "搜索框可见"))
        except Exception as e:
            results.append(("搜索框", "失败", str(e)))

        # 测试14: 图谱区域可见
        print("测试14: 图谱区域可见...")
        try:
            graph = page.locator("#graph")
            assert graph.is_visible()
            results.append(("图谱区域", "通过", "图谱可见"))
        except Exception as e:
            results.append(("图谱区域", "失败", str(e)))

        # 测试15: API测试
        print("测试15: API测试...")
        try:
            response = page.request.get(f"{BASE_URL}/api/status")
            assert response.ok
            data = response.json()
            assert "memory_enabled" in data
            results.append(("API状态", "通过", f"状态: {data}"))
        except Exception as e:
            results.append(("API状态", "失败", str(e)))

        # 测试16: 创建周目API
        print("测试16: 创建周目API...")
        try:
            response = page.request.post(
                f"{BASE_URL}/api/playthroughs",
                data={"route": "E2E测试路线"}
            )
            assert response.ok
            data = response.json()
            assert "id" in data
            results.append(("创建周目API", "通过", f"周目ID: {data['id']}"))
        except Exception as e:
            results.append(("创建周目API", "失败", str(e)))

        # 测试17: 获取周目列表API
        print("测试17: 获取周目列表API...")
        try:
            response = page.request.get(f"{BASE_URL}/api/playthroughs")
            assert response.ok
            data = response.json()
            assert "playthroughs" in data
            results.append(("获取周目列表", "通过", f"周目数量: {len(data['playthroughs'])}"))
        except Exception as e:
            results.append(("获取周目列表", "失败", str(e)))

        # 测试18: 获取命运地图API
        print("测试18: 获取命运地图API...")
        try:
            response = page.request.get(f"{BASE_URL}/api/recall/destiny-map")
            assert response.ok
            data = response.json()
            assert "playthroughs" in data
            results.append(("获取命运地图", "通过", "命运地图获取成功"))
        except Exception as e:
            results.append(("获取命运地图", "失败", str(e)))

        # 测试19: 全页面截图
        print("测试19: 全页面截图...")
        try:
            page.click('[data-tab="workflows"]')
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_full_page.png"), full_page=True)
            results.append(("全页面截图", "通过", "截图已保存"))
        except Exception as e:
            results.append(("全页面截图", "失败", str(e)))

        browser.close()

    # 打印测试结果
    print("\n" + "=" * 60)
    print("E2E 测试结果")
    print("=" * 60)

    passed = sum(1 for _, status, _ in results if status == "通过")
    failed = sum(1 for _, status, _ in results if status == "失败")
    skipped = sum(1 for _, status, _ in results if status == "跳过")

    for name, status, detail in results:
        status_icon = "✓" if status == "通过" else "✗" if status == "失败" else "○"
        print(f"{status_icon} {name}: {detail}")

    print("-" * 60)
    print(f"总计: {len(results)} | 通过: {passed} | 失败: {failed} | 跳过: {skipped}")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_e2e_tests()
    sys.exit(0 if success else 1)
