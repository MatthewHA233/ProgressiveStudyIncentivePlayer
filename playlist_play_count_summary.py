import os
import pandas as pd
import customtkinter as ctk
import json
import math

class PlaylistStatsViewer(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # 加载字体配置
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.default_font = ctk.CTkFont(family=config.get('font', '微软雅黑'))
                self.title_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=24, weight="bold")
                self.subtitle_font = ctk.CTkFont(family=config.get('font', '微软雅黑'), size=14)
        except Exception as e:
            print(f"加载字体配置失败: {str(e)}")
            self.default_font = ctk.CTkFont(family='微软雅黑')
            self.title_font = ctk.CTkFont(family='微软雅黑', size=24, weight="bold")
            self.subtitle_font = ctk.CTkFont(family='微软雅黑', size=14)
        
        # 定义等级颜色映射
        self.rank_colors = {
            'S': {
                "bg": ["#FFD700", "#FFD700"],  # 金色
                "text": ["#000000", "#000000"]
            },
            'A': {
                "bg": ["#FF4D4D", "#FF4D4D"],  # 红色
                "text": ["#000000", "#000000"]
            },
            'B': {
                "bg": ["#4169E1", "#4169E1"],  # 蓝色
                "text": ["#000000", "#000000"]
            },
            'C': {
                "bg": ["#98FB98", "#98FB98"],  # 绿色
                "text": ["#000000", "#000000"]
            }
        }
        
        self.create_ui()
        self.update_stats()
        
    def create_ui(self):
        """创建用户界面"""
        # 创建标题区域
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(
            title_frame,
            text="歌单播放统计",
            font=self.title_font,
            text_color="#FFFFFF"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="查看各等级歌单的累计播放次数",
            font=self.subtitle_font,
            text_color="#888888"
        ).pack(anchor="w")
        
        # 创建滚动容器
        self.container = ctk.CTkScrollableFrame(self)
        self.container.pack(fill="both", expand=True, padx=30, pady=20)
        
    def update_stats(self):
        """更新统计数据并显示"""
        # 先清除容器中的所有部件
        for widget in self.container.winfo_children():
            widget.destroy()
            
        # 更新统计数据
        self.aggregate_play_counts()
        
        # 显示统计数据
        self.display_stats()
        
    def calculate_playlist_plays(self, study_time_hours, level_config):
        """计算某个等级歌单在指定学习时长下的播放次数"""
        start_time = level_config['start']
        random_count = level_config['random_count']
        total_level_duration = random_count * 0.5  # 随机首数 × 30分钟（0.5小时）
        
        # 计算学习时长超过起始时间的部分
        effective_time = study_time_hours - start_time
        
        if effective_time < 0:
            return 0
        elif effective_time >= total_level_duration:
            return random_count
        else:
            return min(random_count, math.floor(effective_time / 0.5) + 1)

    def aggregate_play_counts(self):
        """汇总播放次数统计"""
        try:
            # 读取配置文件获取排序顺序和随机首数
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 创建等级名称和随机首数的映射，确保是整数
                level_configs = {
                    f"『{level['name']}』": {
                        'start': float(level['start']),
                        'random_count': int(level['random_count'])
                    }
                    for level in config['levels']
                }
                playlist_order = list(level_configs.keys())
        except Exception as e:
            print(f"读取配置文件失败，使用默认配置: {str(e)}")
            return

        directory = os.path.join("statistics", "play_count_logs")
        歌单歌曲总播放次数 = {}
        歌单总随机首数 = {playlist: 0 for playlist in playlist_order}
        
        # 遍历并统计每个歌曲的播放次数
        for filename in os.listdir(directory):
            if filename.endswith("_play_count.csv"):
                filepath = os.path.join(directory, filename)
                df = pd.read_csv(filepath)
                
                if "歌单" in df.columns and "学习成就播放次数" in df.columns:
                    for _, row in df.iterrows():
                        playlist_full = row["歌单"]
                        if "『" in playlist_full and "』" in playlist_full:
                            playlist = playlist_full.split("』")[0] + "』"
                        else:
                            playlist = playlist_full
                        
                        play_count = row["学习成就播放次数"]
                        play_count = int(play_count) if pd.notna(play_count) else 0
                        
                        if playlist in 歌单歌曲总播放次数:
                            歌单歌曲总播放次数[playlist] += play_count
                        else:
                            歌单歌曲总播放次数[playlist] = play_count

        # 遍历学习记录文件计算实际播放次数
        study_logs_dir = os.path.join("statistics", "study_time_logs")
        for filename in os.listdir(study_logs_dir):
            if filename.startswith("学习记录_") and filename.endswith(".csv"):
                date = filename[5:-4]  # 提取日期
                filepath = os.path.join(study_logs_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if lines:
                            last_line = lines[-1].strip()
                            time_str = last_line.split(',')[1]  # "6时30分"格式
                            hours = int(time_str.split('时')[0])
                            minutes = int(time_str.split('时')[1].replace('分', ''))
                            total_hours = hours + minutes/60
                            
                            # 打印日期标题
                            print(f"\n{date}：")
                            
                            # 计算每个歌单实际播放次数
                            for playlist, config in level_configs.items():
                                plays = self.calculate_playlist_plays(total_hours, config)
                                歌单总随机首数[playlist] += plays
                                
                                # 提取歌单名称（去掉『』）
                                playlist_name = playlist.strip('『』')
                                # 打印每个歌单的播放次数（只打印有播放的歌单）
                                if plays > 0:
                                    print(f"{playlist_name} 播放{plays}次")
                except Exception as e:
                    print(f"处理学习记录文件 {filename} 时出错: {str(e)}")

        # 转换为DataFrame并添加新列
        summary_df = pd.DataFrame([
            {"渐进学习时长激励歌单": playlist, 
             "总播放次数": 歌单总随机首数.get(playlist, 0),
             "歌曲播放统计": 歌单歌曲总播放次数.get(playlist, 0),
             "随机首数": level_configs[playlist]['random_count']}
            for playlist in playlist_order
        ])
        
        # 添加无随机首数歌单的统计
        无随机首数歌单 = set(歌单歌曲总播放次数.keys()) - set(playlist_order)
        if 无随机首数歌单:
            无随机首数_df = pd.DataFrame([
                {"渐进学习时长激励歌单": playlist,
                 "总播放次数": None,
                 "歌曲播放统计": 歌单歌曲总播放次数.get(playlist, 0),
                 "随机首数": None}
                for playlist in 无随机首数歌单
            ])
            summary_df = pd.concat([summary_df, 无随机首数_df], ignore_index=True)
        
        # 计算播放负载比率
        summary_df['播放负载比率'] = summary_df.apply(
            lambda row: row['总播放次数'] / level_configs[row['渐进学习时长激励歌单']]['random_count']
            if pd.notna(row['总播放次数']) else None,
            axis=1
        )
        
        # 计算推荐歌曲数量
        # 使用播放负载比率的中位数作为基准
        median_load = summary_df.loc[summary_df['播放负载比率'].notna(), '播放负载比率'].median()
        summary_df['推荐歌曲数量'] = summary_df.apply(
            lambda row: int(round(row['总播放次数'] / median_load)) 
            if pd.notna(row['播放负载比率']) else None,
            axis=1
        )
        
        # 排序
        def get_playlist_order(playlist):
            for i, prefix in enumerate(playlist_order):
                if playlist.startswith(f'『{prefix}'):
                    return i
            return float('inf')
        
        summary_df['排序'] = summary_df['渐进学习时长激励歌单'].apply(get_playlist_order)
        summary_df.sort_values(by='排序', inplace=True)
        summary_df.drop(columns=['排序'], inplace=True)
        
        # 保存汇总结果前确保随机首数是整数
        csv_output = os.path.join(directory, "等级歌单播放次数共计.csv")
        # 使用float_format参数来控制数值的格式
        summary_df.to_csv(csv_output, index=False, encoding='utf-8-sig', float_format='%.0f')
        
        # 输出总计信息
        total_plays = summary_df['总播放次数'].sum()
        total_song_plays = summary_df['歌曲播放统计'].sum()
        print(f"\n总计:")
        print(f"总播放次数: {total_plays}")
        print(f"歌曲播放统计: {total_song_plays}")
        
    def display_stats(self):
        """显示统计数据"""
        try:
            csv_path = os.path.join("statistics", "play_count_logs", "等级歌单播放次数共计.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                
                # 从配置文件获取随机首数信息
                try:
                    with open('config.json', 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        level_random_counts = {
                            level['name'].split()[0]: int(level['random_count'])  # 使用int()确保是整数
                            for level in config['levels']
                        }
                except Exception as e:
                    print(f"读取配置文件失败: {str(e)}")
                    level_random_counts = {}
                
                # 添加随机首数列（不设置默认值）
                df['随机首数'] = df['渐进学习时长激励歌单'].apply(
                    lambda x: level_random_counts.get(x.strip('『』').split()[0], None)
                )
                
                # 只为有随机首数的行计算负载比率和推荐数量
                df['播放负载比率'] = None
                df['推荐歌曲数量'] = None
                
                # 计算有效行的负载比率和推荐数量
                valid_rows = df['随机首数'].notna()
                if valid_rows.any():
                    df.loc[valid_rows, '播放负载比率'] = (
                        df.loc[valid_rows, '总播放次数'] / df.loc[valid_rows, '随机首数']
                    )
                    median_load = df.loc[valid_rows, '播放负载比率'].median()
                    df.loc[valid_rows, '推荐歌曲数量'] = round(
                        df.loc[valid_rows, '总播放次数'] / median_load
                    ).astype('Int64')  # 使用可空的整数类型
                
                # 排序逻辑保持不变
                playlist_order = ['C', 'CC', 'CCC', 'B', 'BB', 'BBB', 'A', 'AA', 'AAA', 'S', 'SS', 'SSS']
                
                def get_playlist_order(playlist):
                    prefix = playlist.strip('『』').split()[0]
                    try:
                        return playlist_order.index(prefix)
                    except ValueError:
                        return float('inf')
                
                df['排序'] = df['渐进学习时长激励歌单'].apply(get_playlist_order)
                df = df.sort_values('排序').drop(columns=['排序'])
                
                # 创建表头（降低高度）
                header_frame = ctk.CTkFrame(self.container, fg_color="transparent", height=25)
                header_frame.pack(fill="x", pady=(0, 5), padx=5)
                header_frame.pack_propagate(False)  # 固定高度
                
                # 定义列宽比例和对齐方式
                columns = {
                    "渐进学习时长激励歌单": {"width": 220, "align": "w", "padx": 20},  # 固定宽度220像素
                    "歌单总随机首数": {"width": True, "align": "center", "padx": 5},  # 改名
                    "歌曲播放统计": {"width": True, "align": "center", "padx": 5},  # 新增
                    "负载比率": {"width": True, "align": "center", "padx": 5},
                    "推荐数量": {"width": True, "align": "center", "padx": 5}
                }
                
                # 创建表头标签
                for col, props in columns.items():
                    label_frame = ctk.CTkFrame(
                        header_frame,
                        fg_color="transparent",
                        height=25,
                        width=props["width"] if isinstance(props["width"], int) else None  # 只给第一列设置固定宽度
                    )
                    label_frame.pack(
                        side="left", 
                        fill="x", 
                        expand=props["width"] if isinstance(props["width"], bool) else False,  # 其他列使用 expand
                        padx=1
                    )
                    label_frame.pack_propagate(False)
                    
                    ctk.CTkLabel(
                        label_frame,
                        text=col,
                        font=self.subtitle_font,
                        text_color="#888888",
                        anchor=props["align"]
                    ).pack(
                        side="left" if props["align"] == "w" else "right",
                        padx=props["padx"],
                        fill="both",
                        expand=True
                    )

                # 添加调试信息
                print("\n开始创建数据行...")
                
                # 显示数据行
                for _, row in df.iterrows():
                    row_frame = ctk.CTkFrame(
                        self.container,
                        fg_color="transparent",
                        height=40
                    )
                    row_frame.pack(fill="x", pady=1, padx=5)
                    row_frame.pack_propagate(False)
                    
                    # 创建五个框架来容纳数据块
                    frames = []
                    for col, props in columns.items():
                        frame = ctk.CTkFrame(
                            row_frame,
                            fg_color="transparent",
                            height=40,
                            width=props["width"] if isinstance(props["width"], int) else None  # 只给第一列设置固定宽度
                        )
                        frame.pack(
                            side="left", 
                            fill="x", 
                            expand=props["width"] if isinstance(props["width"], bool) else False,  # 其他列使用 expand
                            padx=1
                        )
                        frame.pack_propagate(False)
                        frames.append(frame)
                    
                    # 获取颜色配置
                    level_name = row["渐进学习时长激励歌单"]
                    level = level_name.strip('『』')
                    colors = None
                    for rank in ['S', 'A', 'B', 'C']:
                        if rank in level:
                            colors = self.rank_colors[rank]
                            break
                    if colors is None:
                        colors = {
                            "bg": ["#2B2B2B", "#2B2B2B"],
                            "text": ["#FFFFFF", "#FFFFFF"]
                        }
                    
                    # 准备数据
                    data = {
                        "渐进学习时长激励歌单": level_name,
                        "歌单总随机首数": str(int(row["总播放次数"])) if pd.notna(row["总播放次数"]) else "",
                        "歌曲播放统计": str(int(row["歌曲播放统计"])) if pd.notna(row["歌曲播放统计"]) else "0",
                        "负载比率": f"{row['播放负载比率']:.2f}" if pd.notna(row["播放负载比率"]) else "",
                        "推荐数量": str(int(row["推荐歌曲数量"])) if pd.notna(row["推荐歌曲数量"]) else ""
                    }
                    
                    # 对于无随机首数的歌单，不显示总播放次数和相关比率
                    if not pd.notna(row["总播放次数"]):
                        data["歌单总随机首数"] = ""
                        data["负载比率"] = ""
                        data["推荐数量"] = ""
                    
                    # 创建数据块
                    for (col, value), frame in zip(data.items(), frames):
                        props = columns[col]
                        
                        # 计算背景色
                        if value == "":
                            bg_color = ["#2B2B2B", "#2B2B2B"]
                        else:
                            bg_color = [
                                self._adjust_color(c, 0.8 if col == "渐进学习时长激励歌单" else 0.6)
                                for c in colors["bg"]
                            ]
                        
                        # 创建块框架
                        block_frame = ctk.CTkFrame(
                            frame,
                            fg_color=bg_color,
                            corner_radius=8,
                            height=40
                        )
                        block_frame.pack(fill="both", expand=True, padx=1)
                        block_frame.pack_propagate(False)
                        
                        # 只在有值时显示标签
                        if value:
                            ctk.CTkLabel(
                                block_frame,
                                text=value,
                                font=self.default_font,
                                text_color=colors["text"][0],
                                anchor=props["align"]
                            ).pack(
                                side="left" if props["align"] == "w" else "right",
                                padx=props["padx"],
                                fill="x",
                                expand=True
                            )
        except Exception as e:
            ctk.CTkLabel(
                self.container,
                text=f"读取数据时出错: {str(e)}",
                font=self.default_font,
                text_color="#FF6B6B"
            ).pack(pady=20)

    def _adjust_color(self, color, factor):
        """调整颜色亮度"""
        if isinstance(color, str) and color.startswith("#"):
            # 将十六进制颜色转换为RGB
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            # 调整亮度
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)
            
            # 确保值在0-255范围内
            r = min(255, max(0, r))
            g = min(255, max(0, g))
            b = min(255, max(0, b))
            
            # 转换回十六进制
            return f"#{r:02x}{g:02x}{b:02x}"
        return color

# 如果直接运行此文件，则创建独立窗口进行测试
if __name__ == "__main__":
    root = ctk.CTk()
    root.title("歌单播放统计")
    root.geometry("1000x600")
    
    # 设置主题
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    viewer = PlaylistStatsViewer(root)
    viewer.pack(fill="both", expand=True)
    
    root.mainloop()
