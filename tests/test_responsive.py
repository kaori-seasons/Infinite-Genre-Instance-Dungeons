"""
响应式设计测试
测试不同视口尺寸下的布局
"""

import os
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screenshots", "responsive")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://localhost:8352"


def test_responsive():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 测试不同视口尺寸
        viewports = [
            {"width": 1400, "height": 900, "name": "desktop"},
            {"width": 1100, "height": 800, "name": "tablet"},
            {"width": 768, "height": 1024, "name": "mobile"},
        ]

        for viewport in viewports:
            print(f"\n测试 {viewport['name']} ({viewport['width']}x{viewport['height']})...")

            page = browser.new_page(viewport={
                "width": viewport["width"],
                "height": viewport["height"]
            })

            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)

            # 点击副本标签
            page.click('[data-tab="workflows"]')
            page.wait_for_timeout(1500)

            # 点击有场景数据的周目
            moonlight_item = page.locator('.playthrough-item:has-text("月光之旅")')
            if moonlight_item.count() > 0:
                moonlight_item.first.scroll_into_view_if_needed()
                moonlight_item.first.click()
                page.wait_for_timeout(2000)

            # 截图
            page.screenshot(
                path=os.path.join(SCREENSHOT_DIR, f"phase4_{viewport['name']}.png"),
                full_page=False
            )
            print(f"  截图已保存: phase4_{viewport['name']}.png")

            page.close()

        browser.close()
        print("\n所有响应式测试完成!")


if __name__ == "__main__":
    test_responsive()
