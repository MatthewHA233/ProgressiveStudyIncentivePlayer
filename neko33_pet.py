import sys
import os
import json
import csv
import time
import threading
from datetime import datetime
try:
    import pygame
    pygame.mixer.init()
    AUDIO_AVAILABLE = True
    print("音频模块初始化成功")
except ImportError:
    print("pygame模块不可用，音频功能将被禁用")
    AUDIO_AVAILABLE = False
except Exception as e:
    print(f"音频初始化失败: {e}")
    AUDIO_AVAILABLE = False

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                            QHBoxLayout, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QRect, QRectF, pyqtSignal
from PyQt5.QtGui import QMovie, QPixmap, QPainter, QColor, QFont, QPainterPath, QBrush, QPen

class SpeechBubble(QWidget):
    """33娘对话气泡组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        # 添加属性减少透明窗口错误
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        self.text = ""
        self.visible = False
        self.max_width = 350
        self.min_width = 180
        
        # 设置字体
        self.font = QFont("黑体", 11, QFont.Bold)
        
    def setText(self, text):
        """设置气泡文本"""
        self.text = text
        self.updateSize()
        self.update()
        
        # 如果有父级33娘组件，通知其更新气泡位置
        if hasattr(self, 'parent_pet') and self.parent_pet:
            QTimer.singleShot(50, self.parent_pet.updateBubblePosition)  # 延迟50ms确保尺寸计算完成
    
    def updateSize(self):
        """根据文本内容更新气泡大小"""
        if not self.text:
            self.hide()
            return
            
        # 设置字体用于计算
        font = QFont("黑体", 11, QFont.Bold)
        self.setFont(font)
        
        # 计算文本大小
        fm = self.fontMetrics()
        
        # 设置最大宽度限制，给边距和三角形留出空间
        max_text_width = self.max_width - 60  # 左右各20边距 + 20三角形空间
        
        # 计算文本边界
        text_rect = fm.boundingRect(0, 0, max_text_width, 0, 
                                   Qt.TextWordWrap, self.text)
        
        # 计算实际需要的宽度和高度
        text_width = text_rect.width()
        text_height = text_rect.height()
        
        # 气泡宽度：文本宽度 + 左右边距 + 三角形空间
        bubble_width = max(self.min_width, text_width + 60)
        bubble_width = min(bubble_width, self.max_width)
        
        # 气泡高度：文本高度 + 上下边距
        bubble_height = text_height + 40
        
        self.setFixedSize(bubble_width, bubble_height)
        print(f"气泡大小: {bubble_width}x{bubble_height}, 文本: '{self.text}'")
    
    def showBubble(self, duration=None):
        """显示气泡"""
        if not self.text:
            return
            
        self.visible = True
        self.show()
        # 确保气泡显示时层级在最前
        self.raise_()
        
        if duration and duration > 0:
            QTimer.singleShot(duration, self.hideBubble)
    
    def hideBubble(self):
        """隐藏气泡"""
        self.visible = False
        self.hide()
    
    def paintEvent(self, event):
        if not self.text or not self.visible:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建圆角路径 - 修复PyQt5兼容性问题
        path = QPainterPath()
        # 为三角形留出右侧空间
        rect = self.rect().adjusted(2, 2, -22, -2)  # 右侧多留20像素给三角形
        rect_f = QRectF(rect)
        path.addRoundedRect(rect_f, 15, 15)  # 圆角稍微小一点
        
        # 绘制背景
        bg_color = QColor(135, 206, 250, 230)  # 天蓝色背景
        painter.fillPath(path, bg_color)
        
        # 绘制边框
        border_color = QColor(255, 156, 206)  # 粉色边框
        painter.setPen(QPen(border_color, 2))
        painter.drawPath(path)
        
        # 绘制文字
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(self.font)
        text_rect = rect.adjusted(15, 15, -15, -15)  # 文字区域边距
        painter.drawText(text_rect, Qt.TextWordWrap | Qt.AlignCenter, self.text)
        
        # 绘制三角形指针（指向33娘）
        bubble_center_y = self.height() // 2
        triangle_points = [
            QPoint(rect.right(), bubble_center_y - 8),  # 上角
            QPoint(rect.right(), bubble_center_y + 8),  # 下角  
            QPoint(rect.right() + 15, bubble_center_y)  # 尖端
        ]
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 2))
        painter.drawPolygon(triangle_points)
        
        # 绘制三角形边框
        painter.setBrush(QBrush())  # 清除填充
        painter.drawPolygon(triangle_points)

class Neko33Pet(QWidget):
    """33娘悬浮窗"""
    
    # 信号
    position_changed = pyqtSignal(QPoint)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        self.setupData()
        self.setupTimers()
        
        # 跟随目标
        self.follow_target = None
        self.offset = QPoint(40, -150)  # 在目标右侧50像素，上方120像素
        
        # 状态控制
        self.enabled = True
        self.obs_mode = False
        
        # 拖拽相关
        self.dragging = False
        self.drag_start = QPoint()
        
        # 音频播放状态管理
        self.audio_playing = False
        self.current_audio_timer = None  # 当前的音频定时器
        self.speech_sequence_timers = []  # 存储当前台词序列的所有定时器
        
        # 新增：学习状态跟踪
        self.last_study_time_string = None  # 上次检测到的学习时长字符串
        self.last_default_speech_time = 0   # 上次播放DEFAULT台词的时间戳
        self.is_in_default_state = False    # 是否处于未学习状态
        
    def setupUI(self):
        """设置UI"""
        # 窗口设置 - 优化透明窗口配置，减少渲染错误
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 优化透明窗口属性设置
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        # 添加这些属性来减少透明窗口错误
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WA_AlwaysShowToolTips, False)
        self.setFixedSize(150, 150)
        
        # 布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 33娘gif标签
        self.neko_label = QLabel()
        self.neko_label.setAlignment(Qt.AlignCenter)
        self.neko_label.setFixedSize(150, 150)
        # 设置标签背景透明
        self.neko_label.setAttribute(Qt.WA_TranslucentBackground)
        
        # 加载默认表情
        self.loadExpression(7)  # 默认惊诧表情
        
        layout.addWidget(self.neko_label)
        self.setLayout(layout)
        
        # 创建对话气泡 - 延迟创建，避免初始化问题
        self.speech_bubble = None
        QTimer.singleShot(100, self.create_speech_bubble)
        
        # 简化阴影效果，减少渲染问题
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)  # 进一步减少模糊半径
        shadow.setColor(QColor(0, 0, 0, 50))  # 进一步降低透明度
        shadow.setOffset(1, 1)  # 减少偏移
        self.setGraphicsEffect(shadow)
        
    def setupData(self):
        """设置数据相关"""
        self.speech_data = None
        self.study_history = []
        self.last_study_time = None
        self.last_status = None
        
        # 加载台词数据
        self.loadSpeechData()
        
    def setupTimers(self):
        """设置定时器"""
        # 状态检查定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.checkStudyStatus)
        self.status_timer.start(5000)  # 5秒检查一次
        
        # 位置跟随定时器
        self.follow_timer = QTimer()
        self.follow_timer.timeout.connect(self.updatePosition)
        self.follow_timer.start(200)  # 从100ms改为200ms，减少更新频率
        
    def loadSpeechData(self):
        """加载台词数据"""
        try:
            speech_data_path = os.path.join(os.path.dirname(__file__), "speech_data.json")
            if os.path.exists(speech_data_path):
                with open(speech_data_path, 'r', encoding='utf-8') as f:
                    self.speech_data = json.load(f)
                print("33娘台词数据加载成功")
            else:
                print("台词数据文件不存在")
        except Exception as e:
            print(f"加载台词数据失败: {e}")
    
    def loadExpression(self, expression_num):
        """加载33娘表情gif"""
        try:
            gif_path = os.path.join("border_assets", f"2233_{expression_num}.gif")
            if os.path.exists(gif_path):
                movie = QMovie(gif_path)
                movie.setScaledSize(self.neko_label.size())
                self.neko_label.setMovie(movie)
                movie.start()
                print(f"加载表情: {expression_num}")
            else:
                print(f"表情文件不存在: {gif_path}")
                # 使用默认图片
                self.loadDefaultImage()
        except Exception as e:
            print(f"加载表情失败: {e}")
            self.loadDefaultImage()
    
    def loadDefaultImage(self):
        """加载默认图片"""
        # 创建一个简单的默认图片
        pixmap = QPixmap(150, 150)
        pixmap.fill(QColor(255, 182, 193, 150))  # 半透明粉色
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 20))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "33娘")
        painter.end()
        self.neko_label.setPixmap(pixmap)
    
    def setFollowTarget(self, target_widget):
        """设置跟随目标"""
        self.follow_target = target_widget
        if target_widget:
            self.updatePosition()
    
    def updatePosition(self):
        """更新位置以跟随目标"""
        if not self.follow_target or not self.enabled:
            return
            
        try:
            target_pos = self.follow_target.pos()
            new_pos = target_pos + self.offset
            
            # 检查位置是否实际发生变化，避免不必要的更新
            if hasattr(self, '_last_pos') and self._last_pos == new_pos:
                return
            
            # 确保不超出屏幕边界
            screen = QApplication.desktop().availableGeometry()
            if new_pos.x() < 0:
                new_pos.setX(0)
            elif new_pos.x() + self.width() > screen.width():
                new_pos.setX(screen.width() - self.width())
                
            if new_pos.y() < 0:
                new_pos.setY(0)
            elif new_pos.y() + self.height() > screen.height():
                new_pos.setY(screen.height() - self.height())
            
            # 记录新位置
            self._last_pos = new_pos
            
            self.move(new_pos)
            
            # 确保33娘始终在最前面，但不抢夺焦点
            self.raise_()
            
            # 更新对话气泡位置 - 检查是否存在
            if self.speech_bubble:
                # 气泡显示在33娘左侧，减少距离让气泡更靠近33娘
                bubble_pos = QPoint(new_pos.x() - self.speech_bubble.width() + 15, 
                                  new_pos.y() + 30)
                
                # 确保气泡不超出屏幕左边界
                if bubble_pos.x() < 0:
                    bubble_pos.setX(0)
                
                self.speech_bubble.move(bubble_pos)
                # 确保气泡也在最前面，但不抢夺焦点
                self.speech_bubble.raise_()
            
            self.position_changed.emit(new_pos)
        except Exception as e:
            print(f"更新位置失败: {e}")
    
    def updateBubblePosition(self):
        """更新对话气泡位置（独立于跟随目标）"""
        if not self.speech_bubble:
            return
            
        try:
            # 获取33娘当前位置
            current_pos = self.pos()
            
            # 计算气泡位置（在33娘左侧）
            bubble_pos = QPoint(current_pos.x() - self.speech_bubble.width() + 15, 
                              current_pos.y() + 30)
            
            # 确保气泡不超出屏幕边界
            screen = QApplication.desktop().availableGeometry()
            if bubble_pos.x() < 0:
                bubble_pos.setX(0)
            if bubble_pos.y() < 0:
                bubble_pos.setY(0)
            elif bubble_pos.y() + self.speech_bubble.height() > screen.height():
                bubble_pos.setY(screen.height() - self.speech_bubble.height())
            
            # 设置气泡位置
            self.speech_bubble.move(bubble_pos)
            print(f"更新气泡位置: {bubble_pos.x()}, {bubble_pos.y()}")
            
            # 确保气泡在最前面
            self.speech_bubble.raise_()
            
        except Exception as e:
            print(f"更新气泡位置失败: {e}")
    
    def checkStudyStatus(self):
        """检查学习状态"""
        if not self.enabled:
            return
            
        try:
            # 检查OBS模式状态
            self.checkOBSMode()
            
            # 如果在OBS模式下，隐藏33娘
            if self.obs_mode:
                self.hide()
                if self.speech_bubble:
                    self.speech_bubble.hide()
                return
            else:
                self.show()
            
            # 获取学习状态
            status = self.getStudyStatus()
            
            # 总是调用handleStatusChange，让它内部判断是否需要触发台词
            # 这样可以支持定期重复DEFAULT台词功能
            self.handleStatusChange(status)
            self.last_status = status
                
        except Exception as e:
            print(f"检查学习状态失败: {e}")
    
    def checkOBSMode(self):
        """检查是否处于OBS模式"""
        try:
            # 从music_playing_status.json读取streaming_mode状态
            status_path = os.path.join(os.path.dirname(__file__), "music_playing_status.json")
            if os.path.exists(status_path):
                with open(status_path, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
                self.obs_mode = status_data.get('streaming_mode', False)
            else:
                # 如果文件不存在，从配置文件读取
                config_path = os.path.join(os.path.dirname(__file__), "config.json")
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    self.obs_mode = config_data.get('streaming_mode', False)
        except Exception as e:
            print(f"检查OBS模式失败: {e}")
    
    def getStudyStatus(self):
        """获取学习状态"""
        try:
            # 读取今天的CSV文件
            today = datetime.now().strftime("%Y-%m-%d")
            csv_path = os.path.join("statistics", "five_minute_logs", f"五分钟记录_{today}.csv")
            
            # 获取学习时长信息
            study_duration_hours = self.getStudyDuration()
            study_time_string = self.getStudyTimeString()
            level = self.getLevelByHours(study_duration_hours)
            
            if not os.path.exists(csv_path):
                return {
                    "studying": False, 
                    "efficient": False,
                    "study_time_string": study_time_string,
                    "study_duration_hours": study_duration_hours,
                    "level": level
                }
            
            # 读取最新状态
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) <= 1:  # 只有标题行
                    return {
                        "studying": False, 
                        "efficient": False,
                        "study_time_string": study_time_string,
                        "study_duration_hours": study_duration_hours,
                        "level": level
                    }
                
                last_line = lines[-1].strip()
                parts = last_line.split(',')
                if len(parts) >= 2:
                    time_str = parts[0]
                    status = parts[1]
                    
                    # 检查时间差
                    now = datetime.now()
                    record_time = datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %H:%M")
                    time_diff = (now - record_time).total_seconds() / 60
                    
                    if time_diff <= 7:  # 7分钟内的记录有效
                        return {
                            "studying": True,
                            "efficient": status == "高效",
                            "study_time_string": study_time_string,
                            "study_duration_hours": study_duration_hours,
                            "level": level
                        }
            
            return {
                "studying": False, 
                "efficient": False,
                "study_time_string": study_time_string,
                "study_duration_hours": study_duration_hours,
                "level": level
            }
        except Exception as e:
            print(f"获取学习状态失败: {e}")
            return {
                "studying": False, 
                "efficient": False,
                "study_time_string": "0时0分",
                "study_duration_hours": 0.0,
                "level": "C"
            }
    
    def getStudyDuration(self):
        """获取当前学习时长（小时）"""
        try:
            button_data_path = os.path.join(os.path.dirname(__file__), "floating_button_data.json")
            if os.path.exists(button_data_path):
                with open(button_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                study_time = data.get('study_time', '0时0分')
                
                # 解析时长
                import re
                match = re.match(r'(\d+)时(\d+)分', study_time)
                if match:
                    hours = int(match.group(1))
                    minutes = int(match.group(2))
                    return hours + minutes / 60.0
            return 0.0
        except Exception as e:
            print(f"获取学习时长失败: {e}")
            return 0.0
    
    def getStudyTimeString(self):
        """获取学习时长字符串"""
        try:
            button_data_path = os.path.join(os.path.dirname(__file__), "floating_button_data.json")
            if os.path.exists(button_data_path):
                with open(button_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('study_time', '0时0分')
            return '0时0分'
        except Exception as e:
            print(f"获取学习时长字符串失败: {e}")
            return '0时0分'
    
    def getLevelByHours(self, hours):
        """根据学习时长获取等级"""
        if not self.speech_data or 'study_duration_levels' not in self.speech_data:
            return 'C'
        
        for level_info in self.speech_data['study_duration_levels']:
            if level_info['range'][0] <= hours < level_info['range'][1]:
                return level_info['level']
        return 'C'
    
    def handleStatusChange(self, status):
        """处理状态变化"""
        try:
            # 检查学习时长是否发生变化
            current_study_time = status.get("study_time_string", "0时0分")
            study_time_changed = (self.last_study_time_string != current_study_time)
            
            if study_time_changed:
                print(f"学习时长变化: {self.last_study_time_string} -> {current_study_time}")
                self.last_study_time_string = current_study_time
            
            # 获取当前时间戳
            current_time = time.time()
            
            # 获取配置信息
            default_repeat_interval = 300  # 默认5分钟间隔（秒）
            if self.speech_data and 'config' in self.speech_data:
                default_repeat_interval = self.speech_data['config'].get('default_repeat_interval', 300000) / 1000  # 转换为秒
            
            if not status["studying"]:
                # 未学习状态 - 使用惊诧表情
                self.loadExpression(7)
                self.is_in_default_state = True
                
                # 检查是否需要播放DEFAULT台词
                # 1. 学习时长发生变化时
                # 2. 距离上次DEFAULT台词已经过了指定间隔时间
                should_play_default = (
                    study_time_changed or 
                    (current_time - self.last_default_speech_time > default_repeat_interval)
                )
                
                if should_play_default:
                    print(f"触发DEFAULT台词 - 时长变化: {study_time_changed}, 时间间隔: {current_time - self.last_default_speech_time:.1f}秒")
                    self.last_default_speech_time = current_time
                    self.showRandomSpeech("DEFAULT")
                    
            elif status["efficient"]:
                # 高效学习状态 - 使用开心表情
                self.loadExpression(2)
                
                # 如果从未学习状态转为学习状态，重置标志
                if self.is_in_default_state:
                    self.is_in_default_state = False
                
                # 只有在学习时长变化时才触发台词
                if study_time_changed:
                    # 5%概率显示EFFICIENT台词，95%概率显示等级台词
                    if self.speech_data:
                        efficient_chance = self.speech_data.get('config', {}).get('efficient_chance', 0.05)
                        import random
                        if random.random() < efficient_chance:
                            self.showRandomSpeech("EFFICIENT")
                        else:
                            # 显示等级对应台词
                            level = status.get("level", "C")
                            self.showRandomSpeech(level, is_duration=True)
                    
            else:
                # 学习但不够专注 - 使用生气表情
                self.loadExpression(1)
                
                # 如果从未学习状态转为学习状态，重置标志
                if self.is_in_default_state:
                    self.is_in_default_state = False
                
                # 只有在学习时长变化时才触发台词
                if study_time_changed:
                    self.showRandomSpeech("NORMAL")
                
        except Exception as e:
            print(f"处理状态变化失败: {e}")
    
    def stopCurrentSpeech(self):
        """停止当前台词播放序列"""
        # 停止音频播放
        if self.audio_playing and AUDIO_AVAILABLE:
            pygame.mixer.music.stop()
            self.audio_playing = False
            print("强制停止音频播放")
        
        # 取消所有相关的定时器
        for timer in self.speech_sequence_timers:
            if timer and timer.isActive():
                timer.stop()
        self.speech_sequence_timers.clear()
        
        if self.current_audio_timer and self.current_audio_timer.isActive():
            self.current_audio_timer.stop()
            self.current_audio_timer = None
            
        # 隐藏气泡
        if self.speech_bubble:
            self.speech_bubble.hideBubble()
            
        print("已停止当前台词播放序列")
    
    def showRandomSpeech(self, category, is_duration=False):
        """显示随机台词"""
        try:
            if not self.speech_data or not self.speech_bubble:
                if not self.speech_bubble:
                    print("对话气泡尚未创建，跳过台词显示")
                return
            
            # 在开始新台词前，停止当前正在播放的台词
            if self.audio_playing or self.speech_sequence_timers:
                print("检测到正在播放的台词，停止当前播放")
                self.stopCurrentSpeech()
            
            # 确保气泡位置正确
            self.updateBubblePosition()
                
            comments = []
            if is_duration:
                comments = self.speech_data.get('duration_comments', {}).get(category, [])
            else:
                if category in ["DEFAULT", "NORMAL", "EFFICIENT"]:
                    comments = self.speech_data.get('expressions_comments', {}).get(category, [])
                else:
                    comments = self.speech_data.get('learning_comments', {}).get(category, [])
            
            if comments:
                import random
                comment_index = random.randint(0, len(comments) - 1)
                comment = comments[comment_index]
                
                # 获取音频配置
                audio_config = self.speech_data.get('config', {})
                audio_path = audio_config.get('audio_path', './audio33/')
                
                # 构建音频文件路径
                if is_duration:
                    audio_prefix = category
                else:
                    audio_prefix = comment.get('audio_prefix', category)
                
                # 显示日文台词并播放日文音频
                jp_text = comment.get('jp', '')
                self.speech_bubble.setText(jp_text)
                self.speech_bubble.showBubble()  # 不设置时长，手动控制
                
                # 播放日文音频并获取时长
                jp_audio_path = os.path.join(audio_path, f"{audio_prefix}{comment_index + 1}.wav")
                jp_duration = self.playAudio(jp_audio_path)
                
                # 根据日文音频时长决定等待时间
                if jp_duration and jp_duration > 0:
                    # 音频时长 + 0.5秒缓冲时间
                    wait_time = int((jp_duration + 0.5) * 1000)
                else:
                    # 如果获取不到时长，使用默认1秒
                    wait_time = 1000
                
                print(f"日文音频时长: {jp_duration}秒, 等待时间: {wait_time}毫秒")
                
                # 创建定时器等待日文音频播放完成后显示中文台词
                zh_text = comment.get('zh', '')
                zh_timer = QTimer()
                zh_timer.setSingleShot(True)
                zh_timer.timeout.connect(lambda: self.showChineseWithAudio(zh_text, audio_path, audio_prefix, comment_index))
                zh_timer.start(wait_time)
                
                # 将定时器加入管理列表
                self.speech_sequence_timers.append(zh_timer)
                self.current_audio_timer = zh_timer
                
        except Exception as e:
            print(f"显示台词失败: {e}")
    
    def showChineseText(self, text):
        """显示中文台词"""
        if self.speech_bubble:
            self.speech_bubble.setText(text)
            self.speech_bubble.showBubble(3000)
    
    def playAudio(self, audio_path):
        """播放音频文件"""
        if not AUDIO_AVAILABLE:
            print("音频功能不可用")
            return False
            
        try:
            if os.path.exists(audio_path):
                # 停止当前正在播放的音频
                if self.audio_playing:
                    pygame.mixer.music.stop()
                    print("停止之前的音频播放")
                
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                self.audio_playing = True
                print(f"播放音频: {audio_path}")
                
                # 获取音频文件时长（秒）
                sound = pygame.mixer.Sound(audio_path)
                duration = sound.get_length()
                
                # 设置音频播放完成的回调
                def on_audio_finished():
                    self.audio_playing = False
                    print("音频播放完成")
                
                # 在音频时长后标记播放完成
                QTimer.singleShot(int(duration * 1000), on_audio_finished)
                
                return duration  # 返回音频时长
            else:
                print(f"音频文件不存在: {audio_path}")
                return False
        except Exception as e:
            print(f"播放音频失败: {e}")
            self.audio_playing = False
            return False
    
    def showChineseWithAudio(self, text, audio_path, audio_prefix, comment_index):
        """显示中文台词并播放中文音频"""
        if self.speech_bubble:
            self.speech_bubble.setText(text)
            self.speech_bubble.showBubble()  # 不设置时长，手动控制
            
            # 播放中文音频并获取时长
            zh_audio_path = os.path.join(audio_path, f"{audio_prefix}{comment_index + 1}中.wav")
            zh_duration = self.playAudio(zh_audio_path)
            
            # 根据中文音频时长决定气泡显示时间
            if zh_duration and zh_duration > 0:
                # 音频时长 + 1秒展示时间
                display_time = int((zh_duration + 1.0) * 1000)
            else:
                # 如果获取不到时长，使用默认3秒
                display_time = 3000
            
            print(f"中文音频时长: {zh_duration}秒, 显示时间: {display_time}毫秒")
            
            # 创建定时器来隐藏气泡
            hide_timer = QTimer()
            hide_timer.setSingleShot(True)
            hide_timer.timeout.connect(self.speech_bubble.hideBubble)
            hide_timer.start(display_time)
            
            # 将定时器加入管理列表
            self.speech_sequence_timers.append(hide_timer)
    
    def setEnabled(self, enabled):
        """设置启用状态"""
        self.enabled = enabled
        if enabled:
            was_hidden = not self.isVisible()
            self.show()
            self.updatePosition()
            # 只在从隐藏变为显示时激活窗口
            if was_hidden:
                self.activateWindow()
            self.raise_()
        else:
            self.hide()
            if self.speech_bubble:
                self.speech_bubble.hide()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start = event.pos()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging and event.buttons() == Qt.LeftButton:
            # 计算新的偏移量
            new_offset = self.offset + (event.pos() - self.drag_start)
            self.offset = new_offset
            self.updatePosition()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止当前台词播放
        self.stopCurrentSpeech()
        
        if self.speech_bubble:
            self.speech_bubble.close()
        super().closeEvent(event)
    
    def testAudioTiming(self):
        """测试音频时机 - 模拟完整的日语->中文对话流程"""
        if not self.speech_bubble:
            print("对话气泡未初始化")
            return
            
        # 模拟一个简单的对话
        test_comment = {
            "jp": "にゃん〜テストだよ！",
            "zh": "喵~这是测试！"
        }
        
        print("开始测试音频时机...")
        
        # 确保气泡位置正确
        self.updateBubblePosition()
        
        # 显示日文
        self.speech_bubble.setText(test_comment["jp"])
        self.speech_bubble.showBubble()
        
        # 模拟日文音频播放（2秒）
        print("模拟播放日文音频（2秒）...")
        
        # 2.5秒后切换到中文
        QTimer.singleShot(2500, lambda: self.showTestChinese(test_comment["zh"]))
    
    def showTestChinese(self, zh_text):
        """显示测试中文台词"""
        if self.speech_bubble:
            print("切换到中文台词")
            self.speech_bubble.setText(zh_text)
            self.speech_bubble.showBubble()
            
            # 模拟中文音频播放（1.5秒），然后隐藏气泡
            print("模拟播放中文音频（1.5秒）...")
            QTimer.singleShot(2500, self.speech_bubble.hideBubble)
    
    def testNoAudioMode(self):
        """测试无音频模式 - 只显示气泡文字"""
        if not self.speech_bubble:
            print("对话气泡未初始化")
            return
            
        # 模拟一个较长的对话测试自适应大小
        test_texts = [
            "短文本测试",
            "这是一个中等长度的文本测试，用来检查气泡是否能正确适应文字长度",
            "にゃん〜ご主人様、今日の計画表は食べられちゃったのかな？毎日頑張っているのに、なかなか進歩が見えないみたい。でも大丈夫！33娘がずっと応援してるから〜♪"
        ]
        
        def show_next_text(index):
            if index < len(test_texts):
                text = test_texts[index]
                print(f"显示第{index + 1}个测试文本: {text[:20]}...")
                self.speech_bubble.setText(text)
                self.speech_bubble.showBubble()
                
                # 3秒后显示下一个文本
                QTimer.singleShot(3000, lambda: show_next_text(index + 1))
            else:
                print("无音频模式测试完成")
                self.speech_bubble.hideBubble()
        
        show_next_text(0)
    
    def testAudioConflict(self):
        """测试音频冲突处理 - 快速触发多个台词"""
        if not self.speech_bubble:
            print("对话气泡未初始化")
            return
            
        print("开始测试音频冲突处理...")
        
        # 模拟快速触发多个台词的情况
        test_speeches = [
            {"jp": "第一句日语台词测试", "zh": "第一句中文台词测试"},
            {"jp": "第二句日语台词测试", "zh": "第二句中文台词测试"},
            {"jp": "第三句日语台词测试", "zh": "第三句中文台词测试"}
        ]
        
        def trigger_speech(index):
            if index < len(test_speeches):
                speech = test_speeches[index]
                print(f"\n=== 触发第{index + 1}个台词 ===")
                
                # 模拟showRandomSpeech的逻辑
                if self.audio_playing or self.speech_sequence_timers:
                    print("检测到冲突，将停止当前播放")
                
                # 显示日文
                self.speech_bubble.setText(speech["jp"])
                self.speech_bubble.showBubble()
                
                # 模拟日文音频播放
                print(f"模拟播放日文: {speech['jp']}")
                
                # 1.5秒后显示中文
                zh_timer = QTimer()
                zh_timer.setSingleShot(True) 
                zh_timer.timeout.connect(lambda: self.showConflictTestChinese(speech["zh"], index))
                zh_timer.start(1500)
                
                # 将定时器加入管理（模拟真实情况）
                if not hasattr(self, 'speech_sequence_timers'):
                    self.speech_sequence_timers = []
                self.speech_sequence_timers.append(zh_timer)
                
                # 0.8秒后触发下一个台词（模拟快速切换场景）
                if index < len(test_speeches) - 1:
                    QTimer.singleShot(800, lambda i=index: trigger_speech(i + 1))
        
        trigger_speech(0)
    
    def showConflictTestChinese(self, zh_text, index):
        """显示冲突测试的中文台词"""
        if self.speech_bubble:
            print(f"显示第{index + 1}个台词的中文: {zh_text}")
            self.speech_bubble.setText(zh_text)
            
            # 2秒后隐藏（如果没有被打断）
            QTimer.singleShot(2000, lambda: print(f"第{index + 1}个台词序列完成"))
    
    def create_speech_bubble(self):
        """延迟创建对话气泡"""
        try:
            self.speech_bubble = SpeechBubble()
            self.speech_bubble.parent_pet = self  # 设置父级引用
            
            # 设置初始位置（在33娘左侧）
            initial_pos = QPoint(self.pos().x() - 200, self.pos().y() + 30)
            self.speech_bubble.move(initial_pos)
            
            print("对话气泡创建成功")
        except Exception as e:
            print(f"创建对话气泡失败: {e}")
            self.speech_bubble = None

# 全局33娘实例
neko33_pet = None

def create_neko33_pet():
    """创建33娘实例"""
    global neko33_pet
    if neko33_pet is None:
        neko33_pet = Neko33Pet()
    return neko33_pet

def get_neko33_pet():
    """获取33娘实例"""
    return neko33_pet

def destroy_neko33_pet():
    """销毁33娘实例"""
    global neko33_pet
    if neko33_pet:
        neko33_pet.close()
        neko33_pet = None

# 测试代码
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    pet = Neko33Pet()
    pet.show()
    
    # 设置合理的测试位置
    screen = QApplication.desktop().availableGeometry()
    test_x = min(300, screen.width() - 200)  # 确保不超出屏幕右边界
    test_y = min(200, screen.height() - 200)  # 确保不超出屏幕下边界
    pet.move(test_x, test_y)
    print(f"33娘位置设置为: ({test_x}, {test_y})")
    
    # 3秒后测试DEFAULT台词（模拟未学习状态）
    def test_default_speech():
        print("测试DEFAULT台词...")
        # 模拟未学习状态
        status = {
            "studying": False,
            "efficient": False,
            "study_time_string": "2时30分",
            "study_duration_hours": 2.5,
            "level": "CC"
        }
        pet.handleStatusChange(status)
    
    QTimer.singleShot(3000, test_default_speech)
    
    sys.exit(app.exec_()) 