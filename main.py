import os
from datetime import datetime
import pickle
import sqlite3
import pandas as pd
from setup import run_setup
from logic import get_monthly_schedule, update_game_counts, calculate_degrees, update_standings_db

# File paths
DB_PATH = "nba_data.db"
GAME_DICT_PATH = "game_counts.pkl"

def check_setup():
    """Check if setup is complete by verifying if database and pickle files exist."""
    return os.path.exists(DB_PATH) and os.path.exists(GAME_DICT_PATH)


def get_team_standings():
    url = "https://www.basketball-reference.com/leagues/NBA_2025_standings.html"
    tables = pd.read_html(url)
    
    # Extract Eastern and Western Conference standings
    eastern_conf = tables[0][['Eastern Conference', 'W', 'L']]
    western_conf = tables[1][['Western Conference', 'W', 'L']]
    
    # Rename columns
    eastern_conf.columns = ['team', 'wins', 'losses']
    western_conf.columns = ['team', 'wins', 'losses']
    
    # Combine tables and clean team names
    standings = pd.concat([eastern_conf, western_conf], ignore_index=True)
    standings['team'] = standings['team'].str.replace(r'\*|\(\d+\)', '', regex=True).str.strip()
    standings.set_index('team', inplace=True)
    
    return standings


def daily_update():
    """Perform daily data update by fetching latest schedule and updating game counts and standings."""
    conn = sqlite3.connect(DB_PATH)
    current_month = datetime.now().strftime("%B").lower()
    
    # Load the current schedule
    schedule = get_monthly_schedule(current_month)
    
    # Load the existing game counts from the pickle file
    with open(GAME_DICT_PATH, "rb") as f:
        game_counts = pickle.load(f)
    
    # Update game counts
    game_counts = update_game_counts(game_counts, schedule)
    
    # Save updated game counts back to pickle
    with open(GAME_DICT_PATH, "wb") as f:
        pickle.dump(game_counts, f)
    
    # Get updated team standings
    standings = get_team_standings()
    # Calculate 2nd and 3rd degree wins
    second_degree, third_degree = calculate_degrees(game_counts, standings)
    
    # Update standings database
    update_standings_db(standings, second_degree, third_degree)
    
    conn.close()
    print("Daily update complete.")

def load_latest_standings():
    """Load the latest team standings sorted by wins."""
    conn = sqlite3.connect(DB_PATH)
    standings = pd.read_sql("SELECT * FROM team_standings ORDER BY datestamp DESC", conn)
    conn.close()
    
    # Sort by wins in descending order and remove duplicates to get the latest standings
    standings = standings.drop_duplicates(subset=['team'], keep='first')
    standings = standings.sort_values(by='wins', ascending=False).reset_index(drop=True)
    
    return standings




if __name__ == "__main__":
    if not check_setup():
        print("Running initial setup...")
        run_setup()
    else:
        print("Running daily update...")
        daily_update()
