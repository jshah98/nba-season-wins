import sqlite3
import pickle
import os
from datetime import datetime
import pandas as pd
from logic import get_monthly_schedule

# Database and file paths
DB_PATH = "nba_data.db"
GAME_DICT_PATH = "game_counts.pkl"
TEAM_LIST_PATH = "team_list.pkl"

# List of all NBA team names
team_list = [
    'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets',
    'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets',
    'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers',
    'Los Angeles Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat',
    'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans', 'New York Knicks',
    'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns',
    'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors',
    'Utah Jazz', 'Washington Wizards'
]

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS games_schedule (
        date TEXT,
        visitor_team TEXT,
        visitor_pts INTEGER,
        home_team TEXT,
        home_pts INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS team_standings (
        datestamp TEXT,
        team TEXT,
        wins INTEGER,
        losses INTEGER,
        second_degree_wins INTEGER,
        third_degree_wins INTEGER
    )
    ''')

    conn.commit()
    conn.close()

def initialize_pickle_files():
    game_counts = {team: {} for team in team_list}
    with open(GAME_DICT_PATH, "wb") as f:
        pickle.dump(game_counts, f)
    
    with open(TEAM_LIST_PATH, "wb") as f:
        pickle.dump(team_list, f)

def load_initial_data():
    conn = sqlite3.connect(DB_PATH)
    current_month = datetime.now().month

    # Loop through months from October (10) to current month
    for month in range(10, current_month + 1):
        month_name = datetime(2024, month, 1).strftime("%B").lower()
        schedule = get_monthly_schedule(month_name)
        
        # Insert data into the games_schedule table
        schedule.to_sql("games_schedule", conn, if_exists="append", index=False)

    conn.close()

def populate_initial_standings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    start_season_date = "2024-10-01"

    # Insert each team with 0 wins, 0 losses, and 0 for degree wins
    for team in team_list:
        cursor.execute('''
            INSERT INTO team_standings (datestamp, team, wins, losses, second_degree_wins, third_degree_wins)
            VALUES (?, ?, 0, 0, 0, 0)
        ''', (start_season_date, team))
        print(f"Inserted {team} into team_standings with initial values.")  # Debug output

    conn.commit()
    conn.close()
    print("Initial standings data inserted successfully.")


def teardown():
    """Delete all setup files and database."""
    # Delete database file
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Deleted database file: {DB_PATH}")

    # Delete pickle files
    if os.path.exists(GAME_DICT_PATH):
        os.remove(GAME_DICT_PATH)
        print(f"Deleted pickle file: {GAME_DICT_PATH}")

    if os.path.exists(TEAM_LIST_PATH):
        os.remove(TEAM_LIST_PATH)
        print(f"Deleted pickle file: {TEAM_LIST_PATH}")

    print("Teardown complete.")


def run_setup():
    create_database()
    initialize_pickle_files()
    load_initial_data()
    populate_initial_standings()  # Populate the team_standings table with initial data
    print("Setup complete.")
