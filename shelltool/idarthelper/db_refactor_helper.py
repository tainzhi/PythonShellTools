import sqlite3
import re

OLD_DB_NAME = 'old.db'
NEW_DB_NAME = 'new.db'

DB_TABLE_REPO_NAME = 'repos'
DB_TABLE_RELEASE_NOTES_NAME = 'release_notes'

# v1: 去除 repos, release_notes 表中的 product 字段
#   repos 添加 name 字段, name 是 url 过滤出的文件名
#   最终把旧db, 切换成色新的db
#
class OldDB:
    def __init__(self):
        self.__con = sqlite3.connect(OLD_DB_NAME)
        self.__cur = self.__con.cursor()

    def get_all_repos(self):
        self.__cur.execute('SELECT * FROM ' + DB_TABLE_REPO_NAME)
        return self.__cur.fetchall()

    def get_all_release_notes(self):
        self.__cur.execute('SELECT * FROM ' + DB_TABLE_RELEASE_NOTES_NAME)
        return self.__cur.fetchall()


class NewDB:
    def __init__(self):
        self.__con = sqlite3.connect(NEW_DB_NAME)
        self.__cur = self.__con.cursor()
        self.__create()

    def __create(self):
        self.__cur.execute('''CREATE TABLE IF NOT EXISTS {} 
                            (name TEXT PRIMARY KEY,
                           url TEXT,
                           version TEXT,
                           detailed_version TEXT)'''
                           .format(DB_TABLE_REPO_NAME))
        self.__cur.execute('''CREATE TABLE IF NOT EXISTS {} 
                            (url TEXT PRIMARY KEY,
                            version TEXT,
                            detailed_version TEXT,
                            camera_version TEXT,
                            build_date TEXT)'''
                           .format(DB_TABLE_RELEASE_NOTES_NAME))

    def bulk_insert_repo(self, repos):
        self.__cur.executemany('INSERT OR REPLACE INTO {} VALUES(?, ?, ?,?)'.format(DB_TABLE_REPO_NAME), repos)
        self.__con.commit()

    def bulk_insert_release(self, release_notes):
        self.__cur.executemany("INSERT OR REPLACE INTO {} (url, version, detailed_version) VALUES (?, ?, ?)"
                               .format(DB_TABLE_RELEASE_NOTES_NAME), release_notes)
        self.__con.commit()


def main():
    oldDb = OldDB()
    repos = oldDb.get_all_repos()
    new_repos = []
    # https://artifacts-bjmirr.mot.com/artifactory/oneli/12/S3SL32.5/oneli_cn/userdebug/intcfg_test-keys/fastboot_oneli_cn_userdebug_12_S3SL32.5_b05136-e745f_intcfg-test-keys_china_CN.tar.gz
    # 过滤出 fastboot_oneli_cn_userdebug_12_S3SL32.5_b05136-e745f_intcfg-test-keys_china_CN.tar.gz
    name_re = re.compile(r'[^\/]+[^\.]+$')
    for repo in repos:
        new_repos.append((re.search(name_re, repo[0]).group(0), repo[0], repo[2], repo[3]))

    new_release_notes = []
    release_notes = oldDb.get_all_release_notes()
    for note in release_notes:
        new_release_notes.append((note[0], note[2], note[3]))

    newDb = NewDB()
    newDb.bulk_insert_repo(new_repos)
    newDb.bulk_insert_release(new_release_notes)


if __name__ == '__main__':
    main()
