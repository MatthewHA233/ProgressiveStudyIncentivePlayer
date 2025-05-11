import pandas as pd
import subprocess
import os
import sys
import time
import pygetwindow as gw
import pyautogui
import threading
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from ctypes import windll
import json  # 添加json导入

# 配置部分
SHOW_POPUP = True  # True 为显示弹窗壁纸，False 为不显示弹窗
RESTORE_ACTIONS = True  # True 为在音乐播放结束后执行恢复音量/播放操作，False 为不执行
RESTORE_VOLUME_PERCENT = 20.0  # wallpaper64.exe 恢复时的音量百分比（0.0 - 100.0）

# 弹窗大小和位置配置
RESIZE_POPUP = False  # True 为缩小弹窗，False 为保持原始大小
REPOSITION_POPUP = False  # True 为移动弹窗到指定位置，False 为保持原始位置
POPUP_RESIZED_WIDTH = 380  # 弹窗缩小后的宽度，严格测量最佳380
POPUP_RESIZED_HEIGHT = 252  # 弹窗缩小后的高度，严格测量最佳252（标题栏高度37）
POPUP_POSITION = 'right_top'  # 弹窗位置，可选值: 'left_top', 'right_top', 'right_bottom', 'left_bottom'

# 控制打印输出
VERBOSE = False  # True 为启用打印，False 为禁用打印

# 壁纸引擎路径配置
wallpaper_engine_path = r"D:\SteamLibrary\steamapps\common\wallpaper_engine"
content_folder = r"D:\SteamLibrary\steamapps\workshop\content\431960"

# 常量定义，用于设置窗口置顶
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_SHOWWINDOW = 0x0040
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2

def log(message):
    """
    控制打印输出的辅助函数。
    """
    if VERBOSE:
        print(message)

def get_wallpaper_engine_id(selected_file, csv_file="WallpaperMusicMatcher.csv"):
    """
    从CSV文件中获取 selected_file 对应的壁纸引擎ID
    """
    try:
        # 读取WallpaperMusicMatcher.csv文件
        df = pd.read_csv(csv_file)
        
        # 查找匹配的歌曲并获取对应的壁纸引擎ID
        wallpaper_row = df[df['歌曲'] == selected_file]
        
        if not wallpaper_row.empty:
            wallpaper_id = wallpaper_row['壁纸引擎ID'].iloc[0]
            wallpaper_name = wallpaper_row['壁纸名称'].iloc[0] if '壁纸名称' in wallpaper_row.columns else "未知壁纸"
            artwork_source = wallpaper_row['所属作品'].iloc[0] if '所属作品' in wallpaper_row.columns else "未知作品"
            return wallpaper_id, wallpaper_name, artwork_source
        else:
            log(f"未找到对应的壁纸引擎ID，歌曲: {selected_file}")
            return None, "未知壁纸", "未知作品"
    except Exception as e:
        log(f"读取CSV文件 {csv_file} 出错: {e}")
        return None, "未知壁纸", "未知作品"

def mute_wallpaper_engine():
    """
    使用 pycaw 将 wallpaper64.exe 进程静音
    """
    try:
        # 获取所有音频会话
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name().lower() == "wallpaper64.exe":
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                volume.SetMute(1, None)  # 静音
                log("wallpaper64.exe 已静音。")
                break
        else:
            log("未找到 wallpaper64.exe 进程或无法静音。")
    except Exception as e:
        log(f"静音 wallpaper64.exe 时出错: {e}")

def pause_wallpaper_engine():
    """
    使用命令行暂停桌面壁纸
    """
    try:
        pause_command = [
            os.path.join(wallpaper_engine_path, "wallpaper64.exe"),
            "-control", "pause"
        ]
        subprocess.Popen(pause_command, shell=True)
        log("已暂停桌面壁纸播放。")
    except Exception as e:
        log(f"暂停桌面壁纸时出错: {e}")

def set_window_always_on_top(hwnd):
    """
    使用 Windows API 将指定窗口设置为置顶或取消置顶
    """
    try:
        windll.user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE
        )
        log(f"窗口句柄 {hwnd} 已设置为置顶。")
    except Exception as e:
        log(f"设置窗口置顶时出错: {e}")

def close_existing_popup(window_title):
    """
    检查是否存在指定标题的弹窗壁纸窗口，如果存在则关闭
    """
    try:
        windows = gw.getWindowsWithTitle(window_title)
        for window in windows:
            window.close()
            log(f"已关闭现有的弹窗壁纸窗口: '{window_title}'")
    except Exception as e:
        log(f"关闭现有弹窗壁纸窗口时出错: {e}")

def get_popup_position_coordinates(position, new_width, new_height, padding=10):
    """
    根据配置的弹窗位置，计算窗口的左上角坐标
    """
    screen_width, screen_height = pyautogui.size()
    if position == 'left_top':
        new_left = padding
        new_top = padding
    elif position == 'right_top':
        new_left = screen_width - new_width - padding
        new_top = padding
    elif position == 'right_bottom':
        new_left = screen_width - new_width - padding
        new_top = screen_height - new_height - padding
    elif position == 'left_bottom':
        new_left = padding
        new_top = screen_height - new_height - padding
    else:
        # 默认位置为右上角
        new_left = screen_width - new_width - padding
        new_top = padding
    return new_left, new_top

def move_window_to_position(window, position, new_width, new_height, padding=10):
    """
    调整窗口大小并移动到指定位置
    """
    try:
        # 根据配置决定是否调整窗口大小
        if RESIZE_POPUP:
            window.resizeTo(new_width, new_height)
            log(f"窗口 '{window.title}' 大小已调整为 {new_width}x{new_height}。")
        
        # 根据配置决定是否移动窗口位置
        if REPOSITION_POPUP:
            # 获取目标位置坐标
            new_left, new_top = get_popup_position_coordinates(position, 
                                                              new_width if RESIZE_POPUP else window.width, 
                                                              new_height if RESIZE_POPUP else window.height, 
                                                              padding)
            
            # 移动窗口
            window.moveTo(new_left, new_top)
            log(f"窗口 '{window.title}' 已移动到屏幕 {position.replace('_', ' ')}。")
        
        # 设置窗口置顶
        hwnd = window._hWnd
        set_window_always_on_top(hwnd)
    except Exception as e:
        log(f"移动并调整窗口大小时出错: {e}")

def gradual_volume_set(hwnd, target_volume=0.04, step=0.01, delay=0.5):
    """
    逐步将指定窗口的音量设置到目标值
    """
    try:
        # 获取音频会话
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name().lower() == "wallpaper64.exe":
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                
                # 解除静音
                volume.SetMute(0, None)
                log("已解除 wallpaper64.exe 的静音。")
                
                # 设置音量为0
                volume.SetMasterVolume(0.0, None)
                log("wallpaper64.exe 的音量已设置为 0%。")
                
                current_volume = 0.0
                
                # 逐步增加音量到目标值
                while current_volume < target_volume:
                    current_volume += step
                    if current_volume > target_volume:
                        current_volume = target_volume
                    volume.SetMasterVolume(current_volume, None)
                    log(f"wallpaper64.exe 音量设置为 {current_volume*100:.0f}%")
                    time.sleep(delay)
                break
        else:
            log("未找到 wallpaper64.exe 进程或无法调整音量。")
    except Exception as e:
        log(f"逐步调整音量时出错: {e}")

def restore_wallpaper_play():
    """
    恢复桌面壁纸播放
    """
    try:
        play_command = [
            os.path.join(wallpaper_engine_path, "wallpaper64.exe"),
            "-control", "play"
        ]
        subprocess.Popen(play_command, shell=True)
        log("已恢复桌面壁纸播放。")
    except Exception as e:
        log(f"恢复桌面壁纸播放时出错: {e}")

def handle_music_end(duration):
    """
    等待音乐播放结束后，执行相应的操作
    """
    def task():
        # 等待音乐播放结束，加上延迟3秒
        total_wait = duration + 3
        log(f"等待 {total_wait} 秒后执行操作。")
        time.sleep(total_wait)
        
        if RESTORE_ACTIONS:
            if SHOW_POPUP:
                # 调整 wallpaper64.exe 音量到配置的百分比
                window_title = "Wallpaper #1"
                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    hwnd = windows[0]._hWnd
                    target_volume = RESTORE_VOLUME_PERCENT / 100.0
                    threading.Thread(target=gradual_volume_set, args=(hwnd, target_volume)).start()
                else:
                    log(f"未找到标题为 '{window_title}' 的窗口，无法调整音量。")
            else:
                # 恢复桌面壁纸播放
                restore_wallpaper_play()
        else:
            log("恢复操作未启用。")
    
    # 启动任务线程
    task_thread = threading.Thread(target=task)
    task_thread.start()

def update_artwork_info(wallpaper_id, wallpaper_name, artwork_source):
    """更新壁纸信息到单独的JSON文件"""
    try:
        artwork_json_path = os.path.join(os.path.dirname(__file__), "artwork_display_info.json")
        floating_button_json_path = os.path.join(os.path.dirname(__file__), "floating_button_data.json")
        
        # 读取现有数据或创建新数据
        if os.path.exists(artwork_json_path):
            with open(artwork_json_path, 'r', encoding='utf-8') as f:
                artwork_data = json.load(f)
        else:
            artwork_data = {}
        
        # 更新壁纸信息
        artwork_data["wallpaper_id"] = str(wallpaper_id)
        artwork_data["wallpaper_name"] = wallpaper_name
        artwork_data["artwork_source"] = artwork_source  # 添加作品来源
        
        # 读取阶段信息
        current_level = "未知阶段"
        if os.path.exists(floating_button_json_path):
            try:
                with open(floating_button_json_path, 'r', encoding='utf-8') as f:
                    floating_data = json.load(f)
                    current_level = floating_data.get("current_level", "未知阶段")
            except Exception as e:
                log(f"读取浮动按钮数据时出错: {e}")
        
        # 添加阶段信息
        artwork_data["current_level"] = current_level
        
        # 保存数据
        with open(artwork_json_path, 'w', encoding='utf-8') as f:
            json.dump(artwork_data, f, ensure_ascii=False, indent=2)
            log(f"已更新作品信息: {artwork_data}")
    except Exception as e:
        log(f"更新作品信息时出错: {e}")

def apply_wallpaper(wallpaper_id, wallpaper_name, artwork_source, duration):
    """
    启动壁纸引擎并应用对应壁纸
    """
    if not wallpaper_id:
        log("无效的壁纸引擎ID，无法启动壁纸引擎。")
        return
    
    # 更新到单独的作品信息JSON文件
    update_artwork_info(wallpaper_id, wallpaper_name, artwork_source)
    
    # 构造项目路径
    project_json_path = os.path.join(content_folder, str(wallpaper_id), "project.json")
    
    # 检查文件是否存在
    if not os.path.exists(project_json_path):
        log(f"壁纸项目文件未找到: {project_json_path}")
        return
    
    # 构造基础命令，用于启动桌面壁纸
    base_command = [
        os.path.join(wallpaper_engine_path, "wallpaper64.exe"),
        "-control", "openWallpaper",
        "-file", project_json_path
    ]
    
    # 如果是弹窗版本
    if SHOW_POPUP:
        window_title = "Wallpaper #1"
        
        # 关闭已存在的弹窗壁纸窗口
        close_existing_popup(window_title)
        
        # 启动弹窗壁纸，设置初始大小为1920x1080
        command_with_popup = base_command + ["-playInWindow", window_title, "-width", "1920", "-height", "1080"]
        try:
            subprocess.Popen(command_with_popup, shell=True)
            log(f"已成功应用弹窗壁纸，壁纸ID: {wallpaper_id}")
            
            # 等待窗口创建
            time.sleep(2)  # 根据需要调整等待时间
            
            # 获取弹窗壁纸窗口
            windows = gw.getWindowsWithTitle(window_title)
            if windows:
                window = windows[0]
                # 调整并移动弹窗壁纸窗口
                move_window_to_position(window, POPUP_POSITION, POPUP_RESIZED_WIDTH, POPUP_RESIZED_HEIGHT, padding=10)
            else:
                log(f"未找到标题为 '{window_title}' 的弹窗壁纸窗口。")
        except Exception as e:
            log(f"启动弹窗壁纸时出错: {e}")
        
        # 启动桌面壁纸
        try:
            subprocess.Popen(base_command, shell=True)
            log(f"已成功将壁纸设置为桌面壁纸，壁纸ID: {wallpaper_id}")
        except Exception as e:
            log(f"设置桌面壁纸时出错: {e}")
        
        # 暂停桌面壁纸
        pause_wallpaper_engine()
        
        # 静音 wallpaper64.exe 已在脚本最前面调用了 mute_wallpaper_engine()
        # 所以这里不需要再次调用
    else:
        # 播放桌面壁纸（不加 -playInWindow 参数）
        try:
            subprocess.Popen(base_command, shell=True)
            log(f"已成功应用桌面壁纸，壁纸ID: {wallpaper_id}")
        except Exception as e:
            log(f"启动壁纸引擎时出错: {e}")
        
        # 暂停桌面壁纸
        pause_wallpaper_engine()
    
    # 启动处理音乐结束的任务
    handle_music_end(duration)

if __name__ == "__main__":
    # 将 mute_wallpaper_engine() 放在最前面
    mute_wallpaper_engine()
    
    # 获取命令行参数
    if len(sys.argv) < 3:
        log("用法: python wallpaper_by_music_apply.py <歌曲文件名> <时长（秒）>")
        sys.exit(1)
    
    selected_file = sys.argv[1]
    try:
        duration = float(sys.argv[2])
        log(f"音乐时长: {duration} 秒")
        log(f"已启动 wallpaper_by_music_apply.py，传递歌曲: {selected_file}, 时长: {duration} 秒")
    except ValueError:
        log(f"无效的时长参数: {sys.argv[2]}")
        sys.exit(1)
    
    # 获取对应的壁纸引擎ID、名称和作品来源
    wallpaper_id, wallpaper_name, artwork_source = get_wallpaper_engine_id(selected_file)
    
    # 如果获取到有效的壁纸引擎ID，应用壁纸
    apply_wallpaper(wallpaper_id, wallpaper_name, artwork_source, duration)
