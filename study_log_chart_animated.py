# 最后一帧停留一会
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from datetime import datetime, timedelta
import os
import time
import subprocess
from PIL import Image
import re
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.progress import Progress
import shutil
import json

# 辅助函数，寻找交点
def find_intersection(df, y_target, index):
    if index <= 0 or index >= len(df):
        return None
    y1 = df.loc[index - 1, '目前已学习时长']
    y2 = df.loc[index, '目前已学习时长']
    if y1 == y2:
        return None
    proportion = (y_target - y1) / (y2 - y1)
    if not 0 <= proportion <= 1:
        return None
    time1 = df.loc[index - 1, '现在时间']
    time2 = df.loc[index, '现在时间']
    delta = (time2 - time1).total_seconds()
    intersect_time = time1 + timedelta(seconds=delta * proportion)
    return intersect_time

# 初始化 rich 控制台输出
console = Console()

def get_user_input_date_for_video():
    today = datetime.now()

    # 默认日期是今天
    default_date = today.strftime('%Y-%m-%d')

    # 提示用户输入想生成图表动画视频的日期
    console.print(f"[#FFA500]请输入想生成图表动画视频的日期，默认为今天 ({default_date})，按 Enter 使用默认日期，或输入 'y' 表示昨天：[/#FFA500]")
    user_input = input(f"（例如：02/08、02-08、2024-02-08）：").strip()

    if user_input == "":
        console.print(f"[#FFA500]未输入日期，使用默认日期: 今天 ({default_date})[/#FFA500]")
        selected_date = today
    elif user_input.lower() == 'y':
        # 昨天的日期
        selected_date = today - timedelta(days=1)
    elif re.match(r'^\d{2}[-/]\d{2}$', user_input):  # 支持 02/08 或 02-08 格式
        # 如果用户输入的是 MM/DD 或 MM-DD 格式
        month_day = user_input.split('/') if '/' in user_input else user_input.split('-')
        month = int(month_day[0])
        day = int(month_day[1])
        
        # 使用当前年份来构造日期
        selected_date = today.replace(month=month, day=day)
    elif re.match(r'^\d{4}-\d{2}-\d{2}$', user_input):  # 支持 2024-02-08 格式
        # 如果用户输入的是 YYYY-MM-DD 格式
        selected_date = datetime.strptime(user_input, '%Y-%m-%d')
    else:
        # 用户输入格式不正确，返回今天的日期
        console.print(f"[bold red]输入的日期格式不正确，使用默认日期: 今天 ({default_date})[/bold red]")
        selected_date = today

    # 输出已选择的日期，并加载等待效果
    selected_date_str = selected_date.strftime('%Y-%m-%d')
    console.print(f"[bold magenta]已选择 {selected_date_str} 的图表视频，正在加载...[/bold magenta]")

    # 模拟加载效果（减少到 1.5 秒以提高速度感）
    with Progress(transient=True) as progress:
        task = progress.add_task("[bold magenta]加载中...[/bold magenta]", total=100)
        for i in range(15):  # 更新15次，每次约0.1秒，总共约1.5秒
            progress.update(task, advance=6.67)  # 每次推进 6.67%，15次共完成 100%
            time.sleep(0.1)

    # 在加载完成后空出三行
    console.print("\n" * 3)

    return selected_date

# 调用函数并获取返回的日期
selected_date = get_user_input_date_for_video()

# 格式化 selected_date 为字符串
selected_date_str = selected_date.strftime('%Y-%m-%d')

# 获取用户输入的日期并根据日期生成图表视频的 CSV 文件路径
def get_csv_file_path_for_video():
    csv_file_path = os.path.join('statistics', 'study_time_logs', f'学习记录_{selected_date.strftime("%Y-%m-%d")}.csv')

    # 检查文件是否存在
    if not os.path.exists(csv_file_path):
        console.print(f"[bold red]错误: CSV 文件 {csv_file_path} 不存在！[/bold red]")
        return None
    return csv_file_path

# 调用函数获取 CSV 文件路径
csv_file_path = get_csv_file_path_for_video()
if csv_file_path:
    console.print(f"[bold green]成功获取 CSV 文件路径: {csv_file_path}[/bold green]")
else:
    console.print(f"[bold red]无法获取 CSV 文件路径，请检查文件是否存在！[/bold red]")

# 读取 CSV 文件
df = pd.read_csv(csv_file_path)

# 将"现在时间"列转换为时间类型
df['现在时间'] = pd.to_datetime(df['现在时间'], format='%H:%M:%S')

# 辅助函数：将目标学习时长转换为分钟
def convert_to_minutes(value):
    try:
        if isinstance(value, (float, int)):
            return value * 60
        elif isinstance(value, str):
            value = value.strip()
            if '时' in value:
                hours = int(value.replace('时', '').strip())
                return hours * 60
            elif ':' in value:
                hours, minutes = map(int, value.split(':'))
                return hours * 60 + minutes
        else:
            raise ValueError(f"Unexpected value format: {value}")
    except Exception as e:
        print(f"Error converting value to minutes: {e}")
        return 0

# 应用转换函数来处理目标学习时长列
df['目标学习时长'] = df['目标学习时长'].apply(convert_to_minutes) / 60  # 转换为小时单位

# 将其余列转换为分钟数，以便于绘制图表
def time_to_minutes(time_str):
    if isinstance(time_str, str):
        parts = time_str.replace('分', '').replace('时', ':').split(':')
        if len(parts) == 2:
            hours, minutes = map(int, parts)
            return hours * 60 + minutes
    return time_str

def minutes_to_hours_minutes(minutes):
    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)
    return f'{hours}时{remaining_minutes}分'

for column in ['目前已学习时长', '预测今日学习时长', '剩余空闲时间']:
    df[column] = df[column].apply(time_to_minutes)

df['目标学习时长'] = df['目标学习时长'].apply(lambda x: round(x * 60) if isinstance(x, float) else time_to_minutes(x))

df['目前已学习时长'] = df['目前已学习时长'] / 60
df['预测今日学习时长'] = df['预测今日学习时长'] / 60
df['目标学习时长'] = df['目标学习时长'] / 60
df['剩余空闲时间'] = df['剩余空闲时间'] / 60

# 按"现在时间"排序数据框
df = df.sort_values(by='现在时间').reset_index(drop=True)

# 创建 "学习时长图表视频" 文件夹（如果不存在的话）
output_video_folder = '学习时长图表视频'
os.makedirs(output_video_folder, exist_ok=True)

# 逐步读取并生成图表
# 创建临时的 "逐帧图片" 文件夹
output_frame_folder = os.path.join(output_video_folder, '逐帧图片')
os.makedirs(output_frame_folder, exist_ok=True)

# 在创建图表之前，添加读取配置文件的函数
def load_color_ranges_from_config():
    """从 config.json 加载颜色区间配置"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        color_ranges = []
        for level in config['levels']:
            color_ranges.append((
                level['start'],
                level['end'],
                level['color'],  # 直接使用 rgba 格式
                level['name']
            ))
            
        return color_ranges
    except Exception as e:
        console.print(f"[bold red]加载颜色配置失败: {str(e)}[/bold red]")
        return []

# 替换原有的 color_ranges 定义
color_ranges = load_color_ranges_from_config()

# 循环处理每一行数据，逐步增加行数
for i in range(1, len(df) + 1):
    # 取前 i 行数据
    df_sub = df.iloc[:i]

    # 设置Plotly折线图
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_sub['现在时间'], 
        y=df_sub['目前已学习时长'], 
        mode='lines+markers', 
        name='目前已学习时长', 
        line=dict(color='#FFD700', width=5, shape='spline', smoothing=1.3), 
        marker=dict(size=10)
    ))
    fig.add_trace(go.Scatter(
        x=df_sub['现在时间'], 
        y=df_sub['预测今日学习时长'], 
        mode='lines+markers', 
        name='预测今日学习时长', 
        line=dict(color='#FF4500', dash='dash', width=4, shape='spline', smoothing=1.3), 
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=df_sub['现在时间'], 
        y=df_sub['目标学习时长'], 
        mode='lines+markers', 
        name='目标学习时长', 
        line=dict(color='#32CD32', width=4), 
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=df_sub['现在时间'], 
        y=df_sub['剩余空闲时间'], 
        mode='lines', 
        name='剩余空闲时间', 
        line=dict(color='#1E90FF', dash='dashdot', width=4)
    ))

    for start, end, color, label in color_ranges:
        filled_x = []
        filled_y = []
        
        for i in range(1, len(df_sub)):
            y_prev = df_sub.loc[i - 1, '目前已学习时长']
            y_curr = df_sub.loc[i, '目前已学习时长']
            
            in_prev = start <= y_prev < end
            in_curr = start <= y_curr < end

            if in_prev:
                filled_x.append(df_sub.loc[i - 1, '现在时间'])
                filled_y.append(y_prev)

            if (y_prev < start and y_curr >= start) or (y_prev >= start and y_curr < start):
                intersect_time = find_intersection(df_sub, start, i)
                if intersect_time:
                    filled_x.append(intersect_time)
                    filled_y.append(start)

            if (y_prev < end and y_curr >= end) or (y_prev >= end and y_curr < end):
                intersect_time = find_intersection(df_sub, end, i)
                if intersect_time:
                    filled_x.append(intersect_time)
                    filled_y.append(end)

            if in_curr:
                filled_x.append(df_sub.loc[i, '现在时间'])
                filled_y.append(y_curr)

        if filled_x:  # 仅当 filled_x 有数据时才添加填充区域
            fig.add_trace(go.Scatter(
                x=filled_x, y=filled_y,
                fill='tozeroy', fillcolor=color,
                line=dict(color=color),
                name=label, showlegend=True
            ))

            # 计算标签的位置，靠近填充区域的下部（例如，30% 位置）
            label_y_position = start + 0.3 * (end - start)

            # 计算标签的中点时间
            midpoint_index = len(filled_x) // 2
            midpoint_time = filled_x[midpoint_index]
            
            # 添加标签
            fig.add_annotation(
                x=midpoint_time,
                y=label_y_position,
                text=label,
                showarrow=False,
                font=dict(size=14, color='white'),
                xanchor='center',
                yanchor='middle',
                align='center',
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='white',
                borderwidth=1,
                borderpad=2
            )
    # 生成每小时的时间点
    hour_ticks = []
    current_time_tick = df['现在时间'].min().replace(minute=0, second=0, microsecond=0)  # 从最接近的整点开始
    while current_time_tick <= df['现在时间'].max():
        hour_ticks.append(current_time_tick)
        current_time_tick += timedelta(hours=1)

    # 添加每小时固定标签作为注释，并添加黄色细虚线垂直线
    for hour_time in hour_ticks:
        # 添加注释
        fig.add_annotation(
            x=hour_time,
            y=0,  # 放置在x轴下方
            xref='x',
            yref='y',
            text=hour_time.strftime('%H点'),  # 简化时间格式为“12点”
            showarrow=False,
            font=dict(size=12, color='yellow'),  # 调整字体大小为12，颜色为黄色
            xanchor='center',
            yanchor='top',
            align='center',
            yshift=-20  # 增加yshift值，进一步向下移动标签
        )
        
        # 添加垂直线，使用布局的 shapes 属性
        fig.add_shape(
            type='line',
            x0=hour_time,
            y0=0,
            x1=hour_time,
            y1=max(df[['目前已学习时长', '预测今日学习时长', '目标学习时长', '剩余空闲时间']].max()) + 1,
            xref='x',
            yref='y',
            line=dict(color='yellow', width=1, dash='dash')
        )


    # 设置图表布局
    fig.update_layout(
        title=f'学习时长记录 - 折线图 ({i} 行数据)',
        xaxis_title='现在时间',
        yaxis_title='时间 (小时)',
        xaxis=dict(
            tickmode='array',
            tickvals=df_sub['现在时间'],
            ticktext=[time.strftime('%H:%M:%S') for time in df_sub['现在时间']],
            tickangle=45,
            tickfont=dict(size=10, color='rgba(255, 255, 255, 0.6)'),
            title_standoff=25,
            showgrid=True,
            gridcolor='LightGray',
            zeroline=False
        ),
        yaxis=dict(
            tickformat='.1f小时',
            showgrid=True,
            gridcolor='LightGray',
            range=[0, max(df_sub[['目前已学习时长', '预测今日学习时长', '目标学习时长', '剩余空闲时间']].max()) + 1]
        ),
        template='plotly_dark',
        autosize=False,
        width=1200,
        height=600,
        legend=dict(x=0.01, y=0.99),
        plot_bgcolor='rgba(30, 30, 30, 1)',
        paper_bgcolor='rgba(30, 30, 30, 1)',
        font=dict(color='white', size=14),
        margin=dict(b=120)
    )

    # 添加图例和样式
    fig.update_traces(marker=dict(symbol='circle', line=dict(width=1, color='DarkSlateGrey')))
    fig.update_xaxes(showline=True, linewidth=2, linecolor='white', mirror=True)
    fig.update_yaxes(showline=True, linewidth=2, linecolor='white', mirror=True)


    # 保存图表到逐帧图片文件夹
    output_file_path = os.path.join(output_frame_folder, f'学习时长图表_{selected_date_str}_frame_{i}.png')
    fig.write_image(output_file_path)

    print(f"Frame {i} saved as {output_file_path}")

# 获取所有保存的图片文件名，筛选出匹配日期的文件，并按帧号排序
image_files = sorted(
    [f for f in os.listdir(output_frame_folder) if f.endswith('.png') and selected_date_str in f],
    key=lambda x: int(x.split('_')[-1].split('.')[0])
)

# 获取图片的分辨率（假设所有图片分辨率相同）
image_path = os.path.join(output_frame_folder, image_files[0])
img = Image.open(image_path)
width, height = img.size

# 设置输出视频文件的路径（保存到 "学习时长图表视频" 文件夹中）
output_video_path = os.path.join(output_video_folder, f'学习时长图表视频_{selected_date_str}.mp4')

# 显示帧率设置的提示，使用 rich 装饰
console.print(Panel("[#FFA500]请输入视频的帧率，默认 10 帧/秒，按 Enter 使用默认帧率：[/#FFA500]"))

# 让用户输入帧率，默认 10 帧每秒
frame_rate_input = Prompt.ask("[#00FF00]请输入视频的帧率[/#00FF00]", default="10")
frame_rate = int(frame_rate_input) if frame_rate_input else 10  # 默认为10帧

console.print(f"[bold green]视频帧率设置为 {frame_rate} 帧每秒。[/bold green]")

# 确保我们从目录中获取最后一帧文件
last_frame_filename = image_files[-1]
last_frame_path = os.path.join(output_frame_folder, last_frame_filename)

# 确保文件存在
if os.path.exists(last_frame_path):
    print(f"确认：最后一帧文件是 {last_frame_filename}，准备复制它。")
else:
    print(f"错误：找不到最后一帧文件 {last_frame_filename}，请检查目录。")
    exit(1)

# 复制最后一帧，假设你需要复制最后一帧 49 次，保持总帧数
for i in range(1, frame_rate * 5):  # 复制 49 次（10帧的5倍）
    new_frame_number = int(last_frame_filename.split('_')[-1].split('.')[0]) + i  # 从当前帧号递增
    duplicate_frame_path = os.path.join(output_frame_folder, f'学习时长图表_{selected_date_str}_frame_{new_frame_number}.png')
    
    # 检查目标文件是否与源文件相同
    if last_frame_path != duplicate_frame_path:
        # 复制最后一帧
        shutil.copy(last_frame_path, duplicate_frame_path)
        print(f"Frame {new_frame_number} saved as {duplicate_frame_path}")
    else:
        print(f"跳过复制：源文件和目标文件是相同的 {duplicate_frame_path}")

# 创建一个临时图像文件名列表
image_file_pattern = os.path.join(output_frame_folder, f'学习时长图表_{selected_date_str}_frame_%d.png')

# 使用 ffmpeg 命令将图片序列合成视频
ffmpeg_command = [
    'ffmpeg',
    '-framerate', str(frame_rate),  # 使用用户输入的帧率
    '-i', image_file_pattern,  # 输入文件名格式
    '-s', f'{width}x{height}',  # 设置分辨率
    '-c:v', 'libx264',  # 使用 x264 编解码器
    '-pix_fmt', 'yuv420p',  # 设置像素格式，保证兼容性
    '-y',  # 覆盖输出文件（如果已经存在）
    output_video_path
]

# 执行命令并等待完成
try:
    console.print(f"[bold magenta]正在生成视频，请稍候...[/bold magenta]")
    subprocess.run(ffmpeg_command, check=True)  # 等待 ffmpeg 完成
    console.print(f"[bold green]视频已成功保存为: {output_video_path}[/bold green]")

    # 增加延时，确保文件释放
    time.sleep(1)

    # 删除逐帧图片文件夹中的所有图片
    for image_file in os.listdir(output_frame_folder):
        if image_file.endswith('.png') and selected_date_str in image_file:
            image_path = os.path.join(output_frame_folder, image_file)
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    console.print(f"[bold red]已删除 {image_file}[/bold red]")
            except PermissionError as e:
                console.print(f"[bold yellow]无法删除 {image_file}: {e}，文件可能被占用。[/bold yellow]")

    print(f"上述图片已删除，文件夹 {output_frame_folder} 现在差不多已清空。")

    # 询问是否查看视频并打开视频文件夹
    view_video = Prompt.ask("[#FFA500]视频生成完毕，是否选择查看视频并打开视频文件夹？[y/n]", default="y").lower()

    if view_video == "y":
        # 打开视频文件夹
        os.startfile(output_video_folder)
        console.print(f"[bold cyan]已打开视频文件夹：{output_video_folder}[/bold cyan]")
        
        # 打开视频文件（使用默认视频播放器）
        os.startfile(output_video_path)
        console.print(f"[bold cyan]正在播放视频：{output_video_path}[/bold cyan]")

except subprocess.CalledProcessError as e:
    console.print(f"[bold red]生成视频时出现错误: {e}[/bold red]")