# ==== 发行版的时候搜索并去掉AUTO_SHUTDOWN相关 ====
import pandas as pd
import time
import pygame
import os
import random
import threading
from datetime import datetime, timedelta
from plyer import notification
from mutagen import File  # 新增导入
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import sys
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich import box
import subprocess
import logging
import json
import pyautogui # 新增导入 pyautogui
# ==== AUTO_SHUTDOWN ====
from pathlib import Path
# ==== AUTO_SHUTDOWN ====

# 在文件顶部导入argparse
import argparse

# 初始化 rich 控制台
console = Console()

# 信号类用于线程间通信
class Signal(QObject):
    show_gif = pyqtSignal()

# 读取配置文件
def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        log_and_print("[bold red]找不到配置文件 config.json[/bold red]")
        sys.exit(1)
    except json.JSONDecodeError:
        log_and_print("[bold red]配置文件格式错误[/bold red]")
        sys.exit(1)

# 加载配置
config = load_config()

# 设置音乐文件夹路径
music_folder = r'music_library'

# 从配置文件读取起始日期和音效设置
start_date = datetime.strptime(config['start_date'], '%Y-%m-%d')
half_hour_effect = config['half_hour_effect']
level_up_effect = config['level_up_effect']
five_minute_effect = config['five_minute_effect']

# 创建主数据文件夹
base_data_folder = 'statistics'
if not os.path.exists(base_data_folder):
    os.makedirs(base_data_folder)

# 设置日志保存路径，按照 YYYY-MM 格式建立子文件夹
base_log_folder = os.path.join(base_data_folder, 'terminal_logs')
current_date = datetime.now().strftime('%Y-%m')
log_folder = os.path.join(base_log_folder, current_date)
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# 设置日志文件路径
log_file_path = os.path.join(log_folder, f"print_logs_{datetime.now().strftime('%Y-%m-%d')}.txt")

# 设置日志记录器
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a',  # 追加模式
    encoding='utf-8'
)
logger = logging.getLogger()

# 自定义的 log_and_print 函数，用于同时输出到控制台和日志文件
# 消除重复打印的行为，保留颜色和样式信息，并减少空行

printed_content = set()  # 用于跟踪已打印的内容

def log_and_print(*args, **kwargs):
    # 针对 rich 对象做特殊处理
    console_capture = Console(record=True, color_system='truecolor')
    for arg in args:
        if isinstance(arg, (Table, Panel, Text)):
            console_capture.print(arg)
        else:
            if str(arg) not in printed_content:  # 检查内容是否已打印过
                printed_content.add(str(arg))
                logger.info(str(arg))  # 直接记录日志
                console.print(arg, **kwargs)  # 打印到控制台

    # 如果存在 rich 对象，导出它们的文本并记录日志
    captured_text = console_capture.export_text().strip()
    if captured_text and captured_text not in printed_content:
        printed_content.add(captured_text)
        logger.info(captured_text)
    # 打印捕获的富文本到控制台，保持样式，去除多余的空行
    if captured_text and captured_text not in printed_content:
        console.print(captured_text, **kwargs)

# 定义播放次数统计文件夹
play_count_folder = os.path.join(base_data_folder, 'play_count_logs')
if not os.path.exists(play_count_folder):
    os.makedirs(play_count_folder)

# 创建用于存储学习记录的 DataFrame
columns = [
    "现在时间",
    "目前已学习时长",
    "预测今日学习时长",
    "目标学习时长",
    "剩余空闲时间"
]
record_df = pd.DataFrame(columns=columns)


# 根据当前日期生成 CSV 文件路径
current_date = datetime.now().strftime("%Y-%m-%d")
log_folder = os.path.join(base_data_folder, 'study_time_logs')
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
csv_file_path = os.path.join(log_folder, f"学习记录_{current_date}.csv")

# 如果 CSV 文件存在，则读取现有内容，并更新
if os.path.exists(csv_file_path):
    existing_df = pd.read_csv(csv_file_path)
    record_df = pd.concat([existing_df, record_df], ignore_index=True)

# 在主循环中，每次打印表格时，将数据追加到 DataFrame 中
def save_record(current_time, formatted_cell_time, formatted_predicted_time, target_study_time_str, formatted_remaining_time):
    global record_df, current_level

    # 创建当前记录的字典
    current_record = {
        "现在时间": current_time,
        "目前已学习时长": formatted_cell_time,
        "预测今日学习时长": formatted_predicted_time,
        "目标学习时长": target_study_time_str,
        "剩余空闲时间": formatted_remaining_time
    }

    # 将当前记录追加到 DataFrame
    record_df = pd.concat([record_df, pd.DataFrame([current_record])], ignore_index=True)

    # 将 DataFrame 保存到 CSV 文件中
    record_df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')

    # 保存后执行"渐进学习时长激励播放器log图表.py"脚本
    try:
        script_path = os.path.join(os.path.dirname(__file__), "study_log_chart.py")
        if os.path.exists(script_path):
            log_and_print(f"[magenta]已生成 {current_time} 的log图表[/magenta]")
            subprocess.run([sys.executable, script_path], check=True)
        else:
            log_and_print(f"[bold red]找不到脚本文件: {script_path}[/bold red]")
    except Exception as e:
        log_and_print(f"[bold red]执行脚本时出错: {e}[/bold red]")

    # 更新悬浮按钮数据
    try:
        json_path = os.path.join(os.path.dirname(__file__), "floating_button_data.json")
        button_data_to_write = {}  # 初始化为空字典

        # 尝试读取现有数据
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                try:
                    button_data_to_write = json.load(f)
                except json.JSONDecodeError:
                    log_and_print(f"[bold yellow]警告: floating_button_data.json 文件格式错误，将使用默认值或创建新的。[/bold yellow]")
                    # 如果JSON解析失败，button_data_to_write 保持为空或根据需要设定初始结构

        # 确定 current_level_name
        determined_level_name = None
        if current_level:  # 全局 current_level 变量优先
            determined_level_name = f"『{current_level}』"
            # log_and_print(f"[cyan]悬浮窗阶段更新来源 (save_record): 程序内 current_level ('{current_level}')[/cyan]")
        elif "current_level" in button_data_to_write and button_data_to_write["current_level"] and button_data_to_write["current_level"] != "未知阶段":
            determined_level_name = button_data_to_write["current_level"] # 使用文件中已有的有效值
            # log_and_print(f"[cyan]悬浮窗阶段更新来源 (save_record): 文件内 current_level ('{determined_level_name}')[/cyan]")
        else:
            determined_level_name = "未知阶段" # 最后的回退
            # log_and_print(f"[yellow]悬浮窗阶段更新来源 (save_record): 默认值 '未知阶段' (程序 current_level: {current_level}, 文件内容: {button_data_to_write.get('current_level')})[/yellow]")
        
        # 准备要更新的数据负载
        update_payload = {
            "current_level": determined_level_name,
            "study_time": formatted_cell_time,
            "target_time": f"{target_study_time_str}小时",
            "predicted_time": formatted_predicted_time,
            "remaining_time": formatted_remaining_time
        }
        
        # 更新字典，这会保留 button_data_to_write 中不在 update_payload 的键 (如 current_music)
        button_data_to_write.update(update_payload)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(button_data_to_write, f, ensure_ascii=False, indent=2)
        log_and_print(f"[cyan]已更新悬浮按钮数据 (save_record): {button_data_to_write}[/cyan]")
            
    except Exception as e:
        log_and_print(f"[bold red]更新悬浮按钮数据时出错 (save_record): {e}[/bold red]")

# 计算当前周数和对应日期范围的函数
def get_current_week_file():
    # 获取当前日期
    today = datetime.now()
    
    # 计算从起始日期到当前日期的天数
    days_difference = (today - start_date).days
    
    # 计算当前是第几周，向上取整
    week_number = days_difference // 7 + 1
    
    # 计算这一周的开始日期（周一）和结束日期（周日）
    start_of_week = start_date + timedelta(weeks=(week_number - 1))
    end_of_week = start_of_week + timedelta(days=6)
    
    # 格式化文件名，使用正斜杠
    file_name = f"第{week_number}周({start_of_week.strftime('%m.%d')}~{end_of_week.strftime('%m.%d')}).xls"
    file_path = os.path.join(config['excel_path'], file_name).replace('\\', '/')
    
    log_and_print(f"[bold green]已读取文件:[/bold green] {file_path}")
    return file_path

# 设置 Excel 文件路径
excel_file = get_current_week_file()

# 从配置文件加载等级设置
level_config = [(level['name'], level['start'], level['end'], level['random_count']) 
                for level in config['levels']]

# 记录已经播放的音乐索引和之前的学习时长
played_music = set()
played_songs = {level: set() for level, _, _, _ in level_config}
current_level = None
previous_time = None
previous_target_time = None  # 新增：跟踪目标时间的变化

# 新增：记录每个级别当前播放次数最低的歌曲集合
level_played_counts = {}

# 设置OBS直播模式
def get_streaming_mode():
    while True:
        try:
            streaming_mode_input = console.input("[bold cyan]是否启用OBS直播模式（y/n，默认y）：[/bold cyan]").strip().lower()
            if not streaming_mode_input or streaming_mode_input == 'y':
                return True
            elif streaming_mode_input == 'n':
                return False
            else:
                log_and_print("[bold red]请输入 y 或 n。[/bold red]")
        except Exception as e:
            log_and_print(f"[bold red]获取OBS直播模式设置时出错: {e}[/bold red]")
            return True  # 错误情况下默认启用

# 设置壁纸引擎模式
def get_wallpaper_engine_mode():
    while True:
        try:
            wallpaper_mode_input = console.input("[bold cyan]是否启用壁纸引擎（y/n，默认y）：[/bold cyan]").strip().lower()
            if not wallpaper_mode_input or wallpaper_mode_input == 'y':
                return True
            elif wallpaper_mode_input == 'n':
                return False
            else:
                log_and_print("[bold red]请输入 y 或 n。[/bold red]")
        except Exception as e:
            log_and_print(f"[bold red]获取壁纸引擎模式设置时出错: {e}[/bold red]")
            return True  # 错误情况下默认启用

# 设置音量
def get_volume():
    while True:
        try:
            volume = console.input("[bold cyan]请输入音量百分比（默认4%）：[/bold cyan]").strip()
            if not volume:
                return 0.04
            volume = float(volume) / 100
            if 0 <= volume <= 1:
                return volume
            else:
                log_and_print("[bold red]请输入0到100之间的数字。[/bold red]")
        except ValueError:
            log_and_print("[bold red]请输入有效的数字。[/bold red]")

# 将 update_artwork_info 函数移到文件前面，在 play_music 函数之前
def update_artwork_info(music_name, music_duration, wallpaper_id=None, wallpaper_name=None):
    """更新作品信息到单独的JSON文件"""
    try:
        artwork_json_path = os.path.join(os.path.dirname(__file__), "artwork_display_info.json")
        
        # 读取现有数据或创建新数据
        if os.path.exists(artwork_json_path):
            with open(artwork_json_path, 'r', encoding='utf-8') as f:
                artwork_data = json.load(f)
        else:
            artwork_data = {}
        
        # 更新音乐信息
        artwork_data["music_name"] = music_name
        artwork_data["music_duration"] = music_duration
        
        # 如果提供了壁纸信息，也更新它
        if wallpaper_id:
            artwork_data["wallpaper_id"] = wallpaper_id
        if wallpaper_name:
            artwork_data["wallpaper_name"] = wallpaper_name
        
        # 保存数据
        with open(artwork_json_path, 'w', encoding='utf-8') as f:
            json.dump(artwork_data, f, ensure_ascii=False, indent=2)
            log_and_print(f"[cyan]已更新作品信息: {artwork_data}[/cyan]")
    except Exception as e:
        log_and_print(f"[bold red]更新作品信息时出错: {e}[/bold red]")

# 新增：直接在主文件中定义场景切换函数
def execute_obs_shortcut(shortcut_str):
    """
    执行OBS场景切换快捷键，模拟同时按下并保持一段时间。
    重复3次，每次间隔2秒。

    参数:
        shortcut_str: 要执行的快捷键组合，例如 "ctrl+alt+shift+q"
    """
    keys = shortcut_str.lower().split('+')
    hold_duration = 0.6  # 按键保持按下的时长（秒）

    log_and_print(f"[magenta]准备执行OBS快捷键 (同时长按模式): {keys}, 按住时长: {hold_duration}s[/magenta]")

    for attempt in range(3):
        try:
            # 1. 按下所有键 (按照快捷键字符串中的顺序)
            for key in keys:
                pyautogui.keyDown(key)
                # time.sleep(0.01) # 可选：在按下每个键之间加入极小的延迟

            # 2. 保持所有按键按下的状态
            time.sleep(hold_duration)

            # 3. 按相反的顺序释放所有键
            for key in reversed(keys):
                pyautogui.keyUp(key)
                # time.sleep(0.01) # 可选：在释放每个键之间加入极小的延迟
            
            log_and_print(f"[magenta]已执行OBS快捷键 (第 {attempt+1} 次，同时长按模式): {shortcut_str}[/magenta]")

        except Exception as e:
            log_and_print(f"[bold red]执行OBS快捷键 {shortcut_str} (第 {attempt+1} 次，同时长按模式) 时出错: {e}[/bold red]")
            # 确保在发生错误时尝试释放所有可能被按下的键
            try:
                for key_to_release in reversed(keys):
                    pyautogui.keyUp(key_to_release)
            except Exception as e_release:
                log_and_print(f"[bold yellow]尝试在错误处理中释放按键时也发生错误: {e_release}[/bold yellow]")
        
        if attempt < 2: # 最后一次执行后不需要等待
            time.sleep(2)

# 播放音乐
def play_music(file_path):
    def play():
        try:
            pygame.mixer.init()
            
            # 获取音乐时长
            audio = File(file_path)
            if audio is not None and audio.info is not None:
                duration = audio.info.length  # 时长（秒）
            else:
                duration = 0  # 如果无法获取，设置为0
            
            # 获取音乐名称（去掉路径和扩展名）
            music_name = os.path.basename(file_path)
            
            # 格式化音乐时长
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            formatted_duration = f"{minutes}:{seconds:02d}"
            
            # 更新到单独的作品信息JSON文件
            update_artwork_info(music_name, formatted_duration)
            
            # 音乐开始播放前，执行OBS场景切换 (Ctrl+Alt+Shift+Q)
            if STREAMING_MODE:
                log_and_print("[cyan]直播模式：执行OBS场景切换(开始)[/cyan]")
                execute_obs_shortcut('ctrl+alt+shift+q') # 直接调用内部函数
            
            pygame.mixer.music.load(file_path)
            
            # 直播模式下设置音量为0（静音）
            if STREAMING_MODE:
                log_and_print("[cyan]直播模式：音乐静音播放[/cyan]")
                pygame.mixer.music.set_volume(0)
            else:
                pygame.mixer.music.set_volume(volume)
                
            pygame.mixer.music.play()

            # 等待音乐播放结束
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # 音乐播放结束后，执行OBS场景切换 (Ctrl+Alt+Shift+A)
            if STREAMING_MODE:
                log_and_print("[cyan]直播模式：执行OBS场景切换(结束)[/cyan]")
                execute_obs_shortcut('ctrl+alt+shift+a') # 直接调用内部函数
                
        except pygame.error as e:
            log_and_print(f"[bold red]无法播放文件 {file_path}: {e}[/bold red]")
        except Exception as e: # 增加一个通用的异常捕获，以防 pyautogui 出错等
            log_and_print(f"[bold red]播放音乐或执行场景切换时发生未知错误: {e}[/bold red]")


    music_thread = threading.Thread(target=play)
    music_thread.start()

# 获取音乐时长的函数
def get_music_duration(file_path):
    audio = File(file_path)
    if audio is not None and audio.info is not None:
        return audio.info.length  # 时长（秒）
    else:
        return 0

# 播放特效音
def play_effect_sound(effect_file):
    def play_sound():
        try:
            pygame.mixer.init()
            sound = pygame.mixer.Sound(effect_file)
            sound.set_volume(volume)
            sound.play()
        except pygame.error as e:
            log_and_print(f"[bold red]无法播放特效音 {effect_file}: {e}[/bold red]")

    sound_thread = threading.Thread(target=play_sound)
    sound_thread.start()

# 每个整5分钟播放一次音效
def play_five_minute_effect():
    while True:
        now = datetime.now()
        # 计算距离下一个整5分钟的秒数
        seconds_until_next_five_minute = (5 - now.minute % 5) * 60 - now.second
        if seconds_until_next_five_minute <= 0:
            seconds_until_next_five_minute += 300  # 防止负数情况
        time.sleep(seconds_until_next_five_minute)
        play_effect_sound(five_minute_effect)

# 读取 Excel 文件
def read_time_from_excel(file_path, row, col):
    """
    读取 Excel 文件中的指定单元格以及相对位置的三个单元格数据。
    """
    try:
        # 移除 mode 参数
        df = pd.read_excel(file_path, header=None)
        
        # 读取主单元格
        cell_value = df.iloc[row, col]
        if pd.isna(cell_value):
            cell_value = "00:00:00"
        
        # 计算相对位置单元格
        relative_positions = [
            (row + 2, col + 5),  # "预测今日学习时长"（S列）
            (row + 5, col + 5),  # "目标学习时长"（S列）
            (row + 5, col + 6)   # "剩余空闲时间"（T列）
        ]

        relative_values = []
        for r, c in relative_positions:
            try:
                value = df.iloc[r, c]
                if pd.isna(value):
                    value = "00:00:00"
                relative_values.append(str(value))
            except IndexError:
                relative_values.append("00:00:00")
        
        return str(cell_value), relative_values

    except Exception as e:
        log_and_print(f"[bold red]读取Excel文件时发生错误: {e}[/bold red]")
        return "00:00:00", ["00:00:00", "12", "00:00:00"]

# 显示通知
def show_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name="学习成就",
        timeout=10
    )

# 更新或创建播放次数的.csv文件
def update_play_count_csv(level, music_files):
    # 获取.csv文件的路径
    csv_file = os.path.join(play_count_folder, f"{level}_play_count.csv")

    # 检查.csv文件是否存在
    if os.path.exists(csv_file):
        # 读取现有的.csv文件
        df = pd.read_csv(csv_file, index_col='序号')
        existing_songs = df['歌曲'].tolist()

        # 检查歌单是否有变动
        added_songs = list(set(music_files) - set(existing_songs))
        removed_songs = list(set(existing_songs) - set(music_files))

        # 如果有新增歌曲，添加到DataFrame
        for song in added_songs:
            df = df.append({'歌单': f"『{level}』渐进学习时长激励歌单", '歌曲': song, '学习成就播放次数': 0}, ignore_index=True)

        # 如果有删除的歌曲，从DataFrame中移除
        if removed_songs:
            df = df[~df['歌曲'].isin(removed_songs)]

        # 重置索引
        df.reset_index(drop=True, inplace=True)
        df.index.name = '序号'
    else:
        # 如果.csv文件不存在，创建新的DataFrame
        df = pd.DataFrame({
            '歌单': [f"『{level}』渐进学习时长激励歌单"] * len(music_files),
            '歌曲': music_files,
            '学习成就播放次数': [0] * len(music_files)
        })
        df.index.name = '序号'

    # 保存到.csv文件
    df.to_csv(csv_file)

    # 更新level_played_counts
    level_played_counts[level] = {'played_songs': set(), 'current_min_count': None}

# 更新歌曲的播放次数
def update_song_play_count(level, song_name):
    # 获取.csv文件的路径
    csv_file = os.path.join(play_count_folder, f"{level}_play_count.csv")

    # 检查.csv文件是否存在
    if os.path.exists(csv_file):
        # 读取.csv文件
        df = pd.read_csv(csv_file, index_col='序号')
        # 查找对应的歌曲
        song_index = df[df['歌曲'] == song_name].index
        if not song_index.empty:
            index = song_index[0]
            # 更新播放次数
            df.at[index, '学习成就播放次数'] += 1
            # 保存到.csv文件
            df.to_csv(csv_file)
        else:
            log_and_print(f"[bold red]歌曲 {song_name} 不在播放次数文件中。[/bold red]")
    else:
        log_and_print(f"[bold red]播放次数文件 {csv_file} 不存在，无法更新播放次数。[/bold red]")


# 打印奖状样式的函数
def print_certificate(formatted_cell_time, music_name, level):
    # 创建居中的标题
    title = Text("🎉 学习成就奖状 🎉", style="bold red", justify="center")

    # 创建内容部分，格式化为居中显示
    congrats_line = Text("🎈  🎓 恭喜你达成了 ", style="bold white")
    congrats_line.append(formatted_cell_time, style="bold yellow")
    congrats_line.append(" 学习时长! 🎓  🎈", style="bold white")

    # 处理音乐名，分离艺术家和歌曲名，并去除扩展名
    music_name_parts = music_name.split(' - ')
    if len(music_name_parts) == 2:
        artist, song = music_name_parts
        song, _ = os.path.splitext(song)  # 使用 os.path.splitext() 去掉文件扩展名

        # 创建显示的音乐文本
        music_text = Text("🎵  🎶 正在播放的是: ", style="bold white")
        music_text.append(artist, style="white")
        music_text.append(" - ", style="white")
        music_text.append(song, style="bold cyan")
        music_text.append(" 🎶  🎵", style="bold white")
    else:
        music_text = Text(f"🎵  🎶 正在播放的是: {music_name} 🎶  🎵", style="bold white")

    # 等级信息
    level_text = Text(f"🌟  🚀『{level}』🚀  🌟", style="bold red")

    # 创建面板，将所有内容组合为一个整体
    content = Text()
    content.append(congrats_line)
    content.append("\n")
    content.append(music_text)
    content.append("\n")
    content.append(level_text)

    panel = Panel(
        content,
        title=title,
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 4)  # 增加内边距来模拟"字体变大"的效果
    )

    # 打印奖状到控制台并保存到日志
    log_and_print(panel)

    # 更新播放次数
    update_song_play_count(level, music_name)

# 打印歌单的函数
def print_song_list(level, music_files):
    # 创建居中的歌单标题
    title = Text(f"『{level}』渐进学习时长激励歌单", style="bold yellow", justify="center")

    # 创建表格并美化显示
    table = Table(
        title=title,
        box=box.MINIMAL_DOUBLE_HEAD,
        show_header=True
    )
    table.add_column("序号", style="cyan", justify="center")
    table.add_column("歌曲", style="white")

    for idx, song in enumerate(music_files, start=1):
        # 特殊处理音乐名：用"-"分割，去掉面的扩展名，并分别处理颜色
        song_parts = song.split(' - ')
        if len(song_parts) == 2:
            artist, song_name = song_parts
            # 使用 os.path.splitext() 去掉文件扩展名
            song_name, _ = os.path.splitext(song_name)

            song_text = Text()
            song_text.append(artist, style="white")  # 艺术家名保留原色
            song_text.append(" - ", style="white")
            song_text.append(song_name, style="bold cyan")  # 使用特殊颜色显示歌曲名部分
        else:
            # 如果歌曲格式不是 "艺术家 - 歌曲名"，保持原样
            song_text = Text(song, style="white")

        table.add_row(str(idx), song_text)

    # 使用 Panel 居中整个表格
    panel = Panel(
        table,
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 2)
    )

    # 打印歌单到控制台
    log_and_print("\n", panel)

    # 更新或创建播放次数的.csv文件
    update_play_count_csv(level, music_files)

# 根据学习时长选择对应的分级文件夹，并随机选择一首音乐文件
def select_music_file(total_minutes, level):
    # 设置基于当前时间的随机种子
    random.seed(int(time.time()))

    level_folder = os.path.join(music_folder, level)
    music_files = [filename for filename in os.listdir(level_folder) if filename.endswith(('.mp3', '.flac'))]

    # 获取.csv文件的路径
    csv_file = os.path.join(play_count_folder, f"{level}_play_count.csv")
    if not os.path.exists(csv_file):
        # 如果CSV文件不存在，先更新
        update_play_count_csv(level, music_files)

    # 读取播放次数数据
    df = pd.read_csv(csv_file, index_col='序号')

    # 找到最小的播放次数
    min_play_count = df['学习成就播放次数'].min()

    # 过滤出放次数等于最小值的歌曲
    min_play_songs = df[df['学习成就播放次数'] == min_play_count]['歌曲'].tolist()

    # 从未播放的歌曲中选择
    if level not in level_played_counts:
        level_played_counts[level] = {'played_songs': set(), 'current_min_count': min_play_count}

    # 检查当前的播放次数级别是否发生变化
    if level_played_counts[level]['current_min_count'] != min_play_count:
        level_played_counts[level]['played_songs'] = set()
        level_played_counts[level]['current_min_count'] = min_play_count

    unplayed_songs = list(set(min_play_songs) - level_played_counts[level]['played_songs'])

    if not unplayed_songs:
        # 如果所有最小播放次数的歌曲都已播放，增加播放次数级别，重新选择
        level_played_counts[level]['played_songs'] = set()
        level_played_counts[level]['current_min_count'] += 1
        min_play_count = level_played_counts[level]['current_min_count']
        min_play_songs = df[df['学习成就播放次数'] == min_play_count]['歌曲'].tolist()
        unplayed_songs = list(set(min_play_songs) - level_played_counts[level]['played_songs'])

        if not unplayed_songs:
            # 如果没有歌曲可以选择，重置播放次数
            df['学习成就播放次数'] = 0
            df.to_csv(csv_file)
            level_played_counts[level]['current_min_count'] = 0
            unplayed_songs = df[df['学习成就播放次数'] == 0]['歌曲'].tolist()

    selected_file = random.choice(unplayed_songs)
    level_played_counts[level]['played_songs'].add(selected_file)
    return selected_file, music_files

# 显示祝贺
def show_congratulations(level, song):
    def display():
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(bg='black')
        root.wm_attributes('-transparentcolor', 'black')

        width, height = root.winfo_screenwidth(), root.winfo_screenheight()
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        draw = ImageDraw.Draw(image)
        font_path_regular = "C:/Windows/Fonts/STXINGKA.TTF"
        font_path_bold = "C:/Windows/Fonts/STHUPO.TTF"
        font_regular = ImageFont.truetype(font_path_regular, 50)
        font_bold = ImageFont.truetype(font_path_bold, 51)

        text_before = "已经进入"
        text_after = "的新篇章"
        song_text = f"接下来播放：{song}"

        before_width = draw.textbbox((0, 0), text_before, font=font_regular)[2]
        level_width = draw.textbbox((0, 0), level, font=font_bold)[2]
        after_width = draw.textbbox((0, 0), text_after, font=font_regular)[2]
        song_width = draw.textbbox((0, 0), song_text, font=font_regular)[2]

        total_width = before_width + level_width + after_width
        start_x = (width - total_width) / 2 + 50  # 向右移动50像素
        y_position = (height - draw.textbbox((0, 0), text_before, font=font_regular)[3]) / 2

        draw.text((start_x, y_position), text_before, font=font_regular, fill=(255, 255, 255, 255))
        draw.text((start_x + before_width, y_position), level, font=font_bold, fill=(255, 0, 0, 255))
        draw.text((start_x + before_width + level_width, y_position), text_after, font=font_regular, fill=(255, 255, 255, 255))
        
        song_x_position = (width - song_width) / 2 + 50  # 同样向右移动50像素
        draw.text((song_x_position, y_position + 60), song_text, font=font_regular, fill=(255, 255, 255, 255))

        tk_image = ImageTk.PhotoImage(image)
        label = tk.Label(root, image=tk_image, bg='black')
        label.pack(expand=True)

        root.after(4000, root.destroy)
        root.mainloop()

    ribbon_thread = threading.Thread(target=display)
    ribbon_thread.start()

def show_congratulations_with_gif():
    app = QApplication(sys.argv)

    window = QLabel()
    window.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    window.setAttribute(Qt.WA_TranslucentBackground)
    window.setAlignment(Qt.AlignCenter)

    # 加载 GIF
    gif_path = "彩带.gif"  # 替换为你的 GIF 路径
    movie = QMovie(gif_path)
    window.setMovie(movie)

    # 启动动画
    movie.start()

    # 全屏显示
    window.showFullScreen()

    # 使用 QTimer 在 4 秒后关闭窗口
    QTimer.singleShot(4000, window.close)

    app.exec_()

# 格式化时间函数
def format_duration_without_seconds(duration):
    """
    将时间字符串或时间差转换为 'HH时MM分' 格式，省略秒数
    """
    # 处理特殊的日期时间格式（1899-12-30 开头的时间）
    if isinstance(duration, str) and duration.startswith('1899-12-30'):
        return "0时00分"
    
    # 处理时间字符串
    if isinstance(duration, str) and ':' in duration:
        try:
            # 去除小数秒部分和任何潜在的空白字符
            duration = duration.split('.')[0].strip() if '.' in duration else duration.strip()
            parts = duration.split(':')
            if len(parts) < 2:
                return duration  # 格式不正，直接返回始值
            hours, minutes = int(parts[0]), int(parts[1])
            return f"{hours}时{minutes:02d}分"
        except (ValueError, IndexError) as e:
            log_and_print(f"[bold red]格式化时间时出错。值: {duration}，错误: {e}[/bold red]")
            return "0时00分"  # 错误情况下返回零时
    # 处理 timedelta 对象
    elif isinstance(duration, timedelta):
        total_minutes = int(duration.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}时{minutes:02d}分"
    # 处理浮点数（秒数）
    elif isinstance(duration, float):
        total_minutes = int(duration // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}时{minutes:02d}分"
    # 如果是整数或其他类型，直接返回
    return str(duration)

# ==== AUTO_SHUTDOWN_START ====
class AutoShutdown:
    shutdown_launched = False  # 类变量，记录是否已启动关机程序
    
    @classmethod
    def check_and_start_shutdown(cls):
        """检查时间并在适当时候启动自动关机程序"""
        # 如果已经启动过，直接返回
        if cls.shutdown_launched:
            return
            
        current_time = datetime.now()
        # 检查是否在21:30或之后
        if (current_time.hour == 21 and current_time.minute >= 30) or current_time.hour > 21:
            # 获取auto_shutdown.pyw的路径
            shutdown_script = Path(__file__).parent / 'auto_shutdown.pyw'
            if shutdown_script.exists():
                # 使用pythonw启动脚本以避免显示控制台
                try:
                    subprocess.Popen(
                        ['pythonw', str(shutdown_script)], 
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    cls.shutdown_launched = True  # 标记为已启动
                    log_and_print(f"[magenta]已启动自动关机程序[/magenta]")
                except Exception:
                    pass
# ==== AUTO_SHUTDOWN_END ====

def main_loop():
    global current_level, previous_time, previous_target_time  # 更新全局变量引用
    while True:
        today = datetime.now().weekday()
        if today == 0:  # 星期一
            row, col = 21, column_to_index('N')
        elif today == 1:  # 星期二
            row, col = 21, column_to_index('AH')
        elif today == 2:  # 星期三
            row, col = 55, column_to_index('N')
        elif today == 3:  # 星期四
            row, col = 55, column_to_index('AH')
        elif today == 4:  # 星期五
            row, col = 89, column_to_index('N')
        elif today == 5:  # 星期六
            row, col = 89, column_to_index('AH')
        elif today == 6:  # 星期日
            row, col = 123, column_to_index('N')

        # 读取 Excel 数据
        cell_time, relative_values = read_time_from_excel(excel_file, row, col)
        predicted_study_time, target_study_time, remaining_free_time = relative_values

        # 格式化时间
        formatted_cell_time = format_duration_without_seconds(cell_time)
        formatted_predicted_time = format_duration_without_seconds(predicted_study_time)
        formatted_remaining_time = format_duration_without_seconds(remaining_free_time)
        target_study_time_str = str(target_study_time)

        # 检查学习时间或目标时间是否发生变化
        if cell_time != previous_time or target_study_time != previous_target_time:
            current_time = datetime.now().strftime("%H:%M:%S")

            # 创建表格
            table = Table(show_header=False, box=box.ROUNDED, border_style="white")
            table.add_column("数据类型", justify="center")
            table.add_column("数值", justify="center")

            # 添加表格内容
            table.add_row("现在时间", current_time)
            table.add_row(Text("目前已学习时长", style="cyan bold"), Text(formatted_cell_time, style="cyan bold"))
            table.add_row(Text("预测今日学习时长", style="orange1 bold"), Text(formatted_predicted_time, style="orange1 bold"))
            table.add_row(Text("目标学习时长", style="red bold"), Text(f"{target_study_time_str} 小时", style="red bold"))
            table.add_row(Text("剩余空闲时间", style="green bold"), Text(formatted_remaining_time, style="green bold"))

            # 如果目标时间发生变化，添加特殊提示
            if target_study_time != previous_target_time and previous_target_time is not None:
                log_and_print(f"[bold yellow]目标学习时长已更新: {previous_target_time} → {target_study_time} 小时[/bold yellow]")

            log_and_print(table)  # 将输出保存到日志

            # 打印总分钟数和半小时数
            if isinstance(cell_time, str) and len(cell_time.split(':')) == 3:
                try:
                    hours, minutes, seconds = map(int, cell_time.split(':'))
                    total_minutes = hours * 60 + minutes
                    total_half_hours = total_minutes // 30

                    log_and_print(f"[magenta]总分钟数: {total_minutes}, 经过的半小时数: {total_half_hours}[/magenta]")
                except ValueError:
                    log_and_print("[bold red]时间格式不正确，无法解析为整数1。[/bold red]")

            # 保存数据到 CSV
            save_record(current_time, formatted_cell_time, formatted_predicted_time, target_study_time_str, formatted_remaining_time)

            # 播放音乐效果和通知
            if isinstance(cell_time, str) and len(cell_time.split(':')) == 3:
                try:
                    hours, minutes, seconds = map(int, cell_time.split(':'))
                    total_minutes = hours * 60 + minutes
                    total_half_hours = total_minutes // 30

                    for level, start_hour, end_hour, _ in level_config:
                        if start_hour * 60 <= total_minutes < end_hour * 60:
                            if total_half_hours not in played_music:
                                selected_file, music_files = select_music_file(total_minutes, level)

                                # 构造音乐文件路径
                                music_path = os.path.join(music_folder, level, selected_file)
                                
                                # 获取音乐时长
                                duration = get_music_duration(music_path)

                                # 更新悬浮按钮数据中的音乐信息
                                try:
                                    json_path_music = os.path.join(os.path.dirname(__file__), "floating_button_data.json")
                                    button_data_for_music = {}
                                    if os.path.exists(json_path_music):
                                        with open(json_path_music, 'r', encoding='utf-8') as f_music:
                                            try:
                                                button_data_for_music = json.load(f_music)
                                            except json.JSONDecodeError:
                                                log_and_print(f"[bold yellow]警告: floating_button_data.json 文件格式错误 (音乐更新前读取)。[/bold yellow]")

                                    # level 是当前音乐所属的级别
                                    level_name_for_music_update = f"『{level}』" 
                                    
                                    # 格式化音乐时长
                                    minutes_calc = int(duration // 60)
                                    seconds_calc = int(duration % 60)
                                    formatted_duration_calc = f"{minutes_calc}:{seconds_calc:02d}"
                                    
                                    music_update_payload = {
                                        "current_level": level_name_for_music_update,
                                        "study_time": formatted_cell_time,
                                        "target_time": f"{target_study_time_str}小时",
                                        "predicted_time": formatted_predicted_time,
                                        "remaining_time": formatted_remaining_time,
                                        "current_music": selected_file,
                                        "music_duration": formatted_duration_calc
                                    }
                                    button_data_for_music.update(music_update_payload)
                                    
                                    with open(json_path_music, 'w', encoding='utf-8') as f_music_write:
                                        json.dump(button_data_for_music, f_music_write, ensure_ascii=False, indent=2)
                                    log_and_print(f"[cyan]已更新悬浮按钮数据(包含音乐): {button_data_for_music}[/cyan]")
                                except Exception as e:
                                    log_and_print(f"[bold red]更新悬浮按钮音乐数据时出错: {e}[/bold red]")
                                
                                # 调用 wallpaper_by_music_apply.py 脚本，并传递 selected_file 和 duration
                                try:
                                    if WALLPAPER_ENGINE_MODE:
                                        subprocess.Popen(['python', 'wallpaper_by_music_apply.py', selected_file, str(duration)])
                                        log_and_print("[cyan]壁纸引擎：根据音乐切换壁纸[/cyan]")
                                    else:
                                        log_and_print("[cyan]壁纸引擎：已禁用[/cyan]")
                                except Exception as e:
                                    log_and_print(f"[bold red]调用 wallpaper_by_music_apply.py 时出错: {e}[/bold red]")

                                if level != current_level:
                                    current_level = level
                                    print_song_list(level, music_files)
                                    play_effect_sound(level_up_effect)
                                    show_congratulations(current_level, selected_file)
                                    show_congratulations_with_gif()
                                    
                                    # 立即更新悬浮按钮数据
                                    try:
                                        json_path_level_change = os.path.join(os.path.dirname(__file__), "floating_button_data.json")
                                        button_data_on_level_change = {}
                                        if os.path.exists(json_path_level_change):
                                            with open(json_path_level_change, 'r', encoding='utf-8') as f_lc:
                                                try:
                                                    button_data_on_level_change = json.load(f_lc)
                                                except json.JSONDecodeError:
                                                    log_and_print(f"[bold yellow]警告: floating_button_data.json 文件格式错误 (阶段变化更新前读取)。[/bold yellow]")
                                        
                                        # 此时全局 current_level 变量已更新为新的 level
                                        level_change_payload = {
                                            "current_level": f"『{current_level}』", 
                                            "study_time": formatted_cell_time,
                                            "target_time": f"{target_study_time_str}小时",
                                            "predicted_time": formatted_predicted_time,
                                            "remaining_time": formatted_remaining_time
                                            # current_music 和 music_duration 会被保留，因为它们刚被上面的音乐更新逻辑写入
                                        }
                                        button_data_on_level_change.update(level_change_payload)
                                        
                                        with open(json_path_level_change, 'w', encoding='utf-8') as f_lc_write:
                                            json.dump(button_data_on_level_change, f_lc_write, ensure_ascii=False, indent=2)
                                        log_and_print(f"[cyan]已更新悬浮按钮数据(阶段变化确认): {button_data_on_level_change}[/cyan]")
                                    except Exception as e:
                                        log_and_print(f"[bold red]更新悬浮按钮数据(阶段变化)时出错: {e}[/bold red]")
                                else:
                                    play_effect_sound(half_hour_effect)

                                # 使用格式化后的时间传递给 print_certificate
                                print_certificate(formatted_cell_time, selected_file, level)
                                notification_thread = threading.Thread(
                                    target=show_notification,
                                    args=("学习成就", f"恭喜你达成了 {formatted_cell_time} 学习时长!\n正在播放的是: {selected_file}")
                                )
                                notification_thread.start()
                                
                                # 播放音乐
                                play_music(music_path)
                                
                                # 添加到已播放的音乐集合
                                played_music.add(total_half_hours)

                except ValueError:
                    log_and_print("[bold red]时间格式不正确，无法解析为整数2。[/bold red]")
                except Exception as e:
                    log_and_print(f"[bold red]发生未知错误。值: {cell_time}，错误: {e}[/bold red]")

            # 更新前一次的值
            previous_time = cell_time
            previous_target_time = target_study_time

        # ==== AUTO_SHUTDOWN_CHECK_START ====
        # 检查是否需要启动自动关机程序
        AutoShutdown.check_and_start_shutdown()
        # ==== AUTO_SHUTDOWN_CHECK_END ====

        time.sleep(5)

# 将列标签转换为索引
def column_to_index(col):
    index = 0
    for char in col:
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1

# 获取音量设置
volume = get_volume()

# 获取OBS直播模式设置
STREAMING_MODE = get_streaming_mode()

# 获取壁纸引擎模式设置
WALLPAPER_ENGINE_MODE = get_wallpaper_engine_mode()

# 启动每5分钟播放音效的线程
five_minute_thread = threading.Thread(target=play_five_minute_effect)
five_minute_thread.daemon = True  # 设置为守护线程，主线程退出时该线程自动退出
five_minute_thread.start()

# 在文件顶部导入部分添加
import subprocess
try:
    # 启动悬浮按钮作为独立进程
    subprocess.Popen([sys.executable, 'floating_button_process.py'], 
                    creationflags=subprocess.CREATE_NO_WINDOW)
except Exception as e:
    log_and_print(f"[bold red]启动悬浮按钮进程时出错: {e}[/bold red]")

# 处理命令行参数
parser = argparse.ArgumentParser(description='渐进学习时长激励播放器')
parser.add_argument('--show-playlist', help='显示指定级别的歌单')
parser.add_argument('--show-certificate', nargs=2, help='显示学习奖状，参数为级别和学习时长')
args = parser.parse_args()

if args.show_playlist:
    # 显示指定级别的歌单
    level_folder = os.path.join(music_folder, args.show_playlist)
    if os.path.exists(level_folder):
        music_files = [filename for filename in os.listdir(level_folder) if filename.endswith(('.mp3', '.flac'))]
        print_song_list(args.show_playlist, music_files)
    else:
        log_and_print(f"[bold red]找不到级别 {args.show_playlist} 的歌单文件夹[/bold red]")
    sys.exit(0)
elif args.show_certificate:
    # 显示学习奖状
    level, study_time = args.show_certificate
    # 获取最后播放的歌曲
    csv_file = os.path.join(play_count_folder, f"{level}_play_count.csv")
    last_song = "最近播放的歌曲"
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file)
            if not df.empty:
                # 获取播放次数最多的歌曲作为最近播放
                last_song = df.loc[df['学习成就播放次数'].idxmax(), '歌曲']
        except Exception as e:
            log_and_print(f"[bold red]读取最近播放歌曲时出错: {e}[/bold red]")
    
    print_certificate(study_time, last_song, level)
    sys.exit(0)

# 启动主循环
main_loop()
