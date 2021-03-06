import logging
import os

import requests
import json
import subprocess
from artifacts import ArtifactsUpdater
from util import *
from downloader import AsyncDownloader


def get_path_stem(file_path):
    if file_path.find('.tar.') != -1:
        tar_path = os.path.splitext(file_path)[0]
        return os.path.splitext(tar_path)[0]
    else:
        return os.path.splitext(file_path)[0]


def open_dir(dir_path):
    if IS_WIN32:
        # TODO: close window after run cmd success
        # startupinfo = subprocess.STARTUPINFO()
        # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # startupinfo.wShowWindow = subprocess.SW_HIDE
        # ret = subprocess.Popen(['explorer', dir_path], startupinfo=startupinfo)
        cmd = f'explorer {dir_path}'.split(' ')
        ret = subprocess.call(cmd)
        if ret == 1:
            pass
        else:
            logging.error("open dir failed")
    else:
        # todo compatible with linux/mac
        cmd = f'gnome-open {dir_path}'.split(' ')
        subprocess.run(cmd, check=True)
        pass


def untar(fname: str):
    """
    解压tar.gz文件
    :param fname: 压缩文件名
    :param dirs: 解压后的存放路径
    :return: bool
    """
    path_stem = get_path_stem(fname)
    # 解压到以去除文件后缀之后的目录作为解压目录
    # 取得无后缀路径
    if os.path.exists(path_stem):
        logging.info("already untared to %s", path_stem)
    else:
        if not os.path.exists(path_stem):
            os.mkdir(path_stem)

        try:
            # todo compatible with linux/mac
            cmd = f'tar -xvf {fname} -C {path_stem}'.split(' ')
            ret = subprocess.run(cmd, check=True)
            if ret.returncode == 0:
                logging.info("untar success to %s", path_stem)
            else:
                logging.error("untar failed")
        except Exception as e:
            logging.exception(e)
            logging.info("remove %s", fname)
            if os.path.exists(fname):
                os.remove(fname)
            logging.info("remove %s", path_stem)
            if os.path.exists(path_stem):
                os.remove(path_stem)
            return False
    open_dir(path_stem)


def download_from_url(url, headers: dict, dist: str="idart.zip", is_bug2go=False):
    if os.path.exists(dist):
        logging.info("%s already downloaded to %s", "bug2go" if is_bug2go else "attachment", dist)
        untar(dist)
    else:
        downloader = AsyncDownloader(url, headers, dist)
        ret = downloader.request()
        if ret:
            logging.info("download success, begin untar")
            untar(dist)
        else:
            os.remove(dist)
            logging.error("download failed")


def main(argv):
    """
    从chrome registry穿过来的参数只有一个, url编码后的json字符串
    """
    # idart://idart//%7B%22url/
    # idart://artifacts//%7B%22url/
    argv_list = argv[0].split('//')
    type_download = argv_list[-2]
    encoded_url_json_string = argv_list[-1]
    # json string不能通过url传过来, 必须要先url编码后才能传过来
    # 传过来后, 再对编码后的json string进行url解码
    # 而且还需要取出末尾的反斜杠 /
    url_json_string = requests.utils.unquote(encoded_url_json_string).strip('/')
    # download idart attachment
    if type_download == 'idart':
        # 解析json字符串
        url_json = json.loads(url_json_string)
        url = url_json['url']
        id = url_json['id']
        cookie = url_json['cookie']
        headers = {
            'Cookie': cookie,
            'host': 'idart.mot.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; xf64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
        }
        logging.info("to download attachment from %s", url)

        # 下载文件
        download_from_url(url, headers=headers, dist=os.path.join(download_dir, id + '.zip'))
    # download logs from bug2go site
    elif type_download == 'bug2go':
        # 解析json字符串
        url_json = json.loads(url_json_string)
        url = url_json['url']
        file_name = url_json['file_name']
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'referer': 'https://mmibug2go.appspot.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; xf64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
        }
        # 下载文件
        # 先去除目录路径中非法字符 : \ / * ? " < > |
        # reference: https://www.mtu.edu/umc/services/websites/writing/characters-avoid/
        logging.info("to download bu2go from %s", url_json['host'])
        download_from_url(url, headers=headers, dist=os.path.join(download_dir, file_name.replace(':', '_')),
                          is_bug2go=True)
    elif type_download == 'artifacts':
        url_json = json.loads(url_json_string)
        artifacts = ArtifactsUpdater(url_json)

    # fixme: remove this
    os.system("pause")


if __name__ == '__main__':
    Util.setup_log()
    logging.debug(sys.argv[1])
    main(sys.argv[1:])