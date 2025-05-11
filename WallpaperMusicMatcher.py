import sys
import os
import pandas as pd
import json
import pygame
import subprocess  # 导入 subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTableWidget, QTableWidgetItem,
    QLabel, QGridLayout, QHBoxLayout, QVBoxLayout, QMessageBox,
    QScrollArea, QAbstractItemView, QPushButton, QDialog, QRadioButton,
    QButtonGroup, QSlider, QLineEdit, QMenu, QInputDialog
)
from PyQt5.QtGui import QFont, QPixmap, QDrag, QIntValidator  # 导入 QIntValidator
from PyQt5.QtCore import Qt, QMimeData, QTimer, QPoint

# 初始化 pygame mixer
pygame.mixer.init(frequency=48000)
pygame.mixer.music.set_volume(0.8)  # 默认音量80%

class MusicPlayer:
    def __init__(self):
        self.current_song = None
        self.is_playing = False

    def load_song(self, song_path):
        try:
            pygame.mixer.music.load(song_path)
            self.current_song = song_path
            print(f"成功加载音乐: {song_path}")
        except Exception as e:
            print(f"加载音乐失败: {e}")

    def play(self):
        try:
            pygame.mixer.music.play()
            self.is_playing = True
            print(f"播放音乐: {self.current_song}")
        except Exception as e:
            print(f"播放音乐失败: {e}")

class SettingsWindow(QDialog):
    def __init__(self, current_setting, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置壁纸浏览方式")
        self.resize(300, 150)
        self.selected_option = current_setting

        layout = QVBoxLayout()
        self.radio_popup = QRadioButton("弹窗预览")
        self.radio_desktop = QRadioButton("桌面预览")
        if self.selected_option == "popup":
            self.radio_popup.setChecked(True)
        else:
            self.radio_desktop.setChecked(True)

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.radio_popup)
        self.button_group.addButton(self.radio_desktop)

        layout.addWidget(self.radio_popup)
        layout.addWidget(self.radio_desktop)
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def save_settings(self):
        self.selected_option = "popup" if self.radio_popup.isChecked() else "desktop"
        self.accept()

    def get_setting(self):
        return self.selected_option

class MusicTableWidget(QTableWidget):
    def __init__(self, df, music_player, parent=None):
        super().__init__(parent)
        self.df = df
        self.parent_widget = parent
        self.music_player = music_player
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(['歌单', '歌曲', '壁纸引擎ID', '壁纸名称', '所属作品'])
        self.setRowCount(len(df))
        self.populate_table()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setDragEnabled(False)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed | QTableWidget.SelectedClicked)
        self.cellChanged.connect(self.on_cell_changed)
        self.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        # 存储所有已添加的作品标签
        self.work_tags = set()
        self.load_work_tags()

    def load_work_tags(self):
        """加载已有的作品标签"""
        if '所属作品' in self.df.columns:
            for tag in self.df['所属作品'].dropna().unique():
                if isinstance(tag, str) and tag.strip():
                    for single_tag in tag.split(','):
                        if single_tag.strip():
                            self.work_tags.add(single_tag.strip())

    def populate_table(self):
        for row in range(len(self.df)):
            # 简化歌单名称
            full_playlist = self.df.at[row, '歌单']
            simplified_playlist = self.simplify_playlist_name(full_playlist)

            # 设置"歌单"列为简化后的名称
            item_playlist = QTableWidgetItem(simplified_playlist)
            item_playlist.setFlags(item_playlist.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 0, item_playlist)

            # 设置"歌曲"列
            item_song = QTableWidgetItem(str(self.df.at[row, '歌曲']))
            item_song.setFlags(item_song.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 1, item_song)

            # 设置"壁纸引擎ID"列
            item_wallpaper_id = QTableWidgetItem(str(self.df.at[row, '壁纸引擎ID']))
            item_wallpaper_id.setFlags(item_wallpaper_id.flags() | Qt.ItemIsEditable)
            self.setItem(row, 2, item_wallpaper_id)
            
            # 设置"壁纸名称"列
            wallpaper_name = ""
            if '壁纸名称' in self.df.columns and not pd.isna(self.df.at[row, '壁纸名称']):
                wallpaper_name = str(self.df.at[row, '壁纸名称'])
            item_wallpaper_name = QTableWidgetItem(wallpaper_name)
            item_wallpaper_name.setFlags(item_wallpaper_name.flags() | Qt.ItemIsEditable)
            self.setItem(row, 3, item_wallpaper_name)
            
            # 设置"所属作品"列
            work_tags = ""
            if '所属作品' in self.df.columns and not pd.isna(self.df.at[row, '所属作品']):
                work_tags = str(self.df.at[row, '所属作品'])
            item_work_tags = QTableWidgetItem(work_tags)
            item_work_tags.setFlags(item_work_tags.flags() | Qt.ItemIsEditable)
            self.setItem(row, 4, item_work_tags)
            
        self.resizeColumnsToContents()

    def simplify_playlist_name(self, full_name):
        if '『' in full_name and '』' in full_name:
            start = full_name.find('『') + 1
            end = full_name.find('』')
            return full_name[start:end]
        else:
            return ' '.join(full_name.split()[:2])

    def update_wallpaper_id(self, row, wallpaper_id):
        self.df.at[row, '壁纸引擎ID'] = wallpaper_id
        self.setItem(row, 2, QTableWidgetItem(str(wallpaper_id)))
        
        # 尝试获取壁纸名称
        wallpaper_name = self.parent_widget.get_wallpaper_name(wallpaper_id)
        if wallpaper_name:
            self.df.at[row, '壁纸名称'] = wallpaper_name
            self.setItem(row, 3, QTableWidgetItem(wallpaper_name))
        
        self.resizeColumnsToContents()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        wallpaper_id = event.mimeData().text()
        position = event.pos()
        index = self.indexAt(position)
        row = index.row()
        if row == -1:
            QMessageBox.warning(self, "无效位置", "请将壁纸拖拽到有效的音乐行上。")
            return
        self.update_wallpaper_id(row, wallpaper_id)
        self.parent_widget.save_changes()
        song = self.df.at[row, '歌曲']
        QMessageBox.information(self, "匹配成功", f"歌曲 '{song}' 已匹配到壁纸 ID: {wallpaper_id}")
        event.acceptProposedAction()

    def on_cell_changed(self, row, column):
        if column == 2:  # 壁纸引擎ID列
            new_id = self.item(row, column).text().strip()
            self.df.at[row, '壁纸引擎ID'] = new_id
            
            # 如果ID变更，尝试自动获取壁纸名称
            wallpaper_name = self.parent_widget.get_wallpaper_name(new_id)
            if wallpaper_name:
                self.df.at[row, '壁纸名称'] = wallpaper_name
                self.setItem(row, 3, QTableWidgetItem(wallpaper_name))
                
            self.parent_widget.save_changes()
        elif column == 3:  # 壁纸名称列
            new_name = self.item(row, column).text().strip()
            self.df.at[row, '壁纸名称'] = new_name
            self.parent_widget.save_changes()
        elif column == 4:  # 所属作品列
            new_tags = self.item(row, column).text().strip()
            self.df.at[row, '所属作品'] = new_tags
            
            # 更新作品标签集合
            if new_tags:
                for tag in new_tags.split(','):
                    if tag.strip():
                        self.work_tags.add(tag.strip())
                        
            self.parent_widget.save_changes()

    def on_cell_double_clicked(self, row, column):
        if column == 2:
            wallpaper_id = self.item(row, column).text().strip()
            if wallpaper_id:  # 确保壁纸ID不为空
                self.parent_widget.scroll_to_wallpaper(wallpaper_id)  # 调用父窗口的方法滚动到对应壁纸
                self.parent_widget.open_wallpaper_preview(wallpaper_id)

    def mouseDoubleClickEvent(self, event):
        # 保留现有双击播放音乐的功能
        row = self.currentRow()
        if row >= 0:
            simplified_playlist = self.item(row, 0).text()
            song_name = self.df.at[row, '歌曲']
            playlist_folder = os.path.join(self.parent_widget.music_library_folder, simplified_playlist)
            music_file = os.path.join(playlist_folder, song_name)
            if not os.path.exists(music_file):
                QMessageBox.warning(self, "错误", f"音乐文件未找到: {song_name}（请确保文件名和路径正确）")
                return
            self.parent_widget.music_player.load_song(music_file)
            self.parent_widget.music_player.play()
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        """右键菜单，用于所属作品列的标签选择"""
        menu = QMenu(self)
        
        # 获取当前单元格
        index = self.indexAt(event.pos())
        if index.isValid() and index.column() == 4:  # 所属作品列
            # 添加标签菜单项
            add_tag_menu = menu.addMenu("添加作品标签")
            
            # 如果有已存在的标签，添加到菜单中
            if self.work_tags:
                for tag in sorted(self.work_tags):
                    action = add_tag_menu.addAction(tag)
                    action.triggered.connect(lambda checked, t=tag: self.add_work_tag(index.row(), t))
            
            # 添加自定义标签选项
            add_custom_tag = menu.addAction("添加自定义标签...")
            add_custom_tag.triggered.connect(lambda: self.add_custom_work_tag(index.row()))
            
            # 添加获取壁纸名称的选项
            if index.column() == 3:  # 壁纸名称列
                get_name_action = menu.addAction("获取壁纸名称")
                get_name_action.triggered.connect(lambda: self.get_wallpaper_name_for_row(index.row()))
            
            menu.exec_(event.globalPos())

    def add_work_tag(self, row, tag):
        """添加作品标签到指定行"""
        current_tags = self.item(row, 4).text().strip()
        if current_tags:
            # 检查标签是否已存在
            tags_list = [t.strip() for t in current_tags.split(',')]
            if tag not in tags_list:
                new_tags = current_tags + ", " + tag
            else:
                return  # 标签已存在，不添加
        else:
            new_tags = tag
            
        # 更新单元格和数据
        self.item(row, 4).setText(new_tags)
        self.df.at[row, '所属作品'] = new_tags
        self.parent_widget.save_changes()

    def add_custom_work_tag(self, row):
        """添加自定义作品标签"""
        tag, ok = QInputDialog.getText(self, "添加作品标签", "请输入作品标签名称:")
        if ok and tag.strip():
            self.work_tags.add(tag.strip())
            self.add_work_tag(row, tag.strip())

    def get_wallpaper_name_for_row(self, row):
        """获取指定行的壁纸名称"""
        wallpaper_id = self.item(row, 2).text().strip()
        if wallpaper_id and wallpaper_id != '无':
            wallpaper_name = self.parent_widget.get_wallpaper_name(wallpaper_id)
            if wallpaper_name:
                self.df.at[row, '壁纸名称'] = wallpaper_name
                self.setItem(row, 3, QTableWidgetItem(wallpaper_name))
                self.parent_widget.save_changes()
                QMessageBox.information(self, "成功", f"已获取壁纸名称: {wallpaper_name}")
            else:
                QMessageBox.warning(self, "警告", "无法获取壁纸名称")

class WallpaperLabel(QLabel):
    def __init__(self, wallpaper, main_window, matched_songs, parent=None):
        super().__init__(parent)
        self.wallpaper = wallpaper
        self.main_window = main_window
        self.matched_songs = matched_songs  # 获取已匹配的歌曲列表

        # 设置更小的固定大小
        self.setFixedSize(120, 120)  # 从150x150减小到120x120

        # 尝试加载 preview.gif 如果存在
        preview_path = self.wallpaper.get('preview_path_gif', None)
        if not preview_path:  # 如果没有 gif，则尝试加载 preview.jpg
            preview_path = self.wallpaper.get('preview_path', None)

        # 设置壁纸的预览图
        try:
            pixmap = QPixmap(preview_path)
            if pixmap.isNull():
                pixmap = QPixmap(120, 120)
                pixmap.fill(Qt.gray)
            # 缩放到更小的尺寸
            self.setPixmap(pixmap.scaled(110, 110, Qt.KeepAspectRatio))
        except Exception as e:
            pixmap = QPixmap(120, 120)
            pixmap.fill(Qt.gray)
            self.setPixmap(pixmap)

        # 设置工具提示
        self.setToolTip(self.generate_tooltip())  # 生成包含壁纸信息和匹配歌曲的工具提示
        self.setStyleSheet("border: 1px solid black;")
        self.setAlignment(Qt.AlignCenter)

        # 大数字显示的 QLabel 用于显示匹配的歌曲数量
        self.matching_label = QLabel(self)
        self.matching_label.setAlignment(Qt.AlignCenter)
        self.matching_label.setStyleSheet("color: black; font-size: 30px; font-weight: bold;")
        self.matching_label.setGeometry(0, 0, 30, 30)  # 设置大小和位置，覆盖在预览图上
        self.matching_label.setFont(QFont("楷体", 300))  # 设置楷体字体，大小为30（适当增大数字）

        # 显示匹配的歌曲数量
        self.update_matching_label()

    def generate_tooltip(self):
        """生成包含壁纸信息和匹配音乐的工具提示"""
        tooltip = f"壁纸名称: {self.wallpaper.get('title', '未知')}\n壁纸 ID: {self.wallpaper['id']}"
        if len(self.matched_songs) > 0:
            song_titles = "\n".join(self.matched_songs)
            tooltip += f"\n匹配的歌曲:\n{song_titles}"
        else:
            tooltip += "\n未匹配歌曲"
        return tooltip

    def update_matching_label(self):
        """更新大数字标签"""
        if len(self.matched_songs) > 0:
            # 显示匹配的歌曲数量
            self.matching_label.setText(f"{len(self.matched_songs)}首")
            self.matching_label.setStyleSheet("color: black; font-size: 30px; font-weight: bold; background-color: rgba(255, 255, 0, 0.6);")
        else:
            # 如果没有匹配，显示"未匹配"并设置透明背景
            self.matching_label.setText("")
            self.matching_label.setStyleSheet("background-color: transparent;")  # 背景透明

        self.matching_label.adjustSize()

    def set_matching_label(self, matched_count):
        """设置大数字标签，显示匹配的音乐数量"""
        if matched_count > 0:
            self.matching_label.setText(f"{matched_count}首")
            self.matching_label.setStyleSheet("color: black; font-size: 50px; font-weight: bold; background-color: rgba(255, 255, 0, 0.6);")
        else:
            self.matching_label.setText("")  # 无匹配时清空文本
            self.matching_label.setStyleSheet("background-color: transparent;")  # 背景透明

        self.matching_label.adjustSize()

    def mouseDoubleClickEvent(self, event):
        """双击事件: 打开对应壁纸的预览"""
        preview_mode = self.main_window.settings.get('preview_mode', 'popup')
        project_json = self.wallpaper['project_path']
        if os.path.exists(project_json):
            try:
                wallpaper_engine_path = self.main_window.wallpaper_engine_path
                wallpaper64_exe = os.path.join(wallpaper_engine_path, "wallpaper64.exe")
                if preview_mode == "desktop":
                    command = [
                        wallpaper64_exe,
                        "-control", "openWallpaper",
                        "-file", project_json
                    ]
                else:
                    command = [
                        wallpaper64_exe,
                        "-control", "openWallpaper",
                        "-file", project_json,
                        "-playInWindow", "Wallpaper #1",
                        "-width", "1920",
                        "-height", "1080"
                    ]
                subprocess.Popen(command, cwd=wallpaper_engine_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法启动预览: {e}")
        else:
            QMessageBox.warning(self, "文件不存在", f"壁纸项目文件未找到: {project_json}")

    def mousePressEvent(self, event):
        """拖拽事件: 将壁纸 ID 拖拽到音乐表格"""
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(str(self.wallpaper['id']))
            drag.setMimeData(mime_data)
            drag.setPixmap(self.pixmap())
            drag.exec_(Qt.MoveAction)

    def enterEvent(self, event):
        """鼠标悬停事件: 显示匹配的音乐信息"""
        # 更新工具提示内容，显示匹配的歌曲
        self.setToolTip(self.generate_tooltip())
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件: 恢复原始的工具提示"""
        self.setToolTip(self.generate_tooltip())
        super().leaveEvent(event)


class WallpaperGridWidget(QWidget):
    def __init__(self, wallpapers, music_table, main_window, parent=None):
        super().__init__(parent)
        self.wallpapers = wallpapers
        self.music_table = music_table
        self.main_window = main_window
        self.parent_widget = parent
        
        # 添加缓存和搜索优化相关变量
        self.all_wallpapers = wallpapers  # 保存所有壁纸的原始列表
        self.filtered_wallpapers = []     # 保存过滤后的壁纸列表
        self.last_search_text = ""        # 上一次搜索的文本
        self.wallpaper_positions = {}     # 壁纸位置映射
        self.search_timer = QTimer()      # 搜索延迟计时器
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        # 创建网格布局，设置更小的间距
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(5)  # 减小间距从10到5
        self.grid_layout.setContentsMargins(5, 5, 5, 5)  # 减小边距
        
        # 初始显示所有壁纸
        self.display_wallpapers(self.wallpapers)
        
        # 监听窗口大小变化，动态调整每行显示的数量
        self.main_window.scroll_area.resizeEvent = self.handle_resize_event

    def handle_resize_event(self, event):
        """处理滚动区域大小变化事件"""
        # 调用原始的resizeEvent
        QScrollArea.resizeEvent(self.main_window.scroll_area, event)
        
        # 获取当前滚动区域的宽度
        width = self.main_window.scroll_area.width()
        
        # 计算每行可以显示的壁纸数量
        # 每个壁纸宽度120 + 间距5 + 边距
        item_width = 120 + 5
        num_columns = max(1, (width - 10) // item_width)
        
        # 如果列数变化，重新布局
        if hasattr(self, 'current_columns') and self.current_columns != num_columns:
            self.current_columns = num_columns
            self.refresh_display()
        else:
            self.current_columns = num_columns

    def filter_wallpapers(self, search_text):
        """接收搜索文本并启动延迟搜索"""
        self.last_search_text = search_text
        
        # 如果搜索文本为空，立即显示所有壁纸
        if not search_text:
            self.filtered_wallpapers = self.all_wallpapers
            self.refresh_display()
            return len(self.filtered_wallpapers)
        
        # 否则，启动延迟搜索（300毫秒）
        self.search_timer.start(300)
        return 0  # 返回0，结果数量将在实际搜索完成后更新
    
    def perform_search(self):
        """执行实际的搜索操作"""
        search_text = self.last_search_text.lower()
        
        # 使用列表推导式进行过滤，比循环更高效
        self.filtered_wallpapers = [
            wp for wp in self.all_wallpapers if (
                search_text in str(wp['id']).lower() or 
                search_text in wp['title'].lower()
            )
        ]
        
        # 刷新显示
        self.refresh_display()
        
        # 更新主窗口中的搜索结果标签
        if hasattr(self.main_window, 'search_result_label'):
            self.main_window.search_result_label.setText(f"找到 {len(self.filtered_wallpapers)} 个结果")
    
    def refresh_display(self):
        """刷新壁纸显示，不重新创建所有组件"""
        # 清除现有布局中的所有项目
        self.clear_layout()
        
        # 重新显示过滤后的壁纸
        self.display_wallpapers(self.filtered_wallpapers)
    
    def clear_layout(self):
        """清除布局中的所有项目"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
    
    def display_wallpapers(self, wallpapers_to_display):
        """显示指定的壁纸列表"""
        # 清空壁纸位置映射
        self.wallpaper_positions = {}
        
        # 获取滚动区域宽度，计算每行显示的壁纸数量
        width = self.main_window.scroll_area.width()
        item_width = 120 + 5  # 壁纸宽度 + 间距
        num_columns = max(1, (width - 10) // item_width)
        self.current_columns = num_columns
        
        # 获取已匹配的壁纸ID
        matched_wallpaper_ids = set()
        for row in range(self.music_table.rowCount()):
            wallpaper_id = self.music_table.item(row, 2).text().strip()
            if wallpaper_id and wallpaper_id != '无':
                matched_wallpaper_ids.add(wallpaper_id)
        
        # 为每个壁纸创建匹配的歌曲列表
        wallpaper_matched_songs = {}
        for row in range(self.music_table.rowCount()):
            wallpaper_id = self.music_table.item(row, 2).text().strip()
            if wallpaper_id and wallpaper_id != '无':
                song = self.music_table.item(row, 1).text()
                if wallpaper_id not in wallpaper_matched_songs:
                    wallpaper_matched_songs[wallpaper_id] = []
                wallpaper_matched_songs[wallpaper_id].append(song)
        
        # 添加壁纸到网格
        for i, wallpaper in enumerate(wallpapers_to_display):
            row = i // num_columns
            col = i % num_columns
            
            # 获取此壁纸匹配的歌曲列表
            matched_songs = wallpaper_matched_songs.get(str(wallpaper['id']), [])
            
            # 创建壁纸标签，使用更小的尺寸
            label = WallpaperLabel(wallpaper, self.main_window, matched_songs)
            
            # 保存壁纸位置
            self.wallpaper_positions[str(wallpaper['id'])] = (row, col, label)
            
            # 添加到网格
            self.grid_layout.addWidget(label, row, col)
        
        # 设置布局
        self.setLayout(self.grid_layout)

class WallpaperMusicMatcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wallpaper Music Matcher")
        self.resize(1800, 800)

        # 初始化设置
        self.settings = {'preview_mode': 'popup', 'music_volume': 80}
        self.settings_file = 'settings.json'
        self.load_settings()

        # 初始化音量标签为 0%
        self.volume_value_label = QLabel("0%", self)  # 在窗口中创建标签

        # 设置标签的位置和样式
        self.volume_value_label.setAlignment(Qt.AlignCenter)  # 居中对齐
        self.volume_value_label.setGeometry(250, 100, 100, 50)  # 根据需要设置位置和大小

        # 初始化音量值
        self.set_music_volume(self.settings.get('music_volume', 80))  # 获取并设置音量值
        
        # 路径配置
        self.output_file = 'WallpaperMusicMatcher.csv'
        self.content_folder = r"D:\SteamLibrary\steamapps\workshop\content\431960"
        self.wallpaper_engine_path = r"D:\SteamLibrary\steamapps\common\wallpaper_engine"
        self.music_library_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'music_library')

        # 加载数据
        self.df = self.load_csv()
        self.wallpapers = self.load_all_wallpapers(self.content_folder)

        # 初始化音乐播放器
        self.music_player = MusicPlayer()

        # 设置UI
        self.setup_ui()

        # 启动定时器以检测音乐播放结束
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_music_playing)
        self.timer.start(1000)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                print(f"加载设置: {self.settings}")
            except Exception as e:
                print(f"加载设置失败: {e}")
        else:
            self.save_settings()

    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            print(f"保存设置: {self.settings}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法保存设置文件: {e}")
            print(f"无法保存设置文件: {e}")

    def load_csv(self):
        if not os.path.exists(self.output_file):
            QMessageBox.critical(self, "错误", f"CSV文件未找到: {self.output_file}")
            print(f"CSV文件未找到: {self.output_file}")
            sys.exit(1)
        try:
            df = pd.read_csv(self.output_file)
            
            # 检查必要的列是否存在
            required_columns = {'歌单', '歌曲', '壁纸引擎ID'}
            if not required_columns.issubset(df.columns):
                QMessageBox.critical(self, "错误", "CSV文件缺少必要的字段: '歌单', '歌曲', '壁纸引擎ID'")
                print("CSV文件缺少必要的字段: '歌单', '歌曲', '壁纸引擎ID'")
                sys.exit(1)
                
            # 确保壁纸名称和所属作品列存在
            if '壁纸名称' not in df.columns:
                df['壁纸名称'] = ""
            if '所属作品' not in df.columns:
                df['所属作品'] = ""
                
            return df
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取CSV文件出错: {e}")
            print(f"读取CSV文件出错: {e}")
            sys.exit(1)

    def load_all_wallpapers(self, folder_path):
        wallpapers = []
        if not os.path.exists(folder_path):
            QMessageBox.critical(self, "错误", f"壁纸内容文件夹未找到: {folder_path}")
            print(f"壁纸内容文件夹未找到: {folder_path}")
            sys.exit(1)
        
        for folder in os.listdir(folder_path):
            folder_full = os.path.join(folder_path, folder)
            project_json = os.path.join(folder_full, 'project.json')
            preview_jpg = os.path.join(folder_full, 'preview.jpg')
            preview_gif = os.path.join(folder_full, 'preview.gif')  # 新增 gif 文件路径

            if os.path.isdir(folder_full) and os.path.exists(project_json):
                try:
                    with open(project_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        title = data.get('title', '未知')
                        contentrating = data.get('contentrating', 'Safe')

                        # 排除不适合的壁纸并输出原因
                        if contentrating == "Questionable":
                            print(f"跳过壁纸 {title}，原因：含有轻微暗示 (Questionable)")
                            continue
                        elif contentrating == "Explicit":
                            print(f"跳过壁纸 {title}，原因：含有极端暴力 (Explicit)")
                            continue
                        elif contentrating == "Mature":
                            print(f"跳过壁纸 {title}，原因：含有成人内容 (Mature)")
                            continue

                    # 如果存在 preview.gif，则优先使用
                    preview_path = preview_gif if os.path.exists(preview_gif) else preview_jpg

                    wallpapers.append({
                        'id': folder,
                        'title': title,
                        'preview_path': preview_jpg,  # 默认使用 preview.jpg 路径
                        'preview_path_gif': preview_gif if os.path.exists(preview_gif) else None,  # 新增 gif 路径
                        'project_path': project_json
                    })
                except Exception as e:
                    print(f"读取壁纸 {folder} 时出错: {e}")
        
        return wallpapers


    def setup_ui(self):
        main_layout = QVBoxLayout()

        # 上部内容布局：音乐表格和壁纸网格
        content_layout = QHBoxLayout()

        # 左侧：音乐表格
        self.music_table = MusicTableWidget(self.df, music_player=self.music_player, parent=self)
        content_layout.addWidget(self.music_table, 3)

        # 右侧：壁纸部分（包括搜索框和壁纸网格）
        right_layout = QVBoxLayout()
        
        # 添加搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索壁纸:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入壁纸名称或ID进行搜索...")
        self.search_input.textChanged.connect(self.search_wallpapers)
        self.search_result_label = QLabel("")  # 显示搜索结果数量
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_result_label)
        right_layout.addLayout(search_layout)
        
        # 壁纸网格（可滚动）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.wallpaper_grid = WallpaperGridWidget(self.wallpapers, self.music_table, main_window=self, parent=self)
        self.scroll_area.setWidget(self.wallpaper_grid)
        right_layout.addWidget(self.scroll_area)
        
        content_layout.addLayout(right_layout, 2)
        main_layout.addLayout(content_layout)

        # 下部控制布局：音量滑块和设置、刷新按钮
        control_layout = QHBoxLayout()

        # 音量滑块
        volume_layout = QHBoxLayout()
        volume_label = QLabel("音量:")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.settings.get('music_volume', 80))
        self.volume_slider.setTickPosition(QSlider.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self.set_music_volume)
        self.volume_value_label = QLabel(f"{self.settings.get('music_volume', 80)}%")
        self.volume_slider.valueChanged.connect(self.update_volume_label)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_value_label)

        # 设置和刷新按钮
        button_layout = QHBoxLayout()
        self.settings_button = QPushButton("设置壁纸浏览方式")
        self.settings_button.clicked.connect(self.open_settings)
        button_layout.addWidget(self.settings_button)

        self.refresh_button = QPushButton("刷新壁纸")
        self.refresh_button.clicked.connect(self.refresh_wallpapers)
        button_layout.addWidget(self.refresh_button)

        # 添加批量获取壁纸名称的按钮
        self.get_names_button = QPushButton("批量获取壁纸名称")
        self.get_names_button.clicked.connect(self.batch_get_wallpaper_names)
        button_layout.addWidget(self.get_names_button)

        button_layout.addStretch()  # 将按钮对齐到右侧

        # 将音量布局和按钮布局添加到控制布局
        control_layout.addLayout(volume_layout)
        control_layout.addLayout(button_layout)

        main_layout.addLayout(control_layout)

        self.setLayout(main_layout)

    def update_volume_label(self, value):
        self.volume_value_label.setText(f"{value}%")

    def set_music_volume(self, volume):
        pygame.mixer.music.set_volume(volume / 100)
        self.settings['music_volume'] = volume
        self.save_settings()
        print(f"音量已设置为: {volume}%")
        self.volume_value_label.setText(f"{volume}%")

    def open_wallpaper_preview(self, wallpaper_id):
        # 根据 wallpaper_id 找到对应的壁纸
        wallpaper = next((wp for wp in self.wallpapers if wp['id'] == wallpaper_id), None)
        if not wallpaper:
            QMessageBox.warning(self, "错误", f"未找到壁纸 ID: {wallpaper_id}")
            return

        project_json = wallpaper['project_path']
        if os.path.exists(project_json):
            try:
                wallpaper_engine_path = self.wallpaper_engine_path
                wallpaper64_exe = os.path.join(wallpaper_engine_path, "wallpaper64.exe")
                preview_mode = self.settings.get('preview_mode', 'popup')
                if preview_mode == "desktop":
                    command = [
                        wallpaper64_exe,
                        "-control", "openWallpaper",
                        "-file", project_json
                    ]
                else:
                    command = [
                        wallpaper64_exe,
                        "-control", "openWallpaper",
                        "-file", project_json,
                        "-playInWindow", "Wallpaper #1",
                        "-width", "1920",
                        "-height", "1080"
                    ]
                subprocess.Popen(command, cwd=wallpaper_engine_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法启动预览: {e}")
        else:
            QMessageBox.warning(self, "文件不存在", f"壁纸项目文件未找到: {project_json}")

    def open_settings(self):
        current_setting = self.settings.get('preview_mode', 'popup')
        settings_window = SettingsWindow(current_setting, parent=self)
        if settings_window.exec_() == QDialog.Accepted:
            new_setting = settings_window.get_setting()
            self.settings['preview_mode'] = new_setting
            self.save_settings()

    def search_wallpapers(self, search_text):
        """根据搜索文本过滤壁纸"""
        result_count = self.wallpaper_grid.filter_wallpapers(search_text)
        
        # 更新搜索结果标签
        if search_text:
            self.search_result_label.setText(f"找到 {result_count} 个结果")
        else:
            self.search_result_label.setText("")
    
    def refresh_wallpapers(self):
        print("正在刷新壁纸...")
        
        # 保存当前搜索文本
        current_search = self.search_input.text()
        
        # 重新加载壁纸数据
        self.wallpapers = self.load_all_wallpapers(self.content_folder)
        
        # 删除旧的 wallpaper_grid
        self.wallpaper_grid.setParent(None)
        
        # 重新创建新的 wallpaper_grid，确保传递 music_table 参数
        self.wallpaper_grid = WallpaperGridWidget(self.wallpapers, main_window=self, music_table=self.music_table, parent=self)
        self.scroll_area.setWidget(self.wallpaper_grid)
        
        # 如果之前有搜索内容，应用相同的搜索过滤
        if current_search:
            self.search_input.setText(current_search)  # 这会触发 search_wallpapers 方法
        
        print("壁纸已刷新。")

    def save_changes(self):
        try:
            self.df.to_csv(self.output_file, index=False, encoding='utf-8-sig')
            print(f"CSV文件已更新: {self.output_file}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法保存CSV文件: {e}")
            print(f"无法保存CSV文件: {e}")  # 调试打印

    def check_music_playing(self):
        if not self.music_player.is_playing and self.music_player.current_song:
            self.music_player.play()

    def scroll_to_wallpaper(self, wallpaper_id):
        """滚动到指定壁纸ID的位置"""
        if not wallpaper_id:
            return
            
        # 查找壁纸在网格中的位置
        if wallpaper_id in self.wallpaper_grid.wallpaper_positions:
            row, col, label = self.wallpaper_grid.wallpaper_positions[wallpaper_id]
            
            # 计算标签在滚动区域中的位置
            pos = label.mapTo(self.wallpaper_grid, QPoint(0, 0))
            
            # 滚动到该位置
            self.scroll_area.ensureWidgetVisible(label, 50, 50)
            
            # 高亮显示该壁纸（可选）
            self.highlight_wallpaper(wallpaper_id)
            
            print(f"已滚动到壁纸ID: {wallpaper_id}")
        else:
            print(f"未找到壁纸ID: {wallpaper_id}")

    def highlight_wallpaper(self, wallpaper_id):
        """临时高亮显示指定的壁纸"""
        if wallpaper_id in self.wallpaper_grid.wallpaper_positions:
            row, col, label = self.wallpaper_grid.wallpaper_positions[wallpaper_id]
            
            # 保存原始样式
            original_style = label.styleSheet()
            
            # 设置高亮样式
            label.setStyleSheet("border: 3px solid red;")
            
            # 创建定时器，2秒后恢复原样式
            QTimer.singleShot(2000, lambda: label.setStyleSheet(original_style))

    def get_wallpaper_name(self, wallpaper_id):
        """根据壁纸ID获取壁纸名称"""
        if not wallpaper_id or wallpaper_id == '无':
            return ""
            
        # 在壁纸列表中查找对应ID的壁纸
        for wallpaper in self.wallpapers:
            if str(wallpaper['id']) == str(wallpaper_id):
                return wallpaper['title']
                
        # 如果在内存中找不到，尝试从文件中读取
        try:
            project_json_path = os.path.join(self.content_folder, str(wallpaper_id), "project.json")
            if os.path.exists(project_json_path):
                with open(project_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('title', '未知')
        except Exception as e:
            print(f"读取壁纸名称时出错: {e}")
            
        return ""

    def batch_get_wallpaper_names(self):
        """批量获取所有有ID但没有名称的壁纸名称"""
        count = 0
        for row in range(self.music_table.rowCount()):
            wallpaper_id = self.music_table.item(row, 2).text().strip()
            wallpaper_name = self.music_table.item(row, 3).text().strip()
            
            if wallpaper_id and wallpaper_id != '无' and not wallpaper_name:
                name = self.get_wallpaper_name(wallpaper_id)
                if name:
                    self.df.at[row, '壁纸名称'] = name
                    self.music_table.setItem(row, 3, QTableWidgetItem(name))
                    count += 1
        
        self.save_changes()
        QMessageBox.information(self, "完成", f"已获取 {count} 个壁纸名称")

def main():
    app = QApplication(sys.argv)
    window = WallpaperMusicMatcher()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
