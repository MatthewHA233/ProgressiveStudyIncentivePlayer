from typing import List, Optional, Tuple
import os
import shutil
import pandas as pd
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image
import json

class PlaylistFileHandler:
    """音乐文件处理类"""
    
    def __init__(self, music_folder: str = 'music_library'):
        self.music_folder = music_folder
        self.supported_formats = ('.mp3', '.flac')
        # 加载配置文件以获取歌单顺序
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.playlist_order = [level['name'] for level in config['levels']]
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            self.playlist_order = []
        
    def add_music_files(self, playlist_name: str) -> Optional[List[str]]:
        """添加音乐文件到指定歌单"""
        # 打开文件选择对话框
        files = filedialog.askopenfilenames(
            title="选择音乐文件",
            filetypes=[
                ("音乐文件", "*.mp3 *.flac"),
                ("MP3文件", "*.mp3"),
                ("FLAC文件", "*.flac")
            ]
        )
        
        if not files:
            return None
            
        # 获取目标文件夹路径
        target_folder = os.path.join(self.music_folder, playlist_name)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
            
        # 读取trash.csv获取播放次数信息
        trash_data = {}
        trash_csv = os.path.join("statistics", "play_count_logs", "trash.csv")
        if os.path.exists(trash_csv):
            df = pd.read_csv(trash_csv)
            # 倒序遍历，保证获取最新的记录
            for idx in range(len(df)-1, -1, -1):
                filename = df.iloc[idx]['歌曲']
                if filename not in trash_data:  # 只记录每个文件的最新播放次数
                    trash_data[filename] = df.iloc[idx]['学习成就播放次数']
            
        # 复制文件
        copied_files = []
        for file_path in files:
            filename = os.path.basename(file_path)
            target_path = os.path.join(target_folder, filename)
            
            # 检查文件是否已存在
            if os.path.exists(target_path):
                continue
                
            try:
                shutil.copy2(file_path, target_path)
                copied_files.append((filename, trash_data.get(filename, 0)))  # 将文件名和播放次数一起存储
            except Exception as e:
                print(f"复制文件失败 {filename}: {str(e)}")
                
        # 更新播放统计
        if copied_files:
            self._update_play_count_csv(playlist_name, copied_files)
            
        return [file[0] for file in copied_files]  # 只返回文件名列表
        
    def _update_play_count_csv(self, playlist_name: str, new_files: List[Tuple[str, int]]) -> None:
        """更新播放统计CSV文件"""
        csv_folder = os.path.join("statistics", "play_count_logs")
        if not os.path.exists(csv_folder):
            os.makedirs(csv_folder)
            
        csv_path = os.path.join(csv_folder, f"{playlist_name}_play_count.csv")
        
        try:
            # 读取现有CSV或创建新的DataFrame
            if os.path.exists(csv_path):
                print(f"读取现有CSV文件: {csv_path}")
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
                print(f"当前CSV内容:\n{df}")
            else:
                print(f"创建新的CSV文件: {csv_path}")
                df = pd.DataFrame(columns=["序号", "歌单", "歌曲", "学习成就播放次数"])
            
            # 准备新数据
            playlist_full_name = f"『{playlist_name}』渐进学习时长激励歌单"
            new_rows = []
            start_index = len(df) if not df.empty else 0
            
            print(f"添加新歌曲到CSV:")
            for i, (filename, play_count) in enumerate(new_files):
                new_row = {
                    "序号": start_index + i,
                    "歌单": playlist_full_name,
                    "歌曲": filename,
                    "学习成就播放次数": play_count  # 使用从trash.csv获取的播放次数
                }
                new_rows.append(new_row)
                print(f"  - {filename} (播放次数: {play_count})")
            
            # 添加新数据
            if new_rows:
                new_df = pd.DataFrame(new_rows)
                df = pd.concat([df, new_df], ignore_index=True)
                print(f"保存更新后的CSV内容:\n{df}")
                # 确保目录存在
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                # 使用utf-8-sig编码保存，以支持中文
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                print(f"CSV文件已更新: {csv_path}")
                
        except Exception as e:
            print(f"更新播放统计失败: {str(e)}")
            # 打印详细的错误信息
            import traceback
            traceback.print_exc() 

    def move_song_between_playlists(self, song_name: str, from_playlist: str, to_playlist: str) -> None:
        """在歌单之间移动歌曲"""
        from_csv = os.path.join("statistics", "play_count_logs", f"{from_playlist}_play_count.csv")
        to_csv = os.path.join("statistics", "play_count_logs", f"{to_playlist}_play_count.csv")
        
        try:
            # 读取源CSV
            from_df = pd.read_csv(from_csv, encoding='utf-8-sig')
            # 找到要移动的行
            move_row = from_df[from_df['歌曲'] == song_name].iloc[0]
            # 从源CSV删除
            from_df = from_df[from_df['歌曲'] != song_name]
            
            # 读取或创建目标CSV
            if os.path.exists(to_csv):
                to_df = pd.read_csv(to_csv, encoding='utf-8-sig')
            else:
                to_df = pd.DataFrame(columns=["序号", "歌单", "歌曲", "学习成就播放次数"])
            
            # 更新歌单名称
            move_row['歌单'] = f"『{to_playlist}』渐进学习时长激励歌单"
            
            # 添加到目标CSV
            to_df = pd.concat([to_df, pd.DataFrame([move_row])], ignore_index=True)
            
            # 重新编号
            from_df['序号'] = range(len(from_df))
            to_df['序号'] = range(len(to_df))
            
            # 保存文件
            from_df.to_csv(from_csv, index=False, encoding='utf-8-sig')
            to_df.to_csv(to_csv, index=False, encoding='utf-8-sig')
            
        except Exception as e:
            raise Exception(f"移动CSV数据失败: {str(e)}")

    def initialize_missing_csvs(self) -> None:
        """在后台检查并初始化缺失的播放统计CSV文件"""
        try:
            # 获取所有歌单文件夹
            all_playlists = [d for d in os.listdir(self.music_folder) 
                        if os.path.isdir(os.path.join(self.music_folder, d)) 
                        and d != "音效"]
            
            # 按照配置文件中的顺序处理歌单
            for playlist in self.playlist_order:
                if playlist in all_playlists:
                    csv_path = os.path.join("statistics", "play_count_logs", f"{playlist}_play_count.csv")
                    
                    # 检查CSV是否存在
                    if not os.path.exists(csv_path):
                        # 获取歌单中的所有音乐文件
                        music_files = [
                            f for f in os.listdir(os.path.join(self.music_folder, playlist))
                            if os.path.isfile(os.path.join(self.music_folder, playlist, f))
                            and f.lower().endswith(self.supported_formats)
                        ]
                        
                        # 创建新的DataFrame
                        df = pd.DataFrame({
                            "序号": range(len(music_files)),
                            "歌单": [f"『{playlist}』渐进学习时长激励歌单"] * len(music_files),
                            "歌曲": music_files,
                            "学习成就播放次数": [0] * len(music_files)
                        })
                        
                        # 确保目录存在
                        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                        
                        # 保存CSV
                        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            # 处理未在配置文件中的歌单（如"未分类"等）
            for playlist in all_playlists:
                if playlist not in self.playlist_order:
                    csv_path = os.path.join("statistics", "play_count_logs", f"{playlist}_play_count.csv")
                    if not os.path.exists(csv_path):
                        music_files = [
                            f for f in os.listdir(os.path.join(self.music_folder, playlist))
                            if os.path.isfile(os.path.join(self.music_folder, playlist, f))
                            and f.lower().endswith(self.supported_formats)
                        ]
                        
                        df = pd.DataFrame({
                            "序号": range(len(music_files)),
                            "歌单": [f"『{playlist}』渐进学习时长激励歌单"] * len(music_files),
                            "歌曲": music_files,
                            "学习成就播放次数": [0] * len(music_files)
                        })
                        
                        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
        except Exception as e:
            print(f"初始化CSV文件失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def move_song_to_trash(self, song_name: str, from_playlist: str) -> None:
        """将歌曲移动到垃圾箱"""
        from_csv = os.path.join("statistics", "play_count_logs", f"{from_playlist}_play_count.csv")
        trash_csv = os.path.join("statistics", "play_count_logs", "trash.csv")
        
        try:
            # 读取源CSV
            from_df = pd.read_csv(from_csv, encoding='utf-8-sig')
            # 找到要移动的行
            move_row = from_df[from_df['歌曲'] == song_name].iloc[0]
            # 从源CSV删除
            from_df = from_df[from_df['歌曲'] != song_name]
            
            # 读取或创建垃圾箱CSV
            if os.path.exists(trash_csv):
                trash_df = pd.read_csv(trash_csv, encoding='utf-8-sig')
            else:
                trash_df = pd.DataFrame(columns=["序号", "歌单", "歌曲", "学习成就播放次数", "删除时间"])
            
            # 添加删除时间
            from datetime import datetime
            move_row['删除时间'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 添加到垃圾箱CSV
            trash_df = pd.concat([trash_df, pd.DataFrame([move_row])], ignore_index=True)
            
            # 重新编号
            from_df['序号'] = range(len(from_df))
            trash_df['序号'] = range(len(trash_df))
            
            # 保存文件
            from_df.to_csv(from_csv, index=False, encoding='utf-8-sig')
            trash_df.to_csv(trash_csv, index=False, encoding='utf-8-sig')
            
            # 删除实际的音乐文件
            file_path = os.path.join(self.music_folder, from_playlist, song_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                
        except Exception as e:
            raise Exception(f"移动到垃圾箱失败: {str(e)}")
