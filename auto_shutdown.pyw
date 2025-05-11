import sys
import time
from datetime import datetime, timedelta
import os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QLabel
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer, Qt, QPoint
import subprocess
import ctypes

# ===== 配置部分 =====
SHUTDOWN_HOUR = 22    # 关机时间：小时（24小时制）
SHUTDOWN_MINUTE = 10  # 关机时间：分钟
# ==================

# 添加隐藏控制台窗口的代码
if sys.platform == 'win32':
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class AutoShutdown:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # 设置正确的图标路径
        icon_path = os.path.join('assets', 'icons', 'app.ico')
        
        # 创建系统托盘图标
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon(icon_path))
        self.tray.setVisible(True)
        
        # 创建右键菜单
        self.menu = QMenu()
        
        # 添加状态显示（不可点击）
        self.status_action = QAction(f"定时关机已启动")
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        
        # 添加分隔线
        self.menu.addSeparator()
        
        # 添加退出选项
        self.quit_action = QAction("退出")
        self.quit_action.triggered.connect(self.quit)
        self.menu.addAction(self.quit_action)
        
        # 设置托盘图标的菜单
        self.tray.setContextMenu(self.menu)
        
        # 设置提示文字
        self.tray.setToolTip(f"定时关机程序 - 将在{SHUTDOWN_HOUR:02d}:{SHUTDOWN_MINUTE:02d}自动关机")
        
        # 创建倒计时标签
        self.countdown_label = QLabel()
        self.countdown_label.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # 无边框
            Qt.WindowType.WindowStaysOnTopHint | # 保持在顶层
            Qt.WindowType.Tool  # 不在任务栏显示
        )
        self.countdown_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        
        # 创建定时器，每秒更新倒计时
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # 1000毫秒 = 1秒
        
        # 显示启动通知
        self.tray.showMessage(
            "定时关机程序已启动",
            f"程序将在{SHUTDOWN_HOUR:02d}:{SHUTDOWN_MINUTE:02d}自动关机\n右键点击托盘图标可以退出程序",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def update_countdown(self):
        current_time = datetime.now()
        target_time = current_time.replace(
            hour=SHUTDOWN_HOUR, 
            minute=SHUTDOWN_MINUTE, 
            second=0, 
            microsecond=0
        )
        
        # 如果当前时间超过目标时间，设置为明天的目标时间
        if current_time >= target_time:
            target_time += timedelta(days=1)
        
        time_diff = target_time - current_time
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # 根据剩余时间设置不同的样式和提醒
        if hours == 0:
            if minutes <= 3:  # 3分钟内显示红色警告
                self.countdown_label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(255, 0, 0, 200);
                        color: white;
                        padding: 10px;
                        border-radius: 5px;
                        font-size: 18px;
                        font-weight: bold;
                    }
                """)
                if minutes == 3 and seconds == 0:
                    self.tray.showMessage("警告", "距离关机还有3分钟！", 
                                        QSystemTrayIcon.MessageIcon.Warning, 5000)
                elif minutes == 1 and seconds == 0:
                    self.tray.showMessage("警告", "距离关机还有1分钟！", 
                                        QSystemTrayIcon.MessageIcon.Critical, 5000)
            elif minutes <= 10:  # 10分钟内显示橙色警告
                self.countdown_label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(255, 165, 0, 180);
                        color: white;
                        padding: 10px;
                        border-radius: 5px;
                        font-size: 16px;
                        font-weight: bold;
                    }
                """)
                if minutes == 10 and seconds == 0:
                    self.tray.showMessage("注意", "距离关机还有10分钟！", 
                                        QSystemTrayIcon.MessageIcon.Information, 5000)
            else:  # 其他时间显示正常样式
                self.countdown_label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(0, 0, 0, 180);
                        color: white;
                        padding: 10px;
                        border-radius: 5px;
                        font-size: 14px;
                    }
                """)
        
        countdown_text = f"距离关机还有: {hours:02d}:{minutes:02d}:{seconds:02d}"
        self.countdown_label.setText(countdown_text)
        
        # 设置标签位置（右上角）
        screen = self.app.primaryScreen().geometry()
        label_width = self.countdown_label.sizeHint().width()
        self.countdown_label.move(screen.width() - label_width - 20, 20)
        self.countdown_label.show()
        
        # 检查是否到达关机时间
        if (current_time.hour == SHUTDOWN_HOUR and 
            current_time.minute == SHUTDOWN_MINUTE and 
            current_time.second == 0):
            self.tray.showMessage(
                "系统即将关机",
                f"已到达预定时间({SHUTDOWN_HOUR:02d}:{SHUTDOWN_MINUTE:02d})，系统将在1分钟后关机",
                QSystemTrayIcon.MessageIcon.Critical,
                5000
            )
            try:
                # 先尝试取消任何现有的关机计划
                subprocess.run(['shutdown', '/a'], shell=True)
                time.sleep(1)  # 等待一秒确保前一个命令执行完成
                # 执行新的关机命令
                subprocess.run(['shutdown', '/s', '/t', '60', '/f'], shell=True)
            except Exception as e:
                print(f"关机命令执行错误: {e}")
            self.quit()

    def quit(self):
        try:
            # 退出时不取消关机命令，除非明确点击了退出按钮
            if self.sender() == self.quit_action:
                subprocess.run(['shutdown', '/a'], shell=True)
        except Exception:
            pass
        # 隐藏倒计时标签
        self.countdown_label.hide()
        # 退出程序
        self.app.quit()

    def run(self):
        # 启动应用程序事件循环
        self.app.exec()

if __name__ == '__main__':
    # 防止程序重复运行
    if QApplication.instance() is None:
        shutdown_app = AutoShutdown()
        shutdown_app.run() 