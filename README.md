# python_speech_recognition
python调用百度标准版语音识别接口API，实现按下鼠标中键快捷语音识别，并输入到光标处
# 安装依赖
```shell 
pip install requests pyaudio pynput Pillow pystray pyinstaller    #python 3.10.11（已测试）
```
# 修改API_KEY和SECRET_KEY
修改修改config.ini配置文件中的API_KEY和SECRET_KEY为百度标准版语音识别接口
# 打包
```shell
pyinstaller --onefile --noconsole --windowed ./VoiceAssistant.py
```
注意将mic_icon.png放在与打包后的exe文件相同目录下
# 用法
按下中键开始录音，再次按下调用API开始识别或按右键取消识别