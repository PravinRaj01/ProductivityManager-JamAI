import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from scheduler import add_and_schedule_tasks
import requests
from st_aggrid import AgGrid, GridOptionsBuilder
import datetime

# Load environment variables
load_dotenv()

# Environment Variables
JAMAI_PAT = os.getenv("JAMAI_PAT")
PROJECT_ID = os.getenv("PROJECT_ID")
BASE_URL = os.getenv("BASE_URL")
TASK_TABLE_ID = os.getenv("TASK_TABLE_ID")


# API Headers
headers = {
    "Authorization": f"Bearer {JAMAI_PAT}",
    "X-PROJECT-ID": PROJECT_ID,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Function to fetch tasks from JamAI
def fetch_tasks_from_table():
    """Fetch tasks from JamAI."""
    url = f"{BASE_URL}/api/v1/gen_tables/action/{TASK_TABLE_ID}/rows"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        rows = response.json().get("items", [])
        if rows:
            tasks = [
                {
                    "id": row["ID"],
                    "task_name": row["task_name"]["value"],
                    "priority": row["priority"]["value"],
                    "estimated_time": row["estimated_time"]["value"],
                    "scheduled_time": row.get("scheduled_time", {}).get("value", "Not Scheduled"),
                    "task_date": row["task_date"]["value"]
                }
                for row in rows
            ]
            return tasks
        else:
            return []
    else:
        st.error(f"Failed to fetch tasks. Error {response.status_code}: {response.text}")
        return []

# Function to delete tasks by ID
def delete_tasks_by_ids(task_ids):
    """Delete tasks by their IDs."""
    url = f"{BASE_URL}/api/v1/gen_tables/action/rows/delete"
    payload = {"table_id": TASK_TABLE_ID, "row_ids": task_ids}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, response.text

# Initialize session state for tasks
if "fetched_tasks" not in st.session_state:
    st.session_state.fetched_tasks = fetch_tasks_from_table()

def refresh_tasks():
    """Refresh tasks and update session state."""
    st.session_state.fetched_tasks = fetch_tasks_from_table()

# Page Content
st.title("📅 My Schedule")
st.markdown("Your scheduled tasks are fetched and arranged below.")

# Refresh tasks when "Refresh Schedule" is clicked
if st.button("🔄 Refresh Schedule"):
    refresh_tasks()

# Fetch tasks from session state
fetched_tasks = st.session_state.fetched_tasks

# Dropdown to select date for viewing tasks
if fetched_tasks:
    dates_available = sorted({task["task_date"] for task in fetched_tasks})
    selected_date = st.selectbox(
        "Select Date to View Schedule",
        options=["All Dates"] + ["Today"] + dates_available,
        index=1  # Default to "Today"
    )
    if selected_date == "Today":
        selected_date = datetime.date.today().strftime("%Y-%m-%d")

    if selected_date != "All Dates":
        tasks_to_display = [task for task in fetched_tasks if task["task_date"] == selected_date]
    else:
        tasks_to_display = fetched_tasks

    if tasks_to_display:
        tasks_df = pd.DataFrame(tasks_to_display)

        # Sort tasks by `task_date` and `scheduled_time`
        tasks_df.sort_values(by=["task_date", "scheduled_time"], inplace=True)

        # Add Emojis for Priorities
        tasks_df["priority"] = tasks_df["priority"].replace(
            {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low", "Meal": "🍴 Meal"}
        )

        # Display the table using AgGrid
        gb = GridOptionsBuilder.from_dataframe(tasks_df.drop(columns=["id"], errors="ignore"))
        gb.configure_default_column(editable=False, sortable=True, filterable=True)
        gb.configure_pagination(paginationAutoPageSize=True)
        grid_options = gb.build()

        st.write(f"### Scheduled Tasks for {selected_date}")
        AgGrid(
            tasks_df.drop(columns=["id"], errors="ignore"),
            gridOptions=grid_options,
            height=500,
            theme="material"
        )

        # Add a "Download Schedule" Button
        csv = tasks_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Schedule as CSV",
            data=csv,
            file_name=f"scheduled_tasks_{selected_date}.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"No tasks found for {selected_date}!")
else:
    st.warning("No tasks found!")

# Task Management Section
st.markdown("---")
st.header("🛠️ Task Management")

# --- Delete Specific Task Section ---
st.subheader("❌ Delete Specific Task")
if fetched_tasks:
    dates_available = sorted({task["task_date"] for task in fetched_tasks})
    selected_date = st.selectbox(
        "Select Date to View Tasks for Deletion",
        options=["Today"] + dates_available,
        index=0
    )
    if selected_date == "Today":
        selected_date = datetime.date.today().strftime("%Y-%m-%d")

    tasks_for_date = [task for task in fetched_tasks if task["task_date"] == selected_date]

    if tasks_for_date:
        task_names = [task["task_name"] for task in tasks_for_date]
        selected_task_name = st.selectbox("Select Task to Delete", options=task_names)
        if st.button(f"Delete Task: {selected_task_name}"):
            task_to_delete = next(task for task in tasks_for_date if task["task_name"] == selected_task_name)
            status_code, response_text = delete_tasks_by_ids([task_to_delete["id"]])
            if status_code == 200:
                st.success(f"Task '{selected_task_name}' removed successfully!")
                refresh_tasks()
            else:
                st.error(f"Failed to delete task. Error {status_code}: {response_text}")
    else:
        st.warning(f"No tasks found for {selected_date}.")
else:
    st.warning("No tasks available for deletion.")

# --- Delete All Tasks Section ---
st.subheader("❌ Delete All Tasks")
if fetched_tasks:
    dates_available = sorted({task["task_date"] for task in fetched_tasks})
    selected_delete_all_date = st.selectbox(
        "Select Date to Delete All Tasks",
        options=["All Days", "Today"] + dates_available,
        index=0
    )
    if selected_delete_all_date == "Today":
        selected_delete_all_date = datetime.date.today().strftime("%Y-%m-%d")

    if selected_delete_all_date == "All Days":
        if st.button("Delete All Tasks for All Days"):
            task_ids = [task["id"] for task in fetched_tasks]
            status_code, response_text = delete_tasks_by_ids(task_ids)
            if status_code == 200:
                st.success("All tasks for all days removed successfully!")
                refresh_tasks()
            else:
                st.error(f"Failed to delete tasks. Error {status_code}: {response_text}")
    else:
        tasks_for_delete_date = [task for task in fetched_tasks if task["task_date"] == selected_delete_all_date]
        if tasks_for_delete_date:
            if st.button(f"Delete All Tasks for {selected_delete_all_date}"):
                task_ids = [task["id"] for task in tasks_for_delete_date]
                status_code, response_text = delete_tasks_by_ids(task_ids)
                if status_code == 200:
                    st.success(f"All tasks for {selected_delete_all_date} removed successfully!")
                    refresh_tasks()
                else:
                    st.error(f"Failed to delete tasks. Error {status_code}: {response_text}")
        else:
            st.warning(f"No tasks found for {selected_delete_all_date}.")
else:
    st.warning("No tasks available for deletion.")
