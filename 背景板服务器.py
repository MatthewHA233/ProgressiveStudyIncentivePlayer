import os
import threading
import time
import pyperclip
import socket
import http.server
import socketserver
import shutil

def get_ip():
    """获取本机IP地址"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 不需要真正连接
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def copy_to_clipboard(text):
    """复制文本到剪贴板"""
    pyperclip.copy(text)
    print(f"已复制URL到剪贴板: {text}")

def ensure_border_assets_folder():
    """确保border_assets文件夹存在，并包含所需资源"""
    # 设置正确的工作目录
    project_dir = r"E:\人工智能\渐进学习时长激励播放器"
    os.chdir(project_dir)
    
    # 创建border_assets文件夹（如果不存在）
    if not os.path.exists("border_assets"):
        os.makedirs("border_assets")
        print("已创建border_assets文件夹")
    
    # 如果src文件夹存在，复制所有资源到border_assets
    if os.path.exists("src"):
        for file in os.listdir("src"):
            src_file = os.path.join("src", file)
            dst_file = os.path.join("border_assets", file)
            if not os.path.exists(dst_file) and os.path.isfile(src_file):
                shutil.copy2(src_file, dst_file)
                print(f"已复制资源: {file}")
    
    # 确保MiSans字体存在
    if not os.path.exists(os.path.join("border_assets", "MiSans-Regular.ttf")):
        # 如果没有MiSans字体，可以复制一个现有字体或提示用户
        print("警告: 未找到MiSans-Regular.ttf字体，请手动添加到border_assets文件夹")

def start_server():
    """启动HTTP服务器"""
    # 设置正确的工作目录
    project_dir = r"E:\人工智能\渐进学习时长激励播放器"
    os.chdir(project_dir)
    print(f"工作目录: {os.getcwd()}")
    
    # 使用自定义处理器来设置正确的字符编码
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def send_header(self, keyword, value):
            if keyword.lower() == 'content-type' and '.html' in self.path:
                value = 'text/html; charset=utf-8'
            super().send_header(keyword, value)
    
    # 使用自定义处理器
    with socketserver.TCPServer(("", 8080), CustomHTTPRequestHandler) as httpd:
        print("服务器已启动在端口8080")
        httpd.serve_forever()

def start_artwork_info_server():
    """启动艺术品信息服务器（端口8081）"""
    # 设置正确的工作目录
    project_dir = r"E:\人工智能\渐进学习时长激励播放器"
    os.chdir(project_dir)
    
    # 使用自定义处理器来设置正确的字符编码
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def send_header(self, keyword, value):
            if keyword.lower() == 'content-type' and '.html' in self.path:
                value = 'text/html; charset=utf-8'
            # 添加CORS头，允许跨域访问
            if keyword.lower() == 'content-type':
                self.send_header('Access-Control-Allow-Origin', '*')
            super().send_header(keyword, value)
    
    # 使用自定义处理器
    with socketserver.TCPServer(("", 8081), CustomHTTPRequestHandler) as httpd:
        print("艺术品信息服务器已启动在端口8081")
        httpd.serve_forever()

def start_audio_visualizer_server():
    """启动音频可视化服务器（端口8082）"""
    # 设置正确的工作目录
    project_dir = r"E:\人工智能\渐进学习时长激励播放器"
    os.chdir(project_dir)
    
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def send_response_only(self, code, message=None):
            super().send_response_only(code, message)
            
        def send_header(self, keyword, value):
            if keyword.lower() == 'content-type' and '.html' in self.path:
                # 确保HTML文件使用UTF-8编码
                value = 'text/html; charset=utf-8'
            # 添加CORS头，允许跨域访问
            if keyword.lower() == 'content-type':
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().send_header(keyword, value)
    
    # 使用自定义处理器
    with socketserver.TCPServer(("", 8082), CustomHTTPRequestHandler) as httpd:
        print("音频可视化服务器已启动在端口8082")
        httpd.serve_forever()

# 确保资源文件夹结构正确
ensure_border_assets_folder()

# 获取本机IP
ip = get_ip()
# 更新URL参数，添加时间戳防止缓存
timestamp = int(time.time())
url = f"http://{ip}:8080/video_border.html?clock_color=skyblue&bgrepeat=off&bg_color=transparent&t={timestamp}"

# 复制URL到剪贴板
copy_to_clipboard(url)

# 打印艺术品信息URL（不复制到剪贴板）
artwork_info_url = f"http://{ip}:8081/artwork_info_display.html"
print(f"艺术品信息URL: {artwork_info_url}")

# 打印音频可视化URL
audio_visualizer_url = f"http://{ip}:8082/audio_visualizer.html"
print(f"音频可视化URL: {audio_visualizer_url}")

# 在新线程中启动主服务器
server_thread = threading.Thread(target=start_server)
server_thread.daemon = True
server_thread.start()

# 在新线程中启动艺术品信息服务器
artwork_info_thread = threading.Thread(target=start_artwork_info_server)
artwork_info_thread.daemon = True
artwork_info_thread.start()

# 在新线程中启动音频可视化服务器
audio_visualizer_thread = threading.Thread(target=start_audio_visualizer_server)
audio_visualizer_thread.daemon = True
audio_visualizer_thread.start()

print(f"HTTP服务器已在 {ip}:8080 启动")
print(f"艺术品信息服务器已在 {ip}:8081 启动")
print(f"音频可视化服务器已在 {ip}:8082 启动")
print("按Ctrl+C停止服务器")

try:
    # 保持主线程运行
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("服务器已停止")