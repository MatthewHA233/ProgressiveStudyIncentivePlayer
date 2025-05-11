import customtkinter as ctk
from tkinter import ttk
import json
import os
from tkinter import filedialog, messagebox
import sys
from pygame import mixer
import threading
import re
import tkinter as tk
from tkinter import font

class LevelManager(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # 初始化音频播放器
        from pygame import mixer
        mixer.init()
        
        # 先加载配置文件以获取字体
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 初始化字体
                self.default_font = ctk.CTkFont(family=config.get('font', '微软雅黑'))
                self.title_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=20, weight="bold")
                self.subtitle_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=12)
        except Exception as e:
            print(f"加载字体配置失败: {str(e)}")
            # 使用默认字体
            self.default_font = ctk.CTkFont(family='微软雅黑')
            self.title_font = ctk.CTkFont(family='微软雅黑', size=20, weight="bold")
            self.subtitle_font = ctk.CTkFont(family='微软雅黑', size=12)
        
        # 基础设置框架
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.pack(fill="x", padx=20, pady=10)
        
        # 字体设置行
        font_frame = ctk.CTkFrame(self.settings_frame)
        font_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(font_frame, text="软件字体:", font=self.default_font).pack(side="left", padx=5)
        self.font_entry = ctk.CTkComboBox(
            font_frame, 
            width=200,
            values=self.get_recent_fonts(),
            state="readonly",
            font=self.default_font
        )
        self.font_entry.pack(side="left", padx=5)
        
        # 添加字体浏览按钮
        ctk.CTkButton(
            font_frame,
            text="浏览",
            width=60,
            command=self.browse_font,
            font=self.default_font
        ).pack(side="left", padx=5)
        
        # 字体预览
        self.font_preview = ctk.CTkLabel(
            font_frame,
            text="字体预览文字",
            width=200,
            height=32,
            fg_color="#2B2B2B",
            corner_radius=6
        )
        self.font_preview.pack(side="left", padx=5)
        
        # 音效设置框架
        effects_frame = ctk.CTkFrame(self.settings_frame)
        effects_frame.pack(fill="x", pady=5)
        
        # 半小时音效
        half_hour_frame = ctk.CTkFrame(effects_frame)
        half_hour_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(half_hour_frame, text="半小时音效:", font=self.default_font).pack(side="left", padx=5)
        self.half_hour_entry = ctk.CTkComboBox(
            half_hour_frame, 
            width=400,
            values=self.get_sound_files(),
            state="readonly",
            font=self.default_font
        )
        self.half_hour_entry.pack(side="left", padx=5)
        ctk.CTkButton(
            half_hour_frame,
            text="试听",
            width=60,
            command=lambda: self.play_sound(self.half_hour_entry.get()),
            font=self.default_font
        ).pack(side="left", padx=5)
        
        # 升级音效
        level_up_frame = ctk.CTkFrame(effects_frame)
        level_up_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(level_up_frame, text="升级音效:", font=self.default_font).pack(side="left", padx=5)
        self.level_up_entry = ctk.CTkComboBox(
            level_up_frame, 
            width=400,
            values=self.get_sound_files(),
            state="readonly",
            font=self.default_font
        )
        self.level_up_entry.pack(side="left", padx=5)
        ctk.CTkButton(
            level_up_frame,
            text="试听",
            width=60,
            command=lambda: self.play_sound(self.level_up_entry.get()),
            font=self.default_font
        ).pack(side="left", padx=5)
        
        # 五分钟音效
        five_min_frame = ctk.CTkFrame(effects_frame)
        five_min_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(five_min_frame, text="五分钟音效:", font=self.default_font).pack(side="left", padx=5)
        self.five_min_entry = ctk.CTkComboBox(
            five_min_frame, 
            width=400,
            values=self.get_sound_files(),
            state="readonly",
            font=self.default_font
        )
        self.five_min_entry.pack(side="left", padx=5)
        ctk.CTkButton(
            five_min_frame,
            text="试听",
            width=60,
            command=lambda: self.play_sound(self.five_min_entry.get()),
            font=self.default_font
        ).pack(side="left", padx=5)
        
        # 添加歌单层级配置标题
        level_title_frame = ctk.CTkFrame(self.settings_frame)
        level_title_frame.pack(fill="x", pady=(20, 5))
        ctk.CTkLabel(
            level_title_frame,
            text="配置歌单层级",
            font=self.title_font,
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=5)
        
        # 添加说明文字
        ctk.CTkLabel(
            level_title_frame,
            text="设置学习激励系统的歌单等级和播放规则",
            font=self.subtitle_font,
            text_color="#888888"
        ).pack(anchor="w", padx=5)
        
        # 分割线
        separator = ctk.CTkFrame(self.settings_frame, fg_color="#3B3B3B", height=2)
        separator.pack(fill="x", padx=5, pady=(5, 10))
        
        # 使用 customtkinter 的颜色格式
        self.rank_colors = {
            'S': {
                "bg": ["#FFD700", "#FFD700"],  # 金色
                "line": "#FFA500",
                "text": ["#000000", "#000000"]
            },
            'A': {
                "bg": ["#FF4D4D", "#FF4D4D"],  # 红色
                "line": "#FF0000",
                "text": ["#000000", "#000000"]
            },
            'B': {
                "bg": ["#4169E1", "#4169E1"],  # 蓝色
                "line": "#0000FF",
                "text": ["#000000", "#000000"]
            },
            'C': {
                "bg": ["#98FB98", "#98FB98"],  # 绿色
                "line": "#32CD32",
                "text": ["#000000", "#000000"]
            }
        }
        
        # 设置背景色为深色
        self.configure(fg_color="#1A1A1A")
        
        # 记录已移动的项目
        self.moved_items = set()
        
        # 创建主滚动容器
        self.container = ctk.CTkScrollableFrame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 拖拽变量
        self.drag_source = None
        self.drag_indicator = None
        self.levels = []
        
        # 初始化insert_button
        self.insert_button = None
        
        # 加载默认配置
        self.load_default_levels()
        
        # 在添加按钮上方创建删除区域
        self.delete_zone = ctk.CTkFrame(
            self.container,
            height=40,
            fg_color="#D22B2B",  # 红色背景
            corner_radius=8
        )
        self.delete_zone.pack(side="bottom", fill="x", pady=(5,10), padx=5)
        self.delete_zone.pack_propagate(False)
        
        # 添加删除区域的提示文本
        self.delete_label = ctk.CTkLabel(
            self.delete_zone,
            text="拖拽到此处删除",
            text_color="white",
            font=("Arial", 14)
        )
        self.delete_label.pack(expand=True)
        
        # 默认隐藏删除区域
        self.delete_zone.pack_forget()
        
        # 添加新等级按钮
        self.add_btn = ctk.CTkButton(
            self.container,
            text="+ 添加新等级",
            command=self.add_new_level,
            width=120,
            height=30,
            fg_color="#2B2B2B",
            hover_color="#3B3B3B"
        )
        self.add_btn.pack(side="bottom", pady=10)
        
        # 重置按钮放在主框架底部
        self.reset_btn = ctk.CTkButton(
            self,
            text="还原默认配置",
            command=self.reset_to_default,
            width=120,
            fg_color="#D22B2B",
            hover_color="#AA0000"
        )
        self.reset_btn.pack(side="bottom", pady=10)
        
        # 绑定鼠标移动事件到容器
        self.container.bind('<Motion>', self.on_mouse_move)
        
        # 添加字体选择的回调
        self.font_entry.configure(command=self.update_font_preview)

    def _apply_font_recursively(self, widget, font):
        """递归设置所有部件的字体"""
        try:
            widget.configure(font=font)
        except:
            pass
        
        # 递归处理所有子部件
        for child in widget.winfo_children():
            self._apply_font_recursively(child, font)

    def get_rank_colors(self, name):
        """获取等级对应的颜色"""
        for rank in ['S', 'A', 'B', 'C']:
            if rank in name:
                colors = self.rank_colors[rank].copy()
                if name in self.moved_items:
                    # 如果是已移动的项目，使用暗色版本
                    colors["bg"] = [
                        self.adjust_color(colors["bg"][0], -30),
                        self.adjust_color(colors["bg"][1], -30)
                    ]
                return colors
        return {
            "bg": ["#2B2B2B", "#2B2B2B"],
            "line": "#1F6AA5"
        }

    def create_level_frame(self, name, songs):
        """创建等级框架"""
        colors = self.get_rank_colors(name)
        
        # 创建框架并设置透明度
        frame = ctk.CTkFrame(
            self.container, 
            fg_color=colors["bg"],
            height=40,
            corner_radius=8,
            bg_color="transparent"
        )
        frame.configure(fg_color=colors["bg"])
        frame.pack(fill="x", pady=1, padx=5)
        frame.pack_propagate(False)
        
        # 拖动手柄
        handle = ctk.CTkLabel(
            frame,
            text="⋮⋮",
            width=20,
            cursor="hand2",
            text_color=colors["text"]
        )
        handle.pack(side="left", padx=5)
        
        # 等级名称
        label = ctk.CTkLabel(
            frame, 
            text=name,
            width=140,  # 减小宽度，为输入框留空间
            anchor="w",
            text_color=colors["text"]
        )
        label.pack(side="left", padx=5)
        
        # 歌曲数量输入框
        songs_entry = ctk.CTkEntry(
            frame,
            width=40,
            height=25,
            justify="center",
            text_color=colors["text"],
            fg_color=self.adjust_color(colors["bg"][0], -20)  # 稍微暗一点的背景色
        )
        songs_entry.insert(0, str(songs))
        songs_entry.pack(side="left", padx=5)
        
        # 显示"首"字
        songs_label = ctk.CTkLabel(
            frame,
            text="首",
            width=20,
            text_color=colors["text"]
        )
        songs_label.pack(side="left")
        
        # 时间线段显示区域
        timeline = ctk.CTkCanvas(
            frame,
            height=20,
            bg="#2B2B2B",
            highlightthickness=0
        )
        timeline.pack(side="left", expand=True, fill="x", padx=10, pady=10)
        
        # 时间标签
        time_label = ctk.CTkLabel(
            frame,
            text="",
            width=100,
            text_color=colors["text"]
        )
        time_label.pack(side="right", padx=10)
        
        frame.level_data = {
            'name': name,
            'songs': songs,
            'timeline': timeline,
            'time_label': time_label,
            'colors': colors,
            'songs_entry': songs_entry  # 保存输入框引用
        }
        
        # 绑定输入框的事件
        def update_songs(event=None):
            try:
                new_songs = int(songs_entry.get())
                if new_songs < 1:
                    raise ValueError
                # 更新数据
                frame.level_data['songs'] = new_songs
                for level in self.levels:
                    if level['frame'] == frame:
                        level['songs'] = new_songs
                        break
                # 更新时间轴
                self.update_positions()
            except ValueError:
                # 如果输入无效，恢复原值
                songs_entry.delete(0, 'end')
                songs_entry.insert(0, str(frame.level_data['songs']))
        
        # 绑定回车键和失去焦点事件
        songs_entry.bind('<Return>', update_songs)
        songs_entry.bind('<FocusOut>', update_songs)
        
        # 绑定拖拽事件（只在手柄处触发）
        handle.bind('<Button-1>', lambda e: self.start_drag(e, frame))
        handle.bind('<B1-Motion>', self.on_drag)
        handle.bind('<ButtonRelease-1>', self.stop_drag)
        
        # 绑定重绘事件
        timeline.bind('<Configure>', lambda e, f=frame: self.on_timeline_resize(e, f))
        
        return frame

    def start_drag(self, event, frame):
        """开始拖拽时显示删除区域"""
        self.drag_source = frame
        self.drag_y = event.y_root
        
        # 创建拖拽时的视觉反馈
        colors = frame.level_data['colors']
        frame.configure(fg_color=self.adjust_color(colors["bg"][0], -30))
        
        # 创建拖拽指示器
        if self.drag_indicator:
            self.drag_indicator.destroy()
        self.drag_indicator = ctk.CTkFrame(
            self.container, 
            height=2,
            fg_color=colors["line"],  # 使用对应的线条颜色
            corner_radius=0
        )
        
        self.delete_zone.pack(side="bottom", fill="x", pady=(5,10), padx=5)
        self.delete_zone.configure(fg_color="#D22B2B")  # 重置颜色

    def on_drag(self, event):
        """改进的拖拽处理"""
        if not self.drag_source:
            return
        
        # 检查是否删除区域上方
        delete_zone_y = self.delete_zone.winfo_rooty()
        delete_zone_height = self.delete_zone.winfo_height()
        
        if delete_zone_y <= event.y_root <= delete_zone_y + delete_zone_height:
            self.delete_zone.configure(fg_color="#AA0000")
            self.delete_label.configure(text="释放以删除")
        else:
            self.delete_zone.configure(fg_color="#D22B2B")
            self.delete_label.configure(text="拖拽到此处删除")
            
            # 计算目标位置
            target_idx = self.get_insert_position(event.y_root)
            
            if target_idx is not None:
                # 获取当前拖拽项的索引
                frames = [f for f in self.container.winfo_children() 
                         if isinstance(f, ctk.CTkFrame) and hasattr(f, 'level_data')]
                try:
                    current_idx = frames.index(self.drag_source)
                    
                    # 移动指示器 - 删除判断条件，总显示指示器
                    self.drag_indicator.pack_forget()
                    
                    # 插入指示器到新位置
                    if target_idx < len(frames):
                        self.drag_indicator.pack(before=frames[target_idx], fill="x", padx=5)
                    else:
                        self.drag_indicator.pack(fill="x", padx=5)
                        
                except ValueError:
                    pass  # 如果找不到索引，不做处理

    def get_insert_position(self, mouse_y):
        """获取更精确的插入位置"""
        frames = self.container.winfo_children()
        frames = [f for f in frames if isinstance(f, ctk.CTkFrame) and f != self.drag_indicator]
        
        container_y = self.container.winfo_rooty()  # 容器的绝对y坐标
        relative_y = mouse_y - container_y  # 相对于容器的y坐标
        
        for i, frame in enumerate(frames):
            if frame == self.drag_source:
                continue  # 跳过正在拖拽的框架
            
            frame_relative_y = frame.winfo_y()  # 框架相对于容器的y坐标
            frame_height = frame.winfo_height()
            
            # 判断鼠标是否在当前框的范围内
            if relative_y < frame_relative_y + frame_height:
                # 如果鼠标在框架的上半部分，插入到这个位置
                if relative_y < frame_relative_y + frame_height/2:
                    return i
                # 如果在下半部分，插入到下一个位置
                else:
                    return i + 1
        
        # 如果鼠标在有框架下方，插入到最后
        return len(frames)

    def stop_drag(self, event):
        """结束拖拽时的处理"""
        if not self.drag_source:
            return
        
        # 检查是否在删除区域释放
        delete_zone_y = self.delete_zone.winfo_rooty()
        delete_zone_height = self.delete_zone.winfo_height()
        
        if delete_zone_y <= event.y_root <= delete_zone_y + delete_zone_height:
            # 删除逻辑...
            level_to_delete = next(
                level for level in self.levels 
                if level['frame'] == self.drag_source
            )
            self.levels.remove(level_to_delete)
            self.drag_source.destroy()
            messagebox.showinfo("删除成功", f"已删除等级: {level_to_delete['name']}")
        else:
            # 获取目标位置
            target_idx = self.get_insert_position(event.y_root)
            if target_idx is not None:
                # 获取源位置
                source_idx = self.levels.index(next(
                    level for level in self.levels 
                    if level['frame'] == self.drag_source
                ))
                
                # 如果目标位置不是源位置或其后一位，才进行移动
                if target_idx != source_idx and target_idx != source_idx + 1:
                    level = self.levels.pop(source_idx)
                    # 如果目标位置在源位置之后，需要减1
                    if target_idx > source_idx:
                        target_idx -= 1
                    self.levels.insert(target_idx, level)
                    self.moved_items.add(level['name'])
                    self.reorder_frames()
        
        # 清理拖拽状态
        self.drag_source = None
        if self.drag_indicator:
            self.drag_indicator.destroy()
            self.drag_indicator = None
        
        # 隐藏删除区域
        self.delete_zone.pack_forget()
        
        # 更新时间位置
        self.update_positions()

    def reorder_frames(self):
        """重新排列所有框架"""
        for level in self.levels:
            level['frame'].pack_forget()
        for level in self.levels:
            level['frame'].pack(fill="x", pady=1, padx=5)

    def update_positions(self):
        """更新所有等级的时间位置"""
        total_songs = sum(level['songs'] for level in self.levels)
        total_time = total_songs * 0.5  # 每首歌0.5小时
        current_time = 0.0
        
        # 从上往下计算位置（移除reversed）
        for level in self.levels:
            duration = level['songs'] * 0.5
            start_time = current_time
            end_time = current_time + duration
            
            # 更新时间标签
            level['frame'].level_data['time_label'].configure(
                text=f"{start_time:.1f}-{end_time:.1f}h"
            )
            
            # 更新时间线段，使用总时长作为基准
            self.update_timeline(level['frame'], start_time, end_time, total_time)
            
            current_time = end_time

    def update_timeline(self, frame, start_time, end_time, total_time):
        """更新时间线段 - 使用总时长作为基准"""
        timeline = frame.level_data['timeline']
        colors = frame.level_data['colors']
        timeline.delete("all")
        
        width = timeline.winfo_width()
        if width > 0:
            # 用总时长作为基准算位置
            x_start = (start_time / total_time) * width
            x_end = (end_time / total_time) * width
            
            # 绘制时间线
            timeline.create_line(
                x_start, 10, x_end, 10,
                fill="#1A1A1A",
                width=8
            )
            
            timeline.create_line(
                x_start, 10, x_end, 10,
                fill=colors["line"],
                width=6
            )
            
            # 绘制端点
            timeline.create_oval(
                x_start-4, 6, x_start+4, 14,
                fill=colors["line"],
                outline=""
            )
            timeline.create_oval(
                x_end-4, 6, x_end+4, 14,
                fill=colors["line"],
                outline=""
            )

    def load_default_levels(self):
        """从JSON文件加载配置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                if 'font' in config:
                    self.font_entry.set(config['font'])
                    self.update_font_preview()
                
                # 处理音效路径，只显示文件名
                if 'half_hour_effect' in config:
                    filename = os.path.basename(config['half_hour_effect'])
                    self.half_hour_entry.set(filename)
                
                if 'level_up_effect' in config:
                    filename = os.path.basename(config['level_up_effect'])
                    self.level_up_entry.set(filename)
                
                if 'five_minute_effect' in config:
                    filename = os.path.basename(config['five_minute_effect'])
                    self.five_min_entry.set(filename)
                
                # 加载等级配置
                for level_config in config['levels']:
                    frame = self.create_level_frame(
                        level_config['name'], 
                        int((level_config['end'] - level_config['start']) * 2)  # 转换为歌曲数
                    )
                    self.levels.append({
                        'frame': frame,
                        'name': level_config['name'],
                        'songs': int((level_config['end'] - level_config['start']) * 2)
                    })
                
                # 更新位置
                self.update_positions()
                
        except FileNotFoundError:
            messagebox.showerror("错误", "未找到配置文件")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")

    def reset_to_default(self):
        """还原默认配置"""
        # 获取主窗口实例
        main_window = self.winfo_toplevel()
        # 调��主窗口的打开配置编辑器方法
        main_window.open_config_editor()

    def on_timeline_resize(self, event, frame):
        """当时间线大小改变时重绘"""
        if hasattr(self, 'levels'):
            self.update_positions()

    def adjust_color(self, color, amount):
        """调整颜色明暗"""
        if not color.startswith('#'):
            return color
        
        # 将颜色转换为RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # 调整每个分量
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        
        return f"#{r:02x}{g:02x}{b:02x}"

    def save_config(self):
        """保存配置到JSON文件"""
        try:
            # 先读取现有配置
            with open('config.json', 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
                
                # 创建color属性映射
                level_colors = {
                    level['name']: level.get('color') 
                    for level in existing_config.get('levels', [])
                    if 'color' in level
                }
                
                # 保留其他配置项
                preserved_keys = ['start_date', 'excel_path', 'template_path']
                preserved_config = {
                    key: existing_config[key]
                    for key in preserved_keys
                    if key in existing_config
                }
        except:
            level_colors = {}
            preserved_config = {}
        
        # 创建新配置，保留原有配置项
        config = {
            'font': self.font_entry.get(),
            'half_hour_effect': os.path.join("music_library", "音效", self.half_hour_entry.get()),
            'level_up_effect': os.path.join("music_library", "音效", self.level_up_entry.get()),
            'five_minute_effect': os.path.join("music_library", "音效", self.five_min_entry.get()),
            'levels': [],
            'recent_fonts': self.update_recent_fonts(self.font_entry.get()),
            **preserved_config  # 合并保留的配置项
        }
        
        current_time = 0.0
        for level in self.levels:
            # 从输入框获取实际的歌曲数量
            songs_count = int(level['frame'].level_data['songs_entry'].get())
            duration = songs_count * 0.5
            level_config = {
                'name': level['name'],
                'start': current_time,
                'end': current_time + duration,
                'random_count': songs_count  # 使用输入框中的值
            }
            # 只有当原配置中存在color属性时才添加
            if level['name'] in level_colors:
                level_config['color'] = level_colors[level['name']]
            
            config['levels'].append(level_config)
            current_time += duration
        
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")

    def on_mouse_move(self, event):
        """处理鼠标移动,显示/隐藏添加按钮"""
        if self.drag_source:  # 如果正在拖拽，不显示添加按钮
            return
        
        # 删除有的插入按钮
        if self.insert_button:
            self.insert_button.destroy()
            self.insert_button = None
        
        # 获取所有框架
        frames = [f for f in self.container.winfo_children() 
                 if isinstance(f, ctk.CTkFrame) and hasattr(f, 'level_data')]
        
        # 获取鼠标相对于容器的位置
        mouse_y = event.y
        
        # 检查鼠标是否在框架之间
        for i, frame in enumerate(frames):
            frame_y = frame.winfo_y()
            frame_height = frame.winfo_height()
            
            # 如果鼠标在框架的中间位置
            if frame_y <= mouse_y <= frame_y + frame_height:
                mid_point = frame_y + frame_height/2
                if abs(mouse_y - mid_point) < 10:  # 增大检测范围到10像素
                    self.insert_button = ctk.CTkButton(
                        self.container,
                        text="+ 添加新等级",
                        command=lambda idx=i: self.add_level_at(idx),
                        width=120,
                        height=25
                    )
                    self.insert_button.place(
                        relx=0.5,
                        y=mid_point,
                        anchor="center"
                    )
                break

    def add_level_at(self, index):
        """在指定位置添加新等级"""
        # 打开文件夹选择对话框
        folder = filedialog.askdirectory(
            title="选择音乐文件夹",
            initialdir="music_library"
        )
        
        if folder:
            # 获取文件夹名称
            name = os.path.basename(folder)
            songs = 1  # 默认歌曲数量
            
            # 创建新框架
            frame = self.create_level_frame(name, songs)
            
            # 在指定位置插入新等级
            self.levels.insert(index, {
                'frame': frame,
                'name': name,
                'songs': songs
            })
            
            # 重新排列所有框架
            self.reorder_frames()
            self.update_positions()
            
            # 移除插入按钮
            if self.insert_button:
                self.insert_button.destroy()
                self.insert_button = None

    def add_new_level(self):
        """添加新等级到底部"""
        folder = filedialog.askdirectory(
            title="选择音乐文件夹",
            initialdir="music_library"
        )
        
        if folder:
            name = os.path.basename(folder)
            songs = 1  # 默认歌曲数量
            
            # 创建新框架
            frame = self.create_level_frame(name, songs)
            
            # 添加到列表末尾
            self.levels.append({
                'frame': frame,
                'name': name,
                'songs': songs
            })
            
            # 重新排列框架并更新时间
            self.reorder_frames()
            self.update_positions()

    def browse_excel_path(self):
        """浏览选择Excel路径"""
        path = filedialog.askdirectory(
            title="选择Excel文件所在文件夹"
        )
        if path:
            self.excel_path.delete(0, 'end')
            self.excel_path.insert(0, path)

    def get_recent_fonts(self):
        """获取最近使用的字体列表"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('recent_fonts', ['微软雅黑'])  # 默认至少返回微软雅黑
        except:
            return ['微软雅黑']

    def update_recent_fonts(self, new_font):
        """更新最近使用的字体列表"""
        recent_fonts = self.get_recent_fonts()
        
        # 如果字体已在列表中，移到最前面
        if new_font in recent_fonts:
            recent_fonts.remove(new_font)
        
        # 将新字体添加到列表开头
        recent_fonts.insert(0, new_font)
        
        # 保持列表最多10个字体
        recent_fonts = recent_fonts[:10]
        
        return recent_fonts

    def get_sound_files(self):
        """获取音效文件列表"""
        sound_dir = "music_library/音效"
        try:
            if not os.path.exists(sound_dir):
                os.makedirs(sound_dir)
            return [f for f in os.listdir(sound_dir) if f.endswith(('.mp3', '.wav'))]
        except Exception as e:
            messagebox.showerror("错误", f"读取音效文件失败: {str(e)}")
            return []

    def play_sound(self, sound_path):
        """播放音效"""
        def play():
            try:
                # 确保使用完整路径
                full_path = os.path.join("music_library", "音效", sound_path)
                mixer.music.load(full_path)
                mixer.music.play()
            except Exception as e:
                messagebox.showerror("错误", f"播放音效失败: {str(e)}")
        
        threading.Thread(target=play, daemon=True).start()

    def browse_font(self):
        """浏览选择字体"""
        from tkinter import font
        
        class FontChooser(ctk.CTkToplevel):
            def __init__(self, parent):
                super().__init__(parent)
                
                # 设置窗口层级为顶层
                self.attributes('-topmost', True)
                
                # 设置模态对话框
                self.transient(parent)
                self.grab_set()
                
                self.title("选择字体")
                self.geometry("600x400")
                
                # 将窗口居中显示
                self.update_idletasks()
                width = self.winfo_width()
                height = self.winfo_height()
                x = (self.winfo_screenwidth() // 2) - (width // 2)
                y = (self.winfo_screenheight() // 2) - (height // 2)
                self.geometry(f'+{x}+{y}')
                
                # 搜索框
                search_frame = ctk.CTkFrame(self)
                search_frame.pack(fill="x", padx=10, pady=5)
                self.search_var = ctk.StringVar()
                self.search_var.trace('w', self.filter_fonts)
                search_entry = ctk.CTkEntry(
                    search_frame, 
                    placeholder_text="搜索字体...",
                    textvariable=self.search_var,
                    width=200
                )
                search_entry.pack(side="left", padx=5)
                
                # 字体列表框
                list_frame = ctk.CTkFrame(self)
                list_frame.pack(fill="both", expand=True, padx=10, pady=5)
                
                # 使用Listbox显示字体
                self.font_listbox = tk.Listbox(
                    list_frame,
                    bg='#2B2B2B',
                    fg='white',
                    selectmode="single",
                    font=('微软雅黑', 12)
                )
                self.font_listbox.pack(side="left", fill="both", expand=True)
                
                # 添加滚动条
                scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
                scrollbar.pack(side="right", fill="y")
                
                # 关联滚动条和列表框
                self.font_listbox.config(yscrollcommand=scrollbar.set)
                scrollbar.config(command=self.font_listbox.yview)
                
                # 获取并显示字体列表
                self.all_fonts = sorted(font.families())
                self.font_listbox.insert(0, *self.all_fonts)
                
                # 预览框
                preview_frame = ctk.CTkFrame(self)
                preview_frame.pack(fill="x", padx=10, pady=5)
                self.preview_label = ctk.CTkLabel(
                    preview_frame,
                    text="字体预览文字",
                    width=200,
                    height=32,
                    fg_color="#2B2B2B",
                    corner_radius=6
                )
                self.preview_label.pack(pady=5)
                
                # 按钮框架
                button_frame = ctk.CTkFrame(self)
                button_frame.pack(fill="x", padx=10, pady=5)
                
                # 确定按钮
                ctk.CTkButton(
                    button_frame,
                    text="确定",
                    command=self.confirm_selection,
                    width=100
                ).pack(side="right", padx=5)
                
                # 取消按钮
                ctk.CTkButton(
                    button_frame,
                    text="取消",
                    command=self.destroy,
                    width=100
                ).pack(side="right", padx=5)
                
                # 绑定选择事件
                self.font_listbox.bind('<<ListboxSelect>>', self.update_preview)
                self.selected_font = None
            
            def filter_fonts(self, *args):
                """过字体列表"""
                search_text = self.search_var.get().lower()
                self.font_listbox.delete(0, tk.END)
                for font_name in self.all_fonts:
                    if search_text in font_name.lower():
                        self.font_listbox.insert(tk.END, font_name)
            
            def update_preview(self, event):
                """更新预览"""
                selection = self.font_listbox.curselection()
                if selection:
                    font_name = self.font_listbox.get(selection[0])
                    try:
                        preview_font = ctk.CTkFont(family=font_name, size=16)
                        self.preview_label.configure(font=preview_font)
                    except Exception as e:
                        print(f"预览更新失败: {str(e)}")
            
            def confirm_selection(self):
                """确认选择"""
                selection = self.font_listbox.curselection()
                if selection:
                    self.selected_font = self.font_listbox.get(selection[0])
                    self.destroy()
        
        # 显示字体选择对话框
        chooser = FontChooser(self.winfo_toplevel())  # 使用主窗口作为父窗口
        self.wait_window(chooser)
        
        # 如果选择了字体，更新字体设置和最近使用列表
        if chooser.selected_font:
            recent_fonts = self.update_recent_fonts(chooser.selected_font)
            self.font_entry.configure(values=recent_fonts)
            self.font_entry.set(chooser.selected_font)
            self.update_font_preview()

    def update_font_preview(self, *args):
        """更新字体预览"""
        try:
            selected_font = self.font_entry.get()
            preview_font = ctk.CTkFont(
                family=selected_font,
                size=16
            )
            self.font_preview.configure(font=preview_font)
        except Exception as e:
            print(f"字体预览更新失败: {str(e)}")

class ConfigEditor(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # 创建等级管理器
        self.level_manager = LevelManager(self)
        self.level_manager.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 保存按钮
        self.save_btn = ctk.CTkButton(
            self,
            text="保存配置",
            command=self.level_manager.save_config,
            width=120
        )
        self.save_btn.pack(pady=5)

# 如果直接运行此文件,则创建独立窗口
if __name__ == "__main__":
    root = ctk.CTk()
    root.title("渐进学习激励配置")
    root.geometry("1000x600")
    
    # 设置主题
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # 创建编辑器实例
    editor = ConfigEditor(root)
    editor.pack(fill="both", expand=True)
    
    root.mainloop() 