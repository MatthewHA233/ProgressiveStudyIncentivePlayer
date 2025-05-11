import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from datetime import datetime, timedelta
import os
import webbrowser
import json

# 辅助函数，寻找交点
def find_intersection(df, y_target, index):
    """
    寻找 y 在 index-1 和 index 之间跨过 y_target 的交点。
    """
    if index <= 0 or index >= len(df):
        return None
    y1 = df.loc[index - 1, '目前已学习时长']
    y2 = df.loc[index, '目前已学习时长']
    if y1 == y2:
        return None
    # 计算交点的比例位置
    proportion = (y_target - y1) / (y2 - y1)
    if not 0 <= proportion <= 1:
        return None
    time1 = df.loc[index - 1, '现在时间']
    time2 = df.loc[index, '现在时间']
    delta = (time2 - time1).total_seconds()
    intersect_time = time1 + timedelta(seconds=delta * proportion)
    return intersect_time

# 获取当天日期
current_date = datetime.now().strftime('%Y-%m-%d')

# CSV 文件路径
csv_file_path = os.path.join('statistics', 'study_time_logs', f'学习记录_{current_date}.csv')

# 读取 CSV 文件
df = pd.read_csv(csv_file_path)

# 将"现在时间"列转换为时间类型
df['现在时间'] = pd.to_datetime(df['现在时间'], format='%H:%M:%S')

# 辅助函数：将目标学习时长转换为分钟
def convert_to_minutes(value):
    """
    将目标学习时长（小时或格式化的字符串，如 '12时'）转换为分钟。
    """
    try:
        # 如果值是浮动的小时数（例如 12.0），直接乘以60转为分钟
        if isinstance(value, (float, int)):
            return value * 60
        # 如果值是字符串格式（如 '12时' 或 '12:30'），需要提取出小时并转为分钟
        elif isinstance(value, str):
            value = value.strip()
            if '时' in value:  # 处理类似 '12时' 的格式
                hours = int(value.replace('时', '').strip())
                return hours * 60
            elif ':' in value:  # 处理类似 '12:30' 的格式
                hours, minutes = map(int, value.split(':'))
                return hours * 60 + minutes
        else:
            raise ValueError(f"Unexpected value format: {value}")
    except Exception as e:
        print(f"Error converting value to minutes: {e}")
        return 0  # 出错时返回 0 以避免中断流程

# 应用转换函数来处理目标学习时长列
df['目标学习时长'] = df['目标学习时长'].apply(convert_to_minutes) / 60  # 转换为小时单位

# 打印转换后的值来检查是否正确
# print("转换后的目标学习时长（小时）：")
# print(df['目标学习时长'])

# 将其余列转换为分钟数，以便于绘制图表
def time_to_minutes(time_str):
    if isinstance(time_str, str):
        parts = time_str.replace('分', '').replace('时', ':').split(':')
        if len(parts) == 2:
            hours, minutes = map(int, parts)
            return hours * 60 + minutes
    return time_str  # 如果已经是数字类型，则直接返回

def minutes_to_hours_minutes(minutes):
    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)
    return f'{hours}时{remaining_minutes}分'

for column in ['目前已学习时长', '预测今日学习时长', '剩余空闲时间']:
    df[column] = df[column].apply(time_to_minutes)

# 处理目标学习时长列（可能包含小数）
df['目标学习时长'] = df['目标学习时长'].apply(lambda x: round(x * 60) if isinstance(x, float) else time_to_minutes(x))

# 将分钟数转换为小时数
df['目前已学习时长'] = df['目前已学习时长'] / 60
df['预测今日学习时长'] = df['预测今日学习时长'] / 60
df['目标学习时长'] = df['目标学习时长'] / 60
df['剩余空闲时间'] = df['剩余空闲时间'] / 60

# 按"现在时间"排序数据框
df = df.sort_values(by='现在时间').reset_index(drop=True)

# 设置Plotly折线图
fig = go.Figure()

# 添加每一列数据的折线图
fig.add_trace(go.Scatter(
    x=df['现在时间'], 
    y=df['目前已学习时长'], 
    mode='lines+markers', 
    name='目前已学习时长', 
    line=dict(color='#FFD700', width=5, shape='spline', smoothing=1.3), 
    marker=dict(size=10)
))
fig.add_trace(go.Scatter(
    x=df['现在时间'], 
    y=df['预测今日学习时长'], 
    mode='lines+markers', 
    name='预测今日学习时长', 
    line=dict(color='#FF4500', dash='dash', width=4, shape='spline', smoothing=1.3), 
    marker=dict(size=8)
))
fig.add_trace(go.Scatter(
    x=df['现在时间'], 
    y=df['目标学习时长'], 
    mode='lines+markers', 
    name='目标学习时长', 
    line=dict(color='#32CD32', width=4), 
    marker=dict(size=8)
))
fig.add_trace(go.Scatter(
    x=df['现在时间'], 
    y=df['剩余空闲时间'], 
    mode='lines', 
    name='剩余空闲时间', 
    line=dict(color='#1E90FF', dash='dashdot', width=4)
))

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
        print(f"加载颜色配置失败: {str(e)}")
        return []

# 替换原有的 color_ranges 定义
color_ranges = load_color_ranges_from_config()

# 为每个区间添加填充色，并在区域靠下的位置添加标签
for start, end, color, label in color_ranges:
    filled_x = []
    filled_y = []
    
    for i in range(1, len(df)):
        y_prev = df.loc[i - 1, '目前已学习时长']
        y_curr = df.loc[i, '目前已学习时长']
        
        # 检查区间是否在当前范围内
        in_prev = start <= y_prev < end
        in_curr = start <= y_curr < end

        # 添加上一个点
        if in_prev:
            filled_x.append(df.loc[i - 1, '现在时间'])
            filled_y.append(y_prev)

        # 检查是否穿过起始边界
        if (y_prev < start and y_curr >= start) or (y_prev >= start and y_curr < start):
            intersect_time = find_intersection(df, start, i)
            if intersect_time:
                filled_x.append(intersect_time)
                filled_y.append(start)
        
        # 检查是否穿过结束边界
        if (y_prev < end and y_curr >= end) or (y_prev >= end and y_curr < end):
            intersect_time = find_intersection(df, end, i)
            if intersect_time:
                filled_x.append(intersect_time)
                filled_y.append(end)

        # 添加当前点
        if in_curr:
            filled_x.append(df.loc[i, '现在时间'])
            filled_y.append(y_curr)

    # 确保列表不为空后转换
    if filled_x and filled_y:
        # 按时间排序点
        sorted_points = sorted(zip(filled_x, filled_y), key=lambda x: x[0])
        sorted_x, sorted_y = zip(*sorted_points)
        
        # 闭合多边形，返回到零点
        filled_x = list(sorted_x) + [sorted_x[-1], sorted_x[0]]
        filled_y = list(sorted_y) + [0, 0]
        
        # 添加填充区域
        fig.add_trace(go.Scatter(
            x=filled_x,
            y=filled_y,
            fill='toself',
            fillcolor=color,
            mode='none',
            name=label,
            showlegend=False
        ))

        # 计算标签的位置，靠近填充区域的下部（例如，30% 位置）
        label_y_position = start + 0.3 * (end - start)
        
        # 计算标签的中点时间
        midpoint_index = len(sorted_x) // 2
        midpoint_time = sorted_x[midpoint_index]
        
        # 添加标签，使用 add_annotation
        fig.add_annotation(
            x=midpoint_time,
            y=label_y_position,
            text=label,
            showarrow=False,
            font=dict(size=14, color='white'),
            xanchor='center',
            yanchor='middle',
            align='center',
            bgcolor='rgba(0,0,0,0.5)',  # 可选：为标签添加半透明背景以提高可读性
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

# 设置图表布局，调整y轴和底部边距
fig.update_layout(
    title='学习时长记录 - 折线图',
    xaxis_title='现在时间',
    yaxis_title='时间 (小时)',
    xaxis=dict(
        tickmode='array',
        tickvals=df['现在时间'],
        ticktext=[time.strftime('%H:%M:%S') for time in df['现在时间']],
        tickangle=45,
        tickfont=dict(size=10, color='rgba(255, 255, 255, 0.6)'),  # 数据点标签稍微缩小一点
        title_standoff=25,
        showgrid=True,
        gridcolor='LightGray',
        zeroline=False
    ),
    yaxis=dict(
        tickformat='.1f小时',
        showgrid=True,
        gridcolor='LightGray',
        range=[0, max(df[['目前已学习时长', '预测今日学习时长', '目标学习时长', '剩余空闲时间']].max()) + 1]
    ),
    template='plotly_dark',
    autosize=False,
    width=1200,
    height=600,
    legend=dict(x=0.01, y=0.99),
    plot_bgcolor='rgba(30, 30, 30, 1)',
    paper_bgcolor='rgba(30, 30, 30, 1)',
    font=dict(color='white', size=14),
    margin=dict(b=120)  # 增加底部边距以容纳更下方的注释
)

# 添加图例和样式
fig.update_traces(marker=dict(symbol='circle', line=dict(width=1, color='DarkSlateGrey')))
fig.update_xaxes(showline=True, linewidth=2, linecolor='white', mirror=True)
fig.update_yaxes(showline=True, linewidth=2, linecolor='white', mirror=True)

# 创建学习时长图表文件夹路径
output_folder = '学习时长图表'
os.makedirs(output_folder, exist_ok=True)

# 保存图表到指定文件夹
output_file_path = os.path.join(output_folder, f'学习时长图表_{current_date}.html')
pio.write_html(fig, file=output_file_path)

# 打开生成的HTML文件
webbrowser.open(f'file://{os.path.realpath(output_file_path)}')
