"""
调试UI - 检查控制台错误和元素状态
"""

import os
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screenshots", "e2e")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def debug_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        # 收集控制台错误
        errors = []
        page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type in ["error", "warning"] else None)

        page.goto("http://localhost:8352")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # 检查控制台错误
        print("=== 控制台错误/警告 ===")
        for e in errors:
            print(e)

        # 检查元素状态
        print("\n=== 元素状态检查 ===")

        # 检查右侧面板
        right_panel = page.locator(".app-right-panel")
        print(f"右侧面板存在: {right_panel.count() > 0}")
        if right_panel.count() > 0:
            box = right_panel.bounding_box()
            print(f"右侧面板位置: {box}")

        # 检查各个面板
        for panel_id in ["attributePanel", "recallPanel", "savePanel", "playthroughPanel", "sceneTimeline"]:
            el = page.locator(f"#{panel_id}")
            print(f"#{panel_id}: count={el.count()}, visible={el.is_visible() if el.count() > 0 else 'N/A'}")

        # 检查tab-workflows
        tab_wf = page.locator("#tab-workflows")
        print(f"tab-workflows: count={tab_wf.count()}, visible={tab_wf.is_visible() if tab_wf.count() > 0 else 'N/A'}")
        if tab_wf.count() > 0:
            box = tab_wf.bounding_box()
            print(f"tab-workflows 位置: {box}")

        # 检查dungeon.js是否加载
        has_dungeon = page.evaluate("typeof DungeonStore !== 'undefined'")
        print(f"DungeonStore 已定义: {has_dungeon}")

        has_playthrough_mgr = page.evaluate("typeof PlaythroughManager !== 'undefined'")
        print(f"PlaythroughManager 已定义: {has_playthrough_mgr}")

        has_scene_timeline = page.evaluate("typeof SceneTimeline !== 'undefined'")
        print(f"SceneTimeline 已定义: {has_scene_timeline}")

        # 尝试手动调用渲染
        print("\n=== 手动渲染测试 ===")
        try:
            page.evaluate("DungeonStore.init().then(() => { PlaythroughManager.render(); SceneTimeline.render(); AttributePanel.render(); RecallSystem.render(); SaveManager.render(); })")
            page.wait_for_timeout(2000)

            # 再次检查
            for panel_id in ["attributePanel", "recallPanel", "savePanel", "playthroughPanel"]:
                el = page.locator(f"#{panel_id}")
                inner = el.inner_html() if el.count() > 0 else ""
                has_content = len(inner.strip()) > 0
                print(f"#{panel_id} 有内容: {has_content}")

            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "debug_after_manual_render.png"))
            print("手动渲染后截图已保存")
        except Exception as e:
            print(f"手动渲染失败: {e}")

        browser.close()


if __name__ == "__main__":
    debug_ui()
