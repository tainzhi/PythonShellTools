import requests
import json
from db import SqliteDB
import asyncio
import re
import logging
from db import Settings

EXCLUDE_REPOS = {'amps', 'amps-cache', 'apps', 'apps-cache', 'archive', 'astro', 'astro-archive', 'banks',
                 'banks-cache',
                 'bathena', 'bathena-cache', 'bingo', 'bingo-cache', 'borneo', 'borneo-cache', 'burton', 'burton-cache',
                 'cebu', 'cebu-cache', 'channel', 'channel-cache', 'chef', 'chef-cache', 'continuous_builds',
                 'continuous_builds-cache',
                 'cptools', 'cptools-cache', 'cw_virtual_US', 'cw_virtual_US-cache', 'davros_us', 'davros_us-cache',
                 'deen', 'deen_32', 'deen_32-cache', 'deen-cache',
                 'def', 'def-cache', 'doha', 'doha-cache', 'drogon', 'drogon_US', 'drogon_US-cache', 'evert',
                 'evert-cache', 'felix', 'felix_us', 'felix_US-cache',
                 'fijisc', 'fijisc-cache', 'foles', 'foles-cache', 'ginna', 'ginna-cache', 'gradle-dev',
                 'gradle-dev_US', 'gradle-dev_US-cache', 'gradle-release_US', 'gradle-release_US-cache',
                 'guam', 'guam-cache', 'guamna', 'guamna-cache', 'guamp', 'guamp-cache', 'hanoi', 'hanoi-cache',
                 'hanoip', 'hanoip-cache', 'harpia', 'harpia-cache',
                 'hawao', 'hawao_US', 'heart', 'heart-cache', 'humphrey', 'humphrey-cache', 'ironmn', 'ironma_US',
                 'ironma_US-cache', 'johnson', 'johson-cache',
                 'hawaii', 'hawaii_US', 'hawaiip', 'hawaiip_US', 'hawaiipl', 'hawaiipl_US', 'hawaiipll', 'hawaiipll_US',
                 'kane', 'kane-cache', 'kinzie', 'kinzie-cache', 'lake', 'lake-cache', 'lima', 'lima-cache', 'lux',
                 'lux-cache', 'malta', 'malta-cache',
                 'maltalite', 'maltalite-cache', 'maltalsc', 'maltalsc-cache', 'maui', 'maui_US', 'maui_US-cache',
                 'messi', 'messi_US', 'messi_US-cache',
                 'minsk', 'minsk-cache', 'modem', 'modem-cache', 'msi', 'msi-cache', 'nairo', 'nairo-cache', 'nio',
                 'nio-cache', 'ocean', 'ocean-cache',
                 'odessa', 'odessa-cache', 'olson', 'olson-cache', 'parker', 'parker-cache', 'pippen', 'pippen-cache',
                 'pypi', 'pypi-cache', 'rav', 'rav-cache',
                 'river', 'river-cache', 'sandbox-eit_mbg', 'sandbox-eit_us', 'sandbox-eit_us-cache', 'scratch',
                 'surfna', 'surfna-cache', 'stability',
                 'sofiar', 'sofiar-cache',
                 'test', 'test-cache', 'tmp_share', 'tools', 'troika', 'troika-cache', 'victara', 'victara-cache',
                 'wlss01_repo_creation_test', 'wlss01_repo_creation_test-cache'
                 }
# TODO: custom hostname, not only artifacts-bjmirr.mot.com
ARTIFACTS_HOST = 'https://artifacts-bjmirr.mot.com/artifactory'


class ArtifactsUpdater:
    def __init__(self, config: dict):
        logging.debug(config)
        self.__is_loading = False
        self.__db = SqliteDB()
        self.__loaded_versions = self.__db.get_all_versions_list()
        self.__url = config['artifacts']['url']
        self.__cookie = config['artifacts']['cookie']
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

        self.__fastboot_re = re.compile(r"fastboot_.*\.tar\.gz")
        self.__release_notes_re = re.compile(r".*ReleaseNotes.html|msi-side_release_notes.*")
        self.__repo_version_re = re.compile(r'(.*?/.*?)/.*')
        self.__start_with_11_12_re = re.compile(r'\d\d.*')

        self.__search_repos(config)

    def __search_repos(self, keys):
        repos = self.__db.search_repos(keys['version'], keys['dist'], keys['finger'])
        if True or len(repos) == 0:
            print("No repos found, updating first")
            # 从 eqs_g/oneli_cn 过滤出eqs/oneli
            product_name_base = keys['product'][0:keys['product'].find('_')]
            self.__check_login_status()
            loop = asyncio.get_event_loop()
            run_code = loop.run_until_complete(
                self.__requests_root(self.__payload, specified_product=product_name_base))
            # asyncio.run(
            #     self.__requests_root(self.__payload, specified_product=product_name_base)
            # )
            if run_code:
                logging.info("search db after loading")
                repos = self.__db.search_repos(keys['version'], keys['dist'], keys['finger'])
                print(repos)
        else:
            logging.info("search db not need update")
            print(repos)

    def __check_login_status(self):
        # FIXME: add login function
        if self.__cookie.find('SESSION') == -1:
            logging.info('cookie is not fully set, need login')
            self.__login_reset_headers()

    # 默认更新所有的 product 的repos
    # 如果指定了 product，则更新指定 product 的repos
    async def __requests_root(self, payload: dict, specified_product=None):
        self.__is_loading = True
        logging.debug(specified_product)
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
            if specified_product is None:
                pl = {'type': 'junction', 'path': item['path'], 'text': item['text'], 'repoKey': item['repoKey'],
                      'repoType': item['repoType']}
                payloads.append(pl)
            else:
                if item['repoKey'].find(specified_product) != -1:
                    logging.info('to update product repo: %s', item['repoKey'])
                    pl = {'type': 'junction', 'path': item['path'], 'text': item['text'], 'repoKey': item['repoKey'],
                          'repoType': item['repoType']}
                    payloads.append(pl)
        task_list = []
        for pl in payloads:
            task = asyncio.create_task(
                self.__requests(pl)
            )
            task_list.append(task)
        results = await asyncio.gather(*task_list)
        for i in results:
            ## FIXME: add to log
            ## print(i)
            logging.info('insert %s items into db', len(i[0]))
            self.__db.bulk_insert_repo(i[0])
            self.__db.bulk_insert_release(i[1])
        return True

    async def __requests(self, payload: dict):
        parent_path = payload['path']
        # FIXME: add to logging
        print("enter: " + parent_path)
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
            # 2. 过滤掉 hawaiip_US 下 files/...,  因为需要查找 hawappip/12/..., hawaiip/13/..., 而不是其他的 hawaiip/13/...
            # 2.1. 过滤掉 rhodep_US 下 S1SU32_rhodep-g_userdebug_mr_r-qsm2021_test-keys_continuous_gc/367
            #    从开始index = 0搜索match
            if not re.match(self.__start_with_11_12_re, item['path']):
                continue
            # 有的 repoKey='austin'下面的子目录中 repoKey='austin_US-cache'
            # 剔除-cache后缀
            repoKeyWithoutSuffix = item['repoKey']
            cacheIndex = repoKeyWithoutSuffix.find('-cache')
            if cacheIndex != -1:
                repoKeyWithoutSuffix = repoKeyWithoutSuffix[0:cacheIndex]
            if (repoKeyWithoutSuffix + '/' + item['path']) in self.__loaded_versions:
                continue
            if item['path'].find('msi_only') != -1:
                continue
            if parent_path.find('key') == -1:
                pl = {'type': 'junction', 'path': item['path'], 'text': item['text'], 'repoKey': item['repoKey'],
                      'repoType': item['repoType']}
                payload_list.append(pl)
            else:
                repo_url = ARTIFACTS_HOST + '/' + repoKeyWithoutSuffix + '/' + item['path']
                repo_name = repoKeyWithoutSuffix
                repo_detailed_version = item['path']
                # from 12/SSL32.9/oneli_factory/userdebug/release-keys_cid255
                # to   12/SSL32.9
                repo_version = repoKeyWithoutSuffix + '/' + re.search(self.__repo_version_re, item['path'])[1]
                if re.search(self.__release_notes_re, item['path']):
                    release_notes.append((repo_url, repo_name, repo_version, repo_detailed_version))
                elif re.search(self.__fastboot_re, item['path']):
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

    def __login_reset_headers(self):
        login_url = 'https://artifacts-bjmirr.mot.com/artifactory/ui/auth/login?_spring_security_remember_me=false'
        settings = Settings()
        username, password = settings.get_username_password()
        if username is None or password is None:
            username = input('Please input username:')
            password = input('Please input password:')
        settings.set_username_password(username, password)
        payload = {'user': username, 'password': password, 'type': 'login'}
        response = requests.post(login_url, headers=self.__headers, json=payload)
        if response.status_code != 200:
            logging.error("login failed: %s", response.text)
            excep = Exception('Login failed!!!')
            logging.exception(excep)
            raise excep
        else:
            response_header = response.headers
            set_cookie = response_header['Set-Cookie']
            session = re.search("(SESSION=.*?);", set_cookie)
            if session is not None:
                self.__cookie = self.__cookie + '; ' + session.group(1)
                self.__headers['Cookie'] = self.__cookie
                logging.info('Login success, reset headers')
            else:
                logging.error('Login success, but get session failed')
