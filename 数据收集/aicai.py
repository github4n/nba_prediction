from requests_futures.sessions import FuturesSession
import json
import pyexcel as pe
import time
import os
from collections import OrderedDict
import requests


class Aicai:
    def __init__(self, txt):
        with open(txt, 'r', encoding='utf-8') as f:
            url_eles, headers = f.read().split('=====')
        url_eles = url_eles.split('\n')
        self.year_urls = OrderedDict()
        for i, year in enumerate(url_eles[1].split(';')):
            self.year_urls[year] = [url_eles[0] + year + url_eles[2] + month
                                    for month in url_eles[3 + i].split(';')]

        self.headers = {}
        for k, v in [line.split(': ') for line in headers.split('\n') if line]:
            self.headers[k] = v

    def send_requests(self, urls):
        session = FuturesSession()
        futures = [session.get(u, headers=self.headers) for u in urls]
        result = []
        for f in futures:
            res = json.loads(f.result().text)['result']['match']  # [{},{},...]
            result += res
        return result

    def save_result(self, year, result):
        pe.save_as(dest_file_name=year + '/lottery_results.xlsx', records=result)

    def main(self):
        print('开始采集篮彩赛程赛果历史数据')
        for year, urls in self.year_urls.items():
            year = '20' + year
            if not os.path.exists(year):
                os.mkdir(year)
            if os.path.exists(year + '/lottery_results.xlsx'):
                print(year, '已采集')
                continue
            res = self.send_requests(urls)
            self.save_result(year, res)
            print(year, '采集完成,稍等10秒...')
            time.sleep(10)


if __name__ == '__main__':
    aicai = Aicai('requests_aicai.txt')
    aicai.main()
