import os
import sys
import requests
import json
from urllib.request import urlopen
import subprocess
from artifacts import ArtifactsUpdater

# FIXME: compatility
download_dir = r'd:\Downloads'
DEBUG = True
KB = 1024
MB = KB * 1024
GB = MB * 1024

IS_WIN32 = 'win32' in str(sys.platform).lower()

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
        ret = subprocess.call(['explorer', dir_path])
        if ret == 1:
            print("open dir success")
        else:
            print("open dir failed")
    else:
        # todo compatible with linux/mac
        subprocess.run(['gnome-open', dir_path], check=True)
        pass


def untar(fname):
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
        print("已经解压好了," + path_stem)
    else:
        if not os.path.exists(path_stem):
            os.mkdir(path_stem)

        try:
            # todo compatible with linux/mac
            ret = subprocess.run(["tar", "-xvf", fname, "-C", path_stem], check=True)
            if ret.returncode == 0:
                print("untar success")
            else:
                print("untar failed")
        except Exception as e:
            print(e)
            return False
    open_dir(path_stem)


def download_from_url(url, headers=None, dist="idart.zip", payload=None):
    if os.path.exists(dist):
        print("已经下载好了:" +dist)
    else:
        # todo  添加progressbar
        # https://blog.csdn.net/shykevin/article/details/105503594
        # https://rich.readthedocs.io/en/stable/progress.html
        req = requests.get(url, stream=True, headers=headers)
        print("headers:", req.headers)
        file_size = req.headers.get('Content-Length')
        print("file size: " , convert_file_size(file_size))
        try:
            with(open(dist, 'wb')) as f:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
        except Exception as e:
            print(e)
            return False
    print("download success, begin untar")
    untar(dist)

def convert_file_size(file_size):
    size = int(file_size)
    if size > GB:
        size = (float)(file_size) / GB
        return f"{size:.2f}G"
    elif size > MB:
        size = float(file_size) / MB
        return f"{size:.2f}M"
    elif size > KB:
        size = float(file_size) / MB
        return f"{size:.2f}K"
    else:
        return f"{size}B"



def main(argv):
    """
    从chrome registry穿过来的参数只有一个, url编码后的json字符串
    """
    # idart://idart//%7B%22url/
    # idart://bug2go//%7B%22url/
    argv_list = argv[0].split('//')
    type_download = argv_list[-2]
    encoded_url_json_string = argv_list[-1]
    # json string不能通过url传过来, 必须要先url编码后才能传过来
    # 传过来后, 再对编码后的json string进行url解码
    # 而且还需要取出末尾的反斜杠 /
    url_json_string = requests.utils.unquote(encoded_url_json_string).strip('/')
    print(url_json_string)
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

        # 下载文件
        download_from_url(url, headers=headers, dist=os.path.join(download_dir, id + '.zip'))
    elif type_download == 'bug2go':
        # 解析json字符串
        url_json = json.loads(url_json_string)
        url = url_json['url']
        file_name = url_json['file_name']
        # 下载文件
        # 先去除目录路径中非法字符 : \ / * ? " < > |
        # reference: https://www.mtu.edu/umc/services/websites/writing/characters-avoid/
        download_from_url(url, dist=os.path.join(download_dir, file_name.replace(':', '_')))
    elif type_download == 'artifacts':
        url_json = json.loads(url_json_string)
        url = url_json['url']
        cookie = url_json['cookie']
        artifacts = ArtifactsUpdater(url, cookie)
        
    os.system("pause")

if __name__ == '__main__':
    print(sys.argv[1])
    main(sys.argv[1:])
