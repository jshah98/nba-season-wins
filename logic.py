import pandas as pd
import sqlite3
from datetime import datetime

DB_PATH = "nba_data.db"

def get_monthly_schedule(month):
    url = f"https://www.basketball-reference.com/leagues/NBA_2025_games-{month}.html"
    try:
        schedule = pd.read_html(url)[0]
        schedule.columns = ['date', 'Start (ET)', 'visitor_team', 'visitor_pts', 'home_team', 'home_pts', 'Box Score', 'OT', 'Attendance', 'LOG', 'Arena', 'Notes']
        schedule = schedule[['date', 'visitor_team', 'visitor_pts', 'home_team', 'home_pts']]
        schedule['date'] = pd.to_datetime(schedule['date'], errors='coerce')
        schedule = schedule.dropna(subset=['date'])
    except Exception as e:
        print(f"Error fetching data for {month}: {e}")
        return pd.DataFrame()  # Return empty DataFrame if there’s an error
    return schedule

def update_game_counts(game_counts, schedule):
    for _, game in schedule.iterrows():
        visitor, home = game['visitor_team'], game['home_team']
        game_counts[visitor][home] = game_counts[visitor].get(home, 0) + 1
        game_counts[home][visitor] = game_counts[home].get(visitor, 0) + 1
    return game_counts

def calculate_degrees(game_counts, standings):
    team_wins = standings['wins'].to_dict()
    second_degree, third_degree = {}, {}

    for team, opponents in game_counts.items():
        second_degree[team] = sum(team_wins.get(opponent, 0) * count for opponent, count in opponents.items())
        third_degree[team] = sum(team_wins.get(opp2, 0) for opponent in opponents for opp2 in game_counts.get(opponent, {}))
    
    return second_degree, third_degree

def update_standings_db(standings, second_degree, third_degree):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    date_today = datetime.now().strftime("%Y-%m-%d")

    for team, row in standings.iterrows():
        cursor.execute('''
            INSERT INTO team_standings (datestamp, team, wins, losses, second_degree_wins, third_degree_wins)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date_today, team, row['wins'], row['losses'], second_degree[team], third_degree[team]))
    
    conn.commit()
    conn.close()
