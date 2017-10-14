from requests_futures.sessions import FuturesSession
import json
import pyexcel as pe
import time
import os
from collections import OrderedDict
import requests


class NbaTeamBoxscores:
    def __init__(self, txt):
        with open(txt, 'r', encoding='utf-8') as f:
            url_eles, headers = f.read().split('====')
        url_eles = url_eles.split()
        headers = headers.split('\n')
        self.year_urls = OrderedDict()
        # {
        #   '2007-08':{
        #               'team':url,
        #               ...},
        #   ...
        # }
        for year in url_eles[-2].split(';'):
            self.year_urls[year] = {}
            for id in url_eles[-3].split(';'):
                self.year_urls[year][id] = \
                    [url_eles[0] + t + url_eles[2] + year + url_eles[3] + id + url_eles[-1]
                     for t in url_eles[1].split(';')]
        self.headers = {}
        for k, v in [h.split(': ') for h in headers if h]:
            self.headers[k] = v

    def sent_requests(self, urls):
        session = FuturesSession()
        futures = [session.get(url, headers=self.headers) for url in urls]
        result = {}
        headers = []
        rowSet = []
        for f in futures:
            res = json.loads(f.result().text)['resultSets'][0]
            headers += res['headers']
            rowSet = res['rowSet'] if len(rowSet) == 0 else \
                [rowSet[i] + game for i, game in enumerate(res['rowSet'])]
        result['headers'] = list(set(headers))
        index = [headers.index(h) for h in result['headers']]
        result['rowSet'] = [[game[i] for i in index] for game in rowSet]
        return result

    def save_result(self, year_team, res):
        pe.save_as(dest_file_name=year_team + '.xlsx',
                   array=[res['headers']] + res['rowSet'])

    def id_to_name(self):
        print('---id_to_name---')
        session = FuturesSession()
        names = []
        urls = [
            'http://stats.nba.com/stats/teaminfocommon?LeagueID=00&Season=2016-17&SeasonType=Regular+Season&TeamID='
            + str(u) for u in range(1610612737, 1610612767)]

        def get_name(urls):
            for f in [session.get(u, headers=self.headers) for u in urls]:
                res = json.loads(f.result().text)['resultSets'][0]['rowSet'][0]
                name = res[2] + ' ' + res[3]
                names.append(name)

        get_name(urls[:15])
        print('完成前15个队,稍等10秒...')
        time.sleep(10)
        get_name(urls[15:])
        with open('id_to_name.txt', 'w', encoding='utf-8') as f:
            for i, id in enumerate(range(1610612737, 1610612767)):
                f.write(str(id) + ',' + names[i] + '\n')
        print('完成后15个队,稍等10秒...')
        time.sleep(10)

    def games(self):
        url = 'http://stats.nba.com/stats/leaguegamelog?Counter=1000&DateFrom=&DateTo=&Direction=DESC&LeagueID=00' \
              '&PlayerOrTeam=T&Season='
        url2 = '&SeasonType=Regular+Season&Sorter=DATE'
        years = list(self.year_urls.keys())
        futures = [FuturesSession().get(url + year + url2, headers=self.headers) for year in years]
        for i, future in enumerate(futures):
            result = json.loads(future.result().text)
            res = result['resultSets'][0]
            pe.save_as(dest_file_name=years[i] + '/games.xlsx', array=[res['headers']] + res['rowSet'])
            print(years[i], '-----games-----')

    def main(self, run_path='teams'):
        if not os.path.exists('id_to_name.txt'):
            self.id_to_name()
        for year in self.year_urls.keys():
            if not os.path.exists(year):
                os.mkdir(year)
        if run_path == 'teams':
            print('开始采集各个球队的历史数据')
            id_to_name = {}
            with open('id_to_name.txt', 'r', encoding='utf-8') as f:
                for id, name in [line.strip().split(',') for line in f.readlines()]:
                    id_to_name[str(id)] = name
            for year, team_urls in self.year_urls.items():
                for team_id, urls in team_urls.items():
                    if id_to_name[str(team_id)] + '.xlsx' in os.listdir(year):
                        print(id_to_name[str(team_id)], '已采集')
                        continue
                    result = self.sent_requests(urls)
                    team = result['rowSet'][0][result['headers'].index('TEAM_NAME')]
                    self.save_result(year + '/' + team, result)
                    print(year, '-', team, '完成,稍等3秒...')
                    time.sleep(3)
                print(year, '-----teams-----')
                print('稍等10秒...')
                time.sleep(10)
        else:
            print('开始采集赛程赛果历史数据')
            self.games()

    def main_robust(self, run_path='teams', error_num=0):
        try:
            self.main(run_path)
        except requests.exceptions.ConnectionError:
            error_num += 1
            print('!!!!!!!!!!!!!!!!!错误次数!!!!!!!!!!!!!  ', error_num, '次\n稍等10秒')
            time.sleep(10)
            self.main_robust(run_path, error_num)


if __name__ == '__main__':
    start = time.clock()
    nba = NbaTeamBoxscores('requests.txt')
    nba.main_robust()
    # print(nba.year_urls)
    print(time.clock() - start)
