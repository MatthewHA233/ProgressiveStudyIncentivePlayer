import os
import pandas as pd

# 定义读取play_count.csv文件的目录
play_count_dir = 'statistics/play_count_logs'

# 定义生成的WallpaperMusicMatcher.csv文件路径
output_file = 'WallpaperMusicMatcher.csv'

# 初始化一个空的DataFrame来存储所有数据
all_data = pd.DataFrame(columns=['歌单', '歌曲', '壁纸引擎ID', '壁纸名称', '所属作品'])

# 遍历play_count_logs文件夹中的所有csv文件
for file_name in os.listdir(play_count_dir):
    if file_name.endswith('_play_count.csv'):
        file_path = os.path.join(play_count_dir, file_name)
        
        # 读取每个csv文件
        try:
            df = pd.read_csv(file_path)
            
            # 确保文件中包含'歌单'和'歌曲'字段
            if '歌单' in df.columns and '歌曲' in df.columns:
                # 为每条记录增加必要的列，初始化为空
                df['壁纸引擎ID'] = '无'
                df['壁纸名称'] = ''
                df['所属作品'] = ''
                
                # 选择我们需要的列，并将它们追加到all_data
                df_selected = df[['歌单', '歌曲', '壁纸引擎ID', '壁纸名称', '所属作品']]
                all_data = pd.concat([all_data, df_selected], ignore_index=True)
            else:
                print(f"文件 {file_name} 缺少必要的字段: '歌单' 或 '歌曲'")
        except Exception as e:
            print(f"读取文件 {file_name} 时出错: {e}")

# 将合并后的数据保存为WallpaperMusicMatcher.csv
all_data.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"数据已成功保存到 {output_file}")
