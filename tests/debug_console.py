"""
深度调试 - 捕获所有控制台消息
"""
import os
from playwright.sync_api import sync_playwright

def debug():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        all_msgs = []
        page.on("console", lambda msg: all_msgs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: all_msgs.append(f"[PAGE_ERROR] {err}"))

        page.goto("http://localhost:8352")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        print("=== 所有控制台消息 ===")
        for m in all_msgs:
            print(m)

        # 检查哪些全局变量存在
        print("\n=== 全局变量检查 ===")
        for var in ["API", "Store", "Graph", "UI", "DungeonStore", "SceneTimeline", "AttributePanel", "RecallSystem", "SaveManager", "PlaythroughManager", "TabManager"]:
            exists = page.evaluate(f"typeof {var} !== 'undefined'")
            print(f"{var}: {exists}")

        browser.close()

if __name__ == "__main__":
    debug()
