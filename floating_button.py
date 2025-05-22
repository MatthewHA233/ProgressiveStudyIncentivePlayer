import sys
import os
import json
import csv
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                            QHBoxLayout, QGraphicsDropShadowEffect, QMenu, QAction)
from PyQt5.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QRect, QRectF
from PyQt5.QtGui import QCursor, QColor, QFont, QPainter, QLinearGradient, QRadialGradient, QPainterPath, QPen, QBrush
import subprocess
from datetime import datetime, timedelta

# 全局变量保存应用实例和按钮实例
app_instance = None
button_instance = None

class ModernLabel(QLabel):
    """现代化标签，支持渐变文字和悬停效果"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.hovered = False
        
        # 移除动画效果，因为它可能导致渲染问题
        # self.animation = QPropertyAnimation(self, b"geometry")
        # self.animation.setDuration(200)
        # self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def enterEvent(self, event):
        self.hovered = True
        # 不再使用动画，直接更新
        # self.animation.setStartValue(self.geometry())
        # target_rect = self.geometry()
        # target_rect.setWidth(target_rect.width() + 4)
        # self.animation.setEndValue(target_rect)
        # self.animation.start()
        self.update()
        
    def leaveEvent(self, event):
        self.hovered = False
        # 不再使用动画，直接更新
        # self.animation.setStartValue(self.geometry())
        # target_rect = self.geometry()
        # target_rect.setWidth(target_rect.width() - 4)
        # self.animation.setEndValue(target_rect)
        # self.animation.start()
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建文字渐变
        if self.hovered:
            gradient = QLinearGradient(0, 0, self.width(), 0)
            gradient.setColorAt(0, QColor(56, 189, 248))
            gradient.setColorAt(0.5, QColor(255, 255, 255))
            gradient.setColorAt(1, QColor(129, 226, 180))
        else:
            gradient = QLinearGradient(0, 0, self.width(), 0)
            gradient.setColorAt(0, QColor(255, 255, 255))
            gradient.setColorAt(1, QColor(200, 200, 255))
            
        painter.setPen(QPen(QBrush(gradient), 1))
        painter.setFont(self.font())
        painter.drawText(self.rect(), self.alignment(), self.text())

class GradientLabel(ModernLabel):
    """始终使用渐变色的标签"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 始终使用渐变色效果
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(56, 189, 248))
        gradient.setColorAt(0.5, QColor(255, 255, 255))
        gradient.setColorAt(1, QColor(129, 226, 180))
            
        painter.setPen(QPen(QBrush(gradient), 1))
        painter.setFont(self.font())
        painter.drawText(self.rect(), self.alignment(), self.text())

class GlassPanel(QWidget):
    """玻璃效果面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hovered = False
        
    def enterEvent(self, event):
        self.hovered = True
        self.update()
        
    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建圆角路径
        path = QPainterPath()
        # 将QRect转换为QRectF
        rect_f = QRectF(self.rect())
        path.addRoundedRect(rect_f, 20, 20)
        
        # 绘制背景 - 提高透明度
        bg_opacity = 0.75 if self.hovered else 0.65  # 降低透明度值，提高透明效果
        bg_color = QColor(20, 20, 30, int(bg_opacity * 255))
        painter.fillPath(path, bg_color)
        
        # 绘制顶部光晕效果 - 常驻显示，不再根据悬停状态变化
        # 使用渐变效果
        gradient = QLinearGradient(self.width()/2, 0, self.width()/2, self.height()/3)
        # 悬停时稍微增强效果
        if self.hovered:
            gradient.setColorAt(0, QColor(56, 189, 248, 70))  # 顶部更亮
            gradient.setColorAt(1, QColor(56, 189, 248, 0))   # 底部渐变消失
        else:
            gradient.setColorAt(0, QColor(56, 189, 248, 60))  # 顶部亮度
            gradient.setColorAt(1, QColor(56, 189, 248, 0))   # 底部渐变消失
        
        painter.fillRect(0, 0, self.width(), int(self.height()/2.5), gradient)
        
        # 绘制边框
        border_color = QColor(255, 255, 255, 40) if self.hovered else QColor(255, 255, 255, 25)
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)
        
        # 绘制底部渐变线 - 更加梦幻的效果
        # 始终显示底部线条，但悬停时更明显
        gradient = QLinearGradient(0, self.height()-2, self.width(), self.height()-2)
        
        if self.hovered:
            # 悬停时更明亮
            gradient.setColorAt(0, QColor(56, 189, 248, 0))   # 左侧透明
            gradient.setColorAt(0.2, QColor(56, 189, 248, 100)) # 渐变到蓝色
            gradient.setColorAt(0.5, QColor(255, 255, 255, 150)) # 中间白色
            gradient.setColorAt(0.8, QColor(129, 226, 180, 100)) # 渐变到绿色
            gradient.setColorAt(1, QColor(129, 226, 180, 0))   # 右侧透明
        else:
            # 非悬停时较淡
            gradient.setColorAt(0, QColor(56, 189, 248, 0))   # 左侧透明
            gradient.setColorAt(0.2, QColor(56, 189, 248, 60)) # 渐变到蓝色
            gradient.setColorAt(0.5, QColor(255, 255, 255, 80)) # 中间白色
            gradient.setColorAt(0.8, QColor(129, 226, 180, 60)) # 渐变到绿色
            gradient.setColorAt(1, QColor(129, 226, 180, 0))   # 右侧透明
        
        painter.setPen(QPen(QBrush(gradient), 2))
        painter.drawLine(int(self.width()*0.05), self.height()-2, int(self.width()*0.95), self.height()-2)

class HeatmapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(220, 100)  # 保持整体大小不变
        
        # 初始化数据结构
        self.hourly_data = {}  # 存储每小时的学习状态数据
        self.current_hour = datetime.now().hour
        self.last_update_hour = self.current_hour  # 用于检测小时变化
        
        # 设置边距和布局参数
        self.margin_top = 20  # 顶部留空给小时标记
        self.margin_bottom = 5
        self.margin_left = 10  # 恢复合理的左边距
        self.margin_right = 10  # 对称的右边距
        self.column_width = 22  # 固定列宽
    
    def update_data(self, csv_path):
        """从CSV文件更新数据"""
        try:
            self.hourly_data.clear()
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    time_str = row['时间']
                    status = row['状态']
                    hour, minute = map(int, time_str.split(':'))
                    
                    if hour not in self.hourly_data:
                        self.hourly_data[hour] = [None] * 12  # 12个5分钟时段
                    
                    # 处理特殊情况：00分的数据存储在上一个小时的最后一个格子
                    if minute == 0:
                        prev_hour = (hour - 1) if hour > 0 else 23
                        if prev_hour not in self.hourly_data:
                            self.hourly_data[prev_hour] = [None] * 12
                        self.hourly_data[prev_hour][11] = status == '高效'  # 存储在上一个小时的最后一个格子
                    else:
                        # 其他时间正常存储
                        index = (minute - 5) // 5
                        if 0 <= index < 11:  # 注意这里改为11，因为最后一个格子(55-00)要特殊处理
                            self.hourly_data[hour][index] = status == '高效'
            
            # 检查是否需要更新显示
            current_hour = datetime.now().hour
            if current_hour != self.last_update_hour:
                self.last_update_hour = current_hour
                self.update()
            else:
                self.update()
        except Exception as e:
            print(f"更新热力图数据时出错: {e}")
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取当前时间
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        # 计算显示范围（前9小时到当前小时）
        start_hour = max(6, current_hour - 8)  # 从6点开始，显示9小时
        end_hour = min(22, current_hour + 1)   # 到22点结束
        
        # 计算可用绘制区域
        available_width = self.width() - self.margin_left - self.margin_right
        available_height = self.height() - self.margin_top - self.margin_bottom
        
        # 计算每个小时格子的高度
        cell_height = int(available_height / 12)  # 转换为整数
        grid_height = cell_height * 12  # 总格子高度
        
        # 计算总列数和总宽度
        total_hours = end_hour - start_hour
        if total_hours <= 0:
            return
            
        total_width = total_hours * self.column_width
        
        # 计算热力图的起始x坐标，使其居中
        start_x = self.margin_left + (available_width - total_width) // 2
        
        # 绘制小时标记
        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Arial", 8))
        
        for hour in range(start_hour, end_hour):
            x = start_x + int((hour - start_hour) * self.column_width)
            # 绘制小时文本
            hour_text = f"{hour:02d}"
            text_rect = painter.fontMetrics().boundingRect(hour_text)
            text_x = x + (self.column_width - text_rect.width()) // 2
            painter.drawText(text_x, 15, hour_text)
            
            # 绘制分隔线，确保完全对齐格子范围
            if hour > start_hour:  # 不绘制第一条分隔线
                line_x = x - 1
                painter.drawLine(line_x, self.margin_top, line_x, self.margin_top + grid_height)
        
        # 绘制每个小时的格子
        for hour in range(start_hour, end_hour):
            x = start_x + int((hour - start_hour) * self.column_width)
            
            if hour in self.hourly_data:
                for i, status in enumerate(self.hourly_data[hour]):
                    if status is not None:
                        y = self.margin_top + int(i * cell_height)
                        rect = QRect(x, y, self.column_width - 1, cell_height - 1)
                        
                        # 创建渐变色
                        if status:  # 高效状态
                            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                            gradient.setColorAt(0, QColor(46, 204, 113, 230))
                            gradient.setColorAt(1, QColor(46, 204, 113, 180))
                        else:  # 普通状态
                            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
                            gradient.setColorAt(0, QColor(241, 196, 15, 230))
                            gradient.setColorAt(1, QColor(241, 196, 15, 180))
                        
                        painter.fillRect(rect, gradient)
                        
                        # 绘制边框
                        painter.setPen(QPen(QColor(255, 255, 255, 30)))
                        painter.drawRect(rect)
        
        # 绘制当前时间指示线
        if current_hour >= start_hour and current_hour < end_hour:
            # 计算当前时间在总高度中的相对位置（基于1-60分钟）
            # 将0-59分钟映射到1-60
            minute_for_calculation = current_minute + 1
            # 计算相对于块底部的位置
            block_index = (minute_for_calculation - 1) // 5  # 确定在哪个5分钟块内
            next_block_boundary = (block_index + 1) * 5  # 下一个块的边界分钟数
            prev_block_boundary = block_index * 5  # 当前块的起始分钟数
            
            # 计算在当前块内的相对位置
            block_y_start = self.margin_top + int(block_index * cell_height)
            block_y_end = block_y_start + cell_height
            
            # 计算在当前块内的精确位置
            within_block_position = (minute_for_calculation - prev_block_boundary - 1) / 5.0
            current_y = block_y_end - int(cell_height * (1 - within_block_position))
            
            # 计算当前时间列的x坐标
            current_hour_offset = current_hour - start_hour
            current_x = start_x + int(current_hour_offset * self.column_width)
            
            # 设置红色渐变线
            painter.setPen(QPen(QColor(255, 50, 50, 200), 2))
            painter.drawLine(
                current_x, current_y,
                current_x + self.column_width - 2, current_y
            )

class FloatingButton(QWidget):
    def __init__(self):
        super().__init__()
        
        # 初始化数据
        self.current_level = "未知阶段"
        self.study_time = "0时00分"
        self.current_time = "00:00:00"
        self.target_time = "12小时"
        self.predicted_time = "0时00分"
        self.remaining_time = "0时00分"
        self.current_date = datetime.now().strftime("%Y-%m-%d")  # 移到这里初始化
        
        # 添加新的控制变量
        self.heatmap_visible = True
        self.opacity = 1.0  # 透明度，1.0表示完全不透明
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 总是在最前
            Qt.Tool  # 工具窗口，不在任务栏显示
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        
        # 初始化UI
        self.initUI()
        
        # 用于跟踪鼠标拖动
        self.dragging = False
        self.offset = QPoint()
        
        # 设置定时器更新时间
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 每秒更新一次
        
        # 添加提示信息
        self.setToolTip("双击打开昼夜表")
        
        # 初始化热力图更新定时器
        self.heatmap_timer = QTimer(self)
        self.heatmap_timer.timeout.connect(self.update_heatmap)
        self.heatmap_timer.start(300000)  # 每5分钟更新一次
        
    def initUI(self):
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建玻璃效果面板
        self.glass_panel = GlassPanel(self)
        panel_layout = QVBoxLayout(self.glass_panel)
        panel_layout.setContentsMargins(15, 10, 15, 10)
        panel_layout.setSpacing(5)
        
        # 添加时间标签
        self.time_label = ModernLabel(self.current_time)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("Arial", 16, QFont.Bold))
        
        # 添加学习时长标签
        self.study_label = ModernLabel(self.study_time)
        self.study_label.setAlignment(Qt.AlignCenter)
        self.study_label.setFont(QFont("Arial", 14))
        
        # 添加阶段标签
        self.level_label = GradientLabel(self.current_level)
        self.level_label.setAlignment(Qt.AlignCenter)
        self.level_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        # 创建热力图组件
        self.heatmap = HeatmapWidget(self)
        
        # 创建信息布局
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # 添加目标时长标签
        self.target_label = ModernLabel(f"目标时长: {self.target_time}")
        self.target_label.setAlignment(Qt.AlignCenter)
        self.target_label.setFont(QFont("Arial", 10))
        
        # 添加预测时长标签
        self.predicted_label = ModernLabel(f"预测时长: {self.predicted_time}")
        self.predicted_label.setAlignment(Qt.AlignCenter)
        self.predicted_label.setFont(QFont("Arial", 10))
        
        # 添加目标外空闲时间标签
        self.remaining_label = ModernLabel(f"若达标则空闲: {self.remaining_time}")
        self.remaining_label.setAlignment(Qt.AlignCenter)
        self.remaining_label.setFont(QFont("Arial", 10))
        
        # 将标签添加到信息布局
        info_layout.addWidget(self.target_label)
        info_layout.addWidget(self.predicted_label)
        info_layout.addWidget(self.remaining_label)
        
        # 将标签添加到面板布局
        panel_layout.addWidget(self.time_label)
        panel_layout.addWidget(self.study_label)
        panel_layout.addWidget(self.level_label)
        panel_layout.addWidget(self.heatmap)  # 添加热力图
        panel_layout.addLayout(info_layout)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(4, 4)
        self.glass_panel.setGraphicsEffect(shadow)
        
        # 将面板添加到主布局
        main_layout.addWidget(self.glass_panel)
        self.setLayout(main_layout)
        
        # 设置窗口大小
        self.setFixedSize(220, 280)  # 增加高度以容纳热力图
        
        # 初始位置
        desktop = QApplication.desktop()
        screen_rect = desktop.availableGeometry(desktop.primaryScreen())
        self.move(screen_rect.width() - 240, screen_rect.height() - 300)
        
        self.show()
        
        # 初始化热力图数据
        self.update_heatmap()
    
    def update_heatmap(self):
        """更新热力图数据"""
        try:
            # 获取当前日期的CSV文件路径
            csv_path = os.path.join("statistics", "five_minute_logs", f"五分钟记录_{self.current_date}.csv")
            if os.path.exists(csv_path):
                self.heatmap.update_data(csv_path)
        except Exception as e:
            print(f"更新热力图时出错: {e}")
    
    def update_data(self, current_level, study_time, target_time, predicted_time=None, remaining_time=None):
        """更新按钮显示的数据"""
        try:
            self.current_level = current_level
            self.study_time = study_time
            self.target_time = target_time
            
            self.level_label.setText(self.current_level)
            self.study_label.setText(self.study_time)
            self.target_label.setText(f"目标时长: {self.target_time}")
            
            # 计算预测时长和空闲时间
            self.calculate_predictions()
            
            # 更新热力图
            self.update_heatmap()
        except Exception as e:
            print(f"更新悬浮按钮数据时出错: {e}")
    
    def update_time(self):
        """更新当前时间并计算预测时长和空闲时间"""
        try:
            # 更新当前时间
            now = datetime.now()
            self.current_time = now.strftime("%H:%M:%S")
            self.time_label.setText(self.current_time)
            
            # 计算预测时长和空闲时间
            self.calculate_predictions()
        except Exception as e:
            print(f"更新时间时出错: {e}")
    
    def calculate_predictions(self):
        """计算预测时长和空闲时间"""
        try:
            now = datetime.now()
            
            # 定义一天的开始和结束时间（6:00 - 22:00）
            day_start = now.replace(hour=6, minute=0, second=0, microsecond=0)
            day_end = now.replace(hour=22, minute=0, second=0, microsecond=0)
            
            # 如果当前时间早于6点，则使用前一天的22点作为结束时间
            if now < day_start:
                day_start = day_start - timedelta(days=1)
                day_end = day_end - timedelta(days=1)
            
            # 如果当前时间晚于22点，则使用下一天的6点作为开始时间
            if now > day_end:
                day_start = day_start + timedelta(days=1)
                day_end = day_end + timedelta(days=1)
            
            # 计算已经过去的时间（分钟）
            elapsed_minutes = (now - day_start).total_seconds() / 60
            
            # 计算一天的总时间（分钟）
            total_day_minutes = (day_end - day_start).total_seconds() / 60
            
            # 解析已学习时间
            study_hours, study_minutes = 0, 0
            if "时" in self.study_time and "分" in self.study_time:
                parts = self.study_time.split("时")
                study_hours = int(parts[0])
                study_minutes = int(parts[1].replace("分", ""))
            
            # 计算已学习的总分钟数
            study_total_minutes = study_hours * 60 + study_minutes
            
            # 计算学习时间占比
            if elapsed_minutes > 0:
                study_ratio = study_total_minutes / elapsed_minutes
            else:
                study_ratio = 0
            
            # 预测全天学习时长（分钟）
            predicted_minutes = study_ratio * total_day_minutes
            predicted_hours = int(predicted_minutes // 60)
            predicted_mins = int(predicted_minutes % 60)
            self.predicted_time = f"{predicted_hours}时{predicted_mins:02d}分"
            
            # 解析目标学习时长（小时）
            target_hours = 0
            if "小时" in self.target_time:
                target_str = self.target_time.replace("小时", "")
                try:
                    target_hours = float(target_str)
                except ValueError:
                    target_hours = 0
            
            # 计算目标学习时长（分钟）
            target_minutes = target_hours * 60
            
            # 计算剩余需要学习的时间（分钟）
            remaining_study_minutes = max(0, target_minutes - study_total_minutes)
            
            # 计算剩余的一天时间（分钟）
            remaining_day_minutes = max(0, (day_end - now).total_seconds() / 60)
            
            # 计算空闲时间（分钟）
            free_minutes = max(0, remaining_day_minutes - remaining_study_minutes)
            free_hours = int(free_minutes // 60)
            free_mins = int(free_minutes % 60)
            self.remaining_time = f"{free_hours}时{free_mins:02d}分"
            
            # 更新标签
            self.predicted_label.setText(f"预测时长: {self.predicted_time}")
            self.remaining_label.setText(f"若达标则空闲: {self.remaining_time}")
        except Exception as e:
            print(f"计算预测时长和空闲时间时出错: {e}")
    
    def mouseDoubleClickEvent(self, event):
        """双击事件处理 - 打开昼夜表"""
        if event.button() == Qt.LeftButton:
            self.open_excel_file()
    
    def open_excel_file(self):
        """打开昼夜表"""
        try:
            # 获取当前日期
            current_date = datetime.now()
            
            # 计算当前是第几周
            # 从配置文件读取起始日期，如果没有配置文件，使用默认值
            try:
                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    start_date = datetime.strptime(config.get('start_date', '2023-01-01'), '%Y-%m-%d')
                else:
                    # 如果没有配置文件，使用默认起始日期
                    start_date = datetime(2023, 1, 1)
            except Exception as e:
                print(f"读取配置文件时出错: {e}")
                # 使用默认起始日期
                start_date = datetime(2023, 1, 1)
            
            # 计算从起始日期到当前日期的天数
            days_difference = (current_date - start_date).days
            
            # 计算当前是第几周，向上取整
            week_number = days_difference // 7 + 1
            
            # 计算这一周的开始日期（周一）和结束日期（周日）
            start_of_week = start_date + timedelta(weeks=(week_number - 1))
            end_of_week = start_of_week + timedelta(days=6)
            
            # 格式化文件名
            file_name = f"第{week_number}周({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')}).xls"
            
            # 尝试从配置文件获取Excel路径
            try:
                excel_path = config.get('excel_path', '')
                if not excel_path:
                    # 如果配置文件中没有路径，使用默认路径
                    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "昼夜表")
            except:
                # 如果出错，使用默认路径
                excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "昼夜表")
            
            # 确保路径存在
            if not os.path.exists(excel_path):
                os.makedirs(excel_path)
            
            # 构建完整的文件路径
            excel_file = os.path.join(excel_path, file_name).replace('\\', '/')
            
            # 检查文件是否存在
            if os.path.exists(excel_file):
                opened_successfully = False
                for attempt in range(1, 3): # 尝试两次
                    try:
                        print(f"尝试第 {attempt} 次打开昼夜表: {excel_file}")
                        # 使用系统默认程序打开Excel文件
                        if sys.platform == 'win32':
                            os.startfile(excel_file)
                        elif sys.platform == 'darwin':  # macOS
                            subprocess.call(['open', excel_file])
                        else:  # Linux
                            subprocess.call(['xdg-open', excel_file])
                        print(f"已成功启动打开昼夜表的命令: {excel_file}")
                        opened_successfully = True
                        break # 如果成功启动命令，则跳出循环
                    except Exception as e_open:
                        print(f"第 {attempt} 次打开昼夜表时出错: {e_open}")
                        if attempt == 2: # 如果是第二次尝试仍然失败
                            print(f"两次尝试打开昼夜表均失败: {excel_file}")
            else:
                print(f"昼夜表文件不存在: {excel_file}")
        except Exception as e:
            print(f"打开昼夜表时出错: {e}")
    
    def contextMenuEvent(self, event):
        """右键菜单事件"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(20, 20, 30, 0.9);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: rgba(56, 189, 248, 0.2);
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 0.1);
                margin: 5px 15px;
            }
        """)
        
        # 添加打开Excel选项
        excel_action = QAction("打开昼夜表", self)
        excel_action.triggered.connect(self.open_excel_file)
        
        # 添加启动5分钟间隔弹窗选项
        auto_logger_action = QAction("启动5分钟间隔弹窗", self)
        auto_logger_action.triggered.connect(self.start_auto_logger)
        
        # 添加打开CSV选项
        csv_action = QAction("打开五分钟记录", self)
        csv_action.triggered.connect(self.open_csv_file)
        
        # 添加热力图显示/隐藏选项
        heatmap_action = QAction("隐藏热力图" if self.heatmap_visible else "显示热力图", self)
        heatmap_action.triggered.connect(self.toggle_heatmap)
        
        # 添加透明度调节子菜单
        opacity_menu = QMenu("调整透明度", self)
        opacity_menu.setStyleSheet(menu.styleSheet())
        
        opacity_values = [("100%", 1.0), ("80%", 0.8), ("60%", 0.6), ("40%", 0.4)]
        for label, value in opacity_values:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, v=value: self.set_opacity(v))
            if abs(self.opacity - value) < 0.01:
                action.setIcon(self.style().standardIcon(self.style().SP_DialogApplyButton))
            opacity_menu.addAction(action)

        # 添加新的功能菜单项
        menu.addAction(excel_action)
        menu.addAction(auto_logger_action)
        menu.addAction(csv_action)
        menu.addSeparator()

        # 添加时间管理相关功能
        time_menu = QMenu("时间管理", self)
        time_menu.setStyleSheet(menu.styleSheet())
        
        time_block_action = QAction("当日块时间总结", self)
        time_block_action.triggered.connect(self.start_time_block_clicker)
        time_menu.addAction(time_block_action)
        
        today_chart_action = QAction("查看今日学习时长图表", self)
        today_chart_action.triggered.connect(self.show_today_chart)
        time_menu.addAction(today_chart_action)
        
        history_chart_action = QAction("生成历史图表动画", self)
        history_chart_action.triggered.connect(self.show_chart_animation)
        time_menu.addAction(history_chart_action)
        
        terminal_replay_action = QAction("查看终端回放", self)
        terminal_replay_action.triggered.connect(self.show_terminal_replay)
        time_menu.addAction(terminal_replay_action)

        # 添加设置相关功能
        settings_menu = QMenu("设置管理", self)
        settings_menu.setStyleSheet(menu.styleSheet())
        
        main_interface_action = QAction("打开主控制界面", self)
        main_interface_action.triggered.connect(self.open_main_interface)
        settings_menu.addAction(main_interface_action)
        settings_menu.addSeparator()
        
        wallpaper_action = QAction("壁纸引擎映射管理", self)
        wallpaper_action.triggered.connect(self.start_wallpaper_music_matcher)
        settings_menu.addAction(wallpaper_action)
        
        activity_type_action = QAction("设置事情类型及坐标", self)
        activity_type_action.triggered.connect(self.start_activity_type_editor)
        settings_menu.addAction(activity_type_action)

        # 将子菜单添加到主菜单
        menu.addMenu(time_menu)
        menu.addMenu(settings_menu)
        menu.addSeparator()
        menu.addAction(heatmap_action)
        menu.addMenu(opacity_menu)
        menu.addSeparator()
        
        # 添加退出选项
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.exit_application)
        menu.addAction(exit_action)
        
        menu.exec_(event.globalPos())

    def start_time_block_clicker(self):
        """启动时间块点击器"""
        script_path = os.path.join(os.path.dirname(__file__), "TimeBlockClicker.py")
        self.run_script(script_path)

    def show_today_chart(self):
        """显示今日学习时长图表"""
        script_path = os.path.join(os.path.dirname(__file__), "study_log_chart_popup.py")
        self.run_script(script_path)

    def show_chart_animation(self):
        """显示历史图表动画"""
        script_path = os.path.join(os.path.dirname(__file__), "study_log_chart_animated.py")
        self.run_script(script_path)

    def show_terminal_replay(self):
        """显示终端回放"""
        script_path = os.path.join(os.path.dirname(__file__), "terminal_log_player.py")
        self.run_script(script_path)

    def start_wallpaper_music_matcher(self):
        """启动壁纸引擎映射管理"""
        script_path = os.path.join(os.path.dirname(__file__), "WallpaperMusicMatcher.py")
        self.run_script(script_path)

    def start_activity_type_editor(self):
        """启动事情类型编辑器"""
        script_path = os.path.join(os.path.dirname(__file__), "activity_type_editor.py")
        self.run_script(script_path)

    def run_script(self, script_path):
        """运行指定的Python脚本"""
        try:
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
                        print("无法找到可用的终端模拟器")
            else:
                print(f"找不到脚本文件: {script_path}")
        except Exception as e:
            print(f"运行脚本时出错: {e}")
    
    def toggle_heatmap(self):
        """切换热力图显示状态"""
        self.heatmap_visible = not self.heatmap_visible
        self.heatmap.setVisible(self.heatmap_visible)
        # 调整窗口大小
        if self.heatmap_visible:
            self.setFixedSize(220, 280)
        else:
            self.setFixedSize(220, 180)
    
    def set_opacity(self, value):
        """设置窗口透明度"""
        self.opacity = value
        self.setWindowOpacity(value)
    
    def open_csv_file(self):
        """打开当日的五分钟记录CSV文件"""
        try:
            csv_path = os.path.join("statistics", "five_minute_logs", f"五分钟记录_{self.current_date}.csv")
            if os.path.exists(csv_path):
                if sys.platform == 'win32':
                    os.startfile(csv_path)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.call(['open', csv_path])
                else:  # Linux
                    subprocess.call(['xdg-open', csv_path])
            else:
                print(f"CSV文件不存在: {csv_path}")
        except Exception as e:
            print(f"打开CSV文件时出错: {e}")
    
    def exit_application(self):
        """退出应用程序"""
        self.close()
        # 终止整个Python进程
        import signal
        os.kill(os.getpid(), signal.SIGTERM)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(self.mapToGlobal(event.pos() - self.offset))
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
    
    def enterEvent(self, event):
        QApplication.setOverrideCursor(QCursor(Qt.PointingHandCursor))
        self.glass_panel.hovered = True
        self.glass_panel.update()
    
    def leaveEvent(self, event):
        QApplication.restoreOverrideCursor()
        self.glass_panel.hovered = False
        self.glass_panel.update()

    def open_main_interface(self):
        """打开主控制界面"""
        script_path = os.path.join(os.path.dirname(__file__), "main_interface.py")
        try:
            if os.path.exists(script_path):
                if sys.platform == "win32":
                    subprocess.Popen([sys.executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
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
                        print("无法找到可用的终端模拟器")
            else:
                print(f"找不到主控制界面脚本: {script_path}")
        except Exception as e:
            print(f"启动主控制界面时出错: {e}")

    def start_auto_logger(self):
        """启动5分钟间隔弹窗"""
        script_path = os.path.join(os.path.dirname(__file__), "DayNightTableAutoLogger.py")
        self.run_script(script_path)

def create_button():
    """创建悬浮按钮"""
    global app_instance, button_instance
    
    # 确保QApplication已经创建
    app_instance = QApplication.instance()
    if app_instance is None:
        app_instance = QApplication(sys.argv)
    
    # 创建悬浮按钮
    button_instance = FloatingButton()
    
    return button_instance

def update_button_data(current_level, study_time, target_time, predicted_time=None, remaining_time=None):
    """更新悬浮按钮数据"""
    global button_instance
    if button_instance:
        try:
            # 只传递必要的参数，预测时长和空闲时间将由按钮自己计算
            button_instance.update_data(current_level, study_time, target_time)
        except Exception as e:
            print(f"更新按钮数据时出错: {e}")

def integrate_with_study_player():
    """与主程序集成"""
    return create_button()

# 独立运行时的测试代码
if __name__ == '__main__':
    app = QApplication(sys.argv)
    floating_button = FloatingButton()
    
    # 测试数据
    floating_button.update_data("『C 理想、进取』", "2时30分", "12小时")
    
    sys.exit(app.exec_())