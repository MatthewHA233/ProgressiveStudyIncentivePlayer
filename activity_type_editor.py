import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import customtkinter as ctk
import cv2
import numpy as np
import threading
import ADBHelper
from PIL import Image, ImageTk

class PointMarkTool(ctk.CTkToplevel):
    def __init__(self, parent, device_id=None, callback=None):
        super().__init__(parent)
        
        self.title("标点工具")
        # 初始窗口大小，后续会根据截图调整
        self.geometry("800x800")
        
        # 设置深色主题
        ctk.set_appearance_mode("dark")
        
        # 回调函数，用于返回坐标
        self.callback = callback
        
        # 设备ID
        self.device_id = device_id
        if not self.device_id:
            # 获取设备列表
            devices = ADBHelper.getDevicesList()
            if devices:
                self.device_id = devices[0]
            else:
                messagebox.showerror("错误", "未找到连接的设备，请确保手机已连接并开启USB调试")
                self.destroy()
                return
        
        # 缩放比例
        self.scale = 0.5
        
        # 点击标记列表
        self.markers = []
        
        # 加载字体
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.default_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=14)
                self.button_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=12)
        except Exception as e:
            print(f"加载字体配置失败: {str(e)}")
            # 使用默认字体
            self.default_font = ctk.CTkFont(family='微软雅黑', size=14)
            self.button_font = ctk.CTkFont(family='微软雅黑', size=12)
        
        # 创建界面
        self.create_widgets()
        
        # 将窗口置于前台
        self.lift()
        self.focus_force()
        
        # 截图并显示
        self.capture_and_show()
    
    def create_widgets(self):
        # 创建主框架
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 创建顶部控制区
        control_frame = ctk.CTkFrame(self.main_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # 按钮区域 - 左侧
        button_area = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_area.pack(side="left", fill="y")
        
        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            button_area,
            text="刷新截图",
            command=self.capture_and_show,
            font=self.button_font,
            width=80,
            height=30
        )
        refresh_btn.pack(side="left", padx=10)
        
        # 清除标记按钮
        clear_btn = ctk.CTkButton(
            button_area,
            text="清除标记",
            command=self.clear_markers,
            font=self.button_font,
            fg_color="#FF8C00",
            hover_color="#FF7F24",
            width=80,
            height=30
        )
        clear_btn.pack(side="left", padx=10)
        
        # 关闭按钮
        close_btn = ctk.CTkButton(
            button_area,
            text="关闭",
            command=self.destroy,
            font=self.button_font,
            fg_color="#FF4D4D",
            hover_color="#DC143C",
            width=80,
            height=30
        )
        close_btn.pack(side="left", padx=10)
        
        # 坐标显示标签
        self.coord_label = ctk.CTkLabel(
            control_frame,
            text="坐标: 点击图片获取坐标",
            font=self.default_font
        )
        self.coord_label.pack(side="right", padx=20)
        
        # 创建图片显示区
        self.image_frame = ctk.CTkFrame(self.main_frame)
        self.image_frame.pack(fill="both", expand=True)
        
        # 使用传统的Canvas，因为CTk没有提供Canvas控件
        self.canvas_frame = tk.Frame(self.image_frame, bg="#2B2B2B")
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建Canvas用于显示图片
        self.canvas = tk.Canvas(self.canvas_frame, bg="#1A1A1A", highlightthickness=0)
        
        # 添加滚动条
        h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        
        # 配置滚动条样式
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Vertical.TScrollbar", background="#2B2B2B", troughcolor="#1A1A1A", arrowcolor="white")
        style.configure("Horizontal.TScrollbar", background="#2B2B2B", troughcolor="#1A1A1A", arrowcolor="white")
        
        self.canvas.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # 布局
        h_scrollbar.pack(side="bottom", fill="x")
        v_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        
        # 绑定鼠标滚轮事件
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)    # Linux上滚
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)    # Linux下滚
    
    def on_mouse_wheel(self, event):
        """处理鼠标滚轮事件"""
        # 确定滚动方向和数量
        if event.num == 4 or event.delta > 0:
            # 向上滚动
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            # 向下滚动
            self.canvas.yview_scroll(1, "units")
    
    def on_mouse_move(self, event):
        """处理鼠标移动事件，显示当前坐标"""
        if hasattr(self, 'display_img'):
            x, y = event.x, event.y
            real_x = int(x / self.scale)
            real_y = int(y / self.scale)
            self.coord_label.configure(text=f"坐标: ({real_x}, {real_y})")
    
    def clear_markers(self):
        """清除所有标记点"""
        self.markers = []
        if hasattr(self, 'display_img') and hasattr(self, 'tk_img'):
            # 重新显示原始图片
            self.tk_img = ImageTk.PhotoImage(image=Image.fromarray(self.display_img))
            self._update_canvas(self.display_img.shape[1], self.display_img.shape[0])
    
    def capture_and_show(self):
        """截图并显示"""
        try:
            # 显示加载中
            self.canvas.delete("all")
            self.canvas.create_text(400, 300, text="正在截图...", fill="white", font=("微软雅黑", 16))
            self.update()
            
            # 在新线程中执行截图，避免界面卡顿
            threading.Thread(target=self._do_capture_and_show).start()
        except Exception as e:
            messagebox.showerror("错误", f"截图失败: {str(e)}")
    
    def _do_capture_and_show(self):
        """实际执行截图并显示的函数"""
        try:
            # 截图
            temp_file = "temp_screenshot.png"
            ADBHelper.screenCapture(self.device_id, temp_file)
            
            if os.path.exists(temp_file):
                # 读取图片
                self.img_source = cv2.imread(temp_file)
                if self.img_source is None:
                    self.after(0, lambda: messagebox.showerror("错误", "无法读取截图"))
                    return
                
                # 转换颜色空间
                self.img_source = cv2.cvtColor(self.img_source, cv2.COLOR_BGR2RGB)
                
                # 获取原始尺寸
                h_src, w_src = self.img_source.shape[:2]
                
                # 计算缩放后的尺寸
                new_w = int(w_src * self.scale)
                new_h = int(h_src * self.scale)
                
                # 调整窗口大小，考虑屏幕尺寸限制
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()
                
                # 窗口宽度完全自适应图像宽度，高度稍大一些
                window_width = min(new_w, int(screen_width * 0.9))
                window_height = min(new_h + 200, int(screen_height * 0.9))
                
                # 计算窗口位置 - 确保不被主窗口遮挡
                parent_x = self.master.winfo_rootx()
                parent_y = self.master.winfo_rooty()
                parent_width = self.master.winfo_width()
                parent_height = self.master.winfo_height()
                
                # 尝试将窗口放在主窗口上方
                pos_x = max(0, parent_x + (parent_width - window_width) // 2)
                pos_y = max(0, parent_y - window_height - 30)  # 30像素的间距
                
                # 如果上方放不下，则放在右侧
                if pos_y < 0:
                    pos_x = min(parent_x + parent_width + 30, screen_width - window_width)
                    pos_y = max(0, parent_y + (parent_height - window_height) // 2)
                
                # 如果右侧也放不下，则放在下方
                if pos_x + window_width > screen_width:
                    pos_x = max(0, parent_x + (parent_width - window_width) // 2)
                    pos_y = min(parent_y + parent_height + 30, screen_height - window_height)
                
                # 设置窗口大小和位置
                self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
                
                # 调整图片大小
                self.display_img = cv2.resize(self.img_source, (new_w, new_h))
                
                # 清除标记
                self.markers = []
                
                # 转换为PhotoImage
                self.tk_img = ImageTk.PhotoImage(image=Image.fromarray(self.display_img))
                
                # 在Canvas上显示图片
                self.after(0, lambda: self._update_canvas(new_w, new_h))
                
                # 删除临时文件
                try:
                    os.remove(temp_file)
                except:
                    pass
                
                # 确保窗口在前台
                self.after(100, self.lift)
                self.after(100, self.focus_force)
            else:
                self.after(0, lambda: messagebox.showerror("错误", "截图失败，未生成图片文件"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("错误", f"处理截图时出错: {str(e)}"))
    
    def _update_canvas(self, img_width, img_height):
        """更新Canvas显示图片"""
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        
        # 设置Canvas的滚动区域
        self.canvas.config(scrollregion=(0, 0, img_width, img_height))
        
        # 更新Canvas的大小
        canvas_frame_width = self.canvas_frame.winfo_width()
        canvas_frame_height = self.canvas_frame.winfo_height()
        
        # 确保Canvas能够正确显示和滚动
        self.canvas.config(width=min(img_width, canvas_frame_width-20), 
                           height=min(img_height, canvas_frame_height-20))
        
        # 重新绘制所有标记点
        for marker in self.markers:
            x, y, real_x, real_y = marker
            self._draw_marker(x, y, real_x, real_y)
    
    def _draw_marker(self, x, y, real_x, real_y):
        """在Canvas上绘制标记点"""
        # 绘制外圈
        self.canvas.create_oval(x-10, y-10, x+10, y+10, outline="#FF4500", width=2)
        # 绘制内圈
        self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="#FF4500")
        # 绘制坐标文本
        self.canvas.create_text(x+15, y-15, text=f"({real_x}, {real_y})", 
                               fill="#FFFFFF", font=("微软雅黑", 10))
    
    def on_click(self, event):
        """处理鼠标点击事件"""
        if not hasattr(self, 'display_img'):
            return
        
        # 获取点击位置
        x, y = event.x, event.y
        
        # 计算实际坐标（考虑缩放）
        real_x = int(x / self.scale)
        real_y = int(y / self.scale)
        
        # 更新坐标显示
        self.coord_label.configure(text=f"坐标: ({real_x}, {real_y})")
        
        # 添加到标记列表
        self.markers.append((x, y, real_x, real_y))
        
        # 在Canvas上绘制标记
        self._draw_marker(x, y, real_x, real_y)
        
        # 弹出确认对话框
        if messagebox.askyesno("确认", f"是否使用坐标 ({real_x}, {real_y})？"):
            if self.callback:
                self.callback(real_x, real_y)
                # 只有在用户确认使用坐标时，才将父窗口置顶
                self.master.after(100, self.master.lift)
                self.master.after(100, self.master.focus_force)
            self.destroy()
        # 如果用户点击"否"，不做任何窗口层级的改变，保持当前窗口在前台
        else:
            # 确保标点工具仍然在前台
            self.after(100, self.lift)
            self.after(100, self.focus_force)

class ActivityTypeEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 设置窗口
        self.title("事情类型编辑器")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        
        # 加载字体配置
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.default_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=16)
                self.title_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=24, weight="bold")
                self.button_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=14)
        except Exception as e:
            print(f"加载字体配置失败: {str(e)}")
            # 使用默认字体
            self.default_font = ctk.CTkFont(family='微软雅黑', size=16)
            self.title_font = ctk.CTkFont(family='微软雅黑', size=24, weight="bold")
            self.button_font = ctk.CTkFont(family='微软雅黑', size=14)
        
        # 事情类型JSON文件路径
        self.json_file = "activity_types.json"
        
        # 创建主框架
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        ctk.CTkLabel(
            self.main_frame,
            text="事情类型及坐标管理",
            font=self.title_font
        ).pack(pady=(0, 20))
        
        # 创建上下分栏
        self.create_list_frame()
        self.create_action_frame()
        
        # 加载事情类型数据
        self.load_activity_types()
    
    def create_list_frame(self):
        """创建事情类型列表框架"""
        list_frame = ctk.CTkFrame(self.main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # 创建表格
        columns = ("事情类型", "坐标X", "坐标Y")
        
        # 创建Treeview
        self.tree_frame = ctk.CTkFrame(list_frame)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 使用传统的ttk.Treeview，因为CTk没有提供表格控件
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2B2B2B", 
                        foreground="white", 
                        fieldbackground="#2B2B2B",
                        font=('微软雅黑', 12))
        style.configure("Treeview.Heading", 
                        background="#3B3B3B", 
                        foreground="white",
                        font=('微软雅黑', 12, 'bold'))
        style.map('Treeview', background=[('selected', '#4169E1')])
        
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        
        # 设置第一列宽度更大
        self.tree.column("事情类型", width=300)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        
        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
    
    def create_action_frame(self):
        """创建操作按钮框架"""
        action_frame = ctk.CTkFrame(self.main_frame)
        action_frame.pack(fill="x", pady=(0, 10))
        
        # 创建输入框和按钮
        input_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=10)
        
        # 事情类型输入
        type_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            type_frame,
            text="事情类型:",
            font=self.default_font,
            width=100
        ).pack(side="left", padx=(0, 10))
        
        self.type_entry = ctk.CTkEntry(
            type_frame,
            font=self.default_font,
            width=300
        )
        self.type_entry.pack(side="left", fill="x", expand=True)
        
        # 坐标输入
        coord_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        coord_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            coord_frame,
            text="坐标 (X,Y):",
            font=self.default_font,
            width=100
        ).pack(side="left", padx=(0, 10))
        
        self.x_entry = ctk.CTkEntry(
            coord_frame,
            font=self.default_font,
            width=100,
            placeholder_text="X"
        )
        self.x_entry.pack(side="left", padx=(0, 5))
        
        ctk.CTkLabel(
            coord_frame,
            text=",",
            font=self.default_font
        ).pack(side="left")
        
        self.y_entry = ctk.CTkEntry(
            coord_frame,
            font=self.default_font,
            width=100,
            placeholder_text="Y"
        )
        self.y_entry.pack(side="left", padx=(5, 0))
        
        # 使用ADB标点工具按钮
        self.mark_button = ctk.CTkButton(
            coord_frame,
            text="使用标点工具",
            font=self.button_font,
            command=self.open_mark_tool,
            fg_color="#4169E1",
            hover_color="#1E90FF",
            width=120
        )
        self.mark_button.pack(side="left", padx=20)
        
        # 按钮框架
        button_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)
        
        # 添加按钮
        self.add_button = ctk.CTkButton(
            button_frame,
            text="添加",
            font=self.button_font,
            command=self.add_activity_type,
            fg_color="#32CD32",
            hover_color="#228B22",
            width=120
        )
        self.add_button.pack(side="left", padx=10)
        
        # 更新按钮
        self.update_button = ctk.CTkButton(
            button_frame,
            text="更新",
            font=self.button_font,
            command=self.update_activity_type,
            fg_color="#FF8C00",
            hover_color="#FF7F24",
            width=120,
            state="disabled"
        )
        self.update_button.pack(side="left", padx=10)
        
        # 删除按钮
        self.delete_button = ctk.CTkButton(
            button_frame,
            text="删除",
            font=self.button_font,
            command=self.delete_activity_type,
            fg_color="#FF4D4D",
            hover_color="#DC143C",
            width=120,
            state="disabled"
        )
        self.delete_button.pack(side="left", padx=10)
        
        # 清空按钮
        self.clear_button = ctk.CTkButton(
            button_frame,
            text="清空输入",
            font=self.button_font,
            command=self.clear_inputs,
            fg_color="#9370DB",
            hover_color="#8A2BE2",
            width=120
        )
        self.clear_button.pack(side="left", padx=10)
        
        # 保存按钮
        self.save_button = ctk.CTkButton(
            button_frame,
            text="保存到文件",
            font=self.button_font,
            command=self.save_to_file,
            fg_color="#4682B4",
            hover_color="#4169E1",
            width=120
        )
        self.save_button.pack(side="right", padx=10)
    
    def load_activity_types(self):
        """从JSON文件加载事情类型数据"""
        try:
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    self.activity_types = json.load(f)
                
                # 清空表格
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                # 添加数据到表格
                for activity_type, data in self.activity_types.items():
                    point = data.get("point", [0, 0])
                    self.tree.insert("", "end", values=(activity_type, point[0], point[1]))
            else:
                self.activity_types = {}
                messagebox.showinfo("提示", f"未找到事情类型文件 {self.json_file}，将创建新文件。")
        except Exception as e:
            messagebox.showerror("错误", f"加载事情类型数据失败: {str(e)}")
            self.activity_types = {}
    
    def on_item_select(self, event):
        """处理表格项选择事件"""
        selected_items = self.tree.selection()
        if selected_items:
            item = selected_items[0]
            values = self.tree.item(item, "values")
            
            # 填充输入框
            self.type_entry.delete(0, "end")
            self.type_entry.insert(0, values[0])
            
            self.x_entry.delete(0, "end")
            self.x_entry.insert(0, values[1])
            
            self.y_entry.delete(0, "end")
            self.y_entry.insert(0, values[2])
            
            # 启用更新和删除按钮
            self.update_button.configure(state="normal")
            self.delete_button.configure(state="normal")
    
    def add_activity_type(self):
        """添加新的事情类型"""
        activity_type = self.type_entry.get().strip()
        try:
            x = int(self.x_entry.get().strip())
            y = int(self.y_entry.get().strip())
        except ValueError:
            messagebox.showerror("错误", "坐标必须是整数")
            return
        
        if not activity_type:
            messagebox.showerror("错误", "事情类型不能为空")
            return
        
        # 检查是否已存在
        if activity_type in self.activity_types:
            messagebox.showerror("错误", f"事情类型 '{activity_type}' 已存在")
            return
        
        # 添加到数据
        self.activity_types[activity_type] = {"point": [x, y]}
        
        # 添加到表格
        self.tree.insert("", "end", values=(activity_type, x, y))
        
        # 清空输入
        self.clear_inputs()
        
        messagebox.showinfo("成功", f"已添加事情类型: {activity_type}")
    
    def update_activity_type(self):
        """更新选中的事情类型"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("错误", "请先选择一个事情类型")
            return
        
        item = selected_items[0]
        old_values = self.tree.item(item, "values")
        old_type = old_values[0]
        
        new_type = self.type_entry.get().strip()
        try:
            x = int(self.x_entry.get().strip())
            y = int(self.y_entry.get().strip())
        except ValueError:
            messagebox.showerror("错误", "坐标必须是整数")
            return
        
        if not new_type:
            messagebox.showerror("错误", "事情类型不能为空")
            return
        
        # 如果类型名称改变，需要删除旧的并添加新的
        if old_type != new_type:
            # 检查新名称是否已存在
            if new_type in self.activity_types:
                messagebox.showerror("错误", f"事情类型 '{new_type}' 已存在")
                return
            
            # 删除旧的
            del self.activity_types[old_type]
        
        # 更新数据
        self.activity_types[new_type] = {"point": [x, y]}
        
        # 更新表格
        self.tree.item(item, values=(new_type, x, y))
        
        # 清空输入并禁用按钮
        self.clear_inputs()
        
        messagebox.showinfo("成功", f"已更新事情类型: {new_type}")
    
    def delete_activity_type(self):
        """删除选中的事情类型"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("错误", "请先选择一个事情类型")
            return
        
        item = selected_items[0]
        values = self.tree.item(item, "values")
        activity_type = values[0]
        
        # 确认删除
        if not messagebox.askyesno("确认", f"确定要删除事情类型 '{activity_type}' 吗？"):
            return
        
        # 从数据中删除
        if activity_type in self.activity_types:
            del self.activity_types[activity_type]
        
        # 从表格中删除
        self.tree.delete(item)
        
        # 清空输入并禁用按钮
        self.clear_inputs()
        
        messagebox.showinfo("成功", f"已删除事情类型: {activity_type}")
    
    def clear_inputs(self):
        """清空输入框并禁用按钮"""
        self.type_entry.delete(0, "end")
        self.x_entry.delete(0, "end")
        self.y_entry.delete(0, "end")
        
        self.update_button.configure(state="disabled")
        self.delete_button.configure(state="disabled")
    
    def save_to_file(self):
        """保存数据到JSON文件"""
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.activity_types, f, ensure_ascii=False, indent=4)
            
            messagebox.showinfo("成功", f"已保存数据到文件: {self.json_file}")
        except Exception as e:
            messagebox.showerror("错误", f"保存数据失败: {str(e)}")
    
    def open_mark_tool(self):
        """打开简化版标点工具"""
        try:
            # 获取设备ID
            devices = ADBHelper.getDevicesList()
            if not devices:
                messagebox.showerror("错误", "未找到连接的设备，请确保手机已连接并开启USB调试")
                return
            
            device_id = devices[0]
            
            # 打开标点工具
            mark_tool = PointMarkTool(self, device_id, self.set_coordinates)
            
            # 确保标点工具窗口在前台
            self.after(200, mark_tool.lift)
            self.after(200, mark_tool.focus_force)
            
            # 不再主动将父窗口置顶，让用户完成标点操作
        except Exception as e:
            messagebox.showerror("错误", f"启动标点工具失败: {str(e)}")
    
    def set_coordinates(self, x, y):
        """设置坐标到输入框"""
        self.x_entry.delete(0, "end")
        self.x_entry.insert(0, str(x))
        
        self.y_entry.delete(0, "end")
        self.y_entry.insert(0, str(y))
        
        # 确保窗口在前台
        self.lift()
        self.focus_force()
        
        messagebox.showinfo("成功", f"已获取坐标: ({x}, {y})")

if __name__ == "__main__":
    app = ActivityTypeEditor()
    app.mainloop() 