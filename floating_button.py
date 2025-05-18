import sys
import os
import json
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
        
        # 创建信息布局
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # 添加目标时长标签 - 修改为居中对齐
        self.target_label = ModernLabel(f"目标时长: {self.target_time}")
        self.target_label.setAlignment(Qt.AlignCenter)  # 改为居中
        self.target_label.setFont(QFont("Arial", 10))
        
        # 添加预测时长标签 - 修改为居中对齐
        self.predicted_label = ModernLabel(f"预测时长: {self.predicted_time}")
        self.predicted_label.setAlignment(Qt.AlignCenter)  # 改为居中
        self.predicted_label.setFont(QFont("Arial", 10))
        
        # 添加目标外空闲时间标签 - 修改为居中对齐
        self.remaining_label = ModernLabel(f"若达标则空闲: {self.remaining_time}")
        self.remaining_label.setAlignment(Qt.AlignCenter)  # 改为居中
        self.remaining_label.setFont(QFont("Arial", 10))
        
        # 将标签添加到信息布局
        info_layout.addWidget(self.target_label)
        info_layout.addWidget(self.predicted_label)
        info_layout.addWidget(self.remaining_label)
        
        # 将标签添加到面板布局
        panel_layout.addWidget(self.time_label)
        panel_layout.addWidget(self.study_label)
        panel_layout.addWidget(self.level_label)
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
        self.setFixedSize(220, 200)
        
        # 初始位置
        desktop = QApplication.desktop()
        screen_rect = desktop.availableGeometry(desktop.primaryScreen())
        self.move(screen_rect.width() - 240, screen_rect.height() - 280)
        
        self.show()
    
    def update_data(self, current_level, study_time, target_time, predicted_time=None, remaining_time=None):
        """更新按钮显示的数据"""
        try:
            self.current_level = current_level
            self.study_time = study_time
            self.target_time = target_time
            
            # 不再使用传入的预测时长和空闲时间，而是自己计算
            # self.predicted_time = predicted_time
            # self.remaining_time = remaining_time
            
            self.level_label.setText(self.current_level)
            self.study_label.setText(self.study_time)
            self.target_label.setText(f"目标时长: {self.target_time}")
            
            # 计算预测时长和空闲时间
            self.calculate_predictions()
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
                    
                    # if opened_successfully:
                    #     print(f"已打开昼夜表: {excel_file}") # 这行可以保留，也可以根据实际情况调整，因为os.startfile等是异步的
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
        """)
        
        # 添加打开Excel选项
        excel_action = QAction("打开昼夜表", self)
        excel_action.triggered.connect(lambda: self.mouseDoubleClickEvent(event))
        
        # 添加退出选项
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.exit_application)
        
        menu.addAction(excel_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        menu.exec_(event.globalPos())
    
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