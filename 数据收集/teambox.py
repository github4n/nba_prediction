from requests_futures.sessions import FuturesSession
import json
import pyexcel as pe
import shelve
import time
import os


class NbaTeamBoxscores:
    def __init__(self, txt):
        with open(txt, 'r', encoding='utf-8') as f:
            url_eles, headers = f.read().split('====')
        url_eles = url_eles.split()
        headers = headers.split('\n')
        self.team_urls = {}
        for id in url_eles[-2].split(';'):
            self.team_urls[id] = [url_eles[0] + t + url_eles[2] + id + url_eles[-1]
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

    def save_result(self, team, res):
        pe.save_as(dest_file_name=team + '.xlsx',
                   array=[res['headers']] + res['rowSet'])

    def id_to_name(self):
        session = FuturesSession()
        names = []
        urls = [
            'http://stats.nba.com/stats/teaminfocommon?LeagueID=00&Season=2016-17&SeasonType=Regular+Season&TeamID='
            + str(u) for u in range(1610612747, 1610612767)]
        for f in [session.get(u, headers=self.headers) for u in urls]:
            res = json.loads(f.result().text)['resultSets'][0]['rowSet'][0]
            name = res[2] + res[3]
            names.append(name)
        f = shelve.open('id_to_name')
        for i, id in enumerate(range(1610612747, 1610612767)):
            f[str(id)] = names[i]

    def games(self):
        url = 'http://stats.nba.com/stats/leaguegamelog?Counter=1000&DateFrom=&DateTo=&Direction=DESC&LeagueID=00&PlayerOrTeam=T&Season=2016-17&SeasonType=Regular+Season&Sorter=DATE'
        result = FuturesSession().get(url, headers=self.headers).result().text
        result = json.loads(result)
        res = result['resultSets'][0]
        pe.save_as(dest_file_name='games.xlsx', array=[res['headers']] + res['rowSet'])

    def main(self):
        f = shelve.open('team_results')
        f2 = shelve.open('id_to_name')
        for team, urls in self.team_urls.items():
            if f2[str(team)] + '.xlsx' in os.listdir():
                continue
            result = self.sent_requests(urls)
            team = result['rowSet'][0][result['headers'].index('TEAM_NAME')]
            f[team] = result
            print(team)
            self.save_result(team, result)
            time.sleep(10)


if __name__ == '__main__':
    start = time.clock()
    nba = NbaTeamBoxscores('requests.txt')
    # nba.main()
    # nba.id_to_name()
    nba.games()
    print(time.clock() - start)