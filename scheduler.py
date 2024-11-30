from datetime import datetime, timedelta

# Reserved meal times
MEAL_TIMES = {
    "Breakfast": ("08:00", "09:00"),
    "Lunch": ("13:00", "14:00"),
    "Dinner": ("19:00", "20:00"),
}

def calculate_schedule(tasks):
    """
    Schedule tasks sequentially, considering meal times and priorities.
    """
    # Sort tasks by priority (High > Medium > Low)
    priority_order = {"High": 1, "Medium": 2, "Low": 3}
    valid_tasks = sorted(
        tasks,
        key=lambda x: (priority_order.get(x["priority"], 999), x.get("task_name", "")),
    )

    # Initialize start time and scheduled tasks
    start_time = datetime.strptime("08:00", "%H:%M")
    end_of_day = datetime.strptime("23:00", "%H:%M")
    scheduled_tasks = []

    # Helper function to check if the current time is during a meal
    def is_during_meal(time):
        for meal, (meal_start, meal_end) in MEAL_TIMES.items():
            meal_start_time = datetime.strptime(meal_start, "%H:%M")
            meal_end_time = datetime.strptime(meal_end, "%H:%M")
            if meal_start_time <= time < meal_end_time:
                return meal, meal_start_time, meal_end_time
        return None, None, None

    # Iterate through the tasks
    for task in valid_tasks:
        while True:
            # Check if the current start time is during a meal
            meal, meal_start_time, meal_end_time = is_during_meal(start_time)
            if meal:
                # Add the meal task and skip the time
                scheduled_tasks.append({
                    "task_name": meal,
                    "priority": "Meal",
                    "estimated_time": 1,
                    "scheduled_time": f"{meal_start_time.strftime('%H:%M')}-{meal_end_time.strftime('%H:%M')}",
                })
                start_time = meal_end_time  # Move past the meal
            else:
                break

        # Calculate the task's end time
        task_end_time = start_time + timedelta(hours=task["estimated_time"])
        if task_end_time > end_of_day:
            # Stop scheduling if beyond the end of the day
            break

        # Assign scheduled time to the task
        task["scheduled_time"] = f"{start_time.strftime('%H:%M')}-{task_end_time.strftime('%H:%M')}"
        scheduled_tasks.append(task)

        # Update start time for the next task
        start_time = task_end_time

    return scheduled_tasks


def add_and_schedule_tasks(tasks, meals=None):
    """
    Arrange and schedule tasks, automatically including fixed meal times.
    """
    if not tasks:
        return []

    # Include meals as additional tasks
    if meals:
        for meal in meals:
            if meal in MEAL_TIMES:
                start, end = MEAL_TIMES[meal]
                tasks.append({
                    "task_name": meal,
                    "priority": "Meal",
                    "estimated_time": 1,
                    "scheduled_time": f"{start}-{end}",
                })

    # Schedule tasks
    return calculate_schedule(tasks)
