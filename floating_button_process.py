import sys
import os
import time
import json
import signal
from PyQt5.QtWidgets import QApplication
from floating_button import FloatingButton

# 设置信号处理函数，确保进程能够正常终止
def signal_handler(sig, frame):
    print("进程收到终止信号，正在退出...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def main():
    app = QApplication(sys.argv)
    button = FloatingButton()
    
    # 监听数据文件的变化
    data_file = os.path.join(os.path.dirname(__file__), "floating_button_data.json")
    last_modified = 0
    
    print(f"启动悬浮按钮进程，监听文件: {data_file}")  # 添加调试信息
    
    try:
        while True:
            try:
                # 检查数据文件是否存在并且有更新
                if os.path.exists(data_file):
                    current_modified = os.path.getmtime(data_file)
                    if current_modified > last_modified:
                        last_modified = current_modified
                        
                        # 读取数据文件
                        with open(data_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        print(f"读取到数据: {data}")  # 添加调试信息
                        
                        # 更新按钮数据
                        button.update_data(
                            data.get('current_level', '未知阶段'),
                            data.get('study_time', '0时00分'),
                            data.get('target_time', '12小时'),
                            data.get('predicted_time', '0时00分'),
                            data.get('remaining_time', '0时00分')
                        )
            except Exception as e:
                print(f"更新数据时出错: {e}")
            
            # 处理Qt事件
            app.processEvents()
            time.sleep(0.1)  # 短暂休眠，减少CPU使用
    except KeyboardInterrupt:
        print("用户中断，正在退出...")
    finally:
        print("悬浮按钮进程已终止")

if __name__ == "__main__":
    main() 