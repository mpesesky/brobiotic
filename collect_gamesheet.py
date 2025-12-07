from bs4 import BeautifulSoup
import requests
import pandas as pd
from io import StringIO
import re
import numpy as np

class HockeyTables:
    def __init__(self, game_num):
        self.home=home
        response = requests.get(
            f"https://lscluster.hockeytech.com/game_reports/official-game-report.php?client_code=pwhl&game_id={game_num}&lang_id=1"
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        self._split_data(pd.read_html(StringIO(str(soup))))
        self._refine()
        self._name_teams()
        

    def _split_data(self, table_list):
        self.refs_raw = table_list[1]
        self.attendance_raw = table_list[2]
        self.scoring_raw = table_list[4]
        self.shots_raw = table_list[5]
        self.pp_raw = table_list[6]
        self.summary_raw = table_list[7]
        if len(table_list) == 15:
            self.visitor_skater_raw = table_list[9]
            self.visitor_goalie_raw = table_list[10]
            self.home_skater_raw = table_list[11]
            self.home_goalie_raw = table_list[12]
            self.penalty_raw = table_list[13]
        else:
            self.visitor_skater_raw = table_list[12]
            self.visitor_goalie_raw = table_list[13]
            self.home_skater_raw = table_list[14]
            self.home_goalie_raw = table_list[15]
            self.penalty_raw = table_list[16]

    def _name_teams(self):
        self.away_team = self.scoring.columns[1]
        self.home_team = self.scoring.columns[2]

    def _get_person(self, names, order):
        name_str = re.compile(r"(?P<ref1>.+)\s\(\d+\)\s(?P<ref2>.+)\s\(\d+\)")
        name_groups = name_str.match(names).groupdict()
        if order == 1:
            return name_groups["ref1"]
        return name_groups["ref2"]

    def _refine_table(self, df):
        df2 = df.T
        df2 = df2.rename(columns=df2.iloc[0]).drop(0).reset_index(drop=True)
        return df2
    
    def _refine_ref(self):
        ref_t = self._refine_table(self.refs_raw)
        ref_t["ref_1"] = ref_t["Referee:"].map(lambda x: self._get_person(x,1))
        ref_t["ref_2"] = ref_t["Referee:"].map(lambda x: self._get_person(x,2))
        ref_t["line_1"] = ref_t["linespersons:"].map(lambda x: self._get_person(x,1))
        ref_t["line_2"] = ref_t["linespersons:"].map(lambda x: self._get_person(x,2))
        return ref_t

    def _refine_period(self, table_name, df):
        score = self._refine_table(df).rename(columns={table_name: "Period"})
        return score

    def _refine_skater(self, df):
        rdf = df.rename(columns=df.iloc[1]).drop([0,1]).reset_index(drop=True)
        return rdf[rdf.No.notnull()].rename(columns={np.nan: 'Pos'})

    def _refine(self):
        self.refs = self._refine_ref()
        self.attendance = self._refine_table(self.attendance_raw)
        self.scoring = self._refine_period("SCORING", self.scoring_raw)
        self.shots = self._refine_period("SHOTS", self.shots_raw)
        self.pp = self.pp_raw.rename(columns=self.pp_raw.iloc[0]).drop(0).reset_index(drop=True)
        self.summary = self.summary_raw.rename(columns=self.summary_raw.iloc[0]).drop(0).reset_index(drop=True)
        self.away_skater = self._refine_skater(self.visitor_skater_raw)
        self.away_goalie = self._refine_skater(self.visitor_goalie_raw)
        self.home_skater = self._refine_skater(self.home_skater_raw)
        self.home_goalie = self._refine_skater(self.home_goalie_raw)
        self.penalty = self.penalty_raw.rename(columns=self.penalty_raw.iloc[1]).drop([0,1]).reset_index(drop=True)
