import customtkinter as ctk
import subprocess
import sys
import os
from datetime import datetime
from tkinter import messagebox
from PIL import Image
import pandas as pd
import json
from playlist_manager import PlaylistManager

class MainInterface(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icons", "app.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
            

        # 加载字体配置
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.default_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=16)
                self.title_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=28, weight="bold")
                self.subtitle_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=14)
                self.heading_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=32, weight="bold")
                self.description_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=16)
        except Exception as e:
            print(f"加载字体配置失败: {str(e)}")
            # 使用默认字体
            self.default_font = ctk.CTkFont(family='微软雅黑', size=16)
            self.title_font = ctk.CTkFont(family='微软雅黑', size=28, weight="bold")
            self.subtitle_font = ctk.CTkFont(family='微软雅黑', size=14)
            self.heading_font = ctk.CTkFont(family='微软雅黑', size=32, weight="bold")
            self.description_font = ctk.CTkFont(family='微软雅黑', size=16)

        # 设置窗口
        self.title("学习时长激励系统")
        self.geometry("1200x700")
        
        # 设置深色主题
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#1A1A1A")
        
        # 创建主容器
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=30, pady=20)
        
        # 创建左右分栏
        self.create_sidebar()
        self.create_main_content()
        
    def create_sidebar(self):
        # 侧边栏
        self.sidebar = ctk.CTkFrame(self.main_container, fg_color="#2B2B2B", width=200)
        self.sidebar.pack(side="left", fill="y", padx=(0, 20))
        
        # Logo或标题区
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(20, 30))
        
        title = ctk.CTkLabel(
            logo_frame,
            text="渐进激励系统",
            font=self.title_font,
            text_color="#FFFFFF"
        )
        title.pack()
        
        subtitle = ctk.CTkLabel(
            logo_frame,
            text="Study Motivation System",
            font=self.subtitle_font,
            text_color="#888888"
        )
        subtitle.pack()
        
        # 分割线
        separator = ctk.CTkFrame(self.sidebar, fg_color="#3B3B3B", height=2)
        separator.pack(fill="x", padx=15, pady=(0, 20))
        
        # 侧边栏按钮
        self.create_sidebar_buttons()
        
    def create_main_content(self):
        # 主内容区
        self.main_frame = ctk.CTkFrame(self.main_container, fg_color="#2B2B2B")
        self.main_frame.pack(side="left", fill="both", expand=True)
        
        # 默认显示主页面
        self.show_home_page()
        
    def show_home_page(self):
        # 停止当前播放的音乐
        self.stop_current_music()
        
        # 清除主框架中的所有部件
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        # 主要功能区
        self.create_main_buttons()
        
    def create_sidebar_buttons(self):
        sidebar_buttons = [
            {
                "text": "主界面",
                "command": self.show_home_page,
                "icon": "🏠"
            },
            {
                "text": "昼夜表管理",
                "command": self.show_schedule_manager,
                "icon": "📅"
            },
            {
                "text": "歌单音乐管理",
                "command": self.show_playlist_manager,
                "icon": "🎵"
            },
            {
                "text": "进行系统设置",
                "command": self.open_config_editor,
                "icon": "⚙️"
            },
            {
                "text": "查看播放统计",
                "command": self.show_playlist_stats,
                "icon": "📊"
            }
        ]
        
        for btn in sidebar_buttons:
            button = ctk.CTkButton(
                self.sidebar,
                text=f"{btn['icon']} {btn['text']}",
                command=btn["command"],
                width=180,
                height=45,
                fg_color="transparent",
                text_color="#FFFFFF",
                hover_color="#3B3B3B",
                anchor="w",
                corner_radius=6,
                font=self.default_font
            )
            button.pack(pady=8, padx=10)
        
    def create_main_buttons(self):
        # 欢迎标语
        welcome_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        welcome_frame.pack(fill="x", padx=30, pady=(30, 20))
        
        ctk.CTkLabel(
            welcome_frame,
            text="今天也要加油学习哦！",
            font=self.heading_font,
            text_color="#FFFFFF"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            welcome_frame,
            text=datetime.now().strftime("%Y年%m月%d日"),
            font=self.description_font,
            text_color="#888888"
        ).pack(anchor="w")
        
        # 主要功能按钮
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # 创建主要功能按钮
        main_buttons = [
            # 第一行 - 两个按钮并排
            [
                {
                    "text": "启动渐进学习时长激励播放器",
                    "command": self.start_player,
                    "color": "#4169E1",
                    "hover_color": "#1E90FF",
                    "icon": "▶️",
                    "description": "开始你的学习之旅"
                },
                {
                    "text": "启动5分钟间隔弹窗",
                    "command": self.start_auto_logger,
                    "color": "#FF8C00",  # 深橙色
                    "hover_color": "#FF7F24",
                    "icon": "⏱️",
                    "description": "记录每5分钟的活动"
                }
            ],
            # 第二行 - 两个按钮并排
            [
                {
                    "text": "当日块时间总结",
                    "command": self.start_time_block_clicker,
                    "color": "#9370DB",  # 紫色
                    "hover_color": "#8A2BE2",
                    "icon": "📊",
                    "description": "处理今日时间块记录"
                },
                {
                    "text": "查看今日学习时长图表",
                    "command": self.show_today_chart,
                    "color": "#32CD32",
                    "hover_color": "#228B22",
                    "icon": "📈",
                    "description": "查看今天的学习进度"
                }
            ],
            # 第三行 - 两个按钮并排
            [
                {
                    "text": "生成历史图表动画",
                    "command": self.show_chart_animation,
                    "color": "#FF4D4D",
                    "hover_color": "#DC143C",
                    "icon": "🎬",
                    "description": "回顾历史学习数据"
                },
                {
                    "text": "查看终端回放",
                    "command": self.show_terminal_replay,
                    "color": "#4682B4",  # 钢蓝色
                    "hover_color": "#4169E1",
                    "icon": "🔄",
                    "description": "回顾历史终端记录"
                }
            ],
            # 第四行 - 两个按钮并排
            [
                {
                    "text": "壁纸引擎映射管理",
                    "command": self.start_wallpaper_music_matcher,
                    "color": "#20B2AA",  # 浅海绿
                    "hover_color": "#008B8B",
                    "icon": "🖼️",
                    "description": "管理壁纸音乐映射"
                },
                {
                    "text": "设置事情类型及坐标",
                    "command": self.start_activity_type_editor,
                    "color": "#FF69B4",  # 热粉红
                    "hover_color": "#FF1493",
                    "icon": "📝",
                    "description": "编辑事情类型及其坐标点"
                }
            ]
        ]
        
        # 创建四行按钮，每行两个并排
        for row_idx, row_buttons in enumerate(main_buttons):
            # 创建行容器
            row_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=(0, 15))
            
            # 为每行创建两列
            for col_idx, btn in enumerate(row_buttons):
                # 创建按钮容器
                btn_container = ctk.CTkFrame(row_frame, fg_color="#363636")
                btn_container.pack(side="left", fill="both", expand=True, padx=(0 if col_idx == 0 else 10, 0 if col_idx == len(row_buttons)-1 else 10))
                
                # 按钮图标和文本
                ctk.CTkLabel(
                    btn_container,
                    text=btn["icon"],
                    font=self.heading_font
                ).pack(side="left", padx=(25, 15))
                
                # 文本区域
                text_frame = ctk.CTkFrame(btn_container, fg_color="transparent")
                text_frame.pack(side="left", fill="x", expand=True)
                
                ctk.CTkLabel(
                    text_frame,
                    text=btn["text"],
                    font=self.default_font,
                    text_color="#FFFFFF"
                ).pack(anchor="w")
                
                ctk.CTkLabel(
                    text_frame,
                    text=btn["description"],
                    font=self.description_font,
                    text_color="#888888"
                ).pack(anchor="w")
                
                # 启动按钮
                ctk.CTkButton(
                    btn_container,
                    text="启动",
                    command=btn["command"],
                    width=120,
                    height=40,
                    fg_color=btn["color"],
                    hover_color=btn["hover_color"],
                    corner_radius=6,
                    font=self.default_font
                ).pack(side="right", padx=25, pady=15)

    def start_player(self):
        """在新终端中启动播放器"""
        script_path = os.path.join(os.path.dirname(__file__), "progressive_study_player.py")
        
        if os.path.exists(script_path):
            if sys.platform == "win32":
                subprocess.Popen(
                    ['start', 'cmd', '/k', sys.executable, script_path],
                    shell=True
                )
            elif sys.platform == "darwin":
                subprocess.Popen([
                    'osascript',
                    '-e',
                    f'tell application "Terminal" to do script "{sys.executable} {script_path}"'
                ])
            else:
                terminals = ['gnome-terminal', 'xterm', 'konsole']
                launched = False
                
                for terminal in terminals:
                    try:
                        subprocess.Popen([terminal, '--', sys.executable, script_path])
                        launched = True
                        break
                    except FileNotFoundError:
                        continue
                        
                if not launched:
                    messagebox.showerror("错误", "无法找到可用的终端模拟器")
        else:
            messagebox.showerror("错误", f"找不到脚本文件: {script_path}")
            
    def open_config_editor(self):
        # 清除主框架中的所有部件
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        # 导入配置编辑器
        from config_editor import ConfigEditor
        
        # 在主框架中创建配置编辑器
        config_editor = ConfigEditor(self.main_frame)
        config_editor.pack(fill="both", expand=True)
        
    def show_today_chart(self):
        self.run_script("study_log_chart_popup.py")
        
    def show_chart_animation(self):
        """在新终端中启动历史图表动画"""
        script_path = os.path.join(os.path.dirname(__file__), "study_log_chart_animated.py")
        
        if os.path.exists(script_path):
            if sys.platform == "win32":
                subprocess.Popen(
                    ['start', 'cmd', '/k', sys.executable, script_path],
                    shell=True
                )
            elif sys.platform == "darwin":
                subprocess.Popen([
                    'osascript',
                    '-e',
                    f'tell application "Terminal" to do script "{sys.executable} {script_path}"'
                ])
            else:
                terminals = ['gnome-terminal', 'xterm', 'konsole']
                launched = False
                
                for terminal in terminals:
                    try:
                        subprocess.Popen([terminal, '--', sys.executable, script_path])
                        launched = True
                        break
                    except FileNotFoundError:
                        continue
                        
                if not launched:
                    messagebox.showerror("错误", "无法找到可用的终端模拟器")
        else:
            messagebox.showerror("错误", f"找不到脚本文件: {script_path}")
            
    def show_terminal_replay(self):
        """在新终端中启动终端回放"""
        script_path = os.path.join(os.path.dirname(__file__), "terminal_log_player.py")
        
        if os.path.exists(script_path):
            if sys.platform == "win32":
                subprocess.Popen(
                    ['start', 'cmd', '/k', sys.executable, script_path],
                    shell=True
                )
            elif sys.platform == "darwin":
                subprocess.Popen([
                    'osascript',
                    '-e',
                    f'tell application "Terminal" to do script "{sys.executable} {script_path}"'
                ])
            else:
                terminals = ['gnome-terminal', 'xterm', 'konsole']
                launched = False
                
                for terminal in terminals:
                    try:
                        subprocess.Popen([terminal, '--', sys.executable, script_path])
                        launched = True
                        break
                    except FileNotFoundError:
                        continue
                        
                if not launched:
                    messagebox.showerror("错误", "无法找到可用的终端模拟器")
        else:
            messagebox.showerror("错误", f"找不到脚本文件: {script_path}")
            
    def show_playlist_stats(self):
        # 停止当前播放的音乐
        self.stop_current_music()
        
        # 清除主框架中的所有部件
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 导入并创建播放统计查看器
        from playlist_play_count_summary import PlaylistStatsViewer
        stats_viewer = PlaylistStatsViewer(self.main_frame)
        stats_viewer.pack(fill="both", expand=True)

    def run_script(self, script_name):
        try:
            script_path = os.path.join(os.path.dirname(__file__), script_name)
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script_path])
            else:
                messagebox.showerror("错误", f"找不到脚本文件: {script_name}")
        except Exception as e:
            messagebox.showerror("错误", f"运行脚本时出错: {str(e)}")

    def show_schedule_manager(self):
        # 停止当前播放的音乐
        self.stop_current_music()
        
        # 清除主框架中的所有部件
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 导入并创建昼夜表管理器
        from schedule_manager import ScheduleManager
        schedule_manager = ScheduleManager(self.main_frame)
        schedule_manager.pack(fill="both", expand=True)

    def show_playlist_manager(self):
        # 停止当前播放的音乐
        self.stop_current_music()
        
        self.clear_main_frame()
        playlist_manager = PlaylistManager(self.main_frame)
        playlist_manager.pack(fill="both", expand=True)

    def clear_main_frame(self):
        """清除主框架中的所有部件"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def stop_current_music(self):
        """停止当前正在播放的音乐"""
        import pygame
        try:
            if pygame.mixer.get_init():  # 检查mixer是否已初始化
                pygame.mixer.music.stop()
        except Exception as e:
            print(f"停止音乐时出错: {str(e)}")

    def start_auto_logger(self):
        """启动5分钟间隔弹窗 (DayNightTableAutoLogger.py)"""
        script_path = os.path.join(os.path.dirname(__file__), "DayNightTableAutoLogger.py")
        
        if os.path.exists(script_path):
            if sys.platform == "win32":
                subprocess.Popen(
                    ['start', 'cmd', '/k', sys.executable, script_path],
                    shell=True
                )
            elif sys.platform == "darwin":
                subprocess.Popen([
                    'osascript',
                    '-e',
                    f'tell application "Terminal" to do script "{sys.executable} {script_path}"'
                ])
            else:
                terminals = ['gnome-terminal', 'xterm', 'konsole']
                launched = False
                
                for terminal in terminals:
                    try:
                        subprocess.Popen([terminal, '--', sys.executable, script_path])
                        launched = True
                        break
                    except FileNotFoundError:
                        continue
                        
                if not launched:
                    messagebox.showerror("错误", "无法找到可用的终端模拟器")
        else:
            messagebox.showerror("错误", f"找不到脚本文件: {script_path}")

    def start_time_block_clicker(self):
        """启动时间块点击器 (TimeBlockClicker.py)"""
        script_path = os.path.join(os.path.dirname(__file__), "TimeBlockClicker.py")
        
        if os.path.exists(script_path):
            if sys.platform == "win32":
                subprocess.Popen(
                    ['start', 'cmd', '/k', sys.executable, script_path],
                    shell=True
                )
            elif sys.platform == "darwin":
                subprocess.Popen([
                    'osascript',
                    '-e',
                    f'tell application "Terminal" to do script "{sys.executable} {script_path}"'
                ])
            else:
                terminals = ['gnome-terminal', 'xterm', 'konsole']
                launched = False
                
                for terminal in terminals:
                    try:
                        subprocess.Popen([terminal, '--', sys.executable, script_path])
                        launched = True
                        break
                    except FileNotFoundError:
                        continue
                        
                if not launched:
                    messagebox.showerror("错误", "无法找到可用的终端模拟器")
        else:
            messagebox.showerror("错误", f"找不到脚本文件: {script_path}")

    def start_wallpaper_music_matcher(self):
        """启动壁纸引擎映射管理 (WallpaperMusicMatcher.py)"""
        script_path = os.path.join(os.path.dirname(__file__), "WallpaperMusicMatcher.py")
        
        if os.path.exists(script_path):
            if sys.platform == "win32":
                subprocess.Popen(
                    ['start', 'cmd', '/k', sys.executable, script_path],
                    shell=True
                )
            elif sys.platform == "darwin":
                subprocess.Popen([
                    'osascript',
                    '-e',
                    f'tell application "Terminal" to do script "{sys.executable} {script_path}"'
                ])
            else:
                terminals = ['gnome-terminal', 'xterm', 'konsole']
                launched = False
                
                for terminal in terminals:
                    try:
                        subprocess.Popen([terminal, '--', sys.executable, script_path])
                        launched = True
                        break
                    except FileNotFoundError:
                        continue
                        
                if not launched:
                    messagebox.showerror("错误", "无法找到可用的终端模拟器")
        else:
            messagebox.showerror("错误", f"找不到脚本文件: {script_path}")

    def start_activity_type_editor(self):
        """启动事情类型编辑器 (activity_type_editor.py)"""
        script_path = os.path.join(os.path.dirname(__file__), "activity_type_editor.py")
        
        if os.path.exists(script_path):
            if sys.platform == "win32":
                subprocess.Popen(
                    ['start', 'cmd', '/k', sys.executable, script_path],
                    shell=True
                )
            elif sys.platform == "darwin":
                subprocess.Popen([
                    'osascript',
                    '-e',
                    f'tell application "Terminal" to do script "{sys.executable} {script_path}"'
                ])
            else:
                terminals = ['gnome-terminal', 'xterm', 'konsole']
                launched = False
                
                for terminal in terminals:
                    try:
                        subprocess.Popen([terminal, '--', sys.executable, script_path])
                        launched = True
                        break
                    except FileNotFoundError:
                        continue
                        
                if not launched:
                    messagebox.showerror("错误", "无法找到可用的终端模拟器")
        else:
            messagebox.showerror("错误", f"找不到脚本文件: {script_path}")

if __name__ == "__main__":
    app = MainInterface()
    app.mainloop() 