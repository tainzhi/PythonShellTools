import os
from platform import system

os_type = system()
home = ''
config_file_name = 'python_shell_tool'
download_dir = "Downloads"

if os_type == 'Darwin':
    home = os.environ['HOME']
elif os_type == 'Linux':
    home = os.environ['HOME']
elif os_type == 'Windows':
    home = os.environ['HOMEPATH']
else:
    print('不支持的系统类型！')

# 配置保存在 ~/.python_shell_tool
config_path = os.path.join(home, config_file_name)
# config_path = home + "\\" + config_file_name
# 默认生成的apk在 ~/Downloads/ 下
default_output = os.path.join(home,download_dir)
