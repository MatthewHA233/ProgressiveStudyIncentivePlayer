import os
import sys
import time
import csv
from datetime import datetime, timedelta
import ADBHelper
import adb_RaphaelScriptHelper as rsh

class TimeBlockClicker:
    def __init__(self):
        # 获取设备ID
        self.devices = ADBHelper.getDevicesList()
        if not self.devices:
            print("未找到连接的设备，请确保手机已连接并开启USB调试")
            sys.exit(1)
        
        # 使用第一个设备
        self.device_id = self.devices[0]
        print(f"使用设备: {self.device_id}")
        
        # 设置脚本助手的设备ID
        rsh.deviceID = self.device_id
        
        # 初始化操作：回到主页并点击指定坐标
        print("执行初始化操作...")
        self.initialize_app()
        
        # 时间块区域坐标
        self.start_point = (155, 385)  # 左上角坐标
        self.end_point = (700, 1992)   # 右下角坐标
        
        # 计算每个时间块的大小
        self.grid_width = (self.end_point[0] - self.start_point[0]) / 12  # 12列
        self.grid_height = (self.end_point[1] - self.start_point[1]) / 16  # 16行
        
        print(f"时间块区域: {self.start_point} 到 {self.end_point}")
        print(f"每个时间块大小: 宽={self.grid_width:.2f}, 高={self.grid_height:.2f}")
    
    def initialize_app(self):
        """初始化操作：回到主页并点击指定坐标"""
        # 回到主页
        print("回到手机主页...")
        # 使用正确的ADB命令执行方式
        os.system(f"adb -s {self.device_id} shell input keyevent KEYCODE_HOME")
        time.sleep(0.5)
        
        # 点击第一个坐标点
        first_point = (412, 2215)
        print(f"点击第一个坐标点: {first_point}")
        rsh.touch(first_point)
        time.sleep(1)  # 等待应用打开
        
        # 点击第二个坐标点
        second_point = (1052, 1245)
        print(f"点击第二个坐标点: {second_point}")
        rsh.touch(second_point)
        time.sleep(1)  # 等待界面加载
        
        print("初始化完成")
    
    def get_time_block_position(self, hour, minute):
        """获取指定时间的时间块位置"""
        # 验证时间输入
        if hour < 6 or hour > 21:
            # print(f"警告: 小时 {hour} 超出有效范围 (6-21)")
            return None # 返回None表示无效
        
        if minute < 0 or minute > 55 or minute % 5 != 0:
            # print(f"警告: 分钟 {minute} 无效 (应为0-55的5的倍数)")
            return None # 返回None表示无效
        
        # 计算行列
        row = hour - 6  # 6点对应第0行
        col = minute // 5  # 每5分钟一列
        
        # 计算点击坐标
        x = self.start_point[0] + (col + 0.5) * self.grid_width
        y = self.start_point[1] + (row + 0.5) * self.grid_height
        
        return (int(x), int(y))
    
    def click_coordinate(self, coords):
        """直接点击给定的坐标点"""
        if coords and len(coords) == 2:
            print(f"点击坐标点: {coords}")
            rsh.touch(coords)
            return True
        else:
            print(f"错误: 无效的坐标点 {coords}")
            return False
    
    def slide_time_blocks(self, start_hour, start_minute, end_hour, end_minute):
        """从开始时间滑动到结束时间（内部处理-5分钟逻辑）"""
        # 调整开始时间，减去5分钟，用于计算滑动起始点
        slide_start_hour, slide_start_minute = start_hour, start_minute
        if slide_start_minute < 5:
            slide_start_hour -= 1
            slide_start_minute = 55
        else:
            slide_start_minute -= 5
        
        # 调整结束时间，减去5分钟，用于计算滑动结束点
        slide_end_hour, slide_end_minute = end_hour, end_minute
        if slide_end_minute < 5:
            slide_end_hour -= 1
            slide_end_minute = 55
        else:
            slide_end_minute -= 5
        
        # 获取滑动开始和结束位置
        start_pos = self.get_time_block_position(slide_start_hour, slide_start_minute)
        end_pos = self.get_time_block_position(slide_end_hour, slide_end_minute)
        
        # 检查获取的位置是否有效
        if start_pos is None:
            print(f"错误: 无法获取滑动开始位置 ({slide_start_hour:02d}:{slide_start_minute:02d})")
            return False
        if end_pos is None:
             # 如果结束位置无效，尝试使用开始位置作为结束位置（相当于点击）
            print(f"警告: 无法获取滑动结束位置 ({slide_end_hour:02d}:{slide_end_minute:02d})，将使用开始位置代替。")
            end_pos = start_pos
        
        print(f"从 {start_hour:02d}:{start_minute:02d} 滑动到 {end_hour:02d}:{end_minute:02d}")
        print(f"计算滑动坐标: 从 {start_pos} 到 {end_pos}")
        
        # 执行滑动
        rsh.slide((start_pos, end_pos))
        # 添加短暂延时确保滑动完成
        time.sleep(0.5)
        return True
    
    def parse_time_input(self, time_str):
        """解析时间输入，格式为HH:MM"""
        try:
            return datetime.strptime(time_str, '%H:%M')
        except ValueError:
            print(f"错误: 时间格式不正确 '{time_str}'，应为HH:MM")
            return None
    
    def parse_coords_input(self, coords_str):
        """解析坐标输入，格式为x,y"""
        try:
            x, y = map(int, coords_str.split(','))
            return (x, y)
        except:
            print(f"错误: 坐标格式不正确 '{coords_str}'，应为x,y")
            return None
    
    def process_csv_log(self):
        """读取当天的CSV日志并处理时间块"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        csv_filename = f"五分钟记录_{today_str}.csv"
        csv_filepath = os.path.join("statistics", "five_minute_logs", csv_filename)
        
        if not os.path.exists(csv_filepath):
            print(f"错误: 找不到今天的日志文件 {csv_filepath}")
            return
        
        print(f"正在处理日志文件: {csv_filepath}")
        log_entries = []
        try:
            with open(csv_filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader) # 跳过表头
                for row in reader:
                    if len(row) >= 4:
                        time_obj = self.parse_time_input(row[0])
                        # 使用第2列作为事情类型，而不是状态标签
                        activity_type = row[2] if len(row) > 2 else ""
                        coords = self.parse_coords_input(row[3])
                        if time_obj and coords:
                            log_entries.append({
                                'time': time_obj, 
                                'activity_type': activity_type,
                                'coords': coords
                            })
                    else:
                         print(f"警告: 跳过格式不正确的行 {row}")
        
        except Exception as e:
            print(f"读取CSV文件时出错: {e}")
            return
        
        if not log_entries:
            print("日志文件为空或无法解析有效条目")
            return
        
        # 按时间排序
        log_entries.sort(key=lambda x: x['time'])
        
        # 首先按事情类型分组
        activity_groups = {}
        for entry in log_entries:
            activity_type = entry['activity_type']
            if activity_type not in activity_groups:
                activity_groups[activity_type] = []
            activity_groups[activity_type].append(entry)
        
        # 在每个事情类型内部，按时间连续性分块
        all_time_blocks = []
        five_minutes = timedelta(minutes=5)
        
        for activity_type, entries in activity_groups.items():
            print(f"\n处理事情类型: {activity_type}")
            
            # 在同一事情类型内按时间连续性分块
            activity_blocks = []
            current_block = None
            
            for entry in entries:
                current_time = entry['time']
                current_coords = entry['coords']
                
                if current_block is None:
                    # 开始新块
                    current_block = {
                        'activity_type': activity_type,
                        'start_time': current_time,
                        'end_time': current_time,
                        'coords': current_coords
                    }
                else:
                    # 检查时间是否连续
                    time_diff = current_time - current_block['end_time']
                    if time_diff == five_minutes:
                        # 扩展当前块
                        current_block['end_time'] = current_time
                        current_block['coords'] = current_coords # 更新为最后一条记录的坐标
                    else:
                        # 时间不连续，结束当前块，开始新块
                        activity_blocks.append(current_block)
                        current_block = {
                            'activity_type': activity_type,
                            'start_time': current_time,
                            'end_time': current_time,
                            'coords': current_coords
                        }
            
            # 添加最后一个块
            if current_block:
                activity_blocks.append(current_block)
            
            all_time_blocks.extend(activity_blocks)
            print(f"事情类型 '{activity_type}' 分为 {len(activity_blocks)} 个时间块")
        
        # 按时间排序所有块
        all_time_blocks.sort(key=lambda x: x['start_time'])
        
        print(f"\n总共识别到 {len(all_time_blocks)} 个时间块，开始处理:")
        for i, block in enumerate(all_time_blocks):
            start_h = block['start_time'].hour
            start_m = block['start_time'].minute
            end_h = block['end_time'].hour
            end_m = block['end_time'].minute
            coords_to_click = block['coords']
            activity_type = block['activity_type']
            
            print(f"\n--- 处理块 {i+1}/{len(all_time_blocks)} ---")
            print(f"事情类型: {activity_type}")
            print(f"时间范围: {start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}")
            print(f"目标坐标点: {coords_to_click}")
            
            # 执行滑动
            if self.slide_time_blocks(start_h, start_m, end_h, end_m):
                 # 滑动成功后，点击坐标点
                self.click_coordinate(coords_to_click)
            else:
                print("滑动失败，跳过此块的点击操作")
            
            # 添加延时，防止操作过快
            print("等待0.2秒...")
            time.sleep(0.2)
        
        print("\n所有时间块处理完毕。")

def main():
    clicker = TimeBlockClicker()
    clicker.process_csv_log()

if __name__ == "__main__":
    main() 