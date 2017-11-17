import requests
from requests_futures.sessions import FuturesSession
import pandas as pd
from datetime import datetime, timedelta
import json
import os


class Predict:
    def __init__(self):
        self.predict_dir = "明日比赛/"
        if not os.path.exists(self.predict_dir):
            os.mkdir(self.predict_dir)
        self.data_source_dir = "NBA统计数据/"
        ###############################
        self.name_to_id = {}
        self.chinese_to_english = {}
        with open("../数据收集/id_to_name.txt", 'r', encoding='utf-8') as f:
            id_name = [line.split(',') for line in f.readlines() if line]
            for _id, name in id_name:
                self.name_to_id[name] = _id
        with open("../数据收集/english_name-to-chinese_name.txt", 'r', encoding='utf-8') as f:
            eng_cn = [line.split('-') for line in f.readlines() if line]
            for eng, cn in eng_cn:
                self.chinese_to_english[cn] = eng
        ###############################
        with open("requests.txt", 'r', encoding='utf-8') as f:
            url_eles, headers = f.read().split("=====")
        self.url_eles = [e for e in url_eles.split('\n') if e]
        self.headers = {}
        for k, v in [h.split(': ') for h in headers if h]:
            self.headers[k] = v

    def predict_tomorrow_game(self):
        today = datetime.today()
        df_today_games = self.get_oneday_games(today)  # 接下来更新NBA官方统计数据
        self.update_nba_data(df_today_games[['客队', '主队']].values.flatten())
        tomorrow = datetime.strftime(today + timedelta(1), "%Y-%m-%d")
        df_tomorrow_games = self.get_oneday_games(tomorrow)
        self.transform_game_data(df_tomorrow_games)  # 构造明日比赛的特征数据

    def transform_game_data(self, games):
        for team1, team2 in games[['客队', '主队']].values:
            pass

    def update_nba_data(self, teams):
        for team in teams:
            self.sent_requests(team)

    def sent_requests(self, team):
        team_id = self.name_to_id[self.chinese_to_english[team]]
        urls = [self.url_eles[0] + _type + self.url_eles[2] + team_id + self.url_eles[3]
                for _type in self.url_eles[1].split(';')]
        result = {}
        headers = []
        rowSet = []
        #########################################
        session = FuturesSession()
        futures = [session.get(url, headers=self.headers) for url in urls]
        for f in futures:
            res = json.loads(f.result().text)['resultSets'][0]
            headers += res['headers']
            rowSet = res['rowSet'] if len(rowSet) == 0 else \
                [rowSet[i] + game for i, game in enumerate(res['rowSet'])]
        ###############################
        result['headers'] = list(set(headers))
        index = [headers.index(h) for h in result['headers']]
        result['rowSet'] = [[game[i] for i in index] for game in rowSet]
        ###############################
        df = pd.DataFrame(result['rowSet'], columns=result['headers'])
        df.to_excel(self.data_source_dir + self.chinese_to_english[team] + ".xlsx", index=False)

    def get_oneday_games(self, oneday):
        if os.path.exists(self.predict_dir + oneday + ".xlsx"):
            return pd.read_excel(self.predict_dir + oneday + ".xlsx")
        url = "http://matchweb.sports.qq.com/kbs/list?from=NBA_PC&columnId=100000&startTime=" \
              + oneday + "&endTime=" + oneday + "&callback=ajaxExec&_=1510925383992"
        text = requests.get(url).text.strip("ajaxExec()")
        result = json.loads(text)['data'][oneday]
        games = [[oneday, r['leftName'], r['rightName']] for r in result]
        df = pd.DataFrame(games, columns=['日期', '客队', '主队'])
        df.to_excel(self.predict_dir + oneday + ".xlsx", index=False)
        return df


if __name__ == '__main__':
    predict = Predict()
    predict.predict_tomorrow_game()
