from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QLineEdit, QFileDialog,
                           QScrollArea, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
import os
import json
import shutil

class ScheduleManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 加载配置
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            self.config = {}
            
        # 创建UI
        self.create_ui()
        
    def create_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        
        # 标题区域
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("昼夜表管理")
        title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        
        subtitle = QLabel("管理昼夜表文件和设置")
        subtitle.setStyleSheet("color: #888888; font-size: 12px;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        # 分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3B3B3B;")
        
        layout.addWidget(title_frame)
        layout.addWidget(separator)
        
        # 设置区域
        self.create_settings_area(layout)
        
        # 文件列表区域
        self.create_files_area(layout)
        
    def create_settings_area(self, layout):
        """创建设置区域"""
        settings_frame = QFrame()
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        # 起始日期设置
        start_date_frame = QFrame()
        start_date_layout = QHBoxLayout(start_date_frame)
        start_date_layout.setContentsMargins(0, 0, 0, 0)
        
        start_date_label = QLabel("起始日期:")
        start_date_label.setStyleSheet("color: #FFFFFF;")
        
        # 日期显示框
        date_display = QFrame()
        date_display.setStyleSheet("""
            QFrame {
                background-color: #2B2B2B;
                border-radius: 6px;
                padding: 5px 10px;
            }
        """)
        date_layout = QHBoxLayout(date_display)
        date_layout.setContentsMargins(10, 5, 10, 5)
        
        self.start_date_label = QLabel(self.config.get('start_date', ''))
        self.start_date_label.setStyleSheet("color: #FFFFFF;")
        date_layout.addWidget(self.start_date_label)
        
        auto_note = QLabel("(自动从第1周文件获取)")
        auto_note.setStyleSheet("color: #888888; font-size: 12px;")
        
        start_date_layout.addWidget(start_date_label)
        start_date_layout.addWidget(date_display)
        start_date_layout.addWidget(auto_note)
        start_date_layout.addStretch()
        
        # Excel目录设置
        excel_path_frame = QFrame()
        excel_layout = QHBoxLayout(excel_path_frame)
        excel_layout.setContentsMargins(0, 0, 0, 0)
        
        excel_label = QLabel("昼夜表目录:")
        excel_label.setStyleSheet("color: #FFFFFF;")
        
        self.excel_path_entry = QLineEdit()
        self.excel_path_entry.setStyleSheet("""
            QLineEdit {
                background-color: #2B2B2B;
                border: none;
                border-radius: 6px;
                padding: 8px;
                color: #FFFFFF;
            }
        """)
        self.excel_path_entry.setText(self.config.get('excel_path', ''))
        
        browse_excel_btn = QPushButton("浏览")
        browse_excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        browse_excel_btn.clicked.connect(self.browse_excel_path)
        
        excel_layout.addWidget(excel_label)
        excel_layout.addWidget(self.excel_path_entry)
        excel_layout.addWidget(browse_excel_btn)
        
        # 模板文件设置
        template_frame = QFrame()
        template_layout = QHBoxLayout(template_frame)
        template_layout.setContentsMargins(0, 0, 0, 0)
        
        template_label = QLabel("模板文件:")
        template_label.setStyleSheet("color: #FFFFFF;")
        
        self.template_path_entry = QLineEdit()
        self.template_path_entry.setStyleSheet("""
            QLineEdit {
                background-color: #2B2B2B;
                border: none;
                border-radius: 6px;
                padding: 8px;
                color: #FFFFFF;
            }
        """)
        self.template_path_entry.setText(self.config.get('template_path', ''))
        
        browse_template_btn = QPushButton("浏览")
        browse_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        browse_template_btn.clicked.connect(self.browse_template_path)
        
        open_template_btn = QPushButton("打开")
        open_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        open_template_btn.clicked.connect(lambda: self.open_file(self.template_path_entry.text()))
        
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_path_entry)
        template_layout.addWidget(browse_template_btn)
        template_layout.addWidget(open_template_btn)
        
        settings_layout.addWidget(start_date_frame)
        settings_layout.addWidget(excel_path_frame)
        settings_layout.addWidget(template_frame)
        
        layout.addWidget(settings_frame)

    def create_files_area(self, layout):
        """创建文件列表区域"""
        # 文件列表标题
        files_title_frame = QFrame()
        files_title_layout = QHBoxLayout(files_title_frame)
        files_title_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("昼夜表文件列表")
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        refresh_btn.clicked.connect(self.update_file_list)
        
        files_title_layout.addWidget(title)
        files_title_layout.addStretch()
        files_title_layout.addWidget(refresh_btn)
        
        # 文件列表滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #2B2B2B;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #404040;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 文件列表容器
        self.files_frame = QFrame()
        self.files_frame.setStyleSheet("background-color: transparent;")
        scroll_area.setWidget(self.files_frame)
        
        layout.addWidget(files_title_frame)
        layout.addWidget(scroll_area)
        
        # 初始化文件列表
        self.update_file_list()

    def browse_excel_path(self):
        """浏览昼夜表目录"""
        path = QFileDialog.getExistingDirectory(self, "选择昼夜表目录")
        if path:
            path = path.replace('\\', '/')
            self.excel_path_entry.setText(path)

    def browse_template_path(self):
        """浏览模板文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择模板文件",
            "",
            "Excel files (*.xls *.xlsx)"
        )
        if path:
            path = path.replace('\\', '/')
            self.template_path_entry.setText(path)

    def save_settings(self):
        """保存设置"""
        try:
            # 自动更新起始日期
            start_date = self.get_start_date_from_files()
            if start_date:
                self.start_date_label.setText(start_date)
            
            # 更新配置
            self.config['start_date'] = self.start_date_label.text()
            self.config['excel_path'] = self.excel_path_entry.text().replace('\\', '/')
            self.config['template_path'] = self.template_path_entry.text().replace('\\', '/')
            
            # 保存配置
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            QMessageBox.information(self, "成功", "设置已保存")
            # 更新文件列表
            self.update_file_list()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置时出错: {str(e)}")

    def create_current_week_file(self):
        """创建本周昼夜表"""
        try:
            file_name = self.get_current_week_filename()
            if not file_name:
                QMessageBox.warning(self, "警告", "无法获取当前周文件名")
                return
            
            target_path = os.path.join(self.excel_path_entry.text(), file_name).replace('\\', '/')
            template_path = self.template_path_entry.text().replace('\\', '/')
            
            if os.path.exists(target_path):
                # 高亮显示已存在的文件
                self.update_file_list(highlight_file=file_name)
                
                reply = QMessageBox.question(
                    self, 
                    "确认覆盖", 
                    f"文件 {file_name} 已存在，是否覆盖？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    shutil.copy2(template_path, target_path)
                    QMessageBox.information(self, "成功", f"已覆盖本周昼夜表：{file_name}")
                
                self.update_file_list()
            else:
                shutil.copy2(template_path, target_path)
                QMessageBox.information(self, "成功", f"已创建本周昼夜表：{file_name}")
                self.update_file_list()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建昼夜表时出错: {str(e)}")

    def update_file_list(self, highlight_file=None):
        """更新文件列表显示"""
        # 清除现有列表
        layout = QVBoxLayout(self.files_frame)
        for i in reversed(range(layout.count())): 
            layout.itemAt(i).widget().setParent(None)
        
        try:
            current_week_file = self.get_current_week_filename()
            excel_path = self.excel_path_entry.text().replace('\\', '/')
            
            if os.path.exists(excel_path):
                files = [f for f in os.listdir(excel_path) if f.endswith('.xls')]
                
                if not files:
                    # 目录为空时显示提示
                    message_frame = QFrame()
                    message_layout = QVBoxLayout(message_frame)
                    
                    message = QLabel("目录为空，是否创建本周的昼夜表？")
                    message.setStyleSheet("color: #FFFFFF;")
                    
                    create_btn = QPushButton("创建第一周昼夜表")
                    create_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #32CD32;
                            border: none;
                            border-radius: 6px;
                            padding: 8px 15px;
                            color: white;
                        }
                        QPushButton:hover {
                            background-color: #228B22;
                        }
                    """)
                    create_btn.clicked.connect(self.create_first_week_file)
                    
                    message_layout.addWidget(message, alignment=Qt.AlignmentFlag.AlignCenter)
                    message_layout.addWidget(create_btn, alignment=Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(message_frame)
                    return
                
                # 按周数排序
                files.sort(key=lambda x: int(x[x.find('第')+1:x.find('周')]), reverse=True)
                
                # 创建网格布局
                grid_frame = QFrame()
                grid = QGridLayout(grid_frame)
                grid.setSpacing(2)
                
                # 分配文件到网格
                for i, file in enumerate(files):
                    row = i // 3
                    col = i % 3
                    
                    # 创建文件按钮框架
                    file_frame = QFrame()
                    if file == highlight_file:
                        file_frame.setStyleSheet("background-color: #FF4D4D; border-radius: 6px;")
                    elif file == current_week_file:
                        file_frame.setStyleSheet("background-color: #363636; border-radius: 6px;")
                    else:
                        file_frame.setStyleSheet("background-color: transparent;")
                    
                    file_layout = QVBoxLayout(file_frame)
                    file_layout.setContentsMargins(2, 2, 2, 2)
                    
                    file_btn = QPushButton(file)
                    file_btn.setStyleSheet("""
                        QPushButton {
                            text-align: left;
                            padding: 8px;
                            border: none;
                            border-radius: 6px;
                            color: white;
                            background-color: transparent;
                        }
                        QPushButton:hover {
                            background-color: #404040;
                        }
                    """)
                    file_btn.clicked.connect(
                        lambda checked, f=file: self.open_file(
                            os.path.join(excel_path, f).replace('\\', '/')
                        )
                    )
                    
                    file_layout.addWidget(file_btn)
                    grid.addWidget(file_frame, row, col)
                
                layout.addWidget(grid_frame)
                
        except Exception as e:
            error_label = QLabel(f"读取文件列表失败: {str(e)}")
            error_label.setStyleSheet("color: #FF6B6B;")
            layout.addWidget(error_label)

    def get_current_week_filename(self):
        """获取当前周的文件名"""
        try:
            today = datetime.now()
            start_date = datetime.strptime(self.config['start_date'], '%Y-%m-%d')
            
            days_difference = (today - start_date).days
            week_number = days_difference // 7 + 1
            
            start_of_week = start_date + timedelta(weeks=(week_number - 1))
            end_of_week = start_of_week + timedelta(days=6)
            
            return f"第{week_number}周({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')}).xls"
        except:
            return ""

    def get_start_date_from_files(self):
        """从第一周文件名获取起始日期"""
        try:
            excel_path = self.excel_path_entry.text().replace('\\', '/')
            if os.path.exists(excel_path):
                files = [f for f in os.listdir(excel_path) if f.endswith('.xls')]
                first_week_file = next((f for f in files if f.startswith('第1周')), None)
                if first_week_file:
                    date_str = first_week_file[first_week_file.find('(')+1:first_week_file.find('~')]
                    month, day = date_str.split('.')
                    year = datetime.now().year
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except Exception as e:
            print(f"获取起始日期失败: {str(e)}")
        return self.config.get('start_date', '')

    def open_file(self, file_path):
        """打开文件"""
        try:
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")

    def create_first_week_file(self):
        """创建第一周昼夜表"""
        try:
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            
            file_name = f"第1周({monday.strftime('%m.%d')}~{sunday.strftime('%m.%d')}).xls"
            target_path = os.path.join(self.excel_path_entry.text(), file_name).replace('\\', '/')
            template_path = self.template_path_entry.text().replace('\\', '/')
            
            shutil.copy2(template_path, target_path)
            QMessageBox.information(self, "成功", f"已创建第一周昼夜表：{file_name}")
            
            self.start_date_label.setText(monday.strftime('%Y-%m-%d'))
            self.save_settings()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建第一周昼夜表时出错: {str(e)}")