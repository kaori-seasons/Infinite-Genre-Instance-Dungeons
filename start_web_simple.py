"""
简单启动 Memora Connect Web 界面的脚本
只提供静态文件服务，无需复杂的依赖
"""
import http.server
import socketserver
import os
import sys

# 设置端口
PORT = 8351

# 设置静态文件目录 - 使用 web 目录作为根目录
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        # 如果请求根路径，重定向到 webui/index.html
        if self.path == "/":
            self.path = "/webui/index.html"
        return super().do_GET()

    def log_message(self, format, *args):
        # 自定义日志格式
        print(f"[Web] {args[0]}")

def main():
    print(f"正在启动 Memora Connect Web 界面...")
    print(f"Web 目录: {WEB_DIR}")

    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"\n✅ Memora Connect Web 界面已启动!")
        print(f"🌐 请在浏览器中访问: http://localhost:{PORT}")
        print(f"按 Ctrl+C 停止服务器\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n正在停止服务器...")
            httpd.shutdown()
            print("服务器已停止")

if __name__ == "__main__":
    main()
