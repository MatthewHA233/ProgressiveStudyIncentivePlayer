import os
import sys
import subprocess
import time
import threading
import argparse
from datetime import datetime, timedelta
import json
import customtkinter as ctk
import cell_time_mapping
from plyer import notification
import win32com.client as win32
import csv

# 设置 customtkinter 外观
ctk.set_appearance_mode("System")  # 系统主题
ctk.set_default_color_theme("blue")  # 蓝色主题

class DayNightTableLogger:
    def __init__(self, test_mode=False):
        self.config = self.load_config()
        self.excel_file = self.get_current_week_file()
        self.running = True
        self.window = None
        self.current_cell = None
        self.test_mode = test_mode
        self.excel = None  # Excel应用程序实例
        self.activity_types = self.load_activity_types()  # 加载活动类型
        self.last_activity_type = None  # 记录上次选择的活动类型

    def load_config(self):
        """读取配置文件"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            print("错误：找不到配置文件 config.json")
            sys.exit(1)
        except json.JSONDecodeError:
            print("错误：配置文件格式错误")
            sys.exit(1)

    def get_current_week_file(self):
        """获取当前周的Excel文件路径"""
        # 获取当前日期
        today = datetime.now()
        
        # 从配置文件读取起始日期
        start_date = datetime.strptime(self.config['start_date'], '%Y-%m-%d')
        
        # 计算从起始日期到当前日期的天数
        days_difference = (today - start_date).days
        
        # 计算当前是第几周，向上取整
        week_number = days_difference // 7 + 1
        
        # 计算这一周的开始日期（周一）和结束日期（周日）
        start_of_week = start_date + timedelta(weeks=(week_number - 1))
        end_of_week = start_of_week + timedelta(days=6)
        
        # 格式化文件名，使用正斜杠
        file_name = f"第{week_number}周({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')}).xls"
        file_path = os.path.join(self.config['excel_path'], file_name).replace('\\', '/')
        
        # 获取绝对路径
        abs_path = os.path.abspath(file_path)
        print(f"已找到文件: {abs_path}")
        return abs_path

    def update_excel(self, symbol):
        """使用win32com更新Excel文件中的单元格"""
        excel_app = None
        workbook = None
        
        try:
            # 获取单元格坐标
            column, row = self.current_cell
            print(f"准备更新单元格: {column}{row}")
            
            # 如果是"none"符号，不进行Excel操作，直接返回
            if symbol == "none":
                print(f"已选择不填写单元格 {column}{row}")
                notification.notify(
                    title="昼夜表记录",
                    message=f"已选择不填写单元格 {column}{row}",
                    app_name="昼夜表自动记录工具",
                    timeout=5
                )
                return
            
            # 每次创建新的Excel应用程序实例，避免使用可能已损坏的实例
            excel_app = win32.Dispatch("Excel.Application")
            excel_app.Visible = False  # 不显示Excel窗口
            excel_app.DisplayAlerts = False  # 不显示警告
            
            # 打开工作簿
            print(f"正在打开工作簿: {self.excel_file}")
            workbook = excel_app.Workbooks.Open(self.excel_file)
            worksheet = workbook.Worksheets(1)  # 第一个工作表
            
            # 根据按钮更新单元格内容
            cell_value = None
            if symbol == "star":
                cell_value = "★"
            elif symbol == "empty_star":
                cell_value = "☆"
            
            # 更新单元格
            col_index = cell_time_mapping.get_column_index(column)
            print(f"更新单元格: 行={row}, 列={col_index} ({column}{row})")
            cell = worksheet.Cells(row, col_index)
            cell.Value = cell_value
            
            # 保存并关闭工作簿
            workbook.Save()
            print(f"已保存工作簿")
            workbook.Close(SaveChanges=True)
            print(f"已关闭工作簿")
            
            # 关闭Excel应用程序
            excel_app.Quit()
            print(f"已关闭Excel应用程序")
            
            # 释放COM对象
            del cell
            del worksheet
            del workbook
            del excel_app
            
            print(f"已更新单元格 {column}{row} 为 {symbol}")
            
            # 显示通知
            notification.notify(
                title="昼夜表已更新",
                message=f"单元格 {column}{row} 已更新为 {symbol}",
                app_name="昼夜表自动记录工具",
                timeout=5
            )
            
        except Exception as e:
            print(f"更新Excel时出错: {e}")
            try:
                # 确保column和row已定义
                if hasattr(self, 'current_cell') and self.current_cell:
                    column, row = self.current_cell
                    notification.notify(
                        title="昼夜表更新失败",
                        message=f"更新单元格 {column}{row} 时出错: {e}",
                        app_name="昼夜表自动记录工具",
                        timeout=5
                    )
                else:
                    notification.notify(
                        title="昼夜表更新失败",
                        message=f"更新Excel时出错: {e}",
                        app_name="昼夜表自动记录工具",
                        timeout=5
                    )
            except Exception as notify_error:
                print(f"发送通知时出错: {notify_error}")
        finally:
            # 确保资源被释放
            try:
                # 尝试关闭工作簿
                if workbook is not None:
                    try:
                        workbook.Close(SaveChanges=False)
                        print("在finally块中关闭了工作簿")
                    except:
                        pass
                
                # 尝试退出Excel应用程序
                if excel_app is not None:
                    try:
                        excel_app.Quit()
                        print("在finally块中退出了Excel应用程序")
                    except:
                        pass
                
                # 强制垃圾回收
                import gc
                gc.collect()
            except:
                pass
    
    def __del__(self):
        """析构函数，确保资源被正确释放"""
        try:
            # 确保Excel应用程序被关闭
            if self.excel:
                self.excel.Quit()
                self.excel = None
            
            # 确保窗口被关闭
            if self.window:
                self.window.quit()
                self.window.destroy()
                self.window = None
        except:
            pass
    
    def get_next_five_minute_time(self):
        """获取下一个5分钟整点时间"""
        now = datetime.now()
        minutes = now.minute
        
        # 计算到下一个5分钟的时间
        next_five_min = 5 - (minutes % 5)
        if next_five_min == 5:
            next_five_min = 0
        
        # 计算下一个5分钟整点
        next_time = now + timedelta(minutes=next_five_min)
        next_time = next_time.replace(second=0, microsecond=0)
        
        # 确保时间在昼夜表范围内
        weekday = next_time.weekday()
        if not cell_time_mapping.get_cell_for_time(next_time.time(), weekday):
            # 如果不在范围内，使用一个有效的时间
            valid_times = [
                now.replace(hour=6, minute=5, second=0),  # 早上6:05
                now.replace(hour=15, minute=5, second=0)  # 下午15:05
            ]
            next_time = min(valid_times, key=lambda x: abs((x - now).total_seconds()))
            print(f"调整为有效时间: {next_time.strftime('%H:%M')}")
        
        return next_time
    
    def load_activity_types(self):
        """加载活动类型列表"""
        try:
            # 检查活动类型配置文件是否存在
            activity_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "activity_types.json")
            if not os.path.exists(activity_file):
                # 如果不存在，创建默认配置，包含坐标点信息
                default_types = {
                    "React学习": {"point": [928, 485]},
                    "博客学习": {"point": [935, 742]},
                    "学习工具探究": {"point": [938, 839]},
                    "学Python": {"point": [932, 942]},
                    "实质思考": {"point": [938, 1048]}
                }
                with open(activity_file, 'w', encoding='utf-8') as f:
                    json.dump(default_types, f, ensure_ascii=False, indent=4)
                return list(default_types.keys())  # 返回活动类型名称列表
            
            # 如果存在，读取配置
            with open(activity_file, 'r', encoding='utf-8') as f:
                activity_data = json.load(f)
            
            # 检查是否是旧格式（纯列表）
            if isinstance(activity_data, list):
                # 转换为新格式
                new_format = {}
                for activity in activity_data:
                    new_format[activity] = {"point": [0, 0]}  # 默认坐标
                
                # 保存新格式
                with open(activity_file, 'w', encoding='utf-8') as f:
                    json.dump(new_format, f, ensure_ascii=False, indent=4)
                
                return activity_data  # 返回原始列表
            else:
                # 已经是新格式，返回键列表
                activity_types = list(activity_data.keys())
                
                # 确保至少有一个活动类型
                if not activity_types:
                    default_type = {"React学习": {"point": [928, 485]}}
                    with open(activity_file, 'w', encoding='utf-8') as f:
                        json.dump(default_type, f, ensure_ascii=False, indent=4)
                    activity_types = list(default_type.keys())
                
                return activity_types
            
        except Exception as e:
            print(f"加载活动类型时出错: {e}")
            # 返回默认值
            return ["React学习", "博客学习", "学习工具探究", "学Python", "实质思考"]

    def create_window(self, test_time=None):
        """创建选择窗口"""
        try:
            if self.window is not None:
                self.window.quit()  # 停止已存在窗口的mainloop
                self.window.destroy()
            
            # 从配置中获取字体
            font_name = self.config.get('font', 'Arial')
            
            self.window = ctk.CTk()
            self.window.title("昼夜表记录")
            
            # 设置更亮的外观
            ctk.set_appearance_mode("light")  # 使用亮色主题
            ctk.set_default_color_theme("blue")  # 使用蓝色主题
            
            # 获取当前时间或测试时间
            if test_time:
                now = test_time
            else:
                now = datetime.now()
            
            time_str = now.strftime("%H:%M")
            
            # 获取单元格坐标
            weekday = now.weekday()  # 0是周一，6是周日
            self.current_cell = cell_time_mapping.get_cell_for_time(now.time(), weekday)
            
            if not self.current_cell:
                print(f"当前时间 {time_str} 不在昼夜表范围内")
                if self.test_mode:
                    # 在测试模式下，如果当前时间不在范围内，使用下一个有效时间
                    test_times = [
                        datetime.now().replace(hour=6, minute=5, second=0),  # 早上6:05
                        datetime.now().replace(hour=15, minute=5, second=0)  # 下午15:05
                    ]
                    
                    # 选择最接近当前时间的有效时间
                    now = min(test_times, key=lambda x: abs((x - datetime.now()).total_seconds()))
                    time_str = now.strftime("%H:%M")
                    weekday = now.weekday()
                    self.current_cell = cell_time_mapping.get_cell_for_time(now.time(), weekday)
                    
                    if not self.current_cell:
                        print(f"测试模式下也无法找到有效单元格，退出")
                        self.window.destroy()
                        return
                else:
                    self.window.destroy()
                    return
            
            column, row = self.current_cell
            
            # 创建主标签 - 当前时间
            ctk.CTkLabel(
                self.window, 
                text=f"当前时间: {time_str}", 
                font=(font_name, 16, "bold"),  # 使用配置的字体
                text_color="#1E88E5"  # 使用蓝色文本
            ).pack(pady=(10, 0))
            
            # 创建单元格标签 - 使用较小的字体和较淡的颜色
            ctk.CTkLabel(
                self.window, 
                text=f"单元格: {column}{row}", 
                font=(font_name, 12),  # 较小的字体
                text_color="#9E9E9E"  # 较淡的灰色
            ).pack(pady=(0, 5))
            
            # 创建活动类型下拉框
            ctk.CTkLabel(
                self.window, 
                text="事情类型:", 
                font=(font_name, 14),
                text_color="#333333"  # 深灰色文本
            ).pack(pady=(5, 0))
            
            # 创建StringVar来存储选择的活动类型
            self.activity_var = ctk.StringVar()
            
            # 设置默认值为上次选择的活动类型或第一个活动类型
            if self.last_activity_type and self.last_activity_type in self.activity_types:
                self.activity_var.set(self.last_activity_type)
            else:
                self.activity_var.set(self.activity_types[0])
            
            # 创建下拉框
            activity_dropdown = ctk.CTkComboBox(
                self.window,
                values=self.activity_types,
                variable=self.activity_var,
                width=220,  # 增加宽度
                font=(font_name, 12),  # 使用配置的字体
                border_color="#1E88E5",  # 蓝色边框
                button_color="#1E88E5",  # 蓝色按钮
                dropdown_hover_color="#42A5F5"  # 浅蓝色悬停效果
            )
            activity_dropdown.pack(pady=5)
            
            ctk.CTkLabel(
                self.window, 
                text="请选择完成状态:", 
                font=(font_name, 14),
                text_color="#333333"  # 深灰色文本
            ).pack(pady=5)
            
            # 创建按钮框架
            button_frame = ctk.CTkFrame(self.window, fg_color="transparent")
            button_frame.pack(pady=10)
            
            # 创建按钮 - 增加宽度
            ctk.CTkButton(
                button_frame, 
                text="✓", 
                font=(font_name, 20, "bold"),
                width=80,  # 增加宽度
                height=35,  # 稍微减少高度
                fg_color="#4CAF50",  # 绿色背景
                hover_color="#388E3C",  # 深绿色悬停效果
                command=lambda: self.handle_button_click("star")
            ).pack(side="left", padx=10)
            
            ctk.CTkButton(
                button_frame, 
                text="○", 
                font=(font_name, 20, "bold"),
                width=80,  # 增加宽度
                height=35,  # 稍微减少高度
                fg_color="#FFC107",  # 黄色背景
                hover_color="#FFA000",  # 深黄色悬停效果
                text_color="#000000",  # 黑色文本
                command=lambda: self.handle_button_click("empty_star")
            ).pack(side="left", padx=10)
            
            ctk.CTkButton(
                button_frame, 
                text="×", 
                font=(font_name, 20, "bold"),
                width=80,  # 增加宽度
                height=35,  # 稍微减少高度
                fg_color="#F44336",  # 红色背景
                hover_color="#D32F2F",  # 深红色悬停效果
                command=lambda: self.handle_button_click("none")
            ).pack(side="left", padx=10)
            
            # 设置自动关闭计时器（60秒后自动关闭）
            self.window.after(60000, self.auto_close_window)
            
            # 设置窗口大小并确保它不会被内容撑大
            self.window.geometry("400x250")
            self.window.minsize(400, 250)  # 设置最小尺寸
            self.window.maxsize(400, 250)  # 设置最大尺寸，防止调整
            
            # 窗口置顶
            self.window.attributes('-topmost', True)
            
            # 窗口居中显示
            self.center_window()
            
            # 设置窗口关闭协议
            self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
            
            try:
                self.window.mainloop()
            except Exception as e:
                print(f"窗口主循环出错: {e}")
            finally:
                # 确保窗口和变量被清理
                if self.window:
                    try:
                        self.window.quit()
                        self.window.destroy()
                        self.window = None
                    except:
                        pass
        except Exception as e:
            print(f"创建窗口时出错: {e}")
            if self.window:
                try:
                    self.window.quit()
                    self.window.destroy()
                    self.window = None
                except:
                    pass
    
    def center_window(self):
        """使窗口居中显示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def handle_button_click(self, symbol):
        """处理按钮点击事件"""
        try:
            # 保存当前选择的活动类型
            activity_type = self.activity_var.get()
            self.last_activity_type = activity_type
            
            # 先关闭窗口，提高用户体验
            window = self.window
            self.window = None
            
            # 确保在主线程中销毁窗口和变量
            if window:
                window.quit()  # 停止mainloop
                window.destroy()  # 销毁窗口
                
            # 在测试模式下同步处理，否则在后台线程中处理
            if self.test_mode and symbol != "none":
                print("测试模式：同步处理按钮操作")
                self.update_excel(symbol)
                self.log_study_status(symbol, activity_type)
            elif symbol != "none":
                # 创建后台线程处理Excel更新和CSV记录
                update_thread = threading.Thread(
                    target=self._process_button_action,
                    args=(symbol, activity_type)
                )
                update_thread.daemon = True
                update_thread.start()
            else:
                # 点击×按钮时只显示通知
                if hasattr(self, 'current_cell') and self.current_cell:
                    column, row = self.current_cell
                    print(f"已选择不填写单元格 {column}{row}")
                    notification.notify(
                        title="昼夜表记录",
                        message=f"已选择不填写单元格 {column}{row}",
                        app_name="昼夜表自动记录工具",
                        timeout=5
                    )
        except Exception as e:
            print(f"处理按钮点击时出错: {e}")
    
    def _process_button_action(self, symbol, activity_type):
        """在后台处理按钮操作"""
        try:
            # 更新Excel
            self.update_excel(symbol)
            
            # 记录学习状态到CSV文件
            self.log_study_status(symbol, activity_type)
        except Exception as e:
            print(f"处理按钮操作时出错: {e}")
    
    def auto_close_window(self):
        """自动关闭窗口"""
        try:
            if self.window:
                print("窗口超时未操作，自动关闭")
                self.window.quit()  # 停止mainloop
                self.window.destroy()
                self.window = None
        except Exception as e:
            print(f"自动关闭窗口时出错: {e}")
    
    def on_window_close(self):
        """窗口关闭事件处理"""
        try:
            if self.window:
                self.window.quit()  # 停止mainloop
                self.window.destroy()
                self.window = None
        except Exception as e:
            print(f"关闭窗口时出错: {e}")
    
    def check_and_show_window(self):
        """检查是否需要显示窗口"""
        now = datetime.now()
        
        # 打印当前时间，便于调试
        print(f"检查时间: {now.strftime('%H:%M:%S')}")
        
        # 特殊处理22:00整点
        is_ten_pm = now.hour == 22 and now.minute == 0 and now.second < 30
        
        # 检查是否在昼夜表时间范围内或是22:00整点
        if ((cell_time_mapping.DAY_START_TIME <= now.time() <= cell_time_mapping.DAY_END_TIME or
             cell_time_mapping.NIGHT_START_TIME <= now.time() <= cell_time_mapping.NIGHT_END_TIME) or
            is_ten_pm):
            
            # 检查是否是整5分钟或22:00整点
            if (now.minute % 5 == 0 and now.second < 30) or is_ten_pm:
                print(f"符合条件！当前时间: {now.strftime('%H:%M:%S')}，创建记录窗口")
                
                # 在新线程中创建窗口，避免阻塞主线程
                if self.window is None:  # 确保没有已经打开的窗口
                    window_thread = threading.Thread(target=self.create_window)
                    window_thread.daemon = True  # 设置为守护线程
                    window_thread.start()
                    
                    return True  # 返回True表示已创建窗口
        
        return False  # 返回False表示未创建窗口
    
    def run(self):
        """运行主循环"""
        print("昼夜表自动记录工具已启动")
        print(f"监控时间范围: {cell_time_mapping.DAY_START_TIME.strftime('%H:%M')} - {cell_time_mapping.DAY_END_TIME.strftime('%H:%M')} 和 {cell_time_mapping.NIGHT_START_TIME.strftime('%H:%M')} - {cell_time_mapping.NIGHT_END_TIME.strftime('%H:%M')}")
        
        # 如果是测试模式，立即打开窗口
        if self.test_mode:
            print("测试模式：立即打开窗口")
            next_time = self.get_next_five_minute_time()
            print(f"下一个5分钟节点: {next_time.strftime('%H:%M')}")
            
            # 在测试模式下，直接在主线程中创建窗口，确保能够正确处理
            self.create_window(test_time=next_time)
            
            # 测试模式下，等待一段时间确保后台线程完成
            time.sleep(2)
            return
        
        # 记录上次创建窗口的时间
        last_window_time = None
        
        try:
            while self.running:
                now = datetime.now()
                
                # 只有当前分钟与上次创建窗口的分钟不同时，才检查是否需要创建窗口
                current_minute = (now.hour, now.minute)
                if last_window_time != current_minute:
                    if self.check_and_show_window():
                        last_window_time = current_minute
                
                # 短暂休眠，避免CPU占用过高
                time.sleep(1)
        except KeyboardInterrupt:
            print("程序已手动停止")
        except Exception as e:
            print(f"运行时出错: {e}")
        finally:
            print("昼夜表自动记录工具已关闭")
            # 确保Excel应用程序被关闭
            try:
                if self.excel:
                    self.excel.Quit()
                    self.excel = None
            except:
                pass

    def log_study_status(self, symbol, activity_type):
        """记录学习状态到CSV文件"""
        # 如果是none，不记录
        if symbol == "none":
            return
        
        try:
            # 确保statistics目录存在
            stats_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "statistics")
            if not os.path.exists(stats_dir):
                os.makedirs(stats_dir)
            
            # 确保five_minute_logs目录存在
            logs_dir = os.path.join(stats_dir, "five_minute_logs")
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            
            # 获取当前日期作为文件名
            today = datetime.now().strftime("%Y-%m-%d")
            csv_file = os.path.join(logs_dir, f"五分钟记录_{today}.csv")
            
            # 使用当前单元格对应的时间，而不是实际点击时间
            time_str = ""
            if self.current_cell:
                column, row = self.current_cell
                # 从单元格映射获取对应的时间
                cell_time = cell_time_mapping.get_time_for_cell(column, row)
                if cell_time:
                    time_str = cell_time.strftime("%H:%M")
                else:
                    # 如果无法获取单元格时间，则使用当前时间的整5分钟
                    now = datetime.now()
                    rounded_minute = (now.minute // 5) * 5
                    time_str = f"{now.hour:02d}:{rounded_minute:02d}"
            else:
                # 如果没有当前单元格信息，使用当前时间的整5分钟
                now = datetime.now()
                rounded_minute = (now.minute // 5) * 5
                time_str = f"{now.hour:02d}:{rounded_minute:02d}"
            
            # 将符号转换为状态描述
            status = "高效" if symbol == "star" else "普通"
            
            # 获取活动类型的坐标点
            activity_point = self.get_activity_point(activity_type)
            point_str = f"{activity_point[0]},{activity_point[1]}" if activity_point else "0,0"
            
            # 检查文件是否存在，如果不存在则创建并写入表头
            file_exists = os.path.isfile(csv_file)
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["时间", "状态", "事情类型", "坐标点"])
                
                # 写入数据行
                writer.writerow([time_str, status, activity_type, point_str])
            
            print(f"已记录学习状态到: {csv_file}")
            
        except Exception as e:
            print(f"记录学习状态时出错: {e}")
    
    def get_activity_point(self, activity_type):
        """获取活动类型的坐标点"""
        try:
            activity_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "activity_types.json")
            if os.path.exists(activity_file):
                with open(activity_file, 'r', encoding='utf-8') as f:
                    activity_data = json.load(f)
                
                # 检查是否是新格式
                if isinstance(activity_data, dict):
                    if activity_type in activity_data and "point" in activity_data[activity_type]:
                        return activity_data[activity_type]["point"]
            
            return None
        except Exception as e:
            print(f"获取活动类型坐标点时出错: {e}")
            return None

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="昼夜表自动记录工具")
    parser.add_argument("--test", action="store_true", help="测试模式：立即打开窗口")
    args = parser.parse_args()
    
    # 创建记录器实例并运行
    logger = DayNightTableLogger(test_mode=args.test)
    logger.run()

if __name__ == "__main__":
    main() 