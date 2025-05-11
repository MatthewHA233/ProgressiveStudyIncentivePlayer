from dataclasses import dataclass
from typing import Dict, List, Callable, Optional, Tuple
import customtkinter as ctk
import os
import json
from PIL import Image
from tkinter import messagebox
from playlist_manager_player import PlaylistPlayer
from playlist_manager_colorpicker import PlaylistColorPicker
from playlist_manager_filehandler import PlaylistFileHandler
import tkinter
import time
import pandas as pd

@dataclass
class PlaylistConfig:
    """歌单配置数据类"""
    name: str
    color: str = "#363636"

class PlaylistConstants:
    """常量配置"""
    MUSIC_FOLDER = 'music_library'
    DEFAULT_FONT_FAMILY = '微软雅黑'
    SPECIAL_PLAYLISTS = {'未分类', '遗弃', '音效'}
    DEFAULT_COLORS = {
        'default_column': "#505050",
        'default_block': "#484848",
        'transparent': "transparent",
        'hover': "#505050",
        'background': "#2B2B2B",
        'text': "#000000",
        'text_header': "#FFFFFF",
        'text_secondary': "#000000",
        'button_bg': "#000000",
        'button_hover': "#797979",
        'header_bg': "#363636"
    }
    DIMENSIONS = {
        'column_width': 300,
        'column_height': 600,
        'header_height': 45,
        'song_block_height': 50,
        'icon_size': (20, 20),
        'corner_radius': 12,
        'block_radius': 8,
        'button_size': 32,
        'button_corner': 8
    }
    FONTS = {
        'title_size': 20,
        'subtitle_size': 12
    }

class PlaylistManager(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config: Dict = {}
        self.color_map: Dict[str, str] = {}
        
        # 初始化顺序很重要
        self._load_config()  # 首先加载配置和字体
        self._load_icons()   # 然后加载图标
        self._init_ui()      # 最后初始化UI
        
        # 在后台线程中初始化CSV文件
        import threading
        file_handler = PlaylistFileHandler(PlaylistConstants.MUSIC_FOLDER)
        csv_thread = threading.Thread(
            target=file_handler.initialize_missing_csvs,
            daemon=True  # 使用daemon线程，这样主程序退出时线程会自动结束
        )
        csv_thread.start()
        
        self._load_color_ranges()
        self._create_kanban()

        # 加载垃圾箱图标（初始较小）
        self.trash_icon = ctk.CTkImage(
            Image.open("assets/icons/actions/trash.png"),
            size=(24, 24)  # 初始小尺寸
        )
        self.trash_red_icon = ctk.CTkImage(
            Image.open("assets/icons/actions/trash-red.png"),
            size=(24, 24)  # 初始小尺寸
        )
        
        # 创建大尺寸图标用于悬停状态
        self.trash_icon_large = ctk.CTkImage(
            Image.open("assets/icons/actions/trash.png"),
            size=(48, 48)  # 悬停时的大尺寸
        )
        self.trash_red_icon_large = ctk.CTkImage(
            Image.open("assets/icons/actions/trash-red.png"),
            size=(48, 48)  # 悬停时的大尺寸
        )
        
        # 创建垃圾箱按钮（放在更靠右的位置）
        self.trash_button = ctk.CTkButton(
            self,
            text="",
            image=self.trash_icon,
            width=32,
            height=32,
            fg_color="#000000",
            hover_color="#363636",
            corner_radius=8,
            command=self._show_trash_history  # 添加点击事件处理
        )
        # 调整位置到更靠右
        self.trash_button.place(x=395, y=68)  # x坐标更大，y坐标稍微往下
        
        # 更新原始位置记录
        self._original_trash_pos = (395, 68)
        
        # 存储动画相关变量
        self._drag_over_trash = False
        self._shake_animation_id = None

    def _load_config(self) -> None:
        """加载配置文件和初始化字体"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self._init_fonts(self.config.get('font', PlaylistConstants.DEFAULT_FONT_FAMILY))
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            self._init_fonts(PlaylistConstants.DEFAULT_FONT_FAMILY)

    def _init_fonts(self, font_family: str) -> None:
        """初始化字体"""
        self.default_font = ctk.CTkFont(family=font_family)
        self.title_font = ctk.CTkFont(
            family=font_family, 
            size=PlaylistConstants.FONTS['title_size'], 
            weight="bold"
        )
        self.subtitle_font = ctk.CTkFont(
            family=font_family, 
            size=PlaylistConstants.FONTS['subtitle_size']
        )

    def _load_icons(self) -> None:
        """加载图标"""
        self.paintbucket_icon = ctk.CTkImage(
            light_image=Image.open("assets/icons/actions/paintbucket.png"),
            dark_image=Image.open("assets/icons/actions/paintbucket.png"),
            size=PlaylistConstants.DIMENSIONS['icon_size']
        )
        # 加载黑色和白色两个版本的拖动图标
        self.drag_icon = ctk.CTkImage(
            light_image=Image.open("assets/icons/actions/drag-node.png"),
            dark_image=Image.open("assets/icons/actions/drag-node.png"),
            size=(16, 16)
        )
        self.drag_icon_white = ctk.CTkImage(  # 添加白色版本
            light_image=Image.open("assets/icons/actions/drag-node-white.png"),
            dark_image=Image.open("assets/icons/actions/drag-node-white.png"),
            size=(16, 16)
        )

    def _init_ui(self) -> None:
        """初始化UI布局"""
        self.main_layout = self._create_main_layout()
        self.top_frame = self._create_top_frame()
        self._create_title()
        self.player = PlaylistPlayer(self.top_frame)
        self.player.pack(side="right", padx=10)

    def _create_main_layout(self) -> ctk.CTkFrame:
        """创建主布局"""
        layout = ctk.CTkFrame(self, fg_color=PlaylistConstants.DEFAULT_COLORS['transparent'])
        layout.pack(fill="both", expand=True)
        return layout

    def _create_top_frame(self) -> ctk.CTkFrame:
        """创建顶部框架"""
        frame = ctk.CTkFrame(
            self.main_layout, 
            fg_color=PlaylistConstants.DEFAULT_COLORS['transparent']
        )
        frame.pack(fill="x", padx=20, pady=(10, 10))
        return frame

    def _create_title(self) -> None:
        """创建标题"""
        ctk.CTkLabel(
            self.top_frame,
            text="歌单音乐管理",
            font=self.title_font
        ).pack(side="left")

    def _load_color_ranges(self) -> None:
        """加载颜色配置"""
        try:
            self.color_map = {
                level['name']: level.get('color', PlaylistConstants.DEFAULT_COLORS['default_column'])
                for level in self.config.get('levels', [])
            }
        except Exception as e:
            print(f"加载颜色配置失败: {str(e)}")
            self.color_map = {}

    def _create_kanban(self) -> None:
        """创建看板"""
        self.kanban_scroll = self._create_kanban_scroll()
        self.kanban_frame = self._create_kanban_frame()
        self._load_playlists()

    def _create_kanban_scroll(self) -> ctk.CTkScrollableFrame:
        """创建看板滚动区域"""
        scroll = ctk.CTkScrollableFrame(
            self.main_layout,
            fg_color=PlaylistConstants.DEFAULT_COLORS['transparent'],
            orientation="horizontal",  # 启用水平滚动
            width=self.winfo_width() - 40,  # 减去左右边距
            height=PlaylistConstants.DIMENSIONS['column_height']
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        return scroll

    def _create_kanban_frame(self) -> ctk.CTkFrame:
        """创建看板框架"""
        frame = ctk.CTkFrame(
            self.kanban_scroll, 
            fg_color=PlaylistConstants.DEFAULT_COLORS['transparent']
        )
        frame.pack(fill="both", expand=True)
        return frame

    def _load_playlists(self) -> None:
        """加载歌单列表"""
        try:
            music_path = PlaylistConstants.MUSIC_FOLDER
            if not os.path.exists(music_path):
                os.makedirs(music_path)
                
            folders = self._get_sorted_playlist_folders()
            for i, folder in enumerate(folders):
                self._create_playlist_column(folder, i)
        except Exception as e:
            messagebox.showerror("错误", f"加载歌单失败: {str(e)}")

    def _get_sorted_playlist_folders(self) -> List[str]:
        """获取排序后的歌单文件夹列表"""
        music_path = PlaylistConstants.MUSIC_FOLDER
        all_folders = [d for d in os.listdir(music_path) 
                      if os.path.isdir(os.path.join(music_path, d))]
        
        # 分类文件夹
        special_folders = []  # 特殊文件夹（未分类、遗弃）
        level_folders = []    # 配置中的歌单
        other_folders = []    # 其他文件夹
        
        for folder in all_folders:
            # 跳过音效文件夹
            if folder == '音效':
                continue
            # 处理其他特殊文件夹
            elif folder in {'未分类', '遗弃'}:
                special_folders.append(folder)
            elif self._is_folder_in_config(folder):
                level_folders.append(folder)
            else:
                other_folders.append(folder)
        
        # 按配置顺序排序
        level_folders.sort(key=self._get_folder_sort_key)
        special_folders.sort()
        other_folders.sort()
        
        # 组合所有文件夹：特殊文件夹 + 配置歌单 + 其他文件夹
        return special_folders + level_folders + other_folders

    def _is_folder_in_config(self, folder_name: str) -> bool:
        """检查文件夹是否在配置中"""
        for level in self.config.get('levels', []):
            if level['name'].startswith(folder_name):
                return True
        return False

    def _get_folder_sort_key(self, folder_name: str) -> float:
        """获件夹排序键值"""
        for level in self.config.get('levels', []):
            if level['name'].startswith(folder_name):
                return level.get('start', 0.0)
        return float('inf')

    def _create_playlist_column(self, playlist_name: str, index: int) -> None:
        """创建歌单列"""
        # 创建主列框架
        column = ctk.CTkFrame(
            self.kanban_frame,
            fg_color=self._get_column_color(playlist_name),
            width=250,
            height=PlaylistConstants.DIMENSIONS['column_height'],
            corner_radius=PlaylistConstants.DIMENSIONS['corner_radius']
        )
        column.pack(side="left", padx=5, fill="y")
        column.pack_propagate(False)
        
        # 存储playlist_name用于颜色更新
        column.playlist_name = playlist_name
        
        # 创建标题区域
        header = self._create_column_header(column, playlist_name)
        header.pack(fill="x", padx=5, pady=5)
        
        # 创建歌曲列表区域
        songs_frame = ctk.CTkScrollableFrame(
            column,
            fg_color=self._get_column_color(playlist_name),
            corner_radius=PlaylistConstants.DIMENSIONS['block_radius']
        )
        songs_frame.pack(fill="both", expand=True, padx=5, pady=(5, 0))
        
        # 标记这个框架为歌曲列表框架
        songs_frame.is_songs_frame = True
        
        # 加载歌曲
        self._load_songs(songs_frame, playlist_name)
        
        # 添加状态栏（在歌曲列表下方）
        status_bar = self._create_status_bar(column, playlist_name)
        status_bar.pack(fill="x", padx=5, pady=5)

    def _create_column_header(self, parent: ctk.CTkFrame, playlist_name: str) -> ctk.CTkFrame:
        """创建歌单标题栏"""
        header = ctk.CTkFrame(
            parent,
            fg_color=PlaylistConstants.DEFAULT_COLORS['header_bg'],
            height=PlaylistConstants.DIMENSIONS['header_height'],
            corner_radius=PlaylistConstants.DIMENSIONS['block_radius']
        )
        header.pack_propagate(False)
        
        # 标题容器（中）- 在左右按钮之间自适应
        title_frame = ctk.CTkFrame(
            header,
            fg_color="transparent"
        )
        title_frame.place(relx=0.5, rely=0.5, anchor="center", x=0)
        
        # 创建标题标签
        display_name = self._get_playlist_display_name(playlist_name)
        title_label = ctk.CTkLabel(
            title_frame,
            text=display_name,
            font=self.subtitle_font,
            text_color=PlaylistConstants.DEFAULT_COLORS['text_header'],
            cursor="hand2"
        )
        title_label.pack(padx=10)
        
        # 绑定点击事件
        title_label.bind("<Button-1>", lambda e: self._open_playlist_folder(playlist_name))
        
        # 按钮容器（左）
        left_buttons = ctk.CTkFrame(
            header,
            fg_color="transparent",
            width=PlaylistConstants.DIMENSIONS['button_size'] * 2
        )
        left_buttons.place(x=5, rely=0.5, anchor="w")
        left_buttons.lift()  # 提升层级
        
        # 按钮容器（右）
        right_buttons = ctk.CTkFrame(
            header,
            fg_color="transparent",
            width=PlaylistConstants.DIMENSIONS['button_size'] * 2
        )
        right_buttons.place(relx=1.0, rely=0.5, anchor="e", x=-5)
        right_buttons.lift()  # 提升层级
        
        # 添加音乐按钮
        self.music_add_icon = ctk.CTkImage(
            light_image=Image.open("assets/icons/actions/music-add.png"),
            dark_image=Image.open("assets/icons/actions/music-add.png"),
            size=PlaylistConstants.DIMENSIONS['icon_size']
        )
        
        add_button = ctk.CTkButton(
            left_buttons,
            text="",
            image=self.music_add_icon,
            width=PlaylistConstants.DIMENSIONS['button_size'],
            height=PlaylistConstants.DIMENSIONS['button_size'],
            corner_radius=PlaylistConstants.DIMENSIONS['button_corner'],
            fg_color=PlaylistConstants.DEFAULT_COLORS['button_bg'],
            hover_color=PlaylistConstants.DEFAULT_COLORS['button_hover'],
            command=lambda: self._add_music_files(playlist_name)
        )
        add_button.pack(side="left", padx=2)
        
        # 添加颜色选择按钮（如果不是特殊歌单）
        if playlist_name not in PlaylistConstants.SPECIAL_PLAYLISTS:
            color_button = ctk.CTkButton(
                right_buttons,
                text="",
                image=self.paintbucket_icon,
                width=PlaylistConstants.DIMENSIONS['button_size'],
                height=PlaylistConstants.DIMENSIONS['button_size'],
                corner_radius=PlaylistConstants.DIMENSIONS['button_corner'],
                fg_color=PlaylistConstants.DEFAULT_COLORS['button_bg'],
                hover_color=PlaylistConstants.DEFAULT_COLORS['button_hover'],
                command=lambda: self._show_color_picker(playlist_name)
            )
            color_button.pack(side="right", padx=2)
        
        return header

    def _create_songs_frame(self, parent: ctk.CTkFrame, playlist_name: str) -> ctk.CTkScrollableFrame:
        """创建歌曲列表框架"""
        return ctk.CTkScrollableFrame(
            parent,
            fg_color=self._get_column_color(playlist_name),
            corner_radius=PlaylistConstants.DIMENSIONS['block_radius']
        )

    def _load_songs(self, songs_frame: ctk.CTkScrollableFrame, playlist_name: str) -> None:
        """加载歌曲列表"""
        try:
            folder_path = os.path.join(PlaylistConstants.MUSIC_FOLDER, playlist_name)
            if not os.path.exists(folder_path):
                return

            songs = [f for f in os.listdir(folder_path) 
                    if os.path.isfile(os.path.join(folder_path, f)) and 
                    f.lower().endswith(('.mp3', '.wav', '.flac'))]
            
            for song in sorted(songs):
                self._create_song_block(songs_frame, song, playlist_name)
        except Exception as e:
            print(f"加载歌曲失败: {str(e)}")

    def _create_song_block(self, parent: ctk.CTkFrame, song_name: str, playlist_name: str, is_new: bool = False) -> None:
        """创建歌曲块"""
        # 确定块的颜色
        base_color = self._get_column_color(playlist_name, for_song_block=True)
        if is_new:
            block_color = "#8B4343"  # 深红色
            text_color = "#FFFFFF"   # 白色文字
        else:
            block_color = base_color
            text_color = PlaylistConstants.DEFAULT_COLORS['text']
        
        # 创建主框架
        block = ctk.CTkFrame(
            parent,
            fg_color=block_color,
            corner_radius=PlaylistConstants.DIMENSIONS['block_radius'],
            height=PlaylistConstants.DIMENSIONS['song_block_height'],
            cursor="hand2"
        )
        block.pack(fill="x", padx=8, pady=4)
        block.pack_propagate(False)
        
        # 调整拖动图标容器的宽度和内边距
        drag_container = ctk.CTkFrame(
            block,
            fg_color="transparent",
            width=28,  # 从30减小到28
            height=PlaylistConstants.DIMENSIONS['song_block_height']
        )
        drag_container.pack(side="left", padx=(2, 0))  # 左侧内边距从4减小到2
        drag_container.pack_propagate(False)
        
        # 创建拖动图标
        drag_label = ctk.CTkLabel(
            drag_container,
            image=self.drag_icon if not is_new else self.drag_icon_white,  # 新块使用白色图标
            text="",
            cursor="hand2"
        )
        drag_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # 创建标签
        label = ctk.CTkLabel(
            block,
            text=song_name,
            font=self.subtitle_font,
            text_color=text_color,
            anchor="w",
            wraplength=150,
            cursor="hand2"
        )
        label.pack(side="left", fill="both", expand=True, padx=(2, 4), pady=5)  # 左侧内边距从4减小到2，右侧从8减小到4
        
        # 播放次数显示部分
        play_count = self._get_song_play_count(song_name, playlist_name)
        if play_count is not None:
            count_container = ctk.CTkFrame(
                block,
                fg_color="transparent",
                width=16,
                height=PlaylistConstants.DIMENSIONS['song_block_height']
            )
            count_container.pack(side="right", padx=(0, 4))
            count_container.pack_propagate(False)
            
            count_label = ctk.CTkLabel(
                count_container,
                text=str(play_count),
                font=ctk.CTkFont(
                    family=PlaylistConstants.DEFAULT_FONT_FAMILY,
                    size=10
                ),
                text_color="#FFFFFF" if is_new else "#000000",  # 新块使用白色文字
                width=16,
                height=20
            )
            count_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # 存储相关信息
        block.song_name = song_name
        block.playlist_name = playlist_name
        block.original_color = block_color
        
        # 绑定拖动事件（仅在拖动图标上）
        drag_label.bind("<Button-1>", lambda e: self._start_drag(e, block))
        drag_label.bind("<B1-Motion>", lambda e: self._on_drag(e, block))
        drag_label.bind("<ButtonRelease-1>", lambda e: self._end_drag(e, block))
        
        # 绑定播放事件（在整个块和标签上，但不包括拖动图标）
        for widget in (block, label):
            widget.bind("<Button-1>", lambda e: self._play_music(song_name, playlist_name))
            widget.bind("<Enter>", lambda e: self._on_song_hover(block, playlist_name, block_color))
            widget.bind("<Leave>", lambda e: self._on_song_leave(block, block_color))

    def _on_song_hover(self, block: ctk.CTkFrame, playlist_name: str, original_color: str) -> None:
        """鼠标悬停效果"""
        if original_color == "#8B4343":  # 如果是新添加的红色块
            hover_color = "#A04949"  # 稍微变亮的红色
        else:
            # 使用原始颜色作为基础，轻微变亮
            hover_color = self._lighten_color(original_color, factor=0.1)
        block.configure(fg_color=hover_color)

    def _on_song_leave(self, block: ctk.CTkFrame, original_color: str) -> None:
        """鼠标离开效果"""
        block.configure(fg_color=original_color)

    def _play_music(self, song_name: str, playlist_name: str) -> None:
        """播放音乐"""
        try:
            music_path = os.path.join(PlaylistConstants.MUSIC_FOLDER, playlist_name, song_name)
            self.player.play_music(
                music_path, 
                song_name, 
                os.path.join(PlaylistConstants.MUSIC_FOLDER, playlist_name)
            )
        except Exception as e:
            messagebox.showerror("错误", f"播放音乐失败: {str(e)}")

    def _show_color_picker(self, playlist_name: str) -> None:
        """显示颜色选择器"""
        current_color = self._get_column_color(playlist_name)
        PlaylistColorPicker(
            self, 
            playlist_name, 
            current_color, 
            self._on_color_selected
        )

    def _on_color_selected(self, playlist_name: str, color: str) -> None:
        """颜色选择回调"""
        try:
            full_name = self._get_playlist_full_name(playlist_name)
            self.color_map[full_name] = color
            self._refresh_playlist_colors()
        except Exception as e:
            messagebox.showerror("错误", f"更新颜色失败: {str(e)}")

    def _refresh_playlist_colors(self) -> None:
        """刷新歌单颜色"""
        try:
            # 遍历所有歌单列
            for column in self.kanban_frame.winfo_children():
                if hasattr(column, 'playlist_name'):
                    playlist_name = column.playlist_name
                    
                    # 更新列的颜色
                    column_color = self._get_column_color(playlist_name)
                    column.configure(fg_color=column_color)
                    
                    # 更新歌曲块的颜色
                    block_color = self._get_column_color(playlist_name, for_song_block=True)
                    for child in column.winfo_children():
                        if isinstance(child, ctk.CTkScrollableFrame):
                            for song_block in child.winfo_children():
                                if isinstance(song_block, ctk.CTkFrame):
                                    song_block.configure(fg_color=block_color)
                            
        except Exception as e:
            print(f"刷新颜色失败: {str(e)}")

    def _get_column_color(self, playlist_name: str, for_song_block: bool = False) -> str:
        """获取列颜色"""
        if playlist_name in PlaylistConstants.SPECIAL_PLAYLISTS:
            return (PlaylistConstants.DEFAULT_COLORS['default_block'] 
                   if for_song_block else PlaylistConstants.DEFAULT_COLORS['default_column'])

        # 获取颜色并转换为hex格式
        full_name = self._get_playlist_full_name(playlist_name)
        rgba_color = self.color_map.get(full_name, PlaylistConstants.DEFAULT_COLORS['default_column'])
        hex_color = self._rgba_to_hex(rgba_color)
        
        return self._darken_color(hex_color) if for_song_block else hex_color

    def _rgba_to_hex(self, rgba_color: str) -> str:
        """将rgba颜色转换为hex格式"""
        try:
            if rgba_color.startswith('rgba'):
                # 从rgba格式解析
                values = rgba_color.strip('rgba()').split(',')
                r = int(values[0])
                g = int(values[1])
                b = int(values[2])
                return f'#{r:02x}{g:02x}{b:02x}'
            elif rgba_color.startswith('#'):
                # 已经是hex格式
                return rgba_color
            else:
                return PlaylistConstants.DEFAULT_COLORS['default_column']
        except Exception:
            return PlaylistConstants.DEFAULT_COLORS['default_column']

    def _darken_color(self, hex_color: str, factor: float = 0.2) -> str:
        """使颜色变暗"""
        try:
            # 确保输入是hex格式
            if not hex_color.startswith('#'):
                hex_color = f"#{hex_color}"
            
            # 解析RGB值
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)

            # 调整颜色
            r = int(r * (1 - factor))
            g = int(g * (1 - factor))
            b = int(b * (1 - factor))

            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return PlaylistConstants.DEFAULT_COLORS['default_block']

    def _get_playlist_full_name(self, playlist_name: str) -> str:
        """获取歌单完整名称"""
        for level in self.config.get('levels', []):
            if level['name'].startswith(playlist_name):
                return level['name']
        return playlist_name

    def _get_playlist_display_name(self, playlist_name: str) -> str:
        """获取歌单显示名称"""
        full_name = self._get_playlist_full_name(playlist_name)
        return full_name.split('-')[-1] if '-' in full_name else full_name

    def _refresh_ui(self) -> None:
        """刷新UI"""
        for widget in self.kanban_frame.winfo_children():
            widget.destroy()
        self._create_kanban()

    def _find_scrollable_frame(self, parent: ctk.CTkFrame) -> Optional[ctk.CTkFrame]:
        """递归查找滚动框架"""
        print(f"检查父组件: {type(parent)}")
        
        # 检查是否是歌曲列表区域
        for child in parent.winfo_children():
            print(f"检查子组件: {type(child)}")
            # 如果找到Canvas和Scrollbar，说明这个frame就是我们要找的
            has_canvas = any(isinstance(c, tkinter.Canvas) for c in parent.winfo_children())
            has_scrollbar = any(isinstance(c, ctk.CTkScrollbar) for c in parent.winfo_children())
            
            if has_canvas and has_scrollbar:
                print("找到包含Canvas和Scrollbar的框架")
                return parent
            
            # 如果是Frame，递归查找
            if isinstance(child, ctk.CTkFrame):
                result = self._find_scrollable_frame(child)
                if result:
                    return result
        return None

    def _add_music_files(self, playlist_name: str) -> None:
        """添加音乐文件"""
        file_handler = PlaylistFileHandler(PlaylistConstants.MUSIC_FOLDER)
        new_files = file_handler.add_music_files(playlist_name)
        
        print(f"新添加的文件: {new_files}")
        
        if new_files:
            print(f"开始查找歌单框架: {playlist_name}")
            # 查找对应的歌单列
            for column in self.kanban_frame.winfo_children():
                if hasattr(column, 'playlist_name') and column.playlist_name == playlist_name:
                    print(f"找到匹配的歌单列: {playlist_name}")
                    
                    # 使用递归方法查找滚动框架
                    songs_frame = self._find_scrollable_frame(column)
                    
                    if songs_frame:
                        print("开始更新UI")
                        # 获取Canvas（实际内容容器）
                        canvas = next(c for c in songs_frame.winfo_children() if isinstance(c, tkinter.Canvas))
                        inner_frame = canvas.winfo_children()[0] if canvas.winfo_children() else None
                        
                        if inner_frame:
                            # 清空现有内容
                            for widget in inner_frame.winfo_children():
                                widget.destroy()
                            
                            # 获取文件夹中所有音乐文件
                            folder_path = os.path.join(PlaylistConstants.MUSIC_FOLDER, playlist_name)
                            all_songs = [f for f in os.listdir(folder_path) 
                                       if os.path.isfile(os.path.join(folder_path, f)) and 
                                       f.lower().endswith(('.mp3', '.wav', '.flac'))]
                            
                            print(f"所有歌曲: {all_songs}")
                            
                            # 先添加新文件（在顶部，带高亮）
                            for song_name in sorted(new_files):
                                print(f"添加新歌曲: {song_name}")
                                self._create_song_block(inner_frame, song_name, playlist_name, is_new=True)
                            
                            # 添加其他文件（正常显示）
                            other_songs = sorted([s for s in all_songs if s not in new_files])
                            for song_name in other_songs:
                                self._create_song_block(inner_frame, song_name, playlist_name, is_new=False)
                            
                            # 更新状态栏
                            self._update_status_bar_content(column, playlist_name)
                            
                            # 强制更新UI
                            inner_frame.update()
                            canvas.update()
                            songs_frame.update()
                            self.update()
                            print("UI更新完成")
                        else:
                            print("未找到内部框架")
                    else:
                        print("未找到歌曲列表框架")
                    break

    def _lighten_color(self, hex_color: str, factor: float = 0.1) -> str:
        """使颜色变亮"""
        try:
            # 将十六进制颜色转换为RGB
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            # 调整颜色（变亮）
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return PlaylistConstants.DEFAULT_COLORS['default_block']

    def _start_drag(self, event, block) -> None:
        """开始拖动"""
        try:
            # 保存拖动相关数据，记录鼠标在块内的相对位置
            self._drag_data = {
                "x_offset": event.x + 90,  # 向左微调偏移量
                "y_offset": event.y + 85,  # 向上微调偏移量
                "block": block,
                "original_playlist": block.playlist_name,
                "song_name": block.song_name
            }
            
            # 创建拖动时的视觉反馈
            self._drag_image = self._create_drag_image(block)
            
            # 初始放置位置（使克隆块的相对点与原始点击位置对齐）
            self._drag_image.place(
                x=event.x_root - self.winfo_rootx() - self._drag_data["x_offset"],
                y=event.y_root - self.winfo_rooty() - self._drag_data["y_offset"]
            )
            
            # 高亮可放置区域
            self._highlight_drop_targets(block.playlist_name)
            
            # 改变鼠标样式
            block.configure(cursor="fleur")
            
            # 重置垃圾箱状态
            self._drag_over_trash = False
            self.trash_button.configure(image=self.trash_red_icon)
          
        except Exception as e:
            print(f"开始拖动时出错: {str(e)}")

    def _on_drag(self, event, block):
        """处理拖动过程"""
        try:
            if hasattr(self, '_drag_data') and hasattr(self, '_drag_image'):
                # 更新拖动图像位置，保持与鼠标的相对位置不变
                x = event.x_root - self.winfo_rootx() - self._drag_data["x_offset"]
                y = event.y_root - self.winfo_rooty() - self._drag_data["y_offset"]
                
                # 更新拖动图像位置
                self._drag_image.place(x=x, y=y)
                
                # 更新高亮效果
                self._update_drop_target_highlight(event)
                
                # 检查是否在垃圾箱上方
                trash_x = self.trash_button.winfo_x()
                trash_y = self.trash_button.winfo_y()
                trash_width = self.trash_button.winfo_width()
                trash_height = self.trash_button.winfo_height()
                
                mouse_over_trash = (
                    trash_x <= event.x_root - self.winfo_rootx() <= trash_x + trash_width and
                    trash_y <= event.y_root - self.winfo_rooty() <= trash_y + trash_height
                )
                
                if mouse_over_trash and not self._drag_over_trash:
                    self._drag_over_trash = True
                    # 计算新的中心点位置
                    new_x = self._original_trash_pos[0] - 12
                    new_y = self._original_trash_pos[1] - 12
                    
                    # 保存新位置用于动画
                    self._current_trash_pos = (new_x, new_y)
                    
                    # 更新按钮配置和位置
                    self.trash_button.configure(
                        image=self.trash_red_icon_large,
                        width=56,
                        height=56
                    )
                    self.trash_button.place(x=new_x, y=new_y)
                    # 开始摇晃动画
                    self._shake_trash_icon()
                elif not mouse_over_trash and self._drag_over_trash:
                    self._drag_over_trash = False
                    # 恢复原始大小但保持红色图标
                    self.trash_button.configure(
                        image=self.trash_red_icon,  # 保持红色图标
                        width=32,
                        height=32
                    )
                    # 停止摇晃动画
                    if self._shake_animation_id:
                        self.after_cancel(self._shake_animation_id)
                        self._shake_animation_id = None
                    # 恢复原始位置
                    self.trash_button.place(x=self._original_trash_pos[0], y=self._original_trash_pos[1])
                
                # 处理自动滚动
                self._handle_auto_scroll(event)
                
        except Exception as e:
            print(f"拖动过程出错: {str(e)}")

    def _create_drag_image(self, block: ctk.CTkFrame) -> ctk.CTkFrame:
        """创建拖动时的视觉反馈"""
        # 创建半透明的克隆块
        clone = ctk.CTkFrame(
            self,  # 使用 self 作为父组件而不是顶层窗口
            fg_color=block.original_color,
            corner_radius=PlaylistConstants.DIMENSIONS['block_radius'],
            height=block.winfo_height(),
            width=block.winfo_width(),
            border_width=2,
            border_color="#FFFFFF"
        )
        
        # 创建拖动图标
        drag_container = ctk.CTkFrame(
            clone,
            fg_color="transparent",
            width=30,
            height=block.winfo_height()
        )
        drag_container.pack(side="left", padx=(4, 0))
        drag_container.pack_propagate(False)
        
        # 添加拖动图标
        ctk.CTkLabel(
            drag_container,
            image=self.drag_icon_white,  # 使用白色图标
            text=""
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        # 创建标签
        ctk.CTkLabel(
            clone,
            text=block.song_name,
            font=self.subtitle_font,
            text_color="#FFFFFF",  # 使用白色文字以提高可见度
            anchor="w",
            wraplength=150
        ).pack(side="left", fill="both", expand=True, padx=(4, 12), pady=5)
        
        # 设置半透明效果
        clone.configure(fg_color=self._adjust_color_alpha(block.original_color, 0.8))
        
        return clone

    def _handle_auto_scroll(self, event):
        """处理自动滚动"""
        try:
            canvas = self.kanban_scroll._parent_canvas
            visible_width = canvas.winfo_width()
            
            edge_size = 200
            scroll_speed = 15  # 增加滚动速度
            
            relative_x = event.x_root - canvas.winfo_rootx()
            
            if relative_x < edge_size:
                # 向左滚动
                canvas.xview_scroll(-scroll_speed, "units")
            elif relative_x > visible_width - edge_size:
                # 向右滚动
                canvas.xview_scroll(scroll_speed, "units")
                
            # 更新拖动图像位置（使用正确的偏移量）
            if hasattr(self, '_drag_data') and hasattr(self, '_drag_image'):
                x = event.x_root - self.winfo_rootx() - self._drag_data["x_offset"]
                y = event.y_root - self.winfo_rooty() - self._drag_data["y_offset"]
                self._drag_image.place(x=x, y=y)
                
        except Exception as e:
            print(f"自动滚动处理出错: {str(e)}")
            # 添加更详细的错误信息
            import traceback
            traceback.print_exc()

    def _adjust_color_alpha(self, hex_color: str, alpha: float) -> str:
        """调整颜色的亮度和透明度"""
        try:
            # 将颜色变亮而不是变暗
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            # 与白色混合而不是背景色
            final_r = int(r * alpha + 255 * (1 - alpha))
            final_g = int(g * alpha + 255 * (1 - alpha))
            final_b = int(b * alpha + 255 * (1 - alpha))
            
            return f"#{final_r:02x}{final_g:02x}{final_b:02x}"
        except Exception as e:
            print(f"调整颜色透明度时出错: {str(e)}")
            return hex_color

    def _update_drag_image_position(self, event):
        """更新拖动图像位置"""
        if hasattr(self, '_drag_image'):
            dx = event.x_root - self._drag_data["x"]
            dy = event.y_root - self._drag_data["y"]
            self._drag_image.place(
                x=self._drag_data["block"].winfo_rootx() - self.winfo_rootx() + dx,
                y=self._drag_data["block"].winfo_rooty() - self.winfo_rooty() + dy
            )

    def _highlight_drop_targets(self, current_playlist: str):
        """高亮可放置区域"""
        try:
            print(f"\n开始创建高亮效果 - 当前歌单: {current_playlist}")
            self._cleanup_highlights()
            
            for column in self.kanban_frame.winfo_children():
                if hasattr(column, 'playlist_name') and column.playlist_name != current_playlist:
                    playlist_name = column.playlist_name
                    print(f"处理歌单列: {playlist_name}")
                    
                    # 查找滚动框架
                    songs_frame = self._find_scrollable_frame(column)
                    if songs_frame:
                        # 创建半透明遮罩
                        highlight = ctk.CTkFrame(
                            songs_frame,  # 改为使用songs_frame作为父组件
                            fg_color=self._adjust_color_alpha(
                                self._get_column_color(playlist_name), 
                                0.3  # 增加透明度使效果更明显
                            ),
                            corner_radius=PlaylistConstants.DIMENSIONS['corner_radius']
                        )
                        highlight.place(relx=0, rely=0, relwidth=1, relheight=1)
                        highlight.lift()  # 确保在最上层
                        column.highlight = highlight
                        print(f"  已创建高亮遮罩")
                        
        except Exception as e:
            print(f"创建高亮效果时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def _cleanup_highlights(self):
        """清理所有高亮效果"""
        print("\n开始清理高亮效果")
        count = 0
        for column in self.kanban_frame.winfo_children():
            if hasattr(column, 'highlight'):
                column.highlight.destroy()
                del column.highlight
                count += 1
        print(f"已清理 {count} 个高亮效果")

    def _update_drop_target_highlight(self, event):
        """更新放置目标的高亮效果"""
        try:
            # 添加节流，减少更新频率
            if hasattr(self, '_last_highlight_update'):
                if event.time - self._last_highlight_update < 50:  # 50ms节流
                    return
            self._last_highlight_update = event.time
            
            target_playlist = self._find_target_playlist(event)
            if target_playlist:
                for column in self.kanban_frame.winfo_children():
                    if hasattr(column, 'highlight') and hasattr(column, 'playlist_name'):
                        base_color = self._get_column_color(column.playlist_name)
                        
                        if column.playlist_name == target_playlist:
                            # 当前悬停的列表更亮
                            alpha = 0.4
                        else:
                            # 其他放置区域保持淡高
                            alpha = 0.3
                        
                        highlight_color = self._adjust_color_alpha(base_color, alpha)
                        column.highlight.configure(fg_color=highlight_color)
                        column.highlight.lift()  # 确保高亮始终在最上层
                    
        except Exception as e:
            print(f"更新高亮效果时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def _end_drag(self, event, block):
        """结束拖动"""
        try:
            if hasattr(self, '_drag_data'):
                if self._drag_over_trash:
                    # 显示确认对话框
                    if messagebox.askyesno("确认删除", f"确定要删除歌曲 {block.song_name} 吗？"):
                        # 删除歌曲
                        file_handler = PlaylistFileHandler(PlaylistConstants.MUSIC_FOLDER)
                        file_handler.move_song_to_trash(block.song_name, block.playlist_name)
                        
                        # 删除音乐块
                        block.destroy()
                        
                        # 更新状态栏
                        for column in self.kanban_frame.winfo_children():
                            if hasattr(column, 'playlist_name') and column.playlist_name == block.playlist_name:
                                self._update_status_bar_content(column, block.playlist_name)
                                break
                else:
                    # 检查是否拖放到其他歌���
                    target_playlist = self._find_target_playlist(event)
                    if target_playlist and target_playlist != self._drag_data["original_playlist"]:
                        self._move_song_to_playlist(
                            block.song_name,
                            self._drag_data["original_playlist"],
                            target_playlist
                        )
                
                # 清理拖动相关的视觉元素
                self._cleanup_drag()
                
                # 恢复光标
                event.widget.configure(cursor="hand2")
                
                # 完全恢复垃圾箱按钮的状态
                self.trash_button.configure(
                    image=self.trash_icon,
                    width=32,
                    height=32,
                    fg_color="#000000",
                    hover_color="#363636"
                )
                self.trash_button.place(x=self._original_trash_pos[0], y=self._original_trash_pos[1])
                self._drag_over_trash = False
                
                # 强制更新UI
                self.update_idletasks()
            
        except Exception as e:
            print(f"结束拖动时出错: {str(e)}")

    def _cleanup_drag(self):
        """清理拖动相关的元素"""
        try:
            # 移除拖动图像
            if hasattr(self, '_drag_image'):
                self._drag_image.place_forget()  # 使用 place_forget 代替 destroy
                self._drag_image.destroy()
                del self._drag_image
            
            # 移除高亮效果
            for column in self.kanban_frame.winfo_children():
                if hasattr(column, 'highlight'):
                    column.highlight.destroy()
                    del column.highlight
            
            # 清理拖动数据
            if hasattr(self, '_drag_data'):
                del self._drag_data
            
            # 确保停止垃圾箱动画
            if self._shake_animation_id:
                self.after_cancel(self._shake_animation_id)
                self._shake_animation_id = None
            
            # 恢复垃圾箱按钮的原始状态（大小和位置）
            self.trash_button.configure(
                image=self.trash_icon,
                width=32,
                height=32,
                fg_color="#000000",
                hover_color="#363636"
            )
            self.trash_button.place(x=self._original_trash_pos[0], y=self._original_trash_pos[1])
            
            # 强制更新UI
            self.update_idletasks()
        except Exception as e:
            print(f"清理拖动元素时出错: {str(e)}")

    def _move_song_to_playlist(self, song_name: str, from_playlist: str, to_playlist: str) -> None:
        """移动歌曲到新歌单"""
        try:
            # 1. 移动文件
            src_path = os.path.join(PlaylistConstants.MUSIC_FOLDER, from_playlist, song_name)
            dst_path = os.path.join(PlaylistConstants.MUSIC_FOLDER, to_playlist, song_name)
            os.rename(src_path, dst_path)
            
            # 2. 更新CSV文件
            file_handler = PlaylistFileHandler(PlaylistConstants.MUSIC_FOLDER)
            file_handler.move_song_between_playlists(song_name, from_playlist, to_playlist)
            
            # 3. 删除原歌单中的音乐块
            for column in self.kanban_frame.winfo_children():
                if hasattr(column, 'playlist_name') and column.playlist_name == from_playlist:
                    songs_frame = self._find_scrollable_frame(column)
                    if songs_frame:
                        canvas = next(c for c in songs_frame.winfo_children() 
                                    if isinstance(c, tkinter.Canvas))
                        inner_frame = canvas.winfo_children()[0] if canvas.winfo_children() else None
                        
                        if inner_frame:
                            # 查找并删除对应的音乐块
                            for block in inner_frame.winfo_children():
                                if (hasattr(block, 'song_name') and 
                                    hasattr(block, 'playlist_name') and
                                    block.song_name == song_name and 
                                    block.playlist_name == from_playlist):
                                    block.destroy()
                                    break
                
                            # 更新原歌单的状态栏内容
                            self._update_status_bar_content(column, from_playlist)
            
            # 4. 在目标歌单顶部创建新的音乐块
            for column in self.kanban_frame.winfo_children():
                if hasattr(column, 'playlist_name') and column.playlist_name == to_playlist:
                    songs_frame = self._find_scrollable_frame(column)
                    if songs_frame:
                        canvas = next(c for c in songs_frame.winfo_children() 
                                    if isinstance(c, tkinter.Canvas))
                        inner_frame = canvas.winfo_children()[0] if canvas.winfo_children() else None
                        
                        if inner_frame:
                            # 创建主框架（使用深蓝色）
                            block = ctk.CTkFrame(
                                inner_frame,
                                fg_color="#435B8B",  # 深蓝色
                                corner_radius=PlaylistConstants.DIMENSIONS['block_radius'],
                                height=PlaylistConstants.DIMENSIONS['song_block_height'],
                                cursor="hand2"
                            )
                            block.pack(fill="x", padx=8, pady=4, side="top", before=inner_frame.winfo_children()[0] if inner_frame.winfo_children() else None)
                            block.pack_propagate(False)
                            
                            # 创建拖动图标容器（使用新的紧凑布局）
                            drag_container = ctk.CTkFrame(
                                block,
                                fg_color="transparent",
                                width=24,  # 减小到24
                                height=PlaylistConstants.DIMENSIONS['song_block_height']
                            )
                            drag_container.pack(side="left", padx=(2, 0))  # 左侧内边距减小到2
                            drag_container.pack_propagate(False)
                            
                            # 创建拖动图标
                            drag_label = ctk.CTkLabel(
                                drag_container,
                                image=self.drag_icon_white,  # 使用白色图标
                                text="",
                                cursor="hand2"
                            )
                            drag_label.place(relx=0.5, rely=0.5, anchor="center")
                            
                            # 创建标签
                            label = ctk.CTkLabel(
                                block,
                                text=song_name,
                                font=self.subtitle_font,
                                text_color="#FFFFFF",
                                anchor="w",
                                wraplength=150,
                                cursor="hand2"
                            )
                            label.pack(side="left", fill="both", expand=True, padx=(2, 4), pady=5)  # 调整内边距
                            
                            # 添加播放次数显示
                            play_count = self._get_song_play_count(song_name, to_playlist)
                            if play_count is not None:
                                count_container = ctk.CTkFrame(
                                    block,
                                    fg_color="transparent",
                                    width=16,  # 减小到16
                                    height=PlaylistConstants.DIMENSIONS['song_block_height']
                                )
                                count_container.pack(side="right", padx=(0, 4))  # 右侧内边距减小到4
                                count_container.pack_propagate(False)
                                
                                count_label = ctk.CTkLabel(
                                    count_container,
                                    text=str(play_count),
                                    font=ctk.CTkFont(
                                        family=PlaylistConstants.DEFAULT_FONT_FAMILY,
                                        size=10
                                    ),
                                    text_color="#FFFFFF",
                                    width=16,
                                    height=20
                                )
                                count_label.place(relx=0.5, rely=0.5, anchor="center")
                            
                            # 存储相关信息
                            block.song_name = song_name
                            block.playlist_name = to_playlist
                            block.original_color = "#435B8B"  # 深蓝色
                            
                            # 绑定拖动事件
                            drag_label.bind("<Button-1>", lambda e: self._start_drag(e, block))
                            drag_label.bind("<B1-Motion>", lambda e: self._on_drag(e, block))
                            drag_label.bind("<ButtonRelease-1>", lambda e: self._end_drag(e, block))
                            
                            # 绑定播放事件
                            for widget in (block, label):
                                widget.bind("<Button-1>", lambda e: self._play_music(song_name, to_playlist))
                                widget.bind("<Enter>", lambda e: self._on_song_hover(block, to_playlist, "#435B8B"))
                                widget.bind("<Leave>", lambda e: self._on_song_leave(block, "#435B8B"))
                            
                            # 更新UI
                            inner_frame.update()
                            canvas.update()
                            songs_frame.update()
                            
                            # 更新目标歌单的状态栏内容
                            self._update_status_bar_content(column, to_playlist)
                            break
            
        except Exception as e:
            messagebox.showerror("错误", f"移动歌曲失败: {str(e)}")

    def _find_target_playlist(self, event) -> Optional[str]:
        """查找鼠标位置下的目标歌单"""
        for column in self.kanban_frame.winfo_children():
            if hasattr(column, 'playlist_name'):
                # 获取列的屏幕坐标
                x = column.winfo_rootx()
                y = column.winfo_rooty()
                width = column.winfo_width()
                height = column.winfo_height()
                
                # 检查鼠标是否在这个列的范围内
                if (x <= event.x_root <= x + width and
                    y <= event.y_root <= y + height):
                    return column.playlist_name
        return None

    def _create_status_bar(self, parent: ctk.CTkFrame, playlist_name: str) -> ctk.CTkFrame:
        """创建底部状态栏"""
        status_bar = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            height=25
        )
        
        # 定义状态栏文字颜色
        status_text_color = "#5c5380"  # 浅紫色
        
        # 获取歌单统计信息
        stats = self._get_playlist_stats(playlist_name)
        
        # 左侧显示：总歌曲数/推荐歌曲数
        if stats['total'] is not None and stats['recommended'] is not None:
            # 创建一个框架来容纳两种不同大小的文本
            left_frame = ctk.CTkFrame(status_bar, fg_color="transparent")
            left_frame.pack(side="left", padx=5)
            
            # 总歌曲数（大字体）
            total_label = ctk.CTkLabel(
                left_frame,
                text=str(stats['total']),
                font=ctk.CTkFont(family=PlaylistConstants.DEFAULT_FONT_FAMILY, size=14),
                text_color=PlaylistConstants.DEFAULT_COLORS['text']  # 使用与音乐块相同的文字颜色
            )
            total_label.pack(side="left")
            
            # 存储标签引用
            if not hasattr(parent, 'status_labels'):
                parent.status_labels = {}
            parent.status_labels['total'] = total_label
            
            # 分隔符（大字体）
            separator = ctk.CTkLabel(
                left_frame,
                text="/",
                font=ctk.CTkFont(family=PlaylistConstants.DEFAULT_FONT_FAMILY, size=14),
                text_color=status_text_color
            )
            separator.pack(side="left")
            
            # 推荐歌曲数（小字体）
            recommended_label = ctk.CTkLabel(
                left_frame,
                text=str(stats['recommended']),
                font=ctk.CTkFont(family=PlaylistConstants.DEFAULT_FONT_FAMILY, size=10),
                text_color=status_text_color
            )
            recommended_label.pack(side="left")
            parent.status_labels['recommended'] = recommended_label
        
        # 右侧显示：随机首数
        if stats['random'] is not None:
            right_label = ctk.CTkLabel(
                status_bar,
                text=str(stats['random']),
                font=ctk.CTkFont(family=PlaylistConstants.DEFAULT_FONT_FAMILY, size=14),
                text_color=status_text_color
            )
            right_label.pack(side="right", padx=5)
            parent.status_labels['random'] = right_label
        
        return status_bar

    def _get_playlist_stats(self, playlist_name: str) -> dict:
        """获取歌单统计信息（使用缓存优化）"""
        try:
            csv_path = os.path.join('statistics', 'play_count_logs', "等级歌单播放次数共计.csv")
            
            # 获取实际的歌曲总数（通过计算文件夹中的音乐文件数量）
            folder_path = os.path.join(PlaylistConstants.MUSIC_FOLDER, playlist_name)
            total = len([f for f in os.listdir(folder_path) 
                        if os.path.isfile(os.path.join(folder_path, f)) and 
                        f.lower().endswith(('.mp3', '.wav', '.flac'))])
            
            if not os.path.exists(csv_path):
                stats = {'total': total, 'recommended': None, 'random': None}
            else:
                # 使用pandas高效读取CSV
                import pandas as pd
                df = pd.read_csv(csv_path, encoding='utf-8')
                
                # 处理歌单名称（去除『』符号）
                clean_name = playlist_name.strip('『』').strip('』')
                
                # 查找对应行
                row = df[df['渐进学习时长激励歌单'].str.strip('『』').str.strip('』') == clean_name]
                
                if not row.empty:
                    stats = {
                        'total': total,  # 使用实际计算的总数
                        'recommended': int(row['推荐歌曲数量'].iloc[0]) if pd.notna(row['推荐歌曲数量'].iloc[0]) else None,
                        'random': int(row['随机首数'].iloc[0]) if pd.notna(row['随机首数'].iloc[0]) else None
                    }
                else:
                    stats = {'total': total, 'recommended': None, 'random': None}
            
            return stats
            
        except Exception as e:
            print(f"读取歌单统计信息失败: {str(e)}")
            return {'total': 0, 'recommended': None, 'random': None}

    def _update_status_bar_content(self, column: ctk.CTkFrame, playlist_name: str) -> None:
        """更新状态栏内容"""
        try:
            # 获取新的统计信息
            stats = self._get_playlist_stats(playlist_name)
            
            # 直接通过存储的引用更新标签
            if hasattr(column, 'status_labels'):
                if 'total' in column.status_labels:
                    column.status_labels['total'].configure(text=str(stats['total']))
                if 'recommended' in column.status_labels and stats['recommended'] is not None:
                    column.status_labels['recommended'].configure(text=str(stats['recommended']))
                if 'random' in column.status_labels and stats['random'] is not None:
                    column.status_labels['random'].configure(text=str(stats['random']))
            
        except Exception as e:
            print(f"更新状态栏内容失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def _shake_trash_icon(self, iteration=0, direction=1):
        """创建垃圾箱摇晃动画"""
        if not self._drag_over_trash:
            return
        
        if iteration >= 8:  # 控制摇晃次数
            iteration = 0
        
        # 摇晃幅度（像素）
        amplitude = 3
        
        # 使用当前位置而不是原始位置
        x = self._current_trash_pos[0] + (amplitude * direction if iteration % 2 == 0 else 0)
        y = self._current_trash_pos[1]
        
        # 更新位置
        self.trash_button.place(x=x, y=y)
        
        # 继续动画
        self._shake_animation_id = self.after(50, 
            lambda: self._shake_trash_icon(iteration + 1, direction * -1 if iteration % 2 == 0 else direction))

    def _show_trash_history(self):
        """显示删除历史记录窗口"""
        from playlist_manager_trash import TrashHistoryWindow
        trash_window = TrashHistoryWindow(self)
        trash_window.focus()  # 聚焦到新窗口

    def _get_song_play_count(self, song_name: str, playlist_name: str) -> Optional[int]:
        """获取歌曲播放次数"""
        try:
            # 构建CSV文件路径
            clean_playlist_name = playlist_name.strip('『』')
            csv_path = os.path.join('statistics', 'play_count_logs', f"{clean_playlist_name}_play_count.csv")
            
            if not os.path.exists(csv_path):
                return None
            
            # 使用pandas读取CSV
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            # 查找对应歌曲的播放次数
            row = df[df['歌曲'] == song_name]
            if not row.empty:
                return int(row['学习成就播放次数'].iloc[0])
            
            return 0
        except Exception as e:
            print(f"读取歌曲播放次数失败: {str(e)}")
            return None

    def _open_playlist_folder(self, playlist_name: str) -> None:
        """打开歌单文件夹"""
        try:
            folder_path = os.path.join(PlaylistConstants.MUSIC_FOLDER, playlist_name)
            if os.path.exists(folder_path):
                # Windows
                if os.name == 'nt':
                    os.startfile(folder_path)
                # macOS
                elif os.name == 'posix':
                    import subprocess
                    subprocess.run(['open', folder_path])
                # Linux
                else:
                    import subprocess
                    subprocess.run(['xdg-open', folder_path])
        except Exception as e:
            print(f"打开文件夹失败: {str(e)}")