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

    def clear_username_password(self):
        self.__open()
        try:
            del self.__d[KEY_USERNAME]
            del self.__d[KEY_PASSWORD]
        except KeyError:
            pass
        self.__close()


class SqliteDB:
    def __init__(self):
        self.__con = sqlite3.connect(DB_NAME)
        self.__cur = self.__con.cursor()
        self.__create()

    def __create(self):
        # Create table
        self.__cur.execute('''CREATE TABLE IF NOT EXISTS {} 
                       (name TEXT PRIMARY KEY,
                       url TEXT,
                       version TEXT,
                       detailed_version TEXT,
                       build_date TEXT)'''
                           .format(DB_TABLE_REPO_NAME))
        self.__cur.execute('''CREATE TABLE IF NOT EXISTS {} 
                        (url TEXT PRIMARY KEY,
                        version TEXT,
                        detailed_version TEXT,
                        camera_version TEXT,
                        build_date TEXT)'''
                           .format(DB_TABLE_RELEASE_NAME))

    def insert_repo(self, name, url, version, detailed_version):
        self.__cur.execute("INSERT OR REPLACE INTO {}(name, url, version, detailed_version) VALUES (?, ?, ?, ?)".format(DB_TABLE_REPO_NAME),
                           (name, url, version, detailed_version))
        self.__con.commit()

    def update_repo_build_date(self, product_base, android_version, image_version, build_date):
        # version like berlin/11/RRG31.9
        self.__cur.execute(f"UPDATE {DB_TABLE_REPO_NAME} SET build_date = '{build_date}' WHERE version LIKE '{product_base}%{android_version}%{image_version}%'")
        self.__con.commit()

    def bulk_insert_repo(self, repos):
        self.__cur.executemany('INSERT OR REPLACE INTO {} (name, url, version, detailed_version) VALUES(?, ?, ?, ?)'.format(DB_TABLE_REPO_NAME), repos)
        self.__con.commit()

    def get_all_repo_urls(self):
        self.__con.row_factory = lambda cursor, row: row[0]
        cursor = self.__con.cursor()
        return cursor.execute('SELECT url FROM {}'.format(DB_TABLE_REPO_NAME)).fetchall()

    def insert_release(self, url, version, detailed_version):
        self.__cur.execute("INSERT OR REPLACE INTO {} (url, version, detailed_version) VALUES (?, ?, ?)"
                           .format(DB_TABLE_RELEASE_NAME), (url, version, detailed_version))
        self.__con.commit()

    def bulk_insert_release(self, release_notes):
        self.__cur.executemany("INSERT OR REPLACE INTO {} (url, version, detailed_version) VALUES (?, ?, ?)"
                               .format(DB_TABLE_RELEASE_NAME), release_notes)
        self.__con.commit()

    def get_all_versions_list(self):
        self.__con.row_factory = lambda cursor, row: row[0]
        cursor = self.__con.cursor()
        versions = cursor.execute("SELECT version FROM {}".format(DB_TABLE_RELEASE_NAME)).fetchall()
        return set(versions)

    def search_repos(self, version, dist, finger):
        """
        :param version: S3SL32.5-10
        :param dist: eqs_g, eqs_cn or eqs_retail
        :param finger: b05136-e745
        :return:
        """
        self.__con.row_factory = lambda cursor, row: (row[0], row[1])
        cursor = self.__con.cursor()
        clause = ''
        if version == '' and finger == '':
            logging.error('version and finger are empty')
        else:
            version = version if version != '' else finger
            clause = "select name, url from {} where name like '%userdebug%{}%test-keys%'".format(DB_TABLE_REPO_NAME, version)
        if dist != '':
            clause = "select name, url from ({}) where name like '%{}%'".format(clause, dist)
        repos = cursor.execute(clause).fetchall()
        return repos

    def get_latest_repos(self, product):
        # FIXME: 在添加UI后, 提供更好的交互方式
        """
        获取最新的版本
        :param product: eqs_g, eqs_cn or eqs_retail
        :param product:
        :return:
        """
        self.__con.row_factory = lambda cursor, row: (row[0], row[1], row[2])
        cursor = self.__con.cursor()
        clause = f"select name, url, build_date from {DB_TABLE_REPO_NAME} where name like '%{product}%userdebug%test-key%' order by build_date desc limit 6"
        repos = cursor.execute(clause).fetchall()
        return repos

    def close(self):
        self.__con.commit()
        self.__con.close()