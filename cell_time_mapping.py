"""
昼夜表单元格时间映射模块

此模块提供了时间点到Excel单元格的映射关系，用于自动记录昼夜表。
"""

from datetime import datetime, time, timedelta
import string

# 基础映射常量
DAY_SHIFT = 34  # 每两天下移的行数
WEEKDAY_SHIFT = 20  # 相邻两天（如周一到周二）的列偏移量

# 昼表起始列和夜表起始列（周一）
DAY_START_COL = 'J'  # 昼表起始列
NIGHT_START_COL = 'A'  # 夜表起始列

# 昼表和夜表的时间范围
DAY_START_TIME = time(6, 5)  # 昼表开始时间 06:05
DAY_END_TIME = time(15, 4)  # 昼表结束时间 15:04
NIGHT_START_TIME = time(15, 5)  # 夜表开始时间 15:05
NIGHT_END_TIME = time(22, 4)  # 夜表结束时间 22:04，修改以包含22:00

def get_column_letter(index):
    """将数字索引转换为Excel列字母"""
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result

def get_column_index(column_letter):
    """将Excel列字母转换为数字索引"""
    index = 0
    for char in column_letter:
        index = index * 26 + (ord(char.upper()) - ord('A') + 1)
    return index

def get_cell_for_time(current_time, weekday):
    """
    根据给定的时间和星期几，返回对应的Excel单元格坐标
    
    参数:
        current_time: datetime.time 对象，表示当前时间
        weekday: int，表示星期几（0-6，0表示星期一）
    
    返回:
        tuple: (列字母, 行号) 表示Excel单元格坐标
    """
    # 计算行偏移（基于星期几）
    row_offset = (weekday // 2) * DAY_SHIFT
    
    # 计算列偏移（基于星期几是否为偶数）
    col_offset = (weekday % 2) * WEEKDAY_SHIFT
    
    # 将时间转换为分钟数，用于计算
    current_minutes = current_time.hour * 60 + current_time.minute
    
    # 判断是昼表还是夜表
    if DAY_START_TIME <= current_time <= DAY_END_TIME:
        # 昼表处理
        day_start_minutes = DAY_START_TIME.hour * 60 + DAY_START_TIME.minute
        minutes_diff = current_minutes - day_start_minutes
        
        # 每5分钟一个单元格，计算偏移量
        time_slots = minutes_diff // 5
        
        # 计算列偏移（每12个时间槽换一列）
        col_index = get_column_index(DAY_START_COL) + col_offset + (time_slots // 12)
        column = get_column_letter(col_index)
        
        # 计算行号（考虑到每5个时间槽有2个空行）
        slot_in_column = time_slots % 12
        if slot_in_column < 2:  # 前两个时间槽 (0, 1)
            row = 2 + slot_in_column + row_offset
        elif slot_in_column < 4:  # 接下来两个时间槽 (2, 3)
            row = 5 + (slot_in_column - 2) + row_offset
        elif slot_in_column < 6:  # 接下来两个时间槽 (4, 5)
            row = 8 + (slot_in_column - 4) + row_offset
        elif slot_in_column < 8:  # 接下来两个时间槽 (6, 7)
            row = 11 + (slot_in_column - 6) + row_offset
        elif slot_in_column < 10:  # 接下来两个时间槽 (8, 9)
            row = 14 + (slot_in_column - 8) + row_offset
        else:  # 最后两个时间槽 (10, 11)
            row = 17 + (slot_in_column - 10) + row_offset
        
        return (column, row)
        
    elif NIGHT_START_TIME <= current_time <= NIGHT_END_TIME:
        # 夜表处理
        night_start_minutes = NIGHT_START_TIME.hour * 60 + NIGHT_START_TIME.minute
        minutes_diff = current_minutes - night_start_minutes
        
        # 每5分钟一个单元格，计算偏移量
        time_slots = minutes_diff // 5
        
        # 计算列偏移（每12个时间槽换一列）
        col_index = get_column_index(NIGHT_START_COL) + col_offset + (time_slots // 12)
        column = get_column_letter(col_index)
        
        # 计算行号（考虑到每5个时间槽有2个空行）
        slot_in_column = time_slots % 12
        if slot_in_column < 2:  # 前两个时间槽 (0, 1)
            row = 14 + slot_in_column + row_offset
        elif slot_in_column < 4:  # 接下来两个时间槽 (2, 3)
            row = 17 + (slot_in_column - 2) + row_offset
        elif slot_in_column < 6:  # 接下来两个时间槽 (4, 5)
            row = 20 + (slot_in_column - 4) + row_offset
        elif slot_in_column < 8:  # 接下来两个时间槽 (6, 7)
            row = 23 + (slot_in_column - 6) + row_offset
        elif slot_in_column < 10:  # 接下来两个时间槽 (8, 9)
            row = 26 + (slot_in_column - 8) + row_offset
        else:  # 最后两个时间槽 (10, 11)
            row = 29 + (slot_in_column - 10) + row_offset
        
        return (column, row)
    
    else:
        # 时间不在昼表或夜表范围内
        return None

def get_cell_for_current_time():
    """获取当前时间对应的单元格坐标"""
    now = datetime.now()
    # 将星期几从0-6（周一到周日）转换为我们的映射（0-6）
    weekday = now.weekday()  # 0是周一，6是周日
    return get_cell_for_time(now.time(), weekday)

def get_next_five_minute_time():
    """获取下一个5分钟整点时间"""
    now = datetime.now()
    minutes = now.minute
    seconds = now.second
    
    # 计算到下一个5分钟的时间
    next_five_min = 5 - (minutes % 5)
    if next_five_min == 5 and seconds == 0:
        # 如果刚好是5分钟整点，且秒数为0，则不需要等待
        return now
    
    # 计算下一个5分钟整点
    next_time = now + timedelta(minutes=next_five_min, seconds=-seconds)
    return next_time

def get_time_for_cell(column, row):
    """
    根据单元格坐标，返回对应的时间
    
    参数:
        column: 列字母
        row: 行号
    
    返回:
        datetime.time: 对应的时间，如果没有匹配则返回None
    """
    # 将列字母转换为索引
    col_index = get_column_index(column)
    
    # 确定是昼表还是夜表
    day_col_index = get_column_index(DAY_START_COL)
    night_col_index = get_column_index(NIGHT_START_COL)
    
    # 计算基础时间和行偏移
    base_time = None
    row_in_block = 0
    
    # 计算行所在的块（每34行为一个块）
    block = (row - 1) // DAY_SHIFT
    row_in_day = row - block * DAY_SHIFT
    
    # 计算列偏移
    weekday_offset = 0
    if (col_index - day_col_index) % WEEKDAY_SHIFT != 0 and (col_index - night_col_index) % WEEKDAY_SHIFT != 0:
        weekday_offset = 1
    
    # 计算星期几
    weekday = block * 2 + weekday_offset
    
    # 确定是昼表还是夜表，并计算时间
    if day_col_index <= col_index < day_col_index + 2 * WEEKDAY_SHIFT:
        # 昼表
        col_offset = (col_index - day_col_index) // WEEKDAY_SHIFT * WEEKDAY_SHIFT
        col_in_day = col_index - day_col_index - col_offset
        
        # 计算时间槽
        time_slot = col_in_day * 12  # 每列12个时间槽
        
        # 根据行号确定时间槽内的位置
        if 2 <= row_in_day <= 3:
            time_slot += row_in_day - 2
        elif 5 <= row_in_day <= 6:
            time_slot += 2 + (row_in_day - 5)
        elif 8 <= row_in_day <= 9:
            time_slot += 4 + (row_in_day - 8)
        elif 11 <= row_in_day <= 12:
            time_slot += 6 + (row_in_day - 11)
        elif 14 <= row_in_day <= 15:
            time_slot += 8 + (row_in_day - 14)
        elif 17 <= row_in_day <= 18:
            time_slot += 10 + (row_in_day - 17)
        else:
            return None
        
        # 计算时间
        minutes = DAY_START_TIME.hour * 60 + DAY_START_TIME.minute + time_slot * 5
        hour = minutes // 60
        minute = minutes % 60
        return time(hour, minute)
        
    elif night_col_index <= col_index < night_col_index + 2 * WEEKDAY_SHIFT:
        # 夜表
        col_offset = (col_index - night_col_index) // WEEKDAY_SHIFT * WEEKDAY_SHIFT
        col_in_night = col_index - night_col_index - col_offset
        
        # 计算时间槽
        time_slot = col_in_night * 12  # 每列12个时间槽
        
        # 根据行号确定时间槽内的位置
        if 14 <= row_in_day <= 15:
            time_slot += row_in_day - 14
        elif 17 <= row_in_day <= 18:
            time_slot += 2 + (row_in_day - 17)
        elif 20 <= row_in_day <= 21:
            time_slot += 4 + (row_in_day - 20)
        elif 23 <= row_in_day <= 24:
            time_slot += 6 + (row_in_day - 23)
        elif 26 <= row_in_day <= 27:
            time_slot += 8 + (row_in_day - 26)
        elif 29 <= row_in_day <= 30:
            time_slot += 10 + (row_in_day - 29)
        else:
            return None
        
        # 计算时间
        minutes = NIGHT_START_TIME.hour * 60 + NIGHT_START_TIME.minute + time_slot * 5
        hour = minutes // 60
        minute = minutes % 60
        return time(hour, minute)
    
    return None

# 测试函数
def test_mapping():
    """测试时间到单元格的映射"""
    print("时间映射测试工具")
    print("请输入要测试的时间（格式：HH:MM）和星期几（1-7，1表示周一）")
    
    try:
        time_str = input("时间（HH:MM）: ")
        weekday_str = input("星期几（1-7）: ")
        
        # 解析时间
        hour, minute = map(int, time_str.split(':'))
        if hour < 0 or hour > 23 or minute < 0 or minute > 59 or minute % 5 != 0:
            print("错误：时间格式不正确或不是整5分钟")
            return
            
        # 解析星期几
        weekday = int(weekday_str) - 1  # 转换为0-6
        if weekday < 0 or weekday > 6:
            print("错误：星期几必须是1-7之间的数字")
            return
            
        # 创建time对象
        test_time = time(hour, minute)
        
        # 获取单元格
        cell = get_cell_for_time(test_time, weekday)
        
        # 显示结果
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        if cell:
            print(f"{weekday_names[weekday]} {hour:02d}:{minute:02d} -> {cell[0]}{cell[1]}")
        else:
            print(f"{weekday_names[weekday]} {hour:02d}:{minute:02d} -> 不在昼夜表范围内")
            
    except ValueError:
        print("错误：输入格式不正确")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    test_mapping() 