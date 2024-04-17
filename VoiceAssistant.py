import tkinter as tk
import requests
import base64
import threading
import sys
from pynput import mouse
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController
import pyaudio
from pystray import MenuItem as item, Icon as tray_icon
from PIL import Image
import winreg as reg
import os

# 全局变量定义
API_KEY = 'cPSZi0gXaOSjt8Bkpz8ViRHG'
SECRET_KEY = 'c9MUo9eqrhRvZdrqBN8Os6VRfeIIyMOp'
ACCESS_TOKEN = None  # 百度API的访问令牌
KEYBOARD_CONTROLLER = KeyboardController()  # 键盘输入模拟器
RECORDING = False  # 录音状态标记
STREAM = None  # PyAudio流对象
STREAM_ACTIVE = False  # 流激活状态标记
FRAMES = []  # 音频帧存储列表
P = pyaudio.PyAudio()  # 创建PyAudio实例
ROOT = tk.Tk()  # 创建Tkinter主窗口实例
ROOT.overrideredirect(True)  # 设置无边框窗口
ROOT.attributes('-topmost', True)  # 窗口置顶
ROOT.withdraw()  # 初始隐藏窗口
STREAM_ACTIVE_LOCK = threading.Lock()  # 添加一个锁

def get_application_path():
    """获取当前执行的程序的路径。"""
    if getattr(sys, 'frozen', False):
        # 如果程序是被打包的，返回打包后的执行文件路径
        return os.path.dirname(sys.executable)
    else:
        # 如果程序是直接从脚本运行的，返回脚本文件的路径
        return os.path.dirname(os.path.abspath(__file__))

def add_to_startup():
    """将应用程序添加到Windows启动项中"""
    app_name = "VoiceAssistant"  # 应用程序名称
    app_path = os.path.join(get_application_path(), 'VoiceAssistant.exe')  # 假设可执行文件名是VoiceAssistant.exe
    # 打开注册表的“Run”键，设置启动项
    try:
        key = reg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        registry_key = reg.OpenKey(key, key_path, 0, reg.KEY_WRITE)
        reg.SetValueEx(registry_key, app_name, 0, reg.REG_SZ, f'"{app_path}"')
        reg.CloseKey(registry_key)
        print("VoiceAssistant 已添加到开机启动。")
    except WindowsError as e:
        print(f"添加到开机启动失败: {e}")

def remove_from_startup():
    """从Windows启动项中移除应用程序"""
    app_name = "VoiceAssistant"  # 应用程序名称
    try:
        key = reg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        registry_key = reg.OpenKey(key, key_path, 0, reg.KEY_WRITE)
        reg.DeleteValue(registry_key, app_name)
        reg.CloseKey(registry_key)
        print("VoiceAssistant 已从开机启动移除。")
    except WindowsError as e:
        print(f"移除开机启动失败: {e}")

def create_image():
    """加载图像文件作为系统托盘图标"""
    # 使用get_application_path()函数获取当前执行程序的路径
    app_path = get_application_path()
    # 构建图像文件的绝对路径
    image_path = os.path.join(app_path, 'mic_icon.png')
    # 使用绝对路径加载图像
    image = Image.open(image_path)
    return image

def setup(icon):
    """设置图标可见"""
    icon.visible = True

def show_icon():
    """在系统托盘创建图标"""
    image = create_image()
    menu = (
        item('启动开机自启', add_to_startup),
        item('关闭开机自启', remove_from_startup),
        item('退出 VoiceAssistant', exit_application),
    )
    icon = tray_icon('VoiceAssistant', image, 'VoiceAssistant', menu)
    icon.run(setup)

def exit_application(icon, item):
    """退出应用程序，关闭所有资源"""
    print("退出程序...")
    icon.stop()  # 停止图标
    ROOT.after(0, close_gui)  # 主线程中执行GUI关闭

def close_gui():
    """关闭GUI和音频资源"""
    global STREAM_ACTIVE
    if STREAM_ACTIVE:
        STREAM.stop_stream()
        STREAM.close()
        STREAM_ACTIVE = False  # 确保状态更新
    P.terminate()  # 关闭PyAudio实例
    ROOT.quit()  # 退出Tkinter主循环
    ROOT.destroy()  # 销毁所有Tkinter资源

def get_access_token():
    """从百度API获取访问令牌"""
    url = 'https://aip.baidubce.com/oauth/2.0/token'
    params = {
        'grant_type': 'client_credentials',
        'client_id': API_KEY,
        'client_secret': SECRET_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # 检查响应状态码是否表示错误
        return response.json().get('access_token')
    except requests.exceptions.HTTPError as e:
        print(f"HTTP请求错误:{e}")
    except requests.exceptions.ConnectionError as e:
        print("网络连接错误，请检查网络连接。")
    except requests.exceptions.Timeout as e:
        print("请求超时，请检查网络连接或稍后再试。")
    except requests.exceptions.RequestException as e:
        print(f"请求异常：{e}")
    except Exception as e:
        print(f"未知错误：{e}")
    return None


def recognize_speech_from_stream(stream_data):
    """使用百度语音识别API识别音频流"""
    url = 'http://vop.baidu.com/server_api'
    headers = {
        'Content-Type': 'audio/pcm; rate=16000',
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    data = {
        'format': 'pcm',
        'rate': 16000,
        'channel': 1,
        'cuid': 'baidu_workshop',
        'token': ACCESS_TOKEN,
        'len': len(stream_data),
        'speech': base64.b64encode(stream_data).decode('utf-8')
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        if result['err_no'] == 0:
            return result['result'][0]  # 返回识别的第一条结果
        print("识别错误: ", result['err_msg'])
    print("HTTP请求错误: ", response.status_code)
    return None

def on_click(x, y, button, pressed):
    """处理鼠标点击事件，控制录音和识别"""
    global RECORDING
    if button == mouse.Button.middle and pressed:
        if not RECORDING:
            start_recording()
        else:
            stop_recording()

def start_recording():
    """开始录音"""
    global RECORDING, STREAM, FRAMES
    print("开始录音...")
    RECORDING = True
    show_mic_icon()
    FRAMES = []
    thread = threading.Thread(target=record_stream)
    thread.daemon = True
    thread.start()

def stop_recording():
    """停止录音并开始识别"""
    global RECORDING, STREAM, FRAMES
    print("停止录音，开始识别...")
    RECORDING = False
    audio_data = b''.join(FRAMES)
    result_text = recognize_speech_from_stream(audio_data)
    if result_text:
        print("识别结果：", result_text)
        KEYBOARD_CONTROLLER.type(result_text)
    else:
        print("无法识别或未获得结果")
    hide_mic_icon()

def record_stream():
    """从麦克风记录音频"""
    global STREAM, FRAMES, STREAM_ACTIVE
    STREAM = P.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
    with STREAM_ACTIVE_LOCK:
        STREAM_ACTIVE = True  # 使用锁来保护状态变更
    while RECORDING:
        data = STREAM.read(1024, exception_on_overflow=False)
        FRAMES.append(data)
    STREAM.stop_stream()
    STREAM.close()
    with STREAM_ACTIVE_LOCK:
        STREAM_ACTIVE = False  # 使用锁来保护状态变更

def show_mic_icon():
    """在鼠标当前位置显示麦克风图标"""
    mouse = MouseController()
    x, y = mouse.position
    ROOT.geometry(f'+{int(x + 20)}+{int(y + 20)}')
    ROOT.deiconify()

def hide_mic_icon():
    """隐藏麦克风图标"""
    ROOT.withdraw()

def main():
    """程序主入口，启动应用程序并显示托盘图标"""
    global ACCESS_TOKEN
    ACCESS_TOKEN = get_access_token()
    if not ACCESS_TOKEN:
        sys.exit("获取访问令牌失败，程序退出。")
    listener = mouse.Listener(on_click=on_click)
    listener.start()
    icon_thread = threading.Thread(target=show_icon)
    icon_thread.daemon = True
    icon_thread.start()  # 运行托盘图标的线程
    canvas = tk.Canvas(ROOT, width=20, height=20, bg='red', highlightthickness=0)
    canvas.pack()
    ROOT.mainloop()

if __name__ == "__main__":
    main()