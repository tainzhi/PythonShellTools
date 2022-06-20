import logging
import sqlite3
import os
import shelve
from util import Util

# fixme: move this to util.py
DB_NAME = 'artifacts.db'
# TODO: use global user directory
base_path = os.path.abspath(os.path.dirname(__file__))
DB_NAME = os.path.join(base_path, DB_NAME)
DB_TABLE_REPO_NAME = 'repos'
DB_TABLE_RELEASE_NAME = 'release_notes'

KEY_USERNAME = "username"
KEY_PASSWORD = "password"


class Settings:
    def __init__(self):
        root_dir = Util.get_config_dir()
        # 配置保存在./config/config.*中
        config_name = 'config'
        self.__path = os.path.join(root_dir, config_name)
        self.__is_d_open = False

    def __open(self):
        if not self.__is_d_open:
            self.__d = shelve.open(self.__path)
            self.__is_d_open = True

    def __close(self):
        if self.__is_d_open:
            self.__d.close()
            self.__is_d_open = False

    def set_username_password(self, username: str, password: str):
        self.__open()
        self.__d[KEY_USERNAME] = username
        self.__d[KEY_PASSWORD] = password
        self.__close()

    def get_username_password(self):
        self.__open()
        try:
            username = self.__d[KEY_USERNAME]
            password = self.__d[KEY_PASSWORD]
        except KeyError:
            username = None
            password = None
        return username, password


class SqliteDB:
    def __init__(self):
        self.__con = sqlite3.connect(DB_NAME)
        self.__cur = self.__con.cursor()
        self.__create()

    def __create(self):
        # Create table
        self.__cur.execute('''CREATE TABLE IF NOT EXISTS {} 
                        (url TEXT PRIMARY KEY,
                       product TEXT,
                       version TEXT,
                       detailed_version TEXT)'''
                           .format(DB_TABLE_REPO_NAME))
        self.__cur.execute('''CREATE TABLE IF NOT EXISTS {} 
                        (url TEXT PRIMARY KEY,
                        product TEXT,
                        version TEXT,
                        detailed_version TEXT,
                        camera_version TEXT,
                        build_date TEXT)'''
                           .format(DB_TABLE_RELEASE_NAME))

    def insert_repo(self, url, product, version, detailed_version):
        self.__cur.execute("INSERT OR REPLACE INTO {} VALUES (?, ?, ?, ?)".format(DB_TABLE_REPO_NAME),
                           (url, product, version, detailed_version))
        self.__con.commit()

    def bulk_insert_repo(self, repos):
        self.__cur.executemany('INSERT OR REPLACE INTO {} VALUES(?, ?, ?,?)'.format(DB_TABLE_REPO_NAME), repos)
        self.__con.commit()

    def get_all_repo_urls(self):
        self.__con.row_factory = lambda cursor, row: row[0]
        cursor = self.__con.cursor()
        return cursor.execute('SELECT url FROM {}'.format(DB_TABLE_REPO_NAME)).fetchall()

    def insert_release(self, url, product, version, detailed_version):
        self.__cur.execute("INSERT OR REPLACE INTO {} (url, product, version, detailed_version) VALUES (?, ?, ?, ?)"
                           .format(DB_TABLE_RELEASE_NAME), (url, product, version, detailed_version))
        self.__con.commit()

    def bulk_insert_release(self, release_notes):
        self.__cur.executemany("INSERT OR REPLACE INTO {} (url, product, version, detailed_version) VALUES (?, ?, ?, ?)"
                               .format(DB_TABLE_RELEASE_NAME), release_notes)
        self.__con.commit()

    def get_all_versions_dict(self):
        # 为啥不从 repos table 获取了
        # 因为某些版本因为已经很久了, 所以 fastboot_ 刷机包已经删除, 只存在 release_notes.xml
        # release_notes.xml 更全面一些
        # self.__con.row_factory = lambda cursor, row: dict(zip(row[0], row[1]))
        self.__con.row_factory = sqlite3.Row
        cursor = self.__con.cursor()
        versions = cursor.execute("SELECT version, product FROM {}".format(DB_TABLE_RELEASE_NAME)).fetchall()
        return dict((row[0], row[1]) for row in versions)

    def get_all_versions_list(self):
        self.__con.row_factory = lambda cursor, row: row[0]
        cursor = self.__con.cursor()
        versions = cursor.execute("SELECT version FROM {}".format(DB_TABLE_RELEASE_NAME)).fetchall()
        return set(versions)

    def search_repos(self, version, dist, finger):
        self.__con.row_factory = lambda cursor, row: row[0]
        cursor = self.__con.cursor()
        clause = ''
        if version == '' and finger == '':
            # FIXME: add to logger
            print('version and finger are empty')
        else:
            version = version if version != '' else finger
            clause = "select url from {} where url like '%{}%userdebug%test-keys%'".format(DB_TABLE_REPO_NAME, version)
        if dist != '':
            clause = "select url from ({}) where url like '%{}%'".format(clause, dist)
        repos = cursor.execute(clause).fetchall()
        return repos

    def close(self):
        self.__con.commit()
        self.__con.close()