import requests
import json
from db import SqliteDB
import asyncio
import re

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
                 'hawaii', 'hawaii_US', 'hawaiip', 'hawaiip_US', 'hawaiipl', 'hawaiipl_US', 'hawaiipll', 'hawaiipll_US',
                 'kane', 'kane-cache', 'kinzie', 'kinzie-cache', 'lake', 'lake-cache', 'lima', 'lima-cache', 'lux', 'lux-cache', 'malta', 'malta-cache',
                 'maltalite', 'maltalite-cache', 'maltalsc', 'maltalsc-cache', 'maui', 'maui_US', 'maui_US-cache', 'messi', 'messi_US', 'messi_US-cache',
                 'minsk', 'minsk-cache', 'modem', 'modem-cache', 'msi', 'msi-cache', 'nairo', 'nairo-cache', 'nio', 'nio-cache', 'ocean', 'ocean-cache',
                 'odessa', 'odessa-cache', 'olson', 'olson-cache', 'parker', 'parker-cache', 'pippen', 'pippen-cache', 'pypi', 'pypi-cache', 'rav', 'rav-cache',
                 'river', 'river-cache', 'sandbox-eit_mbg', 'sandbox-eit_us', 'sandbox-eit_us-cache', 'scratch', 'surfna', 'surfna-cache', 'stability',
                 'sofiar', 'sofiar-cache',
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

        asyncio.run(
            self.__requests_root(self.__payload)
        )

    async def __requests_root(self, payload):
        response = requests.post(self.__url, headers=self.__headers, json=payload)
        if response.status_code != 200:
            # todo optimize notify mesage
            print('Connect artifacts site failed!!!')
            print(response.text)
            return
        response_json = json.loads(response.text)
        payloads = []
        for item in response_json:
            if 'repoKey' in item and item['repoKey'] in EXCLUDE_REPOS:
                continue
            # not traverse directories like cypfg-cache, smith-cache
            if 'repoKey' in item and item['repoKey'].find('cache') != -1:
                continue
            pl = {}
            pl['type'] = 'junction'
            pl['path'] = item['path']
            pl['text'] = item['text']
            pl['repoKey'] = item['repoKey']
            pl['repoType'] = item['repoType']
            payloads.append(pl)
        task_list = []
        for pl in payloads:
            task = asyncio.create_task(
                self.__requests(pl)
            )
            task_list.append(task)
        results = await asyncio.gather(*task_list)
        for i in results:
            print(i)
            self.__db.bulk_insert_repo(i[0])
            self.__db.bulk_insert_release(i[1])

    async def __requests(self, payload):
        # FIXME: remove
        parent_path = payload['path']
        print("enter _requests, parent_path=" +parent_path)
        print(payload)
        repos = []
        release_notes = []
        response = requests.post(self.__url, headers=self.__headers, json=payload)
        if response.status_code != 200:
            # fixme optimize notify message
            print('Connect artifacts site failed!!!')
            print(response.text)
            return
        response_json = json.loads(response.text)
        payload_list = []
        for item in response_json:
            # 1. 过滤掉android 10, 11
            if item['path'].find('10') == 0 or item['path'].find('11') == 0:
                continue
            # 2. 过滤掉 hawaiip_US 下 files/..., rhodep_US 下 S1SU32_rhodep-g_userdebug_mr_r-qsm2021_test-keys_continuous_gc/367
            #    从开始index = 0搜索match
            if not re.match('\d\d.*', item['path']):
                continue
            # 有的 repoKey='austin'下面的子目录中 repoKey='austin_US-cache'
            # 剔除-cache后缀
            repoKeyWithoutSuffix = item['repoKey']
            cacheIndex = repoKeyWithoutSuffix.find('-cache')
            # FIXME: remove 2 line
            print('load_versions size={}'.format(len(self.__loaded_versions)))
            print('not load:' + repoKeyWithoutSuffix + '/' + item['path'])
            if cacheIndex != -1:
                repoKeyWithoutSuffix = repoKeyWithoutSuffix[0:cacheIndex]
            if (repoKeyWithoutSuffix + '/' + item['path']) in self.__loaded_versions:
                continue
            if item['path'].find('msi_only') != -1:
                continue
            if parent_path.find('key') == -1:
                pl = {}
                pl['type'] = 'junction'
                pl['path'] = item['path']
                pl['text'] = item['text']
                pl['repoKey'] = item['repoKey']
                pl['repoType'] = item['repoType']
                payload_list.append(pl)
            else:
                repo_url = HOST + '/' + repoKeyWithoutSuffix + '/' + item['path']
                repo_name = repoKeyWithoutSuffix
                repo_detailed_version = item['path']
                # from 12/SSL32.9/oneli_factory/userdebug/release-keys_cid255
                # to   12/SSL32.9
                repo_version = repoKeyWithoutSuffix + '/' + re.search('(.*?/.*?)/.*', item['path'])[1]
                # FIXME: remove 
                print('repo_version:' + repo_version)
                self.__loaded_versions.add(repo_version)
                if re.search('.*ReleaseNotes.html', item['path']) or re.search('msi-side_release_notes.*', item['path']):
                    # fixme remove print
                    # print('repoKey:{}, {}'.format(repoKeyWithoutSuffix, repo_url))
                    # self.__db.insert_release(repo_url, repo_name, repo_version, repo_detailed_version)
                    release_notes.append((repo_url, repo_name, repo_version, repo_detailed_version))
                elif re.search('fastboot_' + '.*tar.gz', item['path']):
                    # fixme remove print
                    # print('repoKey:{}, {}'.format(repoKeyWithoutSuffix, repo_url))
                    # self.__db.insert_repo(repo_url, repo_name, repo_version, repo_detailed_version)
                    repos.append((repo_url, repo_name, repo_version, repo_detailed_version))
        task_list = []
        for pl in payload_list:
            task = asyncio.create_task(
                self.__requests(pl)
            )
            task_list.append(task)
        results = await asyncio.gather(*task_list)
        for result in results:
            repos.extend(result[0])
            release_notes.extend(result[1])
        return repos, release_notes
