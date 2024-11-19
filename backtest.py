from datetime import datetime, timedelta
import pandas as pd
import os
import matplotlib.pyplot as plt



class BacktestWins():

    def __init__(self, date=None, from_url=False):
        if date is None:
            self.date = datetime.now()
        else:
            self.date = date
        self.schedule = self._get_combined_schedule(from_url)

        self.train_schedule = self.schedule[self.schedule['date'] <= self.date]
        self.pred_schedule = self.schedule[self.schedule['date'] > self.date]
        self.test_schedule = self.pred_schedule[self.pred_schedule['date'] <= (self.date + timedelta(days=1))]

        self.standings = self._get_standings(self.train_schedule)

        team_wins_dict = self.standings['wins'].to_dict()
        self.second_wins = self._get_2nd_degree_wins(team_wins_dict, self.train_schedule)
        self.backtest_results = self.backtest(self.test_schedule.copy(deep=True), self.second_wins)
        
    
    def backtest(self, schedule, second_wins):
        # Initialize new columns 'pred' and 'winner'
        schedule['pred'] = None
        schedule['winner'] = None
        schedule['confidence'] = None

        # Iterate over each row in the schedule
        for index, game in schedule.iterrows():
            # Determine the predicted winner based on second_wins
            if second_wins[game['home_team']] > second_wins[game['visitor_team']]:
                schedule.at[index, 'pred'] = game['home_team']
                schedule.at[index, 'confidence'] = second_wins[game['home_team']]/(second_wins[game['home_team']]+second_wins[game['visitor_team']])
            elif second_wins[game['visitor_team']] > second_wins[game['home_team']]:
                schedule.at[index, 'pred'] = game['visitor_team']
                schedule.at[index, 'confidence'] = second_wins[game['visitor_team']]/(second_wins[game['home_team']]+second_wins[game['visitor_team']])
            else:
                schedule.at[index, 'pred'] = None

            # Determine the actual winner based on points
            if game['home_pts'] > game['visitor_pts']:
                schedule.at[index, 'winner'] = game['home_team']
            else:
                schedule.at[index, 'winner'] = game['visitor_team']

        # Add a new column 'correct' to indicate if the prediction was correct
        schedule['correct'] = schedule.apply(
            lambda row: 1 if row['pred'] and row['pred'] == row['winner'] else 0,
            axis=1
        )
        return schedule

    def _get_months_from_october(self):
        months = [
            "october", "november", "december",
            "january", "february", "march",
            "april", "may", "june",
            "july", "august", "september"
        ]
        current_month = datetime.now().strftime("%B").lower()
        return months[:months.index(current_month)+1]


    def _get_combined_schedule(self, from_url=False, file_path="combined_schedule.csv"):
        months = self._get_months_from_october()
        
        # Check if the combined file exists and if we should not read from the URL
        if not from_url and os.path.exists(file_path):
            # Load the saved data
            combined_schedule = pd.read_csv(file_path)
            combined_schedule['date'] = pd.to_datetime(combined_schedule['date'], errors='coerce')
        else:
            # Fetch data from the URL for each month and combine
            all_schedules = []
            for month in months:
                url = f"https://www.basketball-reference.com/leagues/NBA_2025_games-{month}.html"
                try:
                    schedule = pd.read_html(url)[0]
                    schedule.columns = [
                        'date', 'Start (ET)', 'visitor_team', 'visitor_pts',
                        'home_team', 'home_pts', 'Box Score', 'OT',
                        'Attendance', 'LOG', 'Arena', 'Notes'
                    ]
                    schedule = schedule[['date', 'visitor_team', 'visitor_pts', 'home_team', 'home_pts']]
                    schedule['date'] = pd.to_datetime(schedule['date'], errors='coerce')
                    schedule = schedule.dropna(subset=['date'])
                    all_schedules.append(schedule)
                except Exception as e:
                    print(f"Error fetching data for {month}: {e}")

            # Combine all schedules into a single DataFrame
            combined_schedule = pd.concat(all_schedules, ignore_index=True)

            # Save the combined data to a single file
            combined_schedule.to_csv(file_path, index=False)

        return combined_schedule
    

    def _get_standings(self, schedule):
        standings={}
        for index, row in schedule.iterrows():
            home_team = row['home_team']
            visitor_team = row['visitor_team']
            home_pts = row['home_pts']
            visitor_pts = row['visitor_pts']

            if home_team not in standings:
                standings[home_team]={
                    'wins': 0,
                    'losses':0
                }
            if visitor_team not in standings:
                standings[visitor_team]={
                    'wins': 0,
                    'losses':0
                }

            if home_pts > visitor_pts:
                standings[home_team]['wins'] += 1
                standings[visitor_team]['losses'] += 1
            else:
                standings[visitor_team]['wins'] += 1
                standings[home_team]['losses'] += 1
        df = pd.DataFrame.from_dict(standings, orient='index')
        return df.sort_values(by='wins', ascending=False)
    

    def _get_2nd_degree_wins(self, standings_dict, schedule):
        # Initialize a dictionary to store second-degree wins
        second_wins = {team: 0 for team in standings_dict.keys()}

        # Iterate over each row in the schedule
        for index, row in schedule.iterrows():
            # Determine the winner and loser
            if row['home_pts'] > row['visitor_pts']:
                winner = row['home_team']
                loser = row['visitor_team']
            else:
                winner = row['visitor_team']
                loser = row['home_team']

            # Add the loser's wins to the winner's second-degree wins
            second_wins[winner] += standings_dict.get(loser, 0)

        return second_wins
        # Convert the second_wins dictionary to a DataFrame
        return pd.DataFrame.from_dict(
            second_wins, 
            orient='index', 
            columns=['2nd_degree_wins']).reset_index().rename(
                columns={'index': 'team'}
            ).sort_values(by='2nd_degree_wins', ascending=False)
    

if __name__ == "__main__":
    results = []
    for i in range(10,19,1):
        bt_date = datetime(2024,11,i,0,0,0)
        btw = BacktestWins(bt_date)  
        filename = str(bt_date).replace(':','-')
        results.append(btw.backtest_results)
        btw.backtest_results.to_csv('backtest_results/' + filename + '.csv')
    df = pd.concat(results)
    breakpoint()