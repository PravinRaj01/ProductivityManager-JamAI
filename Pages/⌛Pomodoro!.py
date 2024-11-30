import streamlit as st
import time
from plyer import notification

# Set up page configuration
st.set_page_config(page_title="⌛ Pomodoro Timer", page_icon="⏱️", layout="centered")

# Initialize session state variables
if "timer_mode" not in st.session_state:
    st.session_state.timer_mode = "Work"  # Modes: Work, Short Break, Long Break
if "cycle_count" not in st.session_state:
    st.session_state.cycle_count = 0
if "time_left" not in st.session_state:
    st.session_state.time_left = 0  # Initial time left
if "running" not in st.session_state:
    st.session_state.running = False  # Is the timer running?

# Sidebar settings
st.sidebar.title("Pomodoro Settings")
work_duration = st.sidebar.number_input("Work Duration (minutes)", min_value=1, value=25)
short_break_duration = st.sidebar.number_input("Short Break Duration (minutes)", min_value=1, value=5)
long_break_duration = st.sidebar.number_input("Long Break Duration (minutes)", min_value=1, value=15)
cycles = st.sidebar.number_input("Number of Work Cycles Before Long Break", min_value=1, value=4)

# Sidebar control buttons
if st.sidebar.button("Start Timer"):
    if not st.session_state.running:
        st.session_state.running = True
        if st.session_state.time_left == 0:
            st.session_state.timer_mode = "Work"
            st.session_state.time_left = work_duration * 60

if st.sidebar.button("Pause Timer"):
    st.session_state.running = False

if st.sidebar.button("Reset Timer"):
    st.session_state.running = False
    st.session_state.timer_mode = "Work"
    st.session_state.cycle_count = 0
    st.session_state.time_left = work_duration * 60

# Function for desktop notifications
def send_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        app_name="Pomodoro Timer",
        timeout=5  # Notification duration in seconds
    )

# Timer update logic
def update_timer():
    while st.session_state.time_left > 0 and st.session_state.running:
        mins, secs = divmod(st.session_state.time_left, 60)
        ph.metric(f"{st.session_state.timer_mode} Time Remaining", f"{mins:02d}:{secs:02d}")
        progress_bar.progress(calculate_progress())
        time.sleep(1)
        st.session_state.time_left -= 1

    # Transition to the next phase
    if st.session_state.time_left == 0 and st.session_state.running:
        if st.session_state.timer_mode == "Work":
            st.session_state.cycle_count += 1
            st.success("Work session complete! Time for a break.")
            send_notification("Pomodoro Timer", "Work session complete! Time for a break.")
            if st.session_state.cycle_count % cycles == 0:
                st.session_state.timer_mode = "Long Break"
                st.session_state.time_left = long_break_duration * 60
                st.success("Starting Long Break!")
                send_notification("Pomodoro Timer", "Starting Long Break!")
            elif st.session_state.cycle_count < cycles:
                st.session_state.timer_mode = "Short Break"
                st.session_state.time_left = short_break_duration * 60
                st.success("Starting Short Break!")
                send_notification("Pomodoro Timer", "Starting Short Break!")
            else:
                st.session_state.running = False  # End after the last work cycle
                st.session_state.timer_mode = "Completed"
                st.balloons()
                st.success("Pomodoro session complete! Great job!")
                send_notification("Pomodoro Timer", "Pomodoro session complete! Great job!")
        elif st.session_state.timer_mode in ["Short Break", "Long Break"]:
            st.session_state.timer_mode = "Work"
            st.session_state.time_left = work_duration * 60
            st.success("Break over! Back to work.")
            send_notification("Pomodoro Timer", "Break over! Back to work.")

# Progress bar calculation
def calculate_progress():
    total_time = 0
    if st.session_state.timer_mode == "Work":
        total_time = work_duration * 60
    elif st.session_state.timer_mode == "Short Break":
        total_time = short_break_duration * 60
    elif st.session_state.timer_mode == "Long Break":
        total_time = long_break_duration * 60
    return (total_time - st.session_state.time_left) / total_time

# Main display
st.title("⏱️ Pomodoro Timer")
st.markdown("Enhance focus and productivity using the Pomodoro technique!")

# Timer display and progress
ph = st.empty()
progress_bar = st.progress(0)

# Timer and control logic
if st.session_state.running:
    update_timer()

# Display current state
st.markdown("---")
st.subheader("Pomodoro Progress")
st.write(f"**Current Cycle:** {st.session_state.cycle_count}")
st.write(f"**Current Mode:** {st.session_state.timer_mode}")

# Show timer progress
if st.session_state.time_left > 0:
    mins, secs = divmod(st.session_state.time_left, 60)
    ph.metric(f"{st.session_state.timer_mode} Time Remaining", f"{mins:02d}:{secs:02d}")
    progress_bar.progress(calculate_progress())
else:
    ph.metric("Timer", "00:00")
    progress_bar.progress(0)
