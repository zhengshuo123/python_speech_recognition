# python_speech_recognition
python调用百度短语音识别标准版API接口，实现按下鼠标中键快捷语音识别，并输入到光标处
# 安装依赖
python 3.10.11（已测试）
```shell 
pip install requests pyaudio pynput Pillow pystray pyinstaller
```
# 获取API_KEY和SECRET_KEY
[百度短语音识别标准版](https://cloud.baidu.com/product/speech/asr)
- 点击立即使用 → 免费尝鲜 → 勾选短语音识别-中文普通话 → 0元领取 → 前往应用列表
- 创建应用 → 勾选短语音识别 → 填写信息 → 立即创建
修改修改config.ini配置文件中的API_KEY和SECRET_KEY
# 打包
```shell
pyinstaller --onefile --noconsole --windowed ./VoiceAssistant.py
```
注意将mic_icon.png和config.ini放在与打包后的exe文件相同目录下
# 用法
按下中键开始录音，再次按下中键开始识别并将结果输入到光标处，或按右键取消识别