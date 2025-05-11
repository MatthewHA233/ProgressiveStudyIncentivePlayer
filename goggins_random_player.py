import os
import random
from rich.console import Console
from rich import print
import time
import subprocess
import sys
import csv
from datetime import datetime
import json

# 初始化控制台
console = Console()

# 将 video_folder 设置为全局变量
video_folder = '戈金斯励志视频'

# 定义视频分段信息
VIDEO_SEGMENTS = {
    "大卫戈金斯，今年是准备Stay hard或者成为一个软蛋.mp4": 1,  # 作为1个完整片段
    "含妈量极高的1小时David Goggins跑步训话纯享（中英），stay hard!.mp4": 32,  # 32个2分钟片段
    "自我怀疑会把你搞砸！.mp4": 1  # 作为1个完整片段
}

def get_all_segments():
    """获取所有可能的视频片段"""
    segments = []
    for video_name, segment_count in VIDEO_SEGMENTS.items():
        if segment_count == 1:
            segments.append((video_name, None))  # None 表示完整播放
        else:
            segments.extend([(video_name, i+1) for i in range(segment_count)])
    return segments

def get_video_duration(video_path):
    # 使用 ffprobe 获取视频信息
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', video_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # 解析 JSON 输出
    info = json.loads(result.stdout)
    return float(info['format']['duration'])

def log_played_video(video_name, segment=None):
    log_file = os.path.join(video_folder, 'play_log.csv')
    with open(log_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if segment:
            writer.writerow([f"{video_name}_分段{segment}", timestamp])
        else:
            writer.writerow([video_name, timestamp])

def main():
    # 检查文件夹是否存在
    if not os.path.exists(video_folder):
        os.makedirs(video_folder)
        console.print("[bold red]已创建戈金斯励志视频文件夹，请将视频文件放入其中后重新运行程序。[/bold red]")
        time.sleep(3)
        sys.exit()
    
    # 获取所有视频文件
    video_files = [f for f in os.listdir(video_folder) 
                  if f in VIDEO_SEGMENTS]  # 只获取预定义的视频文件
    
    if not video_files:
        console.print("[bold red]没有找到预定义的视频文件！[/bold red]")
        console.print("[yellow]请确保以下视频文件存在：[/yellow]")
        for video in VIDEO_SEGMENTS.keys():
            console.print(f"[yellow]- {video}[/yellow]")
        time.sleep(3)
        sys.exit()
    
    # 从所有可能的片段中随机选择一个
    all_segments = get_all_segments()
    selected_video, selected_segment = random.choice(all_segments)
    video_path = os.path.join(video_folder, selected_video)
    
    # 打印信息
    console.print("\n[bold cyan]🎬 随机选择的励志视频:[/bold cyan]")
    console.print(f"[bold green]{selected_video}[/bold green]")
    
    if selected_segment is not None:
        console.print(f"[bold cyan]播放分段: {selected_segment}/32[/bold cyan]\n")
        start_time = (selected_segment - 1) * 120
        # 重定向 stdout 和 stderr 到 DEVNULL
        subprocess.run(['ffplay', '-ss', str(start_time), '-t', '120', '-autoexit', video_path],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)
        # 记录播放信息
        log_played_video(selected_video, selected_segment)
    else:
        try:
            # 完整播放视频，同样重定向输出
            subprocess.run(['ffplay', '-autoexit', video_path],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            console.print("[bold magenta]视频已开始播放...[/bold magenta]")
            # 记录播放信息
            log_played_video(selected_video)
            
        except Exception as e:
            console.print(f"[bold red]播放视频时出错: {e}[/bold red]")
            time.sleep(3)

if __name__ == "__main__":
    # 打印欢迎信息
    console.print("[bold cyan]===== 戈金斯励志视频随机播放器 =====[/bold cyan]")
    main() 