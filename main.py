#!/usr/bin/python3

# 这是一个android开发工具
# 目标功能: 解压下载的切图文件, 复制到指定的项目的res文件中
# 应用场景: 下载切图文件(是多种分辨率图片的压缩包), 解压后, 复制到项目res对应的
#           的分辨率目录中;
# 特色功能:
# 1. 重命名
# 2. 记录最近拷贝目录
# 3. 操作当前目录的最新文件
# 4. 撤回操作: 删除刚才拷贝操作; 取消刚才的重命名

import zipfile
import os
import sys
from shutil import copyfile
from shutil import rmtree
import click
import pickle


def copy_from_source_path_to_target_path(source_path_dir, target_path_dir):
    file_exists_and_to_replace_flag = False
    new_dirs = []
    new_files = []
    for i in files_list_in_zip_file:
        if i[-3:] == 'png':
            # 得到的文件名为mipmap-hdpi/slice.png, 和目标项目合并成
            # target_path + "/src/main/res"
            # 最终获得如此文件路径: /Users/00390839/AndroidPorjects/XDroidMvp/app/src/main/res/mipmap-mdpi/members_hover.png
            source_file = os.path.join(source_path_dir, i)
            global new_name
            if new_name == '' or new_name is None:
                target_file = os.path.join(target_path_dir, "src/main/res", i)
            else:
                if not new_name.endswith('.png'):
                    new_name = new_name + '.png'
                target_file = os.path.join(target_path_dir, "src/main/res",
                                           os.path.dirname(i),
                                           new_name)
            if not os.path.exists(os.path.dirname(target_file)):
                os.makedirs(os.path.dirname(target_file))
                new_dirs.append(os.path.dirname(target_file))
            # 判断目标目录是否存在同名文件, 若存在弹出选择y/n
            if not file_exists_and_to_replace_flag and os.path.exists(target_file):
                to_replace = click.prompt("Target module has "
                                          + target_file
                                          + "\n To replace it(y/n)?",
                                          type=click.Choice(['y', 'n']))
                if to_replace == 'n':
                    click.echo("Not replace " + target_file)
                    return
                else:
                    file_exists_and_to_replace_flag = True
            click.echo("copy " + source_path_dir + '/' + i + " >>>>>>>> " + target_file)
            copyfile(source_file, target_file)
            new_files.append(target_file)
    with open(cpad_history_path, 'rb+') as openfile:
        data = pickle.load(openfile)
        data['new_files'] = new_files
        data['new_dirs'] = new_dirs
        pickle.dump(data, openfile, pickle.HIGHEST_PROTOCOL)

def undoPreviousOperations():
    with open(cpad_history_path, 'rb') as openfile:
        data = pickle.load(openfile)
        print(data)
        for i in data['new_files']:
            os.remove(i)
        for j in data['new_dirs']:
            os.rmdir(j)
    click.echo("undo previous operations! delete the created files and dirs")


@click.command()
@click.option('-s', '--source', 'source',
              required=False,
              help="eg ./slice.zip, 默认是当前目录下的最新的zip文件")
@click.option('-t', '--target', 'target',
              required=False,
              help="eg ~/AndroidProjects/app, 默认是上一次命令的目标module路径")
@click.option('-n', '--newname', 'newname',
              required=False,
              help="eg new_png_name, with or without suffix .png")
@click.option('-u', '--undo', is_flag=False,
              help="undo the previous operation")
def cp(source, target, newname, undo):
    global new_name
    new_name = newname
    if undo is True:
        undoPreviousOperations()
        return
    if source is None:
        source_dir = os.getcwd()
        last_zip_file = get_last_modified_zip_file_in_current_directory(source_dir)
        unzip(last_zip_file)
    else:
        unzip(os.path.abspath(source))

    # 若不输入target module path
    # 则从当前目录下的.cpad_history读取最近一次target module path记录
    # 若不存在.cpad_history, 则提醒输入target module_path
    if target is None:
        # 默认从当前目录下的.cpad_history读取历史中最近一次的target moudule path
        if os.path.exists(cpad_history_path):
            with open(cpad_history_path, 'rb+') as openfile:
                data = pickle.load(openfile)
                target = data['last_target']
        else:
            target = click.prompt("Please input target module path:")
            # 默认从当前目录下的.cpad_history读取历史中最近一次的target moudule path
            with open(cpad_history_path, 'wb') as openfile:
                data = {}
                data['last_target'] = target
                pickle.dump(data, openfile, pickle.HIGHEST_PROTOCOL)

    copy_from_source_path_to_target_path(extract_file_path, target)

    clean()



def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print("Hi, {0}".format(name))  # Press Ctrl+F8 to toggle the breakpoint.


if __name__ == '__main__':
    print_hi('PyCharm')