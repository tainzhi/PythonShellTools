#!/user/bin/python3

import zipfile
import os
import sys
from shutil import copyfile
from shutil import rmtree


class File:
    def unzip(file_name):
        zip_file = zipfile.ZipFile(file_name)
        files_in_zip_file = []
        for i in zip_file.namelist():
            files_in_zip_file.append(i)
        # 文件为~/Download/slice.png, 解压到~/Downloads/slice
        global files_list_in_zip_file
        files_list_in_zip_file = files_in_zip_file.copy()
        global extract_file_path
        extract_file_path = file_name[0:-4]
        zip_file.extractall(os.path.splitext(file_name)[-2])

    def get_last_modified_zip_file_in_current_directory(current_path):
        files_dict = {}
        for file_name in os.listdir(current_path):
            files_dict[file_name] = os.path.getatime(file_name)
        # 获取当前目录下文件, 并把{文件名: 文件修改日期}放入dictionary
        # 接下来对文件修改日期排序, 获取最后修改日期的文件
        # kv[0]按照key排序, kv[1]按照value排序; 因为修改日期为value
        sorted_by_atime_files_dict = sorted(files_dict.items(), key = lambda kv: kv[1], reverse=True)
        for i in sorted_by_atime_files_dict:
            if i[0][-3:] == 'zip':
                return os.path.abspath(i[0])

    def clean(file_path):
        # remove file/directory
        rmtree(file_path)
