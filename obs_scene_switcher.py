import pyautogui
import sys
import time

def switch_scene(shortcut):
    """
    执行OBS场景切换快捷键，重复3次，每次间隔0.6秒
    
    参数:
        shortcut: 要执行的快捷键组合，例如 "ctrl+alt+shift+q"
    """
    keys = shortcut.split('+')
    for i in range(3):
        pyautogui.hotkey(*keys)
        print(f"已执行快捷键 (第 {i+1} 次): {shortcut}")
        if i < 2:
            time.sleep(0.6)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        shortcut = sys.argv[1]
        switch_scene(shortcut)
    else:
        print("请提供要执行的快捷键，例如: ctrl+alt+shift+q") 