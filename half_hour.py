import sys
import os
import threading
import time
import signal
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QTimeEdit,
    QMessageBox,
    QSpinBox,
)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QIcon
import pygame


class TimeSetter(QWidget):
    def __init__(self, initial_time, initial_volume):
        super().__init__()
        self.setWindowTitle("设置起始时间和音量")
        self.setFixedSize(300, 200)
        self.selected_time = None
        self.selected_volume = None
        self.init_ui(initial_time, initial_volume)

    def init_ui(self, initial_time, initial_volume):
        layout = QVBoxLayout()

        # 时间选择标签
        self.time_label = QLabel("选择起始时间:")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

        # 时间选择器，允许任意分钟
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(initial_time.hour, initial_time.minute))
        self.time_edit.setAlignment(Qt.AlignCenter)
        self.time_edit.setFixedWidth(100)
        layout.addWidget(self.time_edit, alignment=Qt.AlignCenter)

        # 音量选择标签
        self.volume_label = QLabel("设置音量(%):")
        self.volume_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.volume_label)

        # 音量选择器
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(0, 100)
        self.volume_spin.setValue(int(initial_volume * 100))
        self.volume_spin.setAlignment(Qt.AlignCenter)
        self.volume_spin.setFixedWidth(100)
        layout.addWidget(self.volume_spin, alignment=Qt.AlignCenter)

        # 设置按钮
        self.set_button = QPushButton("设置")
        self.set_button.clicked.connect(self.set_time_and_volume)
        layout.addWidget(self.set_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def set_time_and_volume(self):
        selected_time = self.time_edit.time()
        # 将分钟四舍五入到最接近的5的倍数（可选，如果需要）
        # minute = selected_time.minute()
        # rounded_minute = 5 * round(minute / 5)
        # if rounded_minute == 60:
        #     rounded_minute = 0
        #     hour = (selected_time.hour() + 1) % 24
        # else:
        #     hour = selected_time.hour()
        # self.selected_time = datetime.strptime(f"{hour}:{rounded_minute}", "%H:%M").time()
        # 直接获取选择的时间
        self.selected_time = datetime.strptime(selected_time.toString("HH:mm"), "%H:%M").time()

        # 获取音量
        volume = self.volume_spin.value()
        self.selected_volume = volume / 100.0  # 转换为0.0-1.0之间

        self.close()


def show_time_setter(initial_time, initial_volume):
    app = QApplication(sys.argv)
    time_setter = TimeSetter(initial_time, initial_volume)
    time_setter.show()
    app.exec_()
    return time_setter.selected_time, time_setter.selected_volume


class Scheduler:
    def __init__(self, sound_path, initial_volume=0.07):
        self.sound_path = sound_path
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        self.start_time = None
        self.volume = initial_volume
        pygame.mixer.init()

    def set_start_time_and_volume(self, start_time, volume):
        self.start_time = start_time
        self.volume = volume
        pygame.mixer.music.set_volume(self.volume)
        print(f"已成功设置起始时间为 {self.start_time.strftime('%H:%M')}，音量为 {int(self.volume * 100)}%")

    def start(self):
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.stop()
        self.stop_event.clear()
        self.scheduler_thread = threading.Thread(target=self.run)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()

    def stop(self):
        self.stop_event.set()
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join()

    def run(self):
        while not self.stop_event.is_set():
            now = datetime.now()
            if not self.start_time:
                print("未设置起始时间。")
                time.sleep(1)
                continue

            # 计算下一个报时时间
            next_time = now.replace(hour=self.start_time.hour, minute=self.start_time.minute, second=0, microsecond=0)
            if next_time < now:
                # 计算下一个符合30分钟间隔的时间点
                delta_minutes = 30
                intervals = ((now - next_time).seconds // (delta_minutes * 60)) + 1
                next_time += timedelta(minutes=delta_minutes * intervals)

            wait_seconds = (next_time - now).total_seconds()
            print(f"等待直到 {next_time.strftime('%H:%M')} 播放音效。")
            if self.stop_event.wait(timeout=wait_seconds):
                break

            # 播放音效
            self.play_sound(next_time.strftime('%H:%M'))

            # 设置下一个播放时间
            self.start_time = (next_time + timedelta(minutes=30)).time()

    def play_sound(self, current_time_str):
        next_time_dt = datetime.strptime(current_time_str, '%H:%M') + timedelta(minutes=30)
        next_time_str = next_time_dt.strftime('%H:%M')
        print(f"{current_time_str} 已报时，下一次报时时间为 {next_time_str}")
        sound_path = self.sound_path
        if not os.path.exists(sound_path):
            print(f"音效文件未找到: {sound_path}")
            return
        try:
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if self.stop_event.is_set():
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)
        except Exception as e:
            print(f"播放音效时出错: {e}")


def main():
    # 确定音效文件路径
    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    sound_path = os.path.join(current_dir, "music_library", "音效", "青木森一,佐藤仁美 - きのみを手に入れた!.mp3")
    if not os.path.exists(sound_path):
        print(f"音效文件未找到: {sound_path}")
        sys.exit(1)

    scheduler = Scheduler(sound_path)

    def signal_handler(sig, frame):
        print("\n检测到 Ctrl+C，暂停调度并设置新时间和音量。")
        scheduler.stop()
        # 打开时间和音量设置窗口
        new_time, new_volume = show_time_setter(
            scheduler.start_time if scheduler.start_time else datetime.now().time(),
            scheduler.volume
        )
        if new_time and new_volume is not None:
            scheduler.set_start_time_and_volume(new_time, new_volume)
            scheduler.start()

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)

    # 初始时间和音量设置
    initial_time, initial_volume = show_time_setter(datetime.now().time(), 0.07)
    if not initial_time or initial_volume is None:
        print("未设置起始时间，程序退出。")
        sys.exit(0)
    scheduler.set_start_time_and_volume(initial_time, initial_volume)
    scheduler.start()

    print("按 Ctrl+C 可以暂停并重新设置时间和音量。")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # 这个异常会被 signal_handler 处理
        pass


if __name__ == "__main__":
    main()
