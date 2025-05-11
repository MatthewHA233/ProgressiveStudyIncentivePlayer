# 适配数据统计文件夹
import time
import os
import re
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from rich.progress import Progress
from datetime import datetime, timedelta

# 初始化 rich 控制台
console = Console()

# 获取并格式化用户输入的日期
def get_user_input_date():
    today = datetime.now()

    # 默认日期是今天
    default_date = today.strftime('%Y-%m-%d')

    # 提示用户输入日期
    console.print(f"[#FFA500]请输入日志日期，默认为今天 ({default_date})，按 Enter 使用默认日期，或输入 'y' 表示昨天：[/#FFA500]")
    user_input = input(f"（例如：02/08、02-08、2024-02-08）：").strip()

    if user_input == "":
        console.print(f"[#FFA500]未输入日期，使用默认日期: 今天 ({default_date})[/#FFA500]")
        selected_date = today
    elif user_input.lower() == 'y':
        # 昨天的日期
        selected_date = today - timedelta(days=1)
    elif re.match(r'^\d{2}[-/]\d{2}$', user_input):  # 支持 02/08 或 02-08 格式
        selected_date = today.replace(month=int(user_input.split('/')[0] if '/' in user_input else user_input.split('-')[0]),
                                      day=int(user_input.split('/')[1] if '/' in user_input else user_input.split('-')[1]))
    elif re.match(r'^\d{4}-\d{2}-\d{2}$', user_input):  # 支持 2024-02-08 格式
        selected_date = datetime.strptime(user_input, '%Y-%m-%d')
    else:
        # 用户输入格式不正确，返回今天的日期
        console.print(f"[bold red]输入的日期格式不正确，使用默认日期: 今天 ({default_date})[/bold red]")
        selected_date = today

    # 输出已选择的日期，并加载等待效果
    selected_date_str = selected_date.strftime('%Y-%m-%d')
    console.print(f"[bold magenta]已选择 {selected_date_str} 的日志，正在加载...[/bold magenta]")

    # 模拟加载效果（减少到 1.5 秒以提高速度感）
    with Progress(transient=True) as progress:
        task = progress.add_task("[bold magenta]加载中...[/bold magenta]", total=100)
        for i in range(15):  # 更新15次，每次约0.1秒，总共约1.5秒
            progress.update(task, advance=6.67)  # 每次推进 6.67%，15次共完成 100%
            time.sleep(0.1)

    # 在加载完成后空出三行
    console.print("\n" * 3)

    return selected_date

# 设置日志保存路径，按照 YYYY-MM 格式建立子文件夹
def get_log_file_path(date):
    base_log_folder = os.path.join(os.getcwd(), 'statistics', 'terminal_logs')
    log_folder = os.path.join(base_log_folder, date.strftime('%Y-%m'))
    log_file_path = os.path.join(log_folder, f"print_logs_{date.strftime('%Y-%m-%d')}.txt")
    return log_file_path

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
        box=ROUNDED,
        padding=(1, 4)  # 增加内边距来模拟“字体变大”的效果
    )

    console.print(panel)


# 获取并设置显示日志的“频率”值
def get_log_display_frequency():
    console.print("[#FFA500]请输入日志逐行显示的频率（行/秒），默认 20 行/秒：[/#FFA500]")
    user_input = input("请输入频率（例如：30 或 10）：").strip()
    
    if user_input == "":
        console.print("[#FFA500]未输入频率，使用默认频率: 20 行/秒[/#FFA500]")
        return 20

    try:
        frequency = float(user_input)
        if frequency <= 0:
            raise ValueError("频率必须大于 0")
    except ValueError:
        # 如果用户输入无效，使用默认的 20 行/秒
        console.print(f"[bold red]输入无效，使用默认频率: 20 行/秒[/bold red]")
        frequency = 20
    return frequency

# 读取日志文件并逐行打印的函数
def replay_logs():
    # 获取并设置显示日志的频率
    frequency = get_log_display_frequency()

    # 根据频率计算延迟时间，延迟时间是频率的倒数
    display_delay = 1 / frequency

    while True:
        # 获取用户输入日期
        selected_date = get_user_input_date()

        # 获取日志文件路径
        log_file_path = get_log_file_path(selected_date)

        if not os.path.exists(log_file_path):
            # 如果日志文件不存在，输出提示并重新进入日期选择界面
            console.print(f"[bold red]日志文件 {log_file_path} 不存在，请重新选择日期。[/bold red]")
            continue  # 跳过当前循环，重新输入日期

        # 如果日志文件存在，则开始读取日志
        with open(log_file_path, 'r', encoding='utf-8') as f:
            buffer = []
            inside_panel = False
            for line in f:
                # 使用正则表达式去除时间戳和日志级别信息，但保留日志内容部分
                log_content_match = re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - [A-Z]+ - (.*)', line)
                log_content = log_content_match.group(1).strip() if log_content_match else line.strip()

                # 处理奖状样式的回放
                if "学习成就奖状" in log_content:
                    inside_panel = True
                    buffer.append(log_content)
                    continue
                elif inside_panel:
                    buffer.append(log_content)
                    if "╰" in log_content:
                        # 完整的奖状输出，从 buffer 中提取实际值
                        buffer_str = "\n".join(buffer)

                        # 提取达成时间
                        time_match = re.search(r"恭喜你达成了 (\d+时\d+分) 学习时长", buffer_str)
                        formatted_cell_time = time_match.group(1) if time_match else "未知时间"

                        # 提取音乐名，使用更宽泛的正则表达式匹配“正在播放的是:”到“🎶 🎵”之间的内容
                        music_match = re.search(r"正在播放的是: (.+?) 🎶  🎵", buffer_str, re.DOTALL)
                        music_name = music_match.group(1).strip() if music_match else "未知音乐"

                        # 提取等级
                        level_match = re.search(r"『(.*?)』", buffer_str)
                        level = level_match.group(1) if level_match else "未知等级"

                        # 打印奖状
                        print_certificate(formatted_cell_time, music_name, level)
                        inside_panel = False
                        buffer = []
                    continue

                # 打印一般日志内容
                console.print(log_content)
                time.sleep(display_delay)  # 根据计算出的延迟时间控制逐行输出速度

        # 如果日志存在并已成功读取，则跳出循环
        console.input("\n[bold cyan]回放结束，按回车键退出...[/bold cyan]")
        break  # 跳出循环，结束程序

if __name__ == "__main__":
    replay_logs()
