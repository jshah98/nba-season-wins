import streamlit as st
from datetime import datetime, date
import pandas as pd
import os


def get_months_from_october():
    months = [
        "october", "november", "december",
        "january", "february", "march",
        "april", "may", "june",
        "july", "august", "september"
    ]
    current_month = datetime.now().strftime("%B").lower()


    return months[:months.index(current_month)+1]


def get_combined_schedule(months, from_url=False, file_path="combined_schedule.csv"):
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


def get_team_standings(from_url=False, file_path="team_standings.csv"):
    # Check if the data file exists and if we should not read from the URL
    if not from_url and os.path.exists(file_path):
        # Load the saved data
        standings = pd.read_csv(file_path, index_col='team')
    else:
        # Fetch the data from the URL
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
        
        # Save the data to a file
        standings.to_csv(file_path)

    # Return the standings sorted by wins
    return standings.sort_values(by='wins', ascending=False)

def get_2nd_degree_wins(standings_dict, schedule):
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

    # Convert the second_wins dictionary to a DataFrame
    return pd.DataFrame.from_dict(
        second_wins, 
        orient='index', 
        columns=['2nd_degree_wins']).reset_index().rename(
            columns={'index': 'team'}
        ).sort_values(by='2nd_degree_wins', ascending=False)

def main():
    months = get_months_from_october()
    st.title("NBA Standings and Schedule Tracker")
    
    # Add a button to update the data
    if st.button("Update Data"):
        # Load and display the latest standings from the URL
        standings = get_team_standings(from_url=True)
        schedule = get_combined_schedule(months, from_url=True)
        st.success("Data updated successfully!")
    else:
        # Load the saved data
        standings = get_team_standings()
        schedule = get_combined_schedule(months)
    
    team_wins_dict = standings['wins'].to_dict()
    best_teams = get_2nd_degree_wins(team_wins_dict, schedule)
    new_standings = best_teams.merge(standings, how='left', on='team')

    update_date = schedule[(schedule['visitor_pts'].notna()) & (schedule['home_pts'].notna())]['date'].max()
    st.header(f"NBA - 2nd Degree Wins - {update_date}")
    st.dataframe(new_standings)

    st.header("Latest NBA Standings")
    st.dataframe(standings)

    st.header("NBA Schedule")
    st.dataframe(schedule)

if __name__ == "__main__":
    main()
