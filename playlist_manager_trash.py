import customtkinter as ctk
import pandas as pd
from typing import Optional
import os
from PIL import Image

class TrashHistoryWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 设置窗口属性
        self.title("删除历史记录")
        self.geometry("1000x600")
        
        # 设置为transient并提升窗口层级
        self.transient(self.master)  # 将窗口设置为主窗口的临时窗口
        self.lift()  # 提升窗口层级
        self.focus_force()  # 强制获取焦点
        
        # 设置窗口在屏幕中央
        self.center_window()
        
        # 设置字体
        self.title_font = ctk.CTkFont(family="微软雅黑", size=20, weight="bold")
        self.normal_font = ctk.CTkFont(family="微软雅黑", size=14)
        
        # 加载删除图标
        self.delete_icon = ctk.CTkImage(
            light_image=Image.open("assets/icons/actions/cancel.png"),
            dark_image=Image.open("assets/icons/actions/cancel.png"),
            size=(20, 20)
        )
        
        # 添加动画相关的属性
        self.scroll_labels = []  # 存储所有滚动标签
        self.animation_speed = 50  # 滚动速度(毫秒)
        self.start_pause = 3000   # 开始暂停时间(毫秒)
        self.end_pause = 5000     # 结束暂停时间(毫秒)
        
        self._init_ui()
        self._load_trash_history()
        
    def _init_ui(self):
        """初始化UI"""
        # 创建标题
        title_label = ctk.CTkLabel(
            self,
            text="删除历史记录",
            font=self.title_font
        )
        title_label.pack(pady=20)
        
        # 创建表格框架
        self.table_frame = ctk.CTkScrollableFrame(
            self,
            width=750,
            height=500
        )
        self.table_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # 创建表头
        headers = ["序号", "歌单", "歌曲", "播放次数", "删除时间", "清除记录(谨慎)"]
        widths = [60, 180, 280, 80, 150, 50]  # 调整每列的宽度
        
        for col, (header, width) in enumerate(zip(headers, widths)):
            label = ctk.CTkLabel(
                self.table_frame,
                text=header,
                font=self.normal_font,
                width=width,
                anchor="w"
            )
            label.grid(row=0, column=col, padx=5, pady=5, sticky="w")
        
    def create_scrolling_label(self, parent, text, width):
        """创建可滚动的文本标签"""
        container = ctk.CTkFrame(parent, width=width, height=30, fg_color="transparent")
        label = ctk.CTkLabel(
            container,
            text=text,
            font=self.normal_font,
            anchor="w"
        )
        label.place(x=0, y=0)
        
        # 获取文本实际宽度
        label.update()
        text_width = label.winfo_reqwidth()
        
        # 如果文本宽度超过容器宽度，启用滚动动画
        if text_width > width:
            self.scroll_labels.append({
                'label': label,
                'container': container,
                'text_width': text_width,
                'container_width': width,
                'position': 0,
                'state': 'start_pause',
                'pause_start': None
            })
        
        return container

    def animate_labels(self):
        """处理所有标签的动画"""
        current_time = self.winfo_toplevel().winfo_children()[0].winfo_toplevel().after_idle()
        for label_info in self.scroll_labels:
            label = label_info['label']
            text_width = label_info['text_width']
            container_width = label_info['container_width']
            
            if label_info['state'] == 'start_pause':
                if label_info['pause_start'] is None:
                    label_info['pause_start'] = current_time
                elif current_time - label_info['pause_start'] >= self.start_pause:
                    label_info['state'] = 'scrolling'
                    label_info['pause_start'] = None
            
            elif label_info['state'] == 'scrolling':
                label_info['position'] -= 1
                if abs(label_info['position']) >= text_width:
                    label_info['position'] = 0
                    label_info['state'] = 'end_pause'
                    label_info['pause_start'] = current_time
                label.place(x=label_info['position'], y=0)
            
            elif label_info['state'] == 'end_pause':
                if label_info['pause_start'] is None:
                    label_info['pause_start'] = current_time
                elif current_time - label_info['pause_start'] >= self.end_pause:
                    label_info['state'] = 'start_pause'
                    label_info['pause_start'] = None
                    label_info['position'] = 0
                    label.place(x=0, y=0)
        
        self.after(self.animation_speed, self.animate_labels)

    def _load_trash_history(self):
        """加载删除历史记录"""
        try:
            csv_path = 'statistics/play_count_logs/trash.csv'
            if not os.path.exists(csv_path):
                return
            
            # 读取CSV文件并倒序排列
            df = pd.read_csv(csv_path)
            df = df.iloc[::-1].reset_index(drop=True)  # 倒序并重置索引
            
            # 设置每列的宽度
            widths = [60, 180, 280, 80, 150, 50]
            
            # 显示数据
            for idx, row in df.iterrows():
                # 序号
                ctk.CTkLabel(
                    self.table_frame,
                    text=str(row['序号']),
                    font=self.normal_font,
                    width=widths[0],
                    anchor="w"
                ).grid(row=idx+1, column=0, padx=5, pady=5, sticky="w")
                
                # 歌单（去除『』符号和"渐进学习时长激励歌单"）
                playlist = row['歌单'].replace('『', '').replace('』', '')
                playlist = playlist.replace('渐进学习时长激励歌单', '').replace('渐进学习时长激歌单', '')
                ctk.CTkLabel(
                    self.table_frame,
                    text=playlist.strip(),  # 去除可能的多余空格
                    font=self.normal_font,
                    width=widths[1],
                    anchor="w"
                ).grid(row=idx+1, column=1, padx=5, pady=5, sticky="w")
                
                # 歌曲（使用滚动标签）
                song_container = self.create_scrolling_label(
                    self.table_frame,
                    row['歌曲'],
                    widths[2]
                )
                song_container.grid(row=idx+1, column=2, padx=5, pady=5, sticky="w")
                
                # 播放次数
                ctk.CTkLabel(
                    self.table_frame,
                    text=str(row['学习成就播放次数']),
                    font=self.normal_font,
                    width=widths[3],
                    anchor="center"  # 播放次数居中对齐
                ).grid(row=idx+1, column=3, padx=5, pady=5)
                
                # 删除时间
                ctk.CTkLabel(
                    self.table_frame,
                    text=row['删除时间'],
                    font=self.normal_font,
                    width=widths[4],
                    anchor="w"
                ).grid(row=idx+1, column=4, padx=5, pady=5, sticky="w")
                
                # 添加删除按钮
                delete_button = ctk.CTkButton(
                    self.table_frame,
                    text="",
                    image=self.delete_icon,
                    width=30,
                    height=30,
                    fg_color="transparent",  # 无背景色
                    hover_color="#333333",   # 改为深色
                    corner_radius=8,
                    command=lambda r=row: self._delete_record(r['序号'])
                )
                delete_button.grid(row=idx+1, column=5, padx=5, pady=5)
                
            # 启动动画
            self.animate_labels()
                
        except Exception as e:
            print(f"加载删除历史记录失败: {str(e)}") 
    
    def _delete_record(self, record_id):
        """删除指定的记录"""
        try:
            csv_path = 'statistics/play_count_logs/trash.csv'
            # 读取CSV文件
            df = pd.read_csv(csv_path)
            
            # 删除指定序号的记录
            df = df[df['序号'] != record_id]
            
            # 保存更新后的CSV文件
            df.to_csv(csv_path, index=False)
            
            # 清除现有内容
            for widget in self.table_frame.winfo_children():
                widget.destroy()
            
            # 重新创建表头
            headers = ["序号", "歌单", "歌曲", "播放次数", "删除时间", "清除记录(谨慎)"]
            widths = [60, 180, 280, 80, 150, 50]
            
            for col, (header, width) in enumerate(zip(headers, widths)):
                label = ctk.CTkLabel(
                    self.table_frame,
                    text=header,
                    font=self.normal_font,
                    width=width,
                    anchor="w"
                )
                label.grid(row=0, column=col, padx=5, pady=5, sticky="w")
            
            # 重新加载数据
            self._load_trash_history()
            
        except Exception as e:
            print(f"删除记录失败: {str(e)}")
    
    def center_window(self):
        """将窗口居中显示"""
        # 获取屏幕尺寸
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # 获取窗口尺寸
        window_width = 1000
        window_height = 600
        
        # 计算居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 设置窗口位置
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")