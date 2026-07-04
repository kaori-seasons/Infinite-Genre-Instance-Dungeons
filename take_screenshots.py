"""
使用 Playwright 截取 Memora Connect 界面截图
"""
from playwright.sync_api import sync_playwright
import os

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        # 1. 主页面截图
        print("📸 截取主页面...")
        page.goto("http://localhost:8352")
        page.wait_for_selector("#conceptList .list-item", timeout=10000)
        page.wait_for_timeout(2000)  # 等待图谱渲染
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_main_page.png"), full_page=False)
        print("✅ 主页面截图完成")

        # 2. 点击记忆标签
        print("📸 截取记忆标签...")
        page.click('[data-tab="memories"]')
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_memories_tab.png"), full_page=False)
        print("✅ 记忆标签截图完成")

        # 3. 点击印象标签
        print("📸 截取印象标签...")
        page.click('[data-tab="impressions"]')
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_impressions_tab.png"), full_page=False)
        print("✅ 印象标签截图完成")

        # 4. 点击一个印象查看详情
        print("📸 截取印象详情...")
        impression_items = page.locator("#impressionList .list-item")
        if impression_items.count() > 0:
            impression_items.first.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_impression_detail.png"), full_page=False)
            print("✅ 印象详情截图完成")

        # 5. 关闭面板，回到主页面，点击概念
        print("📸 截取概念详情...")
        page.click("#closePanelBtn")
        page.wait_for_timeout(500)
        page.click('[data-tab="concepts"]')
        page.wait_for_timeout(500)
        concept_items = page.locator("#conceptList .list-item")
        if concept_items.count() > 0:
            concept_items.first.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "05_concept_detail.png"), full_page=False)
            print("✅ 概念详情截图完成")

        browser.close()
        print(f"\n✅ 所有截图已保存到: {SCREENSHOT_DIR}")

if __name__ == "__main__":
    take_screenshots()
