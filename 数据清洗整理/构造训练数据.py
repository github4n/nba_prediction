import pandas as pd
import os
import numpy as np


class GenerateTrainData:
    def __init__(self):
        self.train_data_xlsx = "训练数据1(不含对手特征).xlsx"
        self.train_data_xlsx2 = "训练数据2(加入对手特征).xlsx"

    def generate_traindata1(self):
        excludes = ['games.xlsx', 'lottery_results.xlsx']
        prefix = '../数据收集/2016-17/'
        files = [prefix + f for f in os.listdir(prefix) if f not in excludes]
        ###################################
        df = pd.DataFrame()
        for file in files:
            print(file)
            df_new = self.generate_feature(file)
            df = pd.concat([df, df_new])
        df.to_excel(self.train_data_xlsx)

    def generate_traindata2(self):
        df = pd.read_excel(self.train_data_xlsx)
        df_group = df.groupby("GAME_ID")
        groups = list(df_group.groups.keys())
        df_res = pd.DataFrame()
        for group in groups:
            print(group)
            cache = df_group.get_group(group)
            if cache.shape[0] > 1:
                team1 = cache.iloc[0:1]
                team2 = cache.iloc[1:2]
                df_res = df_res.append(pd.merge(team1, team2, on="GAME_ID", suffixes=('', '_OPP')))
                df_res = df_res.append(pd.merge(team2, team1, on="GAME_ID", suffixes=('', '_OPP')))
        ########################################
        df_group_team = df_res.groupby("TEAM_NAME")
        teams = list(df_group_team.groups.keys())
        df_result = pd.DataFrame()
        for team in teams:
            print(team)
            df_team = df_group_team.get_group(team)
            df_team = df_team.sort_values("GAME_ID")
            ############
            columns_opp = [col for col in df_team.columns if "MEAN_OPP" in col]
            columns_own = [col for col in df_team.columns if "MEAN" not in col and "OPP" not in col]
            ###########
            df_cache_opp = df_team[columns_opp]
            df_team_opp = df_cache_opp.iloc[1:].append(df_cache_opp.iloc[-1]) - df_cache_opp
            df_team_opp.columns = [col.replace("MEAN", "CHANGE") for col in columns_opp]
            df_team_opp['GAME_ID'] = df_team['GAME_ID']
            df_team_opp = df_team_opp.set_index("GAME_ID")
            ############
            df_team_own = df_team[columns_own]
            df_team_own = df_team_own.set_index("GAME_ID")
            ############
            df_result = pd.concat([df_result, pd.concat([df_team_own, df_team_opp], axis=1).reset_index()])
        df_result.sort_values("GAME_ID").to_excel(self.train_data_xlsx2, index=False)

    def generate_feature(self, file):
        df = pd.read_excel(file, index_col="GAME_ID")
        df = df.sort_index()
        ########################
        columns_useful = np.array([col for col in df.columns if "RANK" not in col and "OPP" not in col])
        exclude_cols = ['WL', 'TEAM_ABBREVIATION', 'TEAM_ID', 'MIN', 'SEASON_YEAR', 'PLUS_MINUS', 'GAME_DATE',
                        'TEAM_NAME', 'MATCHUP']
        columns = [col for col in columns_useful if col not in exclude_cols]
        ########################
        means = []
        for i in range(5, df.shape[0]):
            means.append(df.iloc[i - 5:i][columns].mean().values)
        data = [np.array([0] * len(columns))] * 5 + means
        ########################
        df_mean = pd.DataFrame(data, columns=columns, index=df.index)
        df_new = df[columns] - df_mean  # 本场与过去均值的差值
        df_mean.columns = [col + "_MEAN" for col in columns]
        df_new = pd.concat([df_new, df_mean], axis=1)  # 过去均值，为构造对手特征准备
        df_new['TEAM_NAME'] = df['TEAM_NAME']
        ########################
        next_change = []
        for i in range(5, df.shape[0] - 1):
            next_change.append(df.iloc[i + 1]['PTS'] - df.iloc[i]['PTS'])
        data_target = [0] * 5 + next_change + [0]
        df_new['NEXT_CHANGE'] = data_target
        return df_new.iloc[5:-1]


if __name__ == '__main__':
    train_data = GenerateTrainData()
    # train_data.generate_traindata1()
    train_data.generate_traindata2()
