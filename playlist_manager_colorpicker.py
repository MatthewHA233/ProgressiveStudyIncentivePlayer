import customtkinter as ctk
from tkinter import colorchooser, StringVar, messagebox
from PIL import Image
import json
from datetime import datetime
import pyperclip  # 用于复制到剪贴板

# 读取配置文件
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
        FONT_FAMILY = CONFIG.get('font', '微软雅黑')  # 如果没有配置，默认使用微软雅黑
except:
    FONT_FAMILY = '微软雅黑'  # 读取失败时使用默认字体

class PlaylistColorPicker:
    def __init__(self, master, playlist_name, current_color, save_callback):
        self.dialog = ctk.CTkToplevel(master)
        self.dialog.title(f"选择 {playlist_name} 的颜色")
        
        # 加载图标
        self.color_palette_icon = ctk.CTkImage(
            light_image=Image.open("assets/icons/actions/color_palette.png"),
            dark_image=Image.open("assets/icons/actions/color_palette.png"),
            size=(25, 25)
        )
        self.confirm_icon = ctk.CTkImage(
            light_image=Image.open("assets/icons/actions/confirm.png"),
            dark_image=Image.open("assets/icons/actions/confirm.png"),
            size=(25, 25)
        )
        self.cancel_icon = ctk.CTkImage(
            light_image=Image.open("assets/icons/actions/cancel.png"),
            dark_image=Image.open("assets/icons/actions/cancel.png"),
            size=(25, 25)
        )
        
        # 保存必要的属性
        self.playlist_name = playlist_name
        self.save_callback = save_callback
        
        # 设置默认透明度
        self.DEFAULT_ALPHA = 0.4
        
        # 解析当前颜色，分别存储hex和rgba格式
        self.current_rgba = current_color
        rgba_values = self.parse_rgba(current_color)
        self.current_hex = '#{:02x}{:02x}{:02x}'.format(rgba_values[0], rgba_values[1], rgba_values[2])
        self.current_alpha = rgba_values[3]
        
        # 设置更小的窗口大小
        window_width = 500   # 减小宽度
        window_height = 330  # 减小高度
        
        # 获取主窗口位置和大小
        master_x = master.winfo_rootx()
        master_y = master.winfo_rooty()
        master_width = master.winfo_width()
        master_height = master.winfo_height()
        
        # 计算居中位置
        x = master_x + (master_width - window_width) // 2
        y = master_y + (master_height - window_height) // 2
        
        # 设置窗口位置和大小
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.dialog.resizable(False, False)
        
        # 创建变量
        self.hex_var = StringVar(value=self.current_hex)
        self.alpha_var = StringVar(value=str(self.current_alpha))
        
        # 创建主容器，减少内边距
        main_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 颜色预览框架，减小尺寸
        preview_container = ctk.CTkFrame(
            main_frame,
            fg_color="transparent",
            width=150,    # 减小预览区域
            height=150
        )
        preview_container.pack(pady=(15, 15))  # 减少间距
        preview_container.pack_propagate(False)
        
        # 颜色预览背景
        self.preview_frame = ctk.CTkFrame(
            preview_container,
            fg_color=self.current_hex,
            corner_radius=15
        )
        self.preview_frame.place(relx=0.5, rely=0.5, relwidth=1, relheight=1, anchor="center")
        
        # 颜色选择按钮（完全融入背景）
        self.color_button = ctk.CTkButton(
            preview_container,
            image=self.color_palette_icon,
            text="",
            width=30,
            height=30,
            corner_radius=1,
            fg_color=self.current_hex,     # 使用当前颜色作为背景
            hover_color="#333333",         # 悬停时显示深灰色
            border_width=0,                # 无边框
            border_spacing=0,              # 移除内边距
            command=self.choose_color
        )
        self.color_button.place(relx=0.5, rely=0.5, anchor="center")
        
        # 绑定颜色更新事件
        self.hex_var.trace_add("write", self.update_button_color)
        
        # 输入区域，减少间距
        input_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=(0, 15))
        
        # 左侧Hex输入框
        hex_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        hex_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        hex_label = ctk.CTkLabel(
            hex_frame,
            text="Hex 值:",
            font=(FONT_FAMILY, 12),
            anchor="w"
        )
        hex_label.pack(fill="x", pady=(0, 5))
        
        self.hex_entry = ctk.CTkEntry(
            hex_frame,
            textvariable=self.hex_var,
            font=(FONT_FAMILY, 12),
            height=35
        )
        self.hex_entry.pack(fill="x")
        
        # 右侧透明度输入框
        alpha_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        alpha_frame.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        alpha_label = ctk.CTkLabel(
            alpha_frame,
            text="透明度:",
            font=(FONT_FAMILY, 12),
            anchor="w"
        )
        alpha_label.pack(fill="x", pady=(0, 5))
        
        self.alpha_entry = ctk.CTkEntry(
            alpha_frame,
            textvariable=self.alpha_var,
            font=(FONT_FAMILY, 12),
            height=35
        )
        self.alpha_entry.pack(fill="x")
        
        # 历史颜色和操作按钮容器
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=(0, 0))
        
        # 历史颜色区域（靠左）
        history_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        history_frame.pack(side="left")
        
        # 加载历史颜色记录
        self.load_and_show_history(history_frame)
        
        # 操作按钮（靠右）
        button_style = {
            "width": 35,     # 稍微减小按钮尺寸
            "height": 35,
            "corner_radius": 8,
            "fg_color": "#1a1a1a",
            "hover_color": "#333333",
            "border_width": 0,
            "text": ""
        }
        
        # 取消按钮
        ctk.CTkButton(
            bottom_frame,
            image=self.cancel_icon,
            command=self.dialog.destroy,
            **button_style
        ).pack(side="right", padx=(5, 0))
        
        # 确认按钮
        ctk.CTkButton(
            bottom_frame,
            image=self.confirm_icon,
            command=self.save_color,
            **button_style
        ).pack(side="right", padx=5)
        
        # 绑定输入框变化事件
        self.hex_var.trace_add("write", self.update_preview)
        
        # 设置对话框模态
        self.dialog.transient(master)
        self.dialog.grab_set()
        self.dialog.focus_set()
        
        # 修改这里，保存完整的回调函数和playlist_name
        self.master = master
        self.playlist_name = playlist_name
        self.save_callback = save_callback
        
    def parse_rgba(self, rgba_str):
        """从rgba字符串解析出r,g,b,a值"""
        try:
            # 如果是rgba格式
            if rgba_str.startswith('rgba'):
                values = rgba_str.strip('rgba()').split(',')
                r = int(values[0])
                g = int(values[1])
                b = int(values[2])
                a = float(values[3])
                return (r, g, b, a)
            # 如果是hex格式
            elif rgba_str.startswith('#'):
                hex_color = rgba_str.lstrip('#')
                r = int(hex_color[:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:], 16)
                return (r, g, b, self.DEFAULT_ALPHA)  # 使用默认透明度
            else:
                # 无效格式，返回默认值
                return (255, 255, 255, self.DEFAULT_ALPHA)
        except:
            # 解析失败时返回默认值
            return (255, 255, 255, self.DEFAULT_ALPHA)

    def rgba_to_hex(self, rgba_str):
        """将rgba字符串转换为hex格式"""
        r, g, b, _ = self.parse_rgba(rgba_str)
        return '#{:02x}{:02x}{:02x}'.format(r, g, b)

    def hex_to_rgba(self, hex_color, alpha):
        """将hex颜色转换为rgba格式"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:], 16)
        return f'rgba({r},{g},{b},{alpha})'

    def load_and_show_history(self, parent_frame):
        """加载并显示颜色历史记录"""
        try:
            with open('color_history.json', 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        except:
            history_data = {}
            
        history_colors = history_data.get(self.playlist_name, {}).get("history", [])
        
        # 创建历史颜色按钮
        for rgba_color in history_colors[:3]:
            hex_color = self.rgba_to_hex(rgba_color)  # 转换为hex用于显示
            preview = ctk.CTkFrame(
                parent_frame,
                width=20,
                height=20,
                fg_color=hex_color  # 使用hex格式
            )
            preview.pack(side="left", padx=2)
            
            # Hex值按钮（点击复制）
            def create_copy_command(hex_value):
                return lambda: self.copy_color(hex_value)
                
            ctk.CTkButton(
                parent_frame,
                text=hex_color,
                command=create_copy_command(hex_color),
                width=90,  # 缩短按钮宽度
                height=25,
                font=(FONT_FAMILY, 12)
            ).pack(side="left", padx=2)
            
    def copy_color(self, color):
        """复制颜色值到剪贴板"""
        pyperclip.copy(color)
        messagebox.showinfo("提示", "颜色值已复制到剪贴板")
        
    def save_color(self):
        """保存颜色设置"""
        try:
            hex_color = self.hex_var.get()
            if not hex_color.startswith('#'):
                hex_color = f"#{hex_color}"
            
            try:
                alpha = float(self.alpha_var.get())
                if not 0 <= alpha <= 1:
                    raise ValueError("透明度必须在0到1之间")
            except ValueError as e:
                messagebox.showerror("错误", f"无效的透明度值: {str(e)}")
                return
                
            # 转换为rgba格式用于保存
            rgba_color = self.hex_to_rgba(hex_color, alpha)
                
            # 更新历史记录
            try:
                with open('color_history.json', 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
            except:
                history_data = {}
                
            if self.playlist_name not in history_data:
                history_data[self.playlist_name] = {"history": []}
                
            history = history_data[self.playlist_name]["history"]
            if rgba_color in history:
                history.remove(rgba_color)
            history.insert(0, rgba_color)
            history_data[self.playlist_name]["history"] = history[:3]
            history_data[self.playlist_name]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 保存历史记录
            with open('color_history.json', 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=4)
            
            # 更新 config.json
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 更新对应歌单的颜色
                for level in config.get('levels', []):
                    if level['name'] == self.playlist_name:
                        level['color'] = rgba_color
                        break
                        
                # 保存更新后的配置
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"更新配置文件失败: {str(e)}")
                
            # 调用回调函数
            self.save_callback(self.playlist_name, rgba_color)
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存颜色失败: {str(e)}")
        
    def update_preview(self, *args):
        """更新颜色预览"""
        try:
            hex_color = self.hex_var.get()
            if not hex_color.startswith('#'):
                hex_color = f"#{hex_color}"
            if len(hex_color) == 7:  # 确保是有效的hex颜色值
                self.preview_frame.configure(fg_color=hex_color)  # 使用hex格式
        except:
            pass
            
    def choose_color(self):
        """打开系统颜色选择器"""
        color = colorchooser.askcolor(
            color=self.hex_var.get(),
            title="选择颜色"
        )
        if color[1]:
            self.hex_var.set(color[1])
            
    def update_button_color(self, *args):
        """更新颜色选择按钮的背景色"""
        try:
            hex_color = self.hex_var.get()
            if not hex_color.startswith('#'):
                hex_color = f"#{hex_color}"
            if len(hex_color) == 7:  # 确保是有效的hex颜色值
                self.preview_frame.configure(fg_color=hex_color)
                self.color_button.configure(fg_color=hex_color)  # 更新按钮背景色
        except:
            pass
            