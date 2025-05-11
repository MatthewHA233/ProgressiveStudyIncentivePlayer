import sys
import os
import json
from datetime import datetime
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt_schedule_manager import ScheduleManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 加载字体配置
        self.load_fonts()
        
        # 设置窗口
        self.setWindowTitle("学习时长激励系统")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1A1A1A;
            }
            QFrame {
                background-color: transparent;
            }
            QPushButton {
                text-align: left;
                padding: 10px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #3B3B3B;
            }
        """)
        
        # 创建主容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 20, 30, 20)
        
        # 创建左右分栏
        self.create_sidebar()
        self.create_main_content()
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.main_frame)
        
    def load_fonts(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                font_family = config.get('font', '微软雅黑')
        except Exception:
            font_family = '微软雅黑'
            
        self.default_font = QFont(font_family, 16)
        self.title_font = QFont(font_family, 28, QFont.Weight.Bold)
        self.subtitle_font = QFont(font_family, 14)
        self.heading_font = QFont(font_family, 32, QFont.Weight.Bold)
        self.description_font = QFont(font_family, 16)
        
    def create_sidebar(self):
        # 侧边栏
        self.sidebar = QFrame()
        self.sidebar.setStyleSheet("QFrame { background-color: #2B2B2B; }")
        self.sidebar.setFixedWidth(280)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        
        # Logo区域
        logo_frame = QFrame()
        logo_layout = QVBoxLayout(logo_frame)
        
        title = QLabel("渐进激励系统")
        title.setFont(self.title_font)
        title.setStyleSheet("color: #FFFFFF;")
        
        subtitle = QLabel("Study Motivation System")
        subtitle.setFont(self.subtitle_font)
        subtitle.setStyleSheet("color: #888888;")
        
        logo_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3B3B3B;")
        separator.setFixedHeight(2)
        
        sidebar_layout.addWidget(logo_frame)
        sidebar_layout.addWidget(separator)
        
        # 侧边栏按钮
        self.create_sidebar_buttons(sidebar_layout)
        sidebar_layout.addStretch()
        
    def create_sidebar_buttons(self, layout):
        buttons = [
            {"text": "主界面", "command": self.show_home_page, "icon": "🏠"},
            {"text": "昼夜表管理", "command": self.show_schedule_manager, "icon": "📅"},
            {"text": "歌单音乐管理", "command": self.show_playlist_manager, "icon": "🎵"},
            {"text": "进行系统设置", "command": self.open_config_editor, "icon": "⚙️"},
            {"text": "查看播放统计", "command": self.show_playlist_stats, "icon": "📊"}
        ]
        
        for btn in buttons:
            button = QPushButton(f"{btn['icon']} {btn['text']}")
            button.setFont(self.default_font)
            button.setStyleSheet("""
                QPushButton {
                    color: #FFFFFF;
                    background-color: transparent;
                    padding: 12px 15px;
                }
                QPushButton:hover {
                    background-color: #3B3B3B;
                }
            """)
            button.clicked.connect(btn["command"])
            layout.addWidget(button)

    def create_main_content(self):
        # 主内容区
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("QFrame { background-color: #2B2B2B; }")
        
        # 主布局
        self.main_layout = QVBoxLayout(self.main_frame)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 默认显示主页面
        self.show_home_page()
        
    def show_home_page(self):
        # 清除主布局中的所有部件
        self.clear_main_frame()
        
        # 创建主页面内容
        self.create_main_buttons()
        
    def create_main_buttons(self):
        # 欢迎标语
        welcome_frame = QFrame()
        welcome_layout = QVBoxLayout(welcome_frame)
        welcome_layout.setContentsMargins(30, 30, 30, 20)
        
        welcome_title = QLabel("今天也要加油学习哦！")
        welcome_title.setFont(self.heading_font)
        welcome_title.setStyleSheet("color: #FFFFFF;")
        
        date_label = QLabel(datetime.now().strftime("%Y年%m月%d日"))
        date_label.setFont(self.description_font)
        date_label.setStyleSheet("color: #888888;")
        
        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(date_label)
        
        self.main_layout.addWidget(welcome_frame)
        
        # 主功能按钮网格
        button_grid = QWidget()
        grid_layout = QVBoxLayout(button_grid)
        grid_layout.setContentsMargins(30, 0, 30, 30)
        
        # 功能按钮配置
        main_buttons = [
            {
                "text": "启动播放器",
                "description": "开始你的学习之旅",
                "command": self.start_player,
                "icon": "▶️"
            },
            {
                "text": "查看今日统计",
                "description": "实时掌握学习进度",
                "command": self.show_today_chart,
                "icon": "📊"
            },
            {
                "text": "历史数据动画",
                "description": "回顾学习历程",
                "command": self.show_chart_animation,
                "icon": "📈"
            },
            {
                "text": "终端回放",
                "description": "查看历史记录",
                "command": self.show_terminal_replay,
                "icon": "🔄"
            }
        ]
        
        # 创建功能按钮
        for btn_config in main_buttons:
            button_frame = QFrame()
            button_frame.setStyleSheet("""
                QFrame {
                    background-color: #363636;
                    border-radius: 10px;
                }
                QFrame:hover {
                    background-color: #404040;
                }
            """)
            
            button_layout = QVBoxLayout(button_frame)
            button_layout.setSpacing(5)
            
            # 按钮标题
            title_label = QLabel(f"{btn_config['icon']} {btn_config['text']}")
            title_label.setFont(self.default_font)
            title_label.setStyleSheet("color: #FFFFFF;")
            
            # 按钮描述
            desc_label = QLabel(btn_config['description'])
            desc_label.setFont(self.subtitle_font)
            desc_label.setStyleSheet("color: #888888;")
            
            button_layout.addWidget(title_label)
            button_layout.addWidget(desc_label)
            
            # 添加点击事件
            button_frame.mousePressEvent = lambda _, cmd=btn_config['command']: cmd()
            
            grid_layout.addWidget(button_frame)
        
        self.main_layout.addWidget(button_grid)
        self.main_layout.addStretch()
        
    def start_player(self):
        """启动播放器"""
        script_path = os.path.join(os.path.dirname(__file__), "progressive_study_player.py")
        self.run_script_in_terminal(script_path)
        
    def show_chart_animation(self):
        """启动历史图表动画"""
        script_path = os.path.join(os.path.dirname(__file__), "study_log_chart_animated.py")
        self.run_script_in_terminal(script_path)
        
    def show_terminal_replay(self):
        """启动终端回放"""
        script_path = os.path.join(os.path.dirname(__file__), "terminal_log_player.py")
        self.run_script_in_terminal(script_path)
        
    def run_script_in_terminal(self, script_path):
        """在终端中运行脚本"""
        if not os.path.exists(script_path):
            self.show_error(f"找不到脚本文件: {script_path}")
            return
            
        try:
            if sys.platform == "win32":
                subprocess.Popen(['start', 'cmd', '/k', sys.executable, script_path], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(['osascript', '-e', 
                    f'tell application "Terminal" to do script "{sys.executable} {script_path}"'])
            else:
                for terminal in ['gnome-terminal', 'xterm', 'konsole']:
                    try:
                        subprocess.Popen([terminal, '--', sys.executable, script_path])
                        return
                    except FileNotFoundError:
                        continue
                self.show_error("无法找到可用的终端模拟器")
        except Exception as e:
            self.show_error(f"运行脚本时出错: {str(e)}")
            
    def show_error(self, message):
        """显示错误消息"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "错误", message)
        
    def clear_main_frame(self):
        """清除主框架中的所有部件"""
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_schedule_manager(self):
        """显示昼夜表管理界面"""
        self.clear_main_frame()
        
        # 创建昼夜表管理器实例
        schedule_manager = ScheduleManager(self.main_frame)
        
        # 将昼夜表管理器添加到主布局
        self.main_layout.addWidget(schedule_manager)

    def show_playlist_manager(self):
        """显示歌单音乐管理界面"""
        self.clear_main_frame()
        # TODO: 实现歌单管理界面
        self.show_under_development("歌单管理功能正在开发中...")

    def open_config_editor(self):
        """打开配置编辑器"""
        self.clear_main_frame()
        # TODO: 实现配置编辑器界面
        self.show_under_development("配置编辑功能正在开发中...")

    def show_playlist_stats(self):
        """显示播放统计界面"""
        self.clear_main_frame()
        # TODO: 实现播放统计界面
        self.show_under_development("播放统计功能正在开发中...")

    def show_today_chart(self):
        """显示今日统计图表"""
        script_path = os.path.join(os.path.dirname(__file__), "study_log_chart_popup.py")
        self.run_script_in_terminal(script_path)

    def show_under_development(self, message):
        """显示开发中提示"""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        
        # 创建提示标签
        label = QLabel(message)
        label.setFont(self.default_font)
        label.setStyleSheet("color: #FFFFFF;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()
        
        self.main_layout.addWidget(frame)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 