from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QLineEdit, QComboBox,
                           QScrollArea, QMessageBox, QFileDialog, QListWidget,
                           QDialog, QMainWindow)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDrag, QDragEnterEvent, QDropEvent
import json
import os
import threading
from pygame import mixer
import shutil
import sys
from PyQt6.QtWidgets import QApplication

class LevelItem(QFrame):
    """等级项组件"""
    dragStarted = pyqtSignal(QWidget)  # 自定义信号用于通知拖拽开始
    
    def __init__(self, name, songs, parent=None):
        super().__init__(parent)
        self.name = name
        self.songs = songs
        self.init_ui()
        
        # 启用拖放
        self.setAcceptDrops(True)
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 设置样式
        self.setStyleSheet(self.get_style())
        self.setFixedHeight(50)
        
        # 拖动手柄
        handle = QLabel("⋮⋮")
        handle.setStyleSheet("color: #888888; padding: 0 5px;")
        handle.setCursor(Qt.CursorShape.OpenHandCursor)
        
        # 等级名称
        name_label = QLabel(self.name)
        name_label.setStyleSheet("color: white;")
        
        # 歌曲数量输入框
        self.songs_input = QLineEdit(str(self.songs))
        self.songs_input.setFixedWidth(50)
        self.songs_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.songs_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(0, 0, 0, 30);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        self.songs_input.textChanged.connect(self.validate_songs)
        
        # 时间线
        self.timeline = QFrame()
        self.timeline.setFrameShape(QFrame.Shape.HLine)
        self.timeline.setStyleSheet("background-color: #1F6AA5;")
        
        # 时间标签
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: white;")
        self.update_time_label()
        
        # 添加到布局
        layout.addWidget(handle)
        layout.addWidget(name_label)
        layout.addWidget(self.songs_input)
        layout.addWidget(QLabel("首"))
        layout.addWidget(self.timeline, 1)  # 1表示拉伸因子
        layout.addWidget(self.time_label)
        
        # 存储拖拽起始位置
        self.drag_start_position = None
    
    def get_style(self):
        """根据等级获取样式"""
        colors = {
            'S': ("#FFD700", "#000000"),  # 背景色, 文字色
            'A': ("#FF4D4D", "#000000"),
            'B': ("#4169E1", "#FFFFFF"),
            'C': ("#98FB98", "#000000")
        }
        
        for rank, (bg_color, text_color) in colors.items():
            if rank in self.name:
                return f"""
                    QFrame {{
                        background-color: {bg_color};
                        border-radius: 8px;
                    }}
                    QLabel {{
                        color: {text_color};
                    }}
                    QLineEdit {{
                        color: {text_color};
                    }}
                """
        
        # 默认样式
        return """
            QFrame {
                background-color: #2B2B2B;
                border-radius: 8px;
            }
        """
    
    def validate_songs(self):
        """验证歌曲数量输入"""
        try:
            value = int(self.songs_input.text())
            if value < 1:
                raise ValueError
            self.songs = value
            self.update_time_label()
        except ValueError:
            self.songs_input.setText(str(self.songs))
    
    def update_time_label(self):
        """更新时间标签"""
        hours = self.songs * 0.5  # 每首歌0.5小时
        self.time_label.setText(f"{hours:.1f}h")
    
    def mousePressEvent(self, event):
        """记录鼠标按下位置"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
    
    def mouseMoveEvent(self, event):
        """处理拖拽"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not self.drag_start_position:
            return
            
        # 检查是否达到拖拽的最小距离
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return
            
        # 创建拖拽对象
        drag = QDrag(self)
        # 发送拖拽开始信号
        self.dragStarted.emit(self)
        
        # 开始拖拽
        drag.exec(Qt.DropAction.MoveAction)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """处理拖拽进入"""
        if event.source() is not self:
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """处理放下事件"""
        event.acceptProposedAction()

class LevelManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化pygame mixer
        mixer.init()
        
        # 设置默认字体
        self.default_font = QFont("微软雅黑", 12)
        self.title_font = QFont("微软雅黑", 16, QFont.Weight.Bold)
        self.subtitle_font = QFont("微软雅黑", 10)
        
        # 初始化UI
        self.init_ui()
        
        # 加载配置
        self.load_default_levels()
        
    def init_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # 创建设置区域
        self.create_settings_area()
        
        # 创建等级管理区域
        self.create_level_area()
        
        # 创建底部按钮
        self.create_bottom_buttons()
        
    def create_settings_area(self):
        # 设置区域框架
        settings_frame = QFrame()
        settings_frame.setStyleSheet("QFrame { background-color: #2B2B2B; border-radius: 8px; }")
        settings_layout = QVBoxLayout(settings_frame)
        
        # 字体设置
        font_frame = QFrame()
        font_layout = QHBoxLayout(font_frame)
        
        font_label = QLabel("系统字体:")
        font_label.setStyleSheet("color: white;")
        font_label.setFont(self.default_font)
        
        self.font_combo = QComboBox()
        self.font_combo.setStyleSheet("""
            QComboBox {
                background-color: #363636;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.font_combo.addItems(self.get_recent_fonts())
        self.font_combo.currentTextChanged.connect(self.update_font_preview)
        
        browse_font_btn = QPushButton("浏览")
        browse_font_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        browse_font_btn.clicked.connect(self.browse_font)
        
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_combo)
        font_layout.addWidget(browse_font_btn)
        
        # 音效设置
        self.create_sound_settings()
        
        settings_layout.addWidget(font_frame)
        settings_layout.addWidget(self.sound_frame)
        
        self.layout().addWidget(settings_frame) 

    def create_level_area(self):
        # 等级区域标题
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        
        title = QLabel("配置歌单层级")
        title.setFont(self.title_font)
        title.setStyleSheet("color: white;")
        
        subtitle = QLabel("设置学习激励系统的歌单等级和播放规则")
        subtitle.setFont(self.subtitle_font)
        subtitle.setStyleSheet("color: #888888;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        # 分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3B3B3B;")
        
        # 等级列表滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # 等级列表容器
        self.level_container = QWidget()
        self.level_layout = QVBoxLayout(self.level_container)
        self.scroll_area.setWidget(self.level_container)
        
        # 添加到主布局
        self.layout().addWidget(title_frame)
        self.layout().addWidget(separator)
        self.layout().addWidget(self.scroll_area) 

    def create_sound_settings(self):
        self.sound_frame = QFrame()
        sound_layout = QVBoxLayout(self.sound_frame)
        
        # 半小时音效
        half_hour_frame = QFrame()
        half_hour_layout = QHBoxLayout(half_hour_frame)
        
        half_hour_label = QLabel("半小时音效:")
        half_hour_label.setStyleSheet("color: white;")
        half_hour_label.setFont(self.default_font)
        
        self.half_hour_combo = QComboBox()
        self.half_hour_combo.setStyleSheet("""
            QComboBox {
                background-color: #363636;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                min-width: 300px;
            }
        """)
        self.half_hour_combo.addItems(self.get_sound_files())
        
        play_half_hour_btn = QPushButton("试听")
        play_half_hour_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        play_half_hour_btn.clicked.connect(
            lambda: self.play_sound(self.half_hour_combo.currentText())
        )
        
        half_hour_layout.addWidget(half_hour_label)
        half_hour_layout.addWidget(self.half_hour_combo)
        half_hour_layout.addWidget(play_half_hour_btn)
        
        # 升级音效
        level_up_frame = QFrame()
        level_up_layout = QHBoxLayout(level_up_frame)
        
        level_up_label = QLabel("升级音效:")
        level_up_label.setStyleSheet("color: white;")
        level_up_label.setFont(self.default_font)
        
        self.level_up_combo = QComboBox()
        self.level_up_combo.setStyleSheet("""
            QComboBox {
                background-color: #363636;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                min-width: 300px;
            }
        """)
        self.level_up_combo.addItems(self.get_sound_files())
        
        play_level_up_btn = QPushButton("试听")
        play_level_up_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        play_level_up_btn.clicked.connect(
            lambda: self.play_sound(self.level_up_combo.currentText())
        )
        
        level_up_layout.addWidget(level_up_label)
        level_up_layout.addWidget(self.level_up_combo)
        level_up_layout.addWidget(play_level_up_btn)
        
        # 五分钟音效
        five_min_frame = QFrame()
        five_min_layout = QHBoxLayout(five_min_frame)
        
        five_min_label = QLabel("五分钟音效:")
        five_min_label.setStyleSheet("color: white;")
        five_min_label.setFont(self.default_font)
        
        self.five_min_combo = QComboBox()
        self.five_min_combo.setStyleSheet("""
            QComboBox {
                background-color: #363636;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
                min-width: 300px;
            }
        """)
        self.five_min_combo.addItems(self.get_sound_files())
        
        play_five_min_btn = QPushButton("试听")
        play_five_min_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        play_five_min_btn.clicked.connect(
            lambda: self.play_sound(self.five_min_combo.currentText())
        )
        
        five_min_layout.addWidget(five_min_label)
        five_min_layout.addWidget(self.five_min_combo)
        five_min_layout.addWidget(play_five_min_btn)
        
        # 添加所有框架到主布局
        sound_layout.addWidget(half_hour_frame)
        sound_layout.addWidget(level_up_frame)
        sound_layout.addWidget(five_min_frame)
    
    def create_level_item(self, name, songs):
        """创建新的等级项"""
        item = LevelItem(name, songs)
        item.dragStarted.connect(self.handle_drag_started)
        self.level_layout.addWidget(item)
        return item
    
    def handle_drag_started(self, item):
        """处理等级项开始拖拽"""
        # 显示删除区域
        self.show_delete_zone()
        
        # 保存当前拖拽的项
        self.current_drag_item = item
    
    def show_delete_zone(self):
        """显示删除区域"""
        if not hasattr(self, 'delete_zone'):
            self.delete_zone = QFrame()
            self.delete_zone.setStyleSheet("""
                QFrame {
                    background-color: #D22B2B;
                    border-radius: 8px;
                    min-height: 40px;
                }
            """)
            delete_layout = QHBoxLayout(self.delete_zone)
            delete_label = QLabel("拖拽到此处删除")
            delete_label.setStyleSheet("color: white;")
            delete_layout.addWidget(delete_label, alignment=Qt.AlignmentFlag.AlignCenter)
            
            self.layout().addWidget(self.delete_zone)
    
    def hide_delete_zone(self):
        """隐藏删除区域"""
        if hasattr(self, 'delete_zone'):
            self.delete_zone.hide()
    
    def update_levels_position(self):
        """更新所有等级的位置和时间"""
        total_songs = 0
        current_time = 0.0
        
        # 遍历所有等级项
        for i in range(self.level_layout.count()):
            item = self.level_layout.itemAt(i).widget()
            if isinstance(item, LevelItem):
                total_songs += item.songs
        
        # 再次遍历更新时间线
        for i in range(self.level_layout.count()):
            item = self.level_layout.itemAt(i).widget()
            if isinstance(item, LevelItem):
                duration = item.songs * 0.5
                start_time = current_time
                end_time = current_time + duration
                
                # 更新时间标签
                item.time_label.setText(f"{start_time:.1f}-{end_time:.1f}h")
                
                # 更新时间线宽度
                timeline_width = (duration / (total_songs * 0.5)) * 100
                item.timeline.setFixedWidth(int(timeline_width))
                
                current_time = end_time
    
    def load_default_levels(self):
        """从配置文件加载默认配置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # 加载字体设置
                if 'font' in config:
                    index = self.font_combo.findText(config['font'])
                    if index >= 0:
                        self.font_combo.setCurrentIndex(index)
                        self.update_font_preview()
                
                # 加载音效设置
                if 'half_hour_effect' in config:
                    filename = os.path.basename(config['half_hour_effect'])
                    index = self.half_hour_combo.findText(filename)
                    if index >= 0:
                        self.half_hour_combo.setCurrentIndex(index)
                
                if 'level_up_effect' in config:
                    filename = os.path.basename(config['level_up_effect'])
                    index = self.level_up_combo.findText(filename)
                    if index >= 0:
                        self.level_up_combo.setCurrentIndex(index)
                
                if 'five_minute_effect' in config:
                    filename = os.path.basename(config['five_minute_effect'])
                    index = self.five_min_combo.findText(filename)
                    if index >= 0:
                        self.five_min_combo.setCurrentIndex(index)
                
                # 加载等级配置
                if 'levels' in config:
                    # 清除现有等级
                    self.clear_levels()
                    
                    # 添加新等级
                    for level_config in config['levels']:
                        songs = int((level_config['end'] - level_config['start']) * 2)
                        self.create_level_item(level_config['name'], songs)
                    
                    # 更新位置
                    self.update_levels_position()
        
        except FileNotFoundError:
            QMessageBox.warning(self, "警告", "未找到配置文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载配置失败: {str(e)}")
    
    def save_config(self):
        """保存配置到JSON文件"""
        try:
            # 先读取现有配置以保留其他设置
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
                    preserved_keys = ['start_date', 'excel_path', 'template_path']
                    preserved_config = {
                        key: existing_config[key]
                        for key in preserved_keys
                        if key in existing_config
                    }
            except:
                preserved_config = {}
            
            # 创建新配置
            config = {
                'font': self.font_combo.currentText(),
                'half_hour_effect': os.path.join("music_library", "音效", 
                                               self.half_hour_combo.currentText()),
                'level_up_effect': os.path.join("music_library", "音效", 
                                              self.level_up_combo.currentText()),
                'five_minute_effect': os.path.join("music_library", "音效", 
                                                 self.five_min_combo.currentText()),
                'levels': [],
                'recent_fonts': self.update_recent_fonts(self.font_combo.currentText()),
                **preserved_config  # 合并保留的配置
            }
            
            # 收集等级配置
            current_time = 0.0
            for i in range(self.level_layout.count()):
                item = self.level_layout.itemAt(i).widget()
                if isinstance(item, LevelItem):
                    duration = item.songs * 0.5
                    level_config = {
                        'name': item.name,
                        'start': current_time,
                        'end': current_time + duration,
                        'random_count': item.songs
                    }
                    config['levels'].append(level_config)
                    current_time += duration
            
            # 保存到文件
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            QMessageBox.information(self, "成功", "配置已保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
    
    def clear_levels(self):
        """清除所有等级项"""
        while self.level_layout.count():
            item = self.level_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
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
    
    def get_recent_fonts(self):
        """获取最近使用的字体列表"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('recent_fonts', ['微软雅黑'])
        except:
            return ['微软雅黑']
    
    def get_sound_files(self):
        """获取音效文件列表"""
        sound_dir = os.path.join("music_library", "音效")
        try:
            if not os.path.exists(sound_dir):
                os.makedirs(sound_dir)
            return [f for f in os.listdir(sound_dir) 
                   if f.endswith(('.mp3', '.wav'))]
        except Exception as e:
            QMessageBox.warning(self, "警告", f"读取音效文件失败: {str(e)}")
            return []
    
    def play_sound(self, sound_file):
        """播放音效"""
        def play():
            try:
                full_path = os.path.join("music_library", "音效", sound_file)
                mixer.music.load(full_path)
                mixer.music.play()
            except Exception as e:
                QMessageBox.warning(self, "警告", f"播放音效失败: {str(e)}")
        
        threading.Thread(target=play, daemon=True).start()
    
    def browse_font(self):
        """打开字体选择对话框"""
        dialog = FontChooserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_font = dialog.get_selected_font()
            if selected_font:
                # 更新字体下拉框
                recent_fonts = self.update_recent_fonts(selected_font)
                current_index = self.font_combo.currentIndex()
                self.font_combo.clear()
                self.font_combo.addItems(recent_fonts)
                if current_index >= 0:
                    self.font_combo.setCurrentIndex(current_index)
                
                # 更新预览
                self.update_font_preview()
    
    def update_font_preview(self):
        """更新字体预览"""
        try:
            font = QFont(self.font_combo.currentText(), 12)
            self.font_preview.setFont(font)
        except Exception as e:
            print(f"字体预览更新失败: {str(e)}")
    
    def reset_to_default(self):
        """重置为默认配置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要还原默认配置吗？这将丢失当前的所有设置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.load_default_levels()
    
    def create_bottom_buttons(self):
        """创建底部按钮"""
        # 创建按钮容器
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        # 重置按钮
        reset_btn = QPushButton("重置默认")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #363636;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        reset_btn.setFont(self.default_font)
        reset_btn.clicked.connect(self.reset_to_default)
        
        # 保存按钮
        save_btn = QPushButton("保存配置")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        save_btn.setFont(self.default_font)
        save_btn.clicked.connect(self.save_config)
        
        # 添加到布局
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()  # 添加弹性空间
        button_layout.addWidget(save_btn)
        
        # 添加到主布局
        self.layout().addWidget(button_frame)

class FontChooserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_font = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("选择字体")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索字体...")
        self.search_input.textChanged.connect(self.filter_fonts)
        search_layout.addWidget(self.search_input)
        
        # 字体列表
        self.font_list = QListWidget()
        self.font_list.addItems(sorted(QFont.families()))
        self.font_list.currentItemChanged.connect(self.update_preview)
        
        # 预览区域
        self.preview_label = QLabel("字体预览文字")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #2B2B2B;
                color: white;
                padding: 10px;
                border-radius: 4px;
            }
        """)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        # 添加到主布局
        layout.addLayout(search_layout)
        layout.addWidget(self.font_list)
        layout.addWidget(self.preview_label)
        layout.addLayout(button_layout)
    
    def filter_fonts(self, text):
        """过滤字体列表"""
        self.font_list.clear()
        filtered_fonts = [f for f in QFont.families() 
                         if text.lower() in f.lower()]
        self.font_list.addItems(sorted(filtered_fonts))
    
    def update_preview(self, current):
        """更新预览"""
        if current:
            font = QFont(current.text(), 16)
            self.preview_label.setFont(font)
    
    def get_selected_font(self):
        """获取选中的字体"""
        if self.font_list.currentItem():
            return self.font_list.currentItem().text()
        return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建主窗口
    window = QMainWindow()
    window.setWindowTitle("渐进学习激励配置")
    window.setMinimumSize(1000, 600)
    
    # 创建中央部件
    central_widget = QWidget()
    central_layout = QVBoxLayout(central_widget)
    
    # 创建等级管理器
    level_manager = LevelManager()
    central_layout.addWidget(level_manager)
    
    # 设置中央部件
    window.setCentralWidget(central_widget)
    
    # 显示窗口
    window.show()
    
    sys.exit(app.exec())