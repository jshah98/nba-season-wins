import streamlit as st
from datetime import datetime
from main import check_setup, run_setup, daily_update, load_latest_standings
from setup import teardown

def main():
    st.title("NBA Standings Tracker")

    # Check if setup is complete
    setup_complete = check_setup()

    # Load and display the latest standings
    st.header("Latest NBA Standings")
    if setup_complete:
        standings = load_latest_standings()
        if not standings.empty:
            # Display standings sorted by wins in descending order
            st.dataframe(standings)

            # Check if today's update is already done
            today_date = datetime.now().strftime("%Y-%m-%d")
            latest_update_date = standings['datestamp'].max()

            # Show update button only if the latest update isn't from today
            if latest_update_date == today_date:
                st.info("Data is already up-to-date.")
                st.button("Update Data", disabled=True)
            else:
                if st.button("Update Data"):
                    daily_update()
                    st.success("Data update complete! Please reload the app to see the latest standings.")
        else:
            st.write("No standings data available. Please initialize or update the data.")
    else:
        st.warning("Setup is incomplete. Click the button below to initialize data.")
        if st.button("Initialize Data"):
            run_setup()
            st.success("Setup complete. Reload the app to view the latest data.")
            
    # Teardown section
    st.sidebar.header("Admin")
    if st.sidebar.button("Teardown"):
        teardown()
        st.sidebar.success("Teardown complete. All setup files have been deleted.")

if __name__ == "__main__":
    main()
