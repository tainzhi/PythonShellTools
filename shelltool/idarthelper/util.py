import logging.config
import os
import sys
import yaml

log_relative_dir = 'log'
log_config_file = 'config.yaml'
DEBUG = True


# FIXME: compatility
download_dir = r'd:\Downloads'

IS_WIN32 = 'win32' in str(sys.platform).lower()

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
