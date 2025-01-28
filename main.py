import subprocess
import platform
import os

# 要运行的.py文件列表
python_scripts = (
    [bool(input("Type something to open server:"))*"pvpserver.py"]+
                        ["pvpclient.py"]*int(input("How many clients?")))

# 根据操作系统确定启动终端的命令
if platform.system() == "Windows":
    terminal_command = "start cmd /K python"
elif platform.system() == "Linux":
    terminal_command = "xterm -hold -e 'python3 {}'"
elif platform.system() == "Darwin":  # macOS
    terminal_command = "osascript -e 'tell application \"Terminal\" to do script \"python3 {}\"'"
else:
    raise Exception("不支持的操作系统")

# 启动多个终端并运行.py文件
for script in python_scripts:
    script_path = os.path.abspath(script)
    subprocess.Popen(terminal_command.format(script_path), shell=True)
