"""
截图脚本v2 - 测试场景时间线
"""

import os
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screenshots", "e2e")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://localhost:8352"


def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        # 1. 页面加载
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        # 2. 点击副本标签
        page.click('[data-tab="workflows"]')
        page.wait_for_timeout(1500)

        # 3. 点击有场景数据的周目（第1周目 - 月光之旅）
        # 使用文本定位找到月光之旅
        moonlight_item = page.locator('.playthrough-item:has-text("月光之旅")')
        if moonlight_item.count() > 0:
            moonlight_item.first.scroll_into_view_if_needed()
            moonlight_item.first.click()
            page.wait_for_timeout(2000)
            print("已点击月光之旅周目")
        else:
            # 如果找不到，点击第一个可见的
            page.locator('.playthrough-item').first.click()
            page.wait_for_timeout(2000)
            print("已点击第一个周目")

        # 截图场景时间线
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "phase2_scene_timeline.png"))
        print("场景时间线截图完成")

        # 4. 点击一个场景查看详情
        scene_items = page.locator('.scene-item')
        scene_count = scene_items.count()
        print(f"找到 {scene_count} 个场景")

        if scene_count > 0:
            scene_items.first.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "phase2_scene_detail.png"))
            print("场景详情截图完成")

        browser.close()
        print("\n所有截图已完成!")


if __name__ == "__main__":
    take_screenshots()
