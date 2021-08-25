import os

# 配置保存在 ~/.python_shell_tool
config_path = "{}/.python_shell_tool".format(os.environ['HOME'])
# 默认生成的apk在 ~/Downloads/ 下
default_output = "{}/Downloads".format(os.environ['HOME'])
