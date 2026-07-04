"""
截图脚本 - 测试副本工作流UI联动
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
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_initial_load.png"))
        print("1. 初始加载截图完成")

        # 2. 点击副本标签
        page.click('[data-tab="workflows"]')
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_workflow_tab.png"))
        print("2. 副本标签截图完成")

        # 3. 创建新周目
        page.on("dialog", lambda dialog: dialog.accept("测试路线"))
        create_btn = page.locator('button:has-text("新周目")')
        if create_btn.count() > 0:
            create_btn.first.click()
            page.wait_for_timeout(2000)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_after_create.png"))
            print("3. 创建周目后截图完成")

        # 4. 点击概念标签
        page.click('[data-tab="concepts"]')
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_concepts_tab.png"))
        print("4. 概念标签截图完成")

        # 5. 回到副本标签
        page.click('[data-tab="workflows"]')
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "05_back_to_workflow.png"))
        print("5. 回到副本标签截图完成")

        browser.close()
        print("\n所有截图已完成!")


if __name__ == "__main__":
    take_screenshots()
