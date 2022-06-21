import logging.config
import os
import sys
import yaml

log_relative_dir = 'log'
log_config_file = 'config.yaml'
DEBUG = True

# FIXME: compatility
download_dir = r'd:\Downloads'
MIRROR_HOST = 'artifacts-bjmirr.mot.com'
IS_WIN32 = 'win32' in str(sys.platform).lower()

# 对于支持断点续传的下载地址, 默认开启10个并行任务下载
SEGMENT_DOWNLOAD_CHUNK = 10
# 是否需要断点续传, 对于不支持断点续传的下载地址, 默认不开启断点续传
# bug2go, artifacts支持断点续传
# 开启后, 速度更快
SUPPORT_SEGMENT_DOWNLOAD = True

KB = 1024
MB = KB * 1024
GB = MB * 1024


class Util:
    @staticmethod
    def get_executable_path():
        """
        获取exe执行文件所在目录
        为啥不用 os.path.abspath(__file__)
        因为经过 pyinstaller打包后, 路径出错
        """
        if DEBUG:
            return os.path.abspath(os.path.dirname(__file__))
        else:
            return os.path.dirname(os.path.realpath(sys.argv[0]))

    @staticmethod
    def setup_log(path=os.path.join(log_relative_dir, log_config_file), default_level=logging.INFO, env_key="LOG_CFG"):
        """
        从 ./log/config.yaml加载 logging 配置
        :return:
        """
        log_config_location = os.path.join(Util.get_executable_path(), path)
        value = os.getenv(env_key, None)
        if value:
            path = value
        if os.path.exists(log_config_location):
            with open(log_config_location, "rb") as f:
                cfg = yaml.load(f, Loader=yaml.FullLoader)
                logging.config.dictConfig(cfg)
        else:
            logging.basicConfig(level=default_level)

    @staticmethod
    def get_config_dir():
        """
        配置保存目录 ./config/下
        :return:
        """
        root_dir = Util.get_executable_path()
        base_dir = 'config'
        config_dir = os.path.join(root_dir, base_dir)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        return config_dir

    @staticmethod
    def convert_file_size(file_size: int):
        if file_size > GB:
            size = float(file_size) / GB
            return f"{size:.2f}G"
        elif file_size > MB:
            size = float(file_size) / MB
            return f"{size:.2f}M"
        elif file_size > KB:
            size = float(file_size) / MB
            return f"{size:.2f}K"
        else:
            return f"{file_size}B"
