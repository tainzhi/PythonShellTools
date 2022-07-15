import requests
import json
from db import SqliteDB
import asyncio
import re
import logging
from db import Settings
from datetime import datetime, timedelta
from util import *

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
                 'maltalite', 'maltalite-cache', 'maltalsc', 'maltalsc-cache',
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
PRODUCT_VEST_DIST = {'tongal': 'maui'}


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
            'Host': MIRROR_HOST
        }

        self.__fastboot_re = re.compile(r"fastboot_.*\.tar\.gz")
        self.__release_notes_re = re.compile(r".*ReleaseNotes.html|msi-side_release_notes.*")
        self.__repo_version_re = re.compile(r'(.*?/.*?)/.*')
        self.__start_with_11_12_re = re.compile(r'\d\d.*')
        self.__repo_name_re = re.compile(r'[^\/]+[^\.]+$')

        self.__search_repos(config)

    def __search_repos(self, keys):
        # 从 eqs_g/oneli_cn 过滤出eqs/oneli
        if keys['product'].find('_') != -1:
            product_name_base = keys['product'][0:keys['product'].find('_')]
        else:
            product_name_base = keys['product']
        if product_name_base in PRODUCT_VEST_DIST.keys():
            product_name_base = PRODUCT_VEST_DIST[product_name_base]
        repos = self.__db.search_repos(keys['version'], keys['dist'], keys['finger'])
        if len(repos) == 0:
            logging.info("No repos found, updating first")
            loop = asyncio.get_event_loop()
            run_code = loop.run_until_complete(
                self.__requests_root(self.__payload, specified_product=product_name_base))
            # fixme: remove
            # asyncio.run(
            #     self.__requests_root(self.__payload, specified_product=product_name_base)
            # )
            if run_code:
                logging.info("search db after loading")
                repos = self.__db.search_repos(keys['version'], keys['dist'], keys['finger'])
        print('---------------------target repo------------------------')
        print(repos)
        self.__print_latest_repos(product_name_base, keys['android_version'] if len(keys['android_version']) != 0 else '12')

    def __print_latest_repos(self, product_name_base, android_version="12"):
        """
        fixme: to display in UI
        从 https://artifacts-bjmirr.mot.com/artifactory/webapp/#/home 获取的json数据中没有各个 repo image的构建时间
        所以需要从 https://artifacts-bjmirr.mot.com/artifactory/list/smith/12/ 类似的网址中获取 repo 各个版本的构建时间

        S3SG32.11/      21-Jun-2022 11:40    -
        S3SG32.12/->        -    -
        S3SG32.13/      23-Jun-2022 12:04    -
        S3SG32.14/      24-Jun-2022 12:33    -

        只获取过去15天的构建的版本, 然后更新数据库
        从数据库中获取最新的 6 个版本, 并输出

        :param product_name_base: smith
        :param version: 12
        :return:
        """
        url = f'https://{MIRROR_HOST}/artifactory/list/{product_name_base}/{android_version}/'
        response = requests.get(url, headers=self.__headers)
        if response.status_code != 200:
            logging.error(f"{url} request failed, status code: {response.status_code} {response.text}")
            # 登录失败, 重新登录
            self.__login_reset_headers()
            # 重新遍历
            self.__print_latest_repos(product_name_base, android_version)
            return
        else:
            # 遍历过滤出 image版本号 - 构建时间
            regex = r"<.*?>(.*)\/<.*>.*(\d{2}\-\w{3,}\-\d{4}\s\d{2}:\d{2})"
            matches = re.findall(regex, response.text, re.MULTILINE)
            until_half_month_ago = datetime.today() - timedelta(days=15)
            for match in matches:
                image_version = match[0]
                build_date_time = match[1]
                build_date = datetime.strptime(build_date_time, "%d-%b-%Y %H:%M")
                # 只更新过去15天的版本
                if build_date > until_half_month_ago:
                    self.__db.update_repo_build_date(product_name_base, android_version, image_version, build_date)
        print('---------------------latest repos-----------------------')
        latest_repo = self.__db.get_latest_repos(product_name_base)
        for repo in latest_repo:
            print(f'{repo[2]}\t{repo[1]}\n')
        print('--------------------------------------------------------')

    # 默认更新所有的 product 的repos
    # 如果指定了 product，则更新指定 product 的repos
    async def __requests_root(self, payload: dict, specified_product=None):
        self.__is_loading = True
        logging.debug(specified_product)
        response = requests.post(self.__url, headers=self.__headers, json=payload)
        if response.status_code != 200:
            # todo optimize notify mesage
            logging.error('Connect artifacts site failed!!! try first')
            logging.error(response)
            self.__login_reset_headers()
            logging.info('request artifacts with new cookie')
            response = requests.post(self.__url, headers=self.__headers, json=payload)
        response_json = json.loads(response.text)
        payloads = []
        for item in response_json:
            # 1. 一些老项目不再使用, 排除掉
            if 'repoKey' in item and item['repoKey'] in EXCLUDE_REPOS:
                continue
            # 2. cache的项目, 排除掉. 因为cache的项目都可以在非cache的item中找到
            # not traverse directories like cypfg-cache, smith-cache
            if 'repoKey' in item and item['repoKey'].find('cache') != -1:
                continue
            # 3. _US 的项目, 排除掉. 因为_US的项目都可以在非_US的item中找到, 比如 _g的image
            if 'repoKey' in item and item['repoKey'].find('_US') != -1:
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
                repo_url = 'https://artifacts-bjmirr.mot.com/artifactory' + '/' + repoKeyWithoutSuffix + '/' + item[
                    'path']
                repo_detailed_version = item['path']
                # from 12/SSL32.9/oneli_factory/userdebug/release-keys_cid255
                # to   12/SSL32.9
                repo_version = repoKeyWithoutSuffix + '/' + re.search(self.__repo_version_re, item['path'])[1]
                if re.search(self.__release_notes_re, item['path']):
                    release_notes.append((repo_url, repo_version, repo_detailed_version))
                elif re.search(self.__fastboot_re, item['path']):
                    repos.append((re.search(self.__repo_name_re, repo_url).group(0), repo_url, repo_version,
                                  repo_detailed_version))
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
        """
        输入用户名和密码, 进行登录, 获取cookie, 并重新设置 headers
        :return:
        """
        login_url = 'https://{}/artifactory/ui/auth/login?_spring_security_remember_me=false'.format(MIRROR_HOST)
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
            excep = Exception('Login failed!!!, ' + response.text)
            logging.exception(excep)
            settings.clear_username_password()
            raise excep
        else:
            response_header = response.headers
            set_cookie = response_header['Set-Cookie']
            session = re.search("(SESSION=.*?);", set_cookie)
            if session is not None:
                cookie_items = [item for item in self.__cookie.split(';') if item.find('SESSION') == -1]
                self.__cookie = ';'.join(cookie_items) + ';' + session.group(1)
                self.__headers['Cookie'] = self.__cookie
                logging.info('Login success, reset headers')
            else:
                excep = Exception('Login success, but reset headers failed')
                logging.exception(excep)
                raise excep
