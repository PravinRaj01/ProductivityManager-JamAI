import os
from dotenv import load_dotenv
import streamlit as st
import requests
import pandas as pd
import datetime

# Load environment variables
load_dotenv()

# Environment Variables
JAMAI_PAT = os.getenv("JAMAI_PAT")
PROJECT_ID = os.getenv("PROJECT_ID")
BASE_URL = os.getenv("BASE_URL")
TASK_TABLE_ID = os.getenv("TASK_TABLE_ID")
PRODUCTIVITY_TIPS_TABLE_ID = os.getenv("PRODUCTIVITY_TIPS_TABLE_ID")

# API Headers
headers = {
    "Authorization": f"Bearer {JAMAI_PAT}",
    "X-PROJECT-ID": PROJECT_ID,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Reserved meal times
MEAL_DETAILS = {
    "Breakfast": {"time": "08:00-09:00", "priority": "Meal"},
    "Lunch": {"time": "13:00-14:00", "priority": "Meal"},
    "Dinner": {"time": "19:00-20:00", "priority": "Meal"}
}

# Function to fetch tasks from JamAI
def fetch_tasks_from_table():
    url = f"{BASE_URL}/api/v1/gen_tables/action/{TASK_TABLE_ID}/rows"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        rows = response.json().get("items", [])
        if rows:
            tasks = [
                {
                    "task_name": row["task_name"]["value"],
                    "priority": row["priority"]["value"],
                    "estimated_time": row["estimated_time"]["value"],
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

# Function to fetch tasks for today
def fetch_tasks_for_today():
    today_date = datetime.date.today().strftime("%Y-%m-%d")
    tasks = fetch_tasks_from_table()
    return [task for task in tasks if task.get("task_date") == today_date]

# Function to fetch motivation from the productivity_tips action table
def fetch_motivation_from_table(task_count):
    url = f"{BASE_URL}/api/v1/gen_tables/action/{PRODUCTIVITY_TIPS_TABLE_ID}/rows"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        rows = response.json().get("items", [])
        if not rows:
            return "No motivational tips available in the database."

        for row in rows:
            table_task_count = row.get("task_count", {}).get("value", "").strip()
            if table_task_count == str(task_count) or (
                "-" in table_task_count and eval(f"{task_count} in range({table_task_count.replace('-', ',')})")
            ):
                return row.get("motivation", {}).get("value", "Motivational text not found.")
        return "No matching motivational tip found."
    else:
        st.error(f"Failed to fetch motivational tips. Error {response.status_code}: {response.text}")
        return "Error fetching motivational tips."

# Function to add a task to JamAI
def add_task_to_table(task_name, priority, estimated_time, task_date):
    url = f"{BASE_URL}/api/v1/gen_tables/action/rows/add"
    payload = {
        "data": [
            {
                "task_name": task_name,
                "priority": priority,
                "estimated_time": estimated_time,
                "task_date": str(task_date)
            }
        ],
        "table_id": TASK_TABLE_ID
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        st.success(f"Task '{task_name}' added successfully!")
    else:
        st.error(f"Failed to add task. Error {response.status_code}: {response.text}")

# Set up page configuration
st.set_page_config(page_title="Productivity Manager", page_icon="📋", layout="wide")

# Sidebar Content
st.sidebar.title("About")
st.sidebar.markdown(
    """
    **Productivity Manager** is a tool designed to:
    - Help you schedule and prioritize tasks.
    - Provide motivational insights based on your daily workload.
    - Use an AI-powered chatbot for productivity advice.
    """
)
st.sidebar.markdown(
    """
    [![GitHub](https://img.shields.io/badge/View%20on-GitHub-181717?style=for-the-badge&logo=github)](https://github.com/PravinRaj01/TaskScheduler-JamAI-.git)
    """,
    unsafe_allow_html=True
)

# Add content to the main page
st.title("🏠 Welcome to Productivity Manager!")
st.markdown(
    """
    **Features:**
    - Add and manage tasks with a smart scheduler.
    - Get motivational quotes to stay productive.
    - Use the chatbot to get productivity advice.
    """
)


# Fetch existing tasks
tasks = fetch_tasks_from_table()

# Task Submission Section
st.subheader("Add a New Task")
with st.form(key="add_task_form"):
    task_name = st.text_input("Task Name", placeholder="E.g., Complete report")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    estimated_time = st.number_input("Estimated Time (hours)", min_value=1, value=1)
    task_date = st.date_input("Task Date", value=datetime.date.today())

    # Check existing meals for the selected date
    existing_meals = {task["task_name"] for task in tasks if task["task_date"] == str(task_date)}
    breakfast_disabled = "Breakfast" in existing_meals
    lunch_disabled = "Lunch" in existing_meals
    dinner_disabled = "Dinner" in existing_meals

    st.markdown("### Include Meals for the Day")
    include_breakfast = st.checkbox("Breakfast (08:00-09:00)", disabled=breakfast_disabled)
    include_lunch = st.checkbox("Lunch (13:00-14:00)", disabled=lunch_disabled)
    include_dinner = st.checkbox("Dinner (19:00-20:00)", disabled=dinner_disabled)

    submit_task = st.form_submit_button("Add Task")

    if submit_task:
        if task_name or include_breakfast or include_lunch or include_dinner:
            if task_name:
                add_task_to_table(task_name, priority, estimated_time, task_date)
            if include_breakfast:
                add_task_to_table("Breakfast", MEAL_DETAILS["Breakfast"]["priority"], 1, task_date)
            if include_lunch:
                add_task_to_table("Lunch", MEAL_DETAILS["Lunch"]["priority"], 1, task_date)
            if include_dinner:
                add_task_to_table("Dinner", MEAL_DETAILS["Dinner"]["priority"], 1, task_date)
            st.success("All selected tasks and meals added successfully!")
        else:
            st.warning("Please provide a task name or select at least one meal.")


# Fetch tasks for today to calculate the count
tasks_today = fetch_tasks_for_today()
# Exclude meals from the task count
tasks_today_non_meals = [
    task for task in tasks_today if task["priority"] != "Meal"
]
tasks_today_count = len(tasks_today_non_meals)

# Display Motivation of the Day
st.subheader("Motivation of the Day")
motivation_of_the_day = fetch_motivation_from_table(tasks_today_count)
st.write(f"💡 {motivation_of_the_day}")
