import customtkinter as ctk
import pygame
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
import os
import time
from PIL import Image

class PlaylistPlayer(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # 初始化 pygame mixer
        pygame.mixer.init(frequency=48000)
        
        # 设置默认音量为4%
        pygame.mixer.music.set_volume(0.04)
        
        # 初始化播放器状态
        self.current_playing = None
        self.current_playlist = None
        self.is_playing = False
        self.start_time = None
        self.pause_time = 0
        self.pause_start = None
        self.total_length = 0  # 添加总时长属性
        self.playlist_songs = []  # 添加当前播放列表的所有歌曲
        self.current_index = -1  # 添加当前播放索引
        
        # 加载播放器图标
        self.load_player_icons()
        
        # 从config加载字体
        self.load_config_font()
        
        # 创建播放器UI
        self.create_player_ui()
        
        # 启动进度更新定时器
        self.update_progress()
        
    def load_player_icons(self):
        """加载播放器图标"""
        self.play_icon = ctk.CTkImage(
            light_image=Image.open("assets/icons/player/play.png"),
            dark_image=Image.open("assets/icons/player/play.png"),
            size=(20, 20)
        )
        self.pause_icon = ctk.CTkImage(
            light_image=Image.open("assets/icons/player/pause.png"),
            dark_image=Image.open("assets/icons/player/pause.png"),
            size=(20, 20)
        )
        self.prev_icon = ctk.CTkImage(
            light_image=Image.open("assets/icons/player/prev.png"),
            dark_image=Image.open("assets/icons/player/prev.png"),
            size=(15, 15)
        )
        self.next_icon = ctk.CTkImage(
            light_image=Image.open("assets/icons/player/next.png"),
            dark_image=Image.open("assets/icons/player/next.png"),
            size=(15, 15)
        )
        
    def load_config_font(self):
        """从config.json加载字体设置"""
        try:
            import json
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.font_family = config.get('font', '微软雅黑')  # 默认使用微软雅黑
        except Exception as e:
            print(f"加载字体配置失败: {str(e)}")
            self.font_family = '微软雅黑'
        
    def create_player_ui(self):
        """创建播放器UI"""
        # 创建播放器主框架
        self.player_frame = ctk.CTkFrame(
            self,
            fg_color="#1A1A1A",
            corner_radius=15,
            width=400,
            height=90
        )
        self.player_frame.pack(fill="x", padx=10)
        self.player_frame.pack_propagate(False)
        
        # 创建播放器控件
        self.create_info_frame()
        self.create_progress_frame()
        self.create_controls_frame()

    def create_info_frame(self):
        """创建信息显示区域"""
        info_frame = ctk.CTkFrame(
            self.player_frame,
            fg_color="transparent"
        )
        info_frame.pack(fill="x", padx=10, pady=(5, 0))
        
        # 创建滚动文本容器
        self.scroll_container = ctk.CTkFrame(
            info_frame,
            fg_color="transparent",
            width=380,
            height=35
        )
        self.scroll_container.pack(side="left")
        self.scroll_container.pack_propagate(False)
        
        # 创建内部滚动框架
        self.scroll_frame = ctk.CTkFrame(
            self.scroll_container,
            fg_color="transparent"
        )
        self.scroll_frame.place(x=0, y=0)
        
        # 歌曲名标签
        self.song_title_label = ctk.CTkLabel(
            self.scroll_frame,
            text="暂无音乐",
            font=(self.font_family, 14, "bold"),
            text_color="#FFFFFF"
        )
        self.song_title_label.pack(side="left")
        
        # 艺术家标签
        self.artist_label = ctk.CTkLabel(
            self.scroll_frame,
            text="请点击下面音乐块播放音乐",
            font=(self.font_family, 11),
            text_color="#888888"
        )
        self.artist_label.pack(side="left", padx=(8, 0))
        
        # 初始化滚动相关变量
        self.scroll_position = 5  # 起始位置右移5像素
        self.is_scrolling = False
        self.scroll_start_delay = True  # 添加开始延时标记
        self.scroll_end_delay = False   # 添加结束延时标记
        self.last_reset_time = 0        # 记录上次重置时间

    def scroll_text(self):
        """执行文本滚动"""
        if not self.is_scrolling:
            return
        
        current_time = time.time()
        frame_width = self.scroll_frame.winfo_width()
        container_width = self.scroll_container.winfo_width()
        
        # 开始滚动前等待3秒
        if self.scroll_start_delay:
            if current_time - self.last_reset_time >= 3:
                self.scroll_start_delay = False
            else:
                self.after(100, self.scroll_text)
                return
        
        if frame_width > container_width:
            # 检查是否需要暂停
            if abs(self.scroll_position) >= frame_width - container_width:
                if not self.scroll_end_delay:
                    self.scroll_end_delay = True
                    self.after(1500, self.reset_position)  # 1.5秒后重置
                    return
            else:
                self.scroll_position -= 1
                self.scroll_frame.place(x=self.scroll_position, y=0)
        
        self.after(30, self.scroll_text)

    def reset_position(self):
        """重置滚动位置"""
        self.scroll_position = 5  # 起始位置右移5像素
        self.scroll_frame.place(x=self.scroll_position, y=0)
        self.scroll_end_delay = False
        self.scroll_start_delay = True
        self.last_reset_time = time.time()
        self.after(100, self.scroll_text)

    def reset_scroll(self):
        """重置滚动状态"""
        self.scroll_position = 5  # 起始位置右移5像素
        self.scroll_frame.place(x=self.scroll_position, y=0)
        self.is_scrolling = False
        self.scroll_start_delay = True
        self.scroll_end_delay = False
        self.last_reset_time = time.time()
        self.after(100, self.check_scroll_needed)

    def create_progress_frame(self):
        """创建进度条区域"""
        progress_frame = ctk.CTkFrame(
            self.player_frame,
            fg_color="transparent"
        )
        progress_frame.pack(fill="x", padx=10, pady=2)
        
        # 美化进度条 - 加粗版本
        self.progress_bar = ctk.CTkSlider(
            progress_frame,
            from_=0,
            to=100,
            width=380,
            height=16,  # 增加高度
            button_color="#E74C3C",  # 红色滑块
            button_hover_color="#C0392B",  # 深红色悬停效果
            progress_color="#E74C3C",  # 红色进度条
            border_color="#2C3E50",  # 黑色描边
            fg_color="#2B2B2B",  # 背景色
            button_corner_radius=6,  # 滑块圆角
            border_width=2,  # 增加边框宽度
            command=self.seek_position
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        
    def create_controls_frame(self):
        """创建控制按钮区域"""
        controls_frame = ctk.CTkFrame(
            self.player_frame,
            fg_color="transparent"
        )
        controls_frame.pack(fill="x", padx=10, pady=(2, 5))
        
        # 播放控制按钮
        buttons_frame = ctk.CTkFrame(
            controls_frame,
            fg_color="transparent"
        )
        buttons_frame.pack(side="left")
        
        # 上一首按钮
        self.prev_button = ctk.CTkButton(
            buttons_frame,
            text="",
            image=self.prev_icon,
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#2B2B2B",
            command=self.prev_song
        )
        self.prev_button.pack(side="left", padx=5)
        
        # 播放/暂停按钮
        self.play_button = ctk.CTkButton(
            buttons_frame,
            text="",
            image=self.play_icon,
            width=40,
            height=40,
            fg_color="#2B2B2B",
            hover_color="#363636",
            command=self.toggle_play
        )
        self.play_button.pack(side="left", padx=5)
        
        # 下一首按钮
        self.next_button = ctk.CTkButton(
            buttons_frame,
            text="",
            image=self.next_icon,
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#2B2B2B",
            command=self.next_song
        )
        self.next_button.pack(side="left", padx=5)
        
        # 时长信息标签 - 移动到新位置
        self.time_label = ctk.CTkLabel(
            controls_frame,
            text="00:00 / 00:00",
            font=("微软雅黑", 12),
            text_color="#888888"
        )
        self.time_label.pack(side="left", padx=(15, 0))
        
        # 音量控制
        volume_frame = ctk.CTkFrame(
            controls_frame,
            fg_color="transparent"
        )
        volume_frame.pack(side="right")
        
        # 音量百分比标签
        self.volume_label = ctk.CTkLabel(
            volume_frame,
            text="5%",
            font=("微软雅黑", 12),
            text_color="#888888",
            width=35
        )
        self.volume_label.pack(side="right", padx=(5, 0))
        
        # 音量滑块
        self.volume_slider = ctk.CTkSlider(
            volume_frame,
            from_=0,
            to=100,
            width=80,
            height=15,
            button_color="#E74C3C",  # 红色滑块
            button_hover_color="#C0392B",  # 深红色悬停效果
            progress_color="#E74C3C",  # 红色进度条
            border_color="#2C3E50",  # 黑色描边
            fg_color="#2B2B2B",  # 背景色
            button_corner_radius=10,  # 减小滑块圆角
            border_width=1,  # 边框宽度
            number_of_steps=20,
            command=self.update_volume
        )
        self.volume_slider.pack(side="right", padx=(15, 5))
        self.volume_slider.set(5)  # 默认音量5%

    def play_music(self, music_path: str, song_name: str, playlist_path: str) -> None:
        """播放音乐"""
        try:
            # 停止当前播放
            pygame.mixer.music.stop()
            
            # 获取音频时长
            if music_path.lower().endswith('.mp3'):
                audio = MP3(music_path)
            elif music_path.lower().endswith('.flac'):
                audio = FLAC(music_path)
            else:
                raise ValueError("不支持的音频格式")
                
            self.total_length = audio.info.length
            
            # 加载并播放音乐
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play()
            
            # 更新播放状态
            self.current_playing = song_name
            self.current_playlist = playlist_path
            self.is_playing = True
            self.play_button.configure(image=self.pause_icon)
            
            # 更新显示信息
            if ' - ' in song_name:
                artist, title = song_name.rsplit(' - ', 1)
                title = title.rsplit('.', 1)[0]
                self.song_title_label.configure(text=title)
                self.artist_label.configure(text=artist)
            else:
                title = song_name.rsplit('.', 1)[0]
                self.song_title_label.configure(text=title)
                self.artist_label.configure(text="")
            
            # 更新播放列表
            self.playlist_songs = [
                f for f in os.listdir(playlist_path)
                if f.lower().endswith(('.mp3', '.flac'))
            ]
            self.current_index = self.playlist_songs.index(song_name)
            
            # 重置计时器和进度条
            self.start_time = time.time()
            self.pause_time = 0
            self.progress_bar.set(0)
            
            # 立即更新时间显示
            total_time = time.strftime("%M:%S", time.gmtime(self.total_length))
            self.time_label.configure(text=f"00:00 / {total_time}")
            
            if hasattr(self, 'pause_start'):
                delattr(self, 'pause_start')
                
            # 重置滚动位置
            self.reset_scroll()
            
        except Exception as e:
            print(f"播放音乐失败: {str(e)}")

    def toggle_play(self):
        """切换播放状态"""
        if not self.current_playing:
            print("没有选择要播放的歌曲")
            return
        
        if self.is_playing:
            self.pause_playlist()
        else:
            self.resume_playlist()
            
    def pause_playlist(self):
        """暂停播放"""
        try:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_button.configure(image=self.play_icon)
            self.pause_start = time.time()
        except Exception as e:
            print(f"暂停播放失败: {str(e)}")
            
    def resume_playlist(self):
        """恢复播放"""
        try:
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.play_button.configure(image=self.pause_icon)
            if hasattr(self, 'pause_start'):
                self.pause_time += time.time() - self.pause_start
                delattr(self, 'pause_start')
        except Exception as e:
            print(f"恢复播放失败: {str(e)}")

    def seek_position(self, value):
        """拖动进度条时调用"""
        try:
            if not self.current_playing or not self.current_playlist:
                return
            
            if self.is_playing:
                music_path = os.path.join(self.current_playlist, self.current_playing)
                audio = MP3(music_path)
                total_length = audio.info.length
                
                # 计算目标位置（秒）
                target_pos = (float(value) / 100) * total_length
                
                # 重新加载并从目标位置开始播放
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(start=target_pos)
                
                # 更新计时器
                self.start_time = time.time() - target_pos
                self.pause_time = 0
                
        except Exception as e:
            print(f"设置播放位置失败: {str(e)}")

    def update_volume(self, value):
        """更新音量"""
        try:
            pygame.mixer.music.set_volume(float(value) / 100)
            self.volume_label.configure(text=f"{int(value)}%")
        except Exception as e:
            print(f"更新音量失败: {str(e)}")

    def prev_song(self):
        """播放上一首"""
        if not self.current_playing or not self.playlist_songs:
            return
            
        try:
            # 计算上一首索引
            self.current_index = (self.current_index - 1) % len(self.playlist_songs)
            next_song = self.playlist_songs[self.current_index]
            
            # 播放上一首
            music_path = os.path.join(self.current_playlist, next_song)
            self.play_music(music_path, next_song, self.current_playlist)
            
        except Exception as e:
            print(f"播放上一首失败: {str(e)}")

    def next_song(self):
        """播放下一首"""
        if not self.current_playing or not self.playlist_songs:
            return
            
        try:
            # 计算下一首索引
            self.current_index = (self.current_index + 1) % len(self.playlist_songs)
            next_song = self.playlist_songs[self.current_index]
            
            # 播放下一首
            music_path = os.path.join(self.current_playlist, next_song)
            self.play_music(music_path, next_song, self.current_playlist)
            
        except Exception as e:
            print(f"播放下一首失败: {str(e)}")

    def update_progress(self):
        """更新进度条和时间显示"""
        try:
            if not self.current_playing or not self.current_playlist:
                self.progress_bar.set(0)
                self.time_label.configure(text="00:00 / 00:00")
                return
            
            if self.is_playing and pygame.mixer.music.get_busy():
                # 计算当前播放位置
                if not hasattr(self, 'start_time'):
                    self.start_time = time.time()
                    self.pause_time = 0
                
                if not hasattr(self, 'pause_start'):
                    elapsed = time.time() - self.start_time - self.pause_time
                else:
                    elapsed = self.pause_start - self.start_time - self.pause_time
                
                # 计算当前播放进度
                current_pos = elapsed / self.total_length if self.total_length > 0 else 0
                
                # 更新进度条
                self.progress_bar.set(current_pos * 100)
                
                # 更新时间显示
                current_time = time.strftime("%M:%S", time.gmtime(elapsed))
                total_time = time.strftime("%M:%S", time.gmtime(self.total_length))
                self.time_label.configure(text=f"{current_time} / {total_time}")
                
                # 检查是否播放完毕，自动播放下一首
                if elapsed >= self.total_length:
                    self.next_song()
            
        except Exception as e:
            print(f"更新进度条和时间显示失败: {str(e)}")
            
        finally:
            # 每100ms更新一次
            self.after(100, self.update_progress)

    def start_scroll(self):
        """开始文本滚动"""
        if not self.is_scrolling:
            self.is_scrolling = True
            self.scroll_text()

    def stop_scroll(self):
        """停止文本滚动"""
        self.is_scrolling = False

    def check_scroll_needed(self):
        """检查是否需要开始滚动"""
        frame_width = self.scroll_frame.winfo_width()
        container_width = self.scroll_container.winfo_width()
        
        if frame_width > container_width:
            self.start_scroll()
        else:
            self.stop_scroll()