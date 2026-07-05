"""
场景详情面板测试
"""

import os
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screenshots", "phase5")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://localhost:8352"


def test_scene_detail():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        print("1. 页面加载...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        print("2. 点击副本标签...")
        page.click('[data-tab="workflows"]')
        page.wait_for_timeout(1500)

        print("3. 选择月光之旅周目...")
        moonlight_item = page.locator('.playthrough-item:has-text("月光之旅")')
        if moonlight_item.count() > 0:
            moonlight_item.first.scroll_into_view_if_needed()
            moonlight_item.first.click()
            page.wait_for_timeout(2000)

        print("4. 点击场景查看详情...")
        scene_items = page.locator('.scene-item')
        if scene_items.count() > 0:
            scene_items.first.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "scene_detail_panel.png"))
            print("   场景详情面板截图完成")

        print("5. 关闭面板...")
        # 使用JavaScript关闭面板
        page.evaluate('DungeonUI.hidePanel()')
        page.wait_for_timeout(500)

        print("6. 点击属性+按钮...")
        add_attr_btn = page.locator('.btn-add:has-text("添加")')
        if add_attr_btn.count() > 0:
            add_attr_btn.scroll_into_view_if_needed()
            add_attr_btn.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "add_attribute_panel.png"))
            print("   添加属性面板截图完成")

        browser.close()
        print("\n所有测试完成!")


if __name__ == "__main__":
    test_scene_detail()
