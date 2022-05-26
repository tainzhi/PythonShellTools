import requests
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from db import SqliteDB

# todo add global DEBUG sign
DEBUG = True
EXCLUDE_REPOS = {'amps', 'amps-cache', 'apps', 'apps-cache', 'archive', 'astro', 'astro-archive', 'banks', 'banks-cache',
                 'bathena', 'bathena-cache', 'bingo', 'bingo-cache', 'borneo', 'borneo-cache', 'burton', 'burton-cache',
                 'cebu', 'cebu-cache', 'channel', 'channel-cache', 'chef', 'chef-cache', 'continuous_builds', 'continuous_builds-cache',
                 'cptools', 'cptools-cache', 'cw_virtual_US', 'cw_virtual_US-cache', 'davros_us', 'davros_us-cache', 'deen', 'deen_32', 'deen_32-cache', 'deen-cache',
                 'def', 'def-cache', 'doha', 'doha-cache', 'drogon', 'drogon_US', 'drogon_US-cache', 'evert', 'evert-cache', 'felix', 'felix_us', 'felix_US-cache',
                 'fijisc', 'fijisc-cache', 'foles', 'foles-cache', 'ginna', 'ginna-cache', 'gradle-dev', 'gradle-dev_US', 'gradle-dev_US-cache','gradle-release_US', 'gradle-release_US-cache',
                 'guam', 'guam-cache', 'guamna', 'guamna-cache', 'guamp', 'guamp-cache', 'hanoi', 'hanoi-cache', 'hanoip', 'hanoip-cache', 'harpia', 'harpia-cache',
                 'hawao', 'hawao_US', 'heart', 'heart-cache', 'humphrey', 'humphrey-cache', 'ironmn', 'ironma_US', 'ironma_US-cache', 'johnson', 'johson-cache',
                 'kane', 'kane-cache', 'kinzie', 'kinzie-cache', 'lake', 'lake-cache', 'lima', 'lima-cache', 'lux', 'lux-cache', 'malta', 'malta-cache',
                 'maltalite', 'maltalite-cache', 'maltalsc', 'maltalsc-cache', 'maui', 'maui_US', 'maui_US-cache', 'messi', 'messi_US', 'messi_US-cache',
                 'minsk', 'minsk-cache', 'modem', 'modem-cache', 'msi', 'msi-cache', 'nairo', 'nairo-cache', 'nio', 'nio-cache', 'ocean', 'ocean-cache',
                 'odessa', 'odessa-cache', 'olson', 'olson-cache', 'parker', 'parker-cache', 'pippen', 'pippen-cache', 'pypi', 'pypi-cache', 'rav', 'rav-cache',
                 'river', 'river-cache', 'sandbox-eit_mbg', 'sandbox-eit_us', 'sandbox-eit_us-cache', 'scratch', 'surfna', 'surfna-cache', 'stability',
                 'test', 'test-cache', 'tmp_share', 'tools', 'troika', 'troika-cache', 'victara', 'victara-cache', 'wlss01_repo_creation_test', 'wlss01_repo_creation_test-cache'
                 }
HOST = 'https://artifacts-bjmirr.mot.com/artifactory'

class ArtifactsDb:
    def __init__(self):
        pass


class ArtifactsUpdater:
    def __init__(self, url, cookie):
        self.__db = SqliteDB()
        self.__loaded_versions = self.__db.get_all_versions_list()
        self.__url = url
        self.__cookie = cookie
        self.__payload = {'type': 'root',
                         'path': '',
                         'repoType': 'remote',
                         'repoKey': 'key',
                         'text': 'text',
                         'trashcan': 'false',
                         }
        self.__headers = {
            'Content-Type': 'application/json',
            'Cookie': self.__cookie,
            'Host': 'artifacts-bjmirr.mot.com'
        }

        self.__requests_root(self.__payload)
        # todo multiple thread support
        # self.__pool = ThreadPoolExecutor(max_workers=10)

    def __requests_root(self, payload):
        response = requests.post(self.__url, headers=self.__headers, json=payload)
        if response.status_code != 200:
            # todo optimize notify mesage
            print('Connect artifacts site failed!!!')
            print(response.text)
            return
        response_json = json.loads(response.text)
        for item in response_json:
            if 'repoKey' in item and item['repoKey'] in EXCLUDE_REPOS:
                continue
            # not traverse directories like cypfg-cache, smith-cache
            if 'repoKey' in item and item['repoKey'].find('cache') != -1:
                continue
            self.__payload['type'] = 'junction'
            self.__payload['path'] = item['path']
            self.__payload['text'] = item['text']
            self.__payload['repoKey'] = item['repoKey']
            self.__payload['repoType'] = item['repoType']
            self.__requests(self.__payload, item['path'])

    def __requests(self, payload, parent_path):
        response = requests.post(self.__url, headers=self.__headers, json=payload)
        if response.status_code != 200:
            # fixme optimize notify mesage
            print('Connect artifacts site failed!!!')
            print(response.text)
            return
        response_json = json.loads(response.text)
        for item in response_json:
            # 有的 repoKey='austin'下面的子目录中 repoKey='austin_US-cache'
            # 剔除-cache后缀
            repoKeyWithoutSuffix = item['repoKey']
            cacheIndex = repoKeyWithoutSuffix.find('-cache')
            # FIXME: remove
            print('not load:' + item['repoKey'] + '/' + item['path'])
            if cacheIndex != -1:
                repoKeyWithoutSuffix = repoKeyWithoutSuffix[0:cacheIndex]
            if (item['repoKey'] + '/' + item['path']) in self.__loaded_versions:
                continue
            if item['path'].find('msi_only') != -1:
                continue
            if parent_path.find('key') == -1:
                self.__payload['type'] = 'junction'
                self.__payload['path'] = item['path']
                self.__payload['text'] = item['text']
                self.__payload['repoKey'] = item['repoKey']
                self.__payload['repoType'] = item['repoType']
                self.__requests(self.__payload, payload['path'])
            else:
                repo_url = HOST + '/' + repoKeyWithoutSuffix + '/' + item['path']
                repo_name = repoKeyWithoutSuffix
                repo_detailed_version = item['path']
                # from 12/SSL32.9/oneli_factory/userdebug/release-keys_cid255
                # to   12/SSL32.9
                repo_version = repoKeyWithoutSuffix + '/' + re.search('(.*?/.*?)/.*', item['path'])[1]
                if re.search('.*ReleaseNotes.html', item['path']) or re.search('msi-side_release_notes.*', item['path']):
                    # fixme remove print
                    print('repoKey:{}, {}'.format(repoKeyWithoutSuffix, repo_url))
                    self.__db.insert_release(repo_url, repo_name, repo_version, repo_detailed_version)
                elif re.search('fastboot_' + '.*tar.gz', item['path']):
                    # fixme remove print
                    print('repoKey:{}, {}'.format(repoKeyWithoutSuffix, repo_url))
                    self.__db.insert_repo(repo_url, repo_name, repo_version, repo_detailed_version)