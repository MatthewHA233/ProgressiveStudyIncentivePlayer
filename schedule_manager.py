import customtkinter as ctk
import os
import json
import shutil
from datetime import datetime, timedelta
from tkinter import messagebox, filedialog

class ScheduleManager(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # 加载配置
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                self.default_font = ctk.CTkFont(family=self.config.get('font', '微软雅黑'))
                self.title_font = ctk.CTkFont(family=self.config.get('font', '微软雅黑'), size=20, weight="bold")
                self.subtitle_font = ctk.CTkFont(family=self.config.get('font', '微软雅黑'), size=12)
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            self.default_font = ctk.CTkFont(family='微软雅黑')
            self.title_font = ctk.CTkFont(family='微软雅黑', size=20, weight="bold")
            self.subtitle_font = ctk.CTkFont(family='微软雅黑', size=12)
        
        self.create_ui()
        
    def create_ui(self):
        # 标题
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(10, 5))
        
        ctk.CTkLabel(
            title_frame,
            text="昼夜表管理",
            font=self.title_font
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="管理昼夜表文件和设置",
            font=self.subtitle_font,
            text_color="#888888"
        ).pack(anchor="w")
        
        # 分割线
        separator = ctk.CTkFrame(self, fg_color="#3B3B3B", height=2)
        separator.pack(fill="x", padx=20, pady=(5, 20))
        
        # 设置区域
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(fill="x", padx=20, pady=5)
        
        # 起始日期设置
        start_date_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        start_date_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            start_date_frame,
            text="起始日期:",
            font=self.default_font
        ).pack(side="left")
        
        # 创建一个带背景的框架来包含日期标签
        date_display_frame = ctk.CTkFrame(
            start_date_frame,
            fg_color="#2B2B2B",
            corner_radius=6,
            height=32
        )
        date_display_frame.pack(side="left", padx=10)
        
        # 在框架内显示日期
        self.start_date_label = ctk.CTkLabel(
            date_display_frame,
            text=self.config.get('start_date', ''),
            font=self.default_font,
            width=120,
            padx=10
        )
        self.start_date_label.pack(pady=5)
        
        ctk.CTkLabel(
            start_date_frame,
            text="(自动从第1周文件获取)",
            font=self.subtitle_font,
            text_color="#888888"
        ).pack(side="left", padx=5)
        
        # Excel目录设置
        excel_path_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        excel_path_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            excel_path_frame,
            text="昼夜表目录:",
            font=self.default_font
        ).pack(side="left")
        
        self.excel_path_entry = ctk.CTkEntry(
            excel_path_frame,
            font=self.default_font,
            width=400
        )
        self.excel_path_entry.pack(side="left", padx=10)
        self.excel_path_entry.insert(0, self.config.get('excel_path', ''))
        
        ctk.CTkButton(
            excel_path_frame,
            text="浏览",
            command=self.browse_excel_path,
            width=60,
            font=self.default_font
        ).pack(side="left")
        
        # 模板文件设置
        template_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        template_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            template_frame,
            text="模板文件:",
            font=self.default_font
        ).pack(side="left")
        
        self.template_path_entry = ctk.CTkEntry(
            template_frame,
            font=self.default_font,
            width=400
        )
        self.template_path_entry.pack(side="left", padx=10)
        self.template_path_entry.insert(0, self.config.get('template_path', ''))
        
        ctk.CTkButton(
            template_frame,
            text="浏览",
            command=self.browse_template_path,
            width=60,
            font=self.default_font
        ).pack(side="left")
        
        ctk.CTkButton(
            template_frame,
            text="打开",
            command=lambda: self.open_file(self.template_path_entry.get()),
            width=60,
            font=self.default_font
        ).pack(side="left", padx=5)
        
        # 操作按钮
        button_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(
            button_frame,
            text="保存设置",
            command=self.save_settings,
            font=self.default_font,
            fg_color="#4169E1",
            hover_color="#1E90FF"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="创建本周昼夜表",
            command=self.create_current_week_file,
            font=self.default_font,
            fg_color="#32CD32",
            hover_color="#228B22"
        ).pack(side="left", padx=5)
        
        # 文件列表标题
        files_title_frame = ctk.CTkFrame(self, fg_color="transparent")
        files_title_frame.pack(fill="x", padx=20, pady=(10, 2))
        
        ctk.CTkLabel(
            files_title_frame,
            text="文件列表",
            font=self.title_font
        ).pack(anchor="w")
        
        # 创建文件列表框架
        self.files_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#2B2B2B",
            height=300  # 增加高度以显示更多内容
        )
        self.files_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        # 更新文件列表
        self.update_file_list()
        
    def browse_excel_path(self):
        path = filedialog.askdirectory()
        if path:
            # 统一转换为正斜杠格式
            path = path.replace('\\', '/')
            self.excel_path_entry.delete(0, 'end')
            self.excel_path_entry.insert(0, path)
            
    def browse_template_path(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xls;*.xlsx")])
        if path:
            # 统一转换为正斜杠格式
            path = path.replace('\\', '/')
            self.template_path_entry.delete(0, 'end')
            self.template_path_entry.insert(0, path)
            
    def save_settings(self):
        try:
            # 自动更新起始日期
            start_date = self.get_start_date_from_files()
            if start_date:
                # 更新标签文本而不是输入框
                self.start_date_label.configure(text=start_date)
            
            # 更新配置
            self.config['start_date'] = self.start_date_label.cget("text")  # 从标签获取文本
            self.config['excel_path'] = self.excel_path_entry.get().replace('\\', '/')
            self.config['template_path'] = self.template_path_entry.get().replace('\\', '/')
            
            # 保存配置
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
                
            messagebox.showinfo("成功", "设置已保存")
            # 更新文件列表
            self.update_file_list()
        except ValueError:
            messagebox.showerror("错误", "请输入正确的日期格式 (YYYY-MM-DD)")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置时出错: {str(e)}")
            
    def create_current_week_file(self):
        try:
            # 获取当前日期
            today = datetime.now()
            start_date = datetime.strptime(self.config['start_date'], '%Y-%m-%d')
            
            # 计算周数
            days_difference = (today - start_date).days
            week_number = days_difference // 7 + 1
            
            # 计算本周日期范围
            start_of_week = start_date + timedelta(weeks=(week_number - 1))
            end_of_week = start_of_week + timedelta(days=6)
            
            # 生成文件名
            file_name = f"第{week_number}周({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')}).xls"
            target_path = os.path.join(self.excel_path_entry.get(), file_name).replace('\\', '/')
            template_path = self.template_path_entry.get().replace('\\', '/')
            
            # 检查文件是否已存在
            if os.path.exists(target_path):
                # 高亮显示已存在的文件（红色背景）
                self.update_file_list(highlight_file=file_name)
                messagebox.showwarning("警告", f"文件 {file_name} 已存在！")
                
                # 再次确认是否覆盖
                if messagebox.askyesno("确认覆盖", f"是否确定要覆盖 {file_name}？"):
                    shutil.copy2(template_path, target_path)
                    messagebox.showinfo("成功", f"已覆盖本周昼夜表：{file_name}")
                    # 更新文件列表，恢复正常显示
                    self.update_file_list()
                else:
                    # 更新文件列表，恢复正常显示
                    self.update_file_list()
            else:
                # 创建新文件
                shutil.copy2(template_path, target_path)
                messagebox.showinfo("成功", f"已创建本周昼夜表：{file_name}")
                # 更新文件列表
                self.update_file_list()
                
        except Exception as e:
            messagebox.showerror("错误", f"创建昼夜表时出错: {str(e)}")

    def update_file_list(self, highlight_file=None):
        # 清除现有列表
        for widget in self.files_frame.winfo_children():
            widget.destroy()
        
        try:
            current_week_file = self.get_current_week_filename()
            excel_path = self.excel_path_entry.get().replace('\\', '/')
            
            if os.path.exists(excel_path):
                # 修改文件过滤逻辑，只获取符合格式的文件
                files = [f for f in os.listdir(excel_path) if f.endswith('.xls') and f.startswith('第') and '周' in f]
                
                if not files:
                    # 如果目录为空，显示提示并添加创建按钮
                    message_frame = ctk.CTkFrame(self.files_frame, fg_color="transparent")
                    message_frame.pack(fill="x", pady=20, padx=20)
                    
                    ctk.CTkLabel(
                        message_frame,
                        text="目录为空，是否创建本周的昼夜表？",
                        font=self.default_font
                    ).pack(pady=(0, 10))
                    
                    ctk.CTkButton(
                        message_frame,
                        text="创建第一周昼夜表",
                        command=self.create_first_week_file,
                        font=self.default_font,
                        fg_color="#32CD32",
                        hover_color="#228B22"
                    ).pack()
                    return
                
                # 修改排序逻辑，添加错误处理
                def get_week_number(filename):
                    try:
                        return int(filename[filename.find('第')+1:filename.find('周')])
                    except ValueError:
                        return 0  # 对于无法解析的文件名返回0
                
                files.sort(key=get_week_number, reverse=True)
                
                # 创建3列布局
                columns_frame = ctk.CTkFrame(self.files_frame, fg_color="transparent")
                columns_frame.pack(fill="both", expand=True)
                
                # 创建三个列框架
                columns = [ctk.CTkFrame(columns_frame, fg_color="transparent") for _ in range(3)]
                for i, col in enumerate(columns):
                    col.grid(row=0, column=i, sticky="nsew", padx=2)
                    columns_frame.grid_columnconfigure(i, weight=1)
                
                # 分配文件到三列
                for i, file in enumerate(files):
                    col_idx = i % 3
                    
                    # 决定背景颜色
                    if file == highlight_file:
                        bg_color = "#FF4D4D"  # 红色背景用于警告
                    elif file == current_week_file:
                        bg_color = "#363636"  # 深灰色背景用于当前周
                    else:
                        bg_color = "transparent"
                    
                    file_frame = ctk.CTkFrame(
                        columns[col_idx],
                        fg_color=bg_color
                    )
                    file_frame.pack(fill="x", pady=1, padx=2)
                    
                    file_button = ctk.CTkButton(
                        file_frame,
                        text=file,
                        font=self.default_font,
                        fg_color="transparent",
                        text_color="#FFFFFF",
                        hover_color="#404040",
                        command=lambda f=file: self.open_file(os.path.join(excel_path, f).replace('\\', '/')),
                        anchor="w"
                    )
                    file_button.pack(fill="x", pady=1, padx=2)
                    
        except Exception as e:
            ctk.CTkLabel(
                self.files_frame,
                text=f"读取文件列表失败: {str(e)}",
                font=self.default_font,
                text_color="#FF6B6B"
            ).pack(pady=5)

    def get_current_week_filename(self):
        try:
            # 获取当前日期
            today = datetime.now()
            start_date = datetime.strptime(self.config['start_date'], '%Y-%m-%d')
            
            # 计算周数
            days_difference = (today - start_date).days
            week_number = days_difference // 7 + 1
            
            # 计算本周日期范围
            start_of_week = start_date + timedelta(weeks=(week_number - 1))
            end_of_week = start_of_week + timedelta(days=6)
            
            # 返回文件名
            return f"第{week_number}周({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')}).xls"
        except:
            return ""

    def get_start_date_from_files(self):
        try:
            excel_path = self.excel_path_entry.get().replace('\\', '/')
            if os.path.exists(excel_path):
                files = [f for f in os.listdir(excel_path) if f.endswith('.xls')]
                # 找到第1周的文件
                first_week_file = next((f for f in files if f.startswith('第1周')), None)
                if first_week_file:
                    # 从文件名解析日期，例如 "第1周(9.23~9.29).xls"
                    date_str = first_week_file[first_week_file.find('(')+1:first_week_file.find('~')]
                    month, day = date_str.split('.')
                    year = datetime.now().year
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except Exception as e:
            print(f"获取起始日期失败: {str(e)}")
        return self.config.get('start_date', '')

    def open_file(self, file_path):
        """打开文件的通用函数"""
        try:
            os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("错误", f"打开文件失败: {str(e)}")

    def create_first_week_file(self):
        """当目录为空时创建第一周的昼夜表"""
        try:
            # 获取本周的周一和周日日期
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            
            # 生成文件名
            file_name = f"第1周({monday.strftime('%m.%d')}~{sunday.strftime('%m.%d')}).xls"
            target_path = os.path.join(self.excel_path_entry.get(), file_name).replace('\\', '/')
            template_path = self.template_path_entry.get().replace('\\', '/')
            
            # 复制模板文件
            shutil.copy2(template_path, target_path)
            messagebox.showinfo("成功", f"已创建第一周昼夜表：{file_name}")
            
            # 更新起始日期为本周一
            self.start_date_label.configure(text=monday.strftime('%Y-%m-%d'))
            
            # 保存配置并更新文件列表
            self.save_settings()
            
        except Exception as e:
            messagebox.showerror("错误", f"创建第一周昼夜表时出错: {str(e)}")