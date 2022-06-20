import asyncio
import logging
import httpx
import requests
from util import Util


class AsyncDownloader:
    def __init__(self, url: str, headers: dict = None, filename: str=None):
        self.__url = url
        self.__headers = headers
        self.__filename = filename

    def request(self):
        try:
            if self.__check_support_acceptrange():
                self.__async_download()
            else:
                self.__download_file()
            return True
        except Exception as e:
            logging.exception(e)
            return False

    def __check_support_acceptrange(self):
        """
        检查是否支持断点续传
        """
        head = requests.head(self.__url, headers=self.__headers)
        content_length = head.headers.get('Content-Length')
        accept_range = head.headers.get('Accept-Ranges')
        if content_length is None:
            logging.error("content length is None")
        else:
            self.__file_size = int(self.__content_length)
            formated_file_size = Util.convert_file_size(self.__file_size)
            logging.info("file size: %s", formated_file_size)
        if accept_range is None:
            logging.info("don't support 断点续传")
            return False
        else:
            logging.info("support 断点续传")
            return True

    def __download(self):
        """
        not segment-based download
        """
        req = requests.get(self.__url, stream=True, headers=self.__headers)
        with(open(self.__filename, 'wb')) as f:
            for chunk in req.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()

    def __async_download(self):
        """
        segment-based download
        """
        # TODO: replace httpx with requests
        client = httpx.AsyncClient()
        divisional_ranges = self.__calc_divisional_range(self.__file_size)
        # create empty file
        with open(self.__filename, 'wb') as f:
            pass
        loop = asyncio.get_event_loop()
        tasks = [self.__async_download_task(client, s, e) for s, e in divisional_ranges]
        loop.run_until_complete(asyncio.wait(tasks))

    async def __async_download_task(self, client, range_start, range_end):
        if self.__headers is None:
            headers = {'Range': 'bytes={}-{}'.format(range_start, range_end)}
        else:
            self.__headers['Range'] = f'bytes={range_start}-{range_end}'
            headers = self.__headers
        res = await client.get(self.__url, headers=headers)
        with open(self.__filename, "rb+") as f:
            f.seek(range_start)
            f.write(res.content)

    def __calc_divisional_range(self, filesize, chuck=10):
        """
        默认分成10片
        :param filesize:
        :param chuck:
        :return:
        """
        step = filesize // chuck
        arr = list(range(0, filesize, step))
        result = []
        for i in range(len(arr) - 1):
            s_pos, e_pos = arr[i], arr[i + 1] - 1
            result.append([s_pos, e_pos])
        result[-1][-1] = filesize - 1
        return result
