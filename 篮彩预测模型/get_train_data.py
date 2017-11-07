import pandas as pd


class GetTrainData:
    def __init__(self, n=10):
        self.start_index = n
        self.last_N_game = n
        self.factors = ['FGM', 'FTM', 'AST', 'FG3M', 'OREB']
        self.factors_opp = ['PTS_OPP', 'FGM_OPP', 'FG3M_OPP', 'AST_OPP', 'OREB_OPP', 'DREB']
        self.quantiles = [0.25, 0.75]

        self.big_suffix = '_big_0.75'
        self.small_suffix = '_small_0.25'
        self.features = [f + s for f in self.factors for s in [self.big_suffix, self.small_suffix]]

        self.big_suffix_opp = '_big_mean'
        self.small_suffix_opp = '_small_mean'
        self.features_opp = [f + s for f in self.factors_opp for s in [self.big_suffix_opp, self.small_suffix_opp]]

        self.is_big_or_small_code = {'small': 100, 'big': 200, 'none': 300}

    def is_big_or_small(self, series):
        # <0.25
        if series[self.quantiles[0]] == 0:
            return self.is_big_or_small_code['small']
        # >0.75
        if series[self.quantiles[1]] == 1:
            return self.is_big_or_small_code['big']
        return self.is_big_or_small_code['none']

    def get_game_feature(self, df_base, game_series):
        series_result = pd.Series([0] * len(self.factors) * 2, index=self.features)
        df_compare = (game_series - df_base).applymap(lambda x: 1 if x > 0 else 0)
        series_features = df_compare.apply(self.is_big_or_small)
        for f in series_features.index:
            if series_features[f] == self.is_big_or_small_code['small']:
                series_result[f + self.small_suffix] = 1
            elif series_features[f] == self.is_big_or_small_code['big']:
                series_result[f + self.big_suffix] = 1
        return series_result

    def get_team_features(self, df_team):
        df_factor = df_team[self.factors]
        df_result = pd.DataFrame()
        for i in range(self.start_index, df_factor.shape[0]):
            df_base = df_factor.iloc[i - self.last_N_game:i].quantile(self.quantiles)
            game_series = self.get_game_feature(df_base, df_factor.iloc[i])
            df_result = df_result.append(game_series, ignore_index=True)
        return df_result

    def validate_feature(self, df_team, i):
        # 参数i指第几场比赛，需要大于self.last_N_game
        df_factor = df_team[self.factors]
        return (df_factor.iloc[i - self.last_N_game:i].quantile(self.quantiles),
                df_factor.iloc[i])

    def get_gamex_feature(self, df_up_to_date, team, opp, opp_next):
        pass