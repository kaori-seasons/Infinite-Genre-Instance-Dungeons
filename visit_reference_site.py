"""
访问参考网站并截图学习其设计
"""
from playwright.sync_api import sync_playwright
import os

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "reference_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def visit_site():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        print("🌐 访问参考网站...")
        page.goto("https://wbmnbwl.vercel.app/creator", timeout=30000)
        page.wait_for_timeout(3000)

        # 截图1: 首页
        print("📸 截取首页...")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_homepage.png"), full_page=False)

        # 截图2: 滚动查看内容
        print("📸 滚动页面查看更多内容...")
        page.evaluate("window.scrollBy(0, 500)")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_scrolled.png"), full_page=False)

        # 截图3: 再次滚动
        page.evaluate("window.scrollBy(0, 500)")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_more_content.png"), full_page=False)

        # 截图4: 查找并点击可能的工作流相关元素
        print("📸 查找工作流相关元素...")
        # 尝试点击一些按钮或链接
        try:
            buttons = page.locator("button, a, [role='button']")
            count = buttons.count()
            print(f"找到 {count} 个可点击元素")

            # 点击前几个按钮看看
            for i in range(min(5, count)):
                try:
                    btn = buttons.nth(i)
                    if btn.is_visible():
                        text = btn.inner_text()
                        if text and len(text) > 0:
                            print(f"  点击按钮: {text[:30]}...")
                            btn.click()
                            page.wait_for_timeout(1500)
                            page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"04_button_{i}.png"), full_page=False)
                except Exception as e:
                    print(f"  跳过按钮 {i}: {e}")
        except Exception as e:
            print(f"查找按钮失败: {e}")

        # 截图5: 全页面截图
        print("📸 截取全页面...")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "05_full_page.png"), full_page=True)

        browser.close()
        print(f"\n✅ 所有截图已保存到: {SCREENSHOT_DIR}")

if __name__ == "__main__":
    visit_site()
