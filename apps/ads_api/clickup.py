import os
from datetime import datetime, timedelta
from pprint import pprint
from typing import Optional

import requests


def get_teams():
    url = "https://api.clickup.com/api/v2/team"
    headers = {"Authorization": "pk_4756058_ONQ9IB0O5VCG7RJ1PVRKD980GA1A5NU0"}
    response = requests.get(url=url, headers=headers)
    pprint(response.json())


def get_spaces(team_id: int = 2611824):
    url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
    params = {"archived": False}
    headers = {"Authorization": "pk_4756058_ONQ9IB0O5VCG7RJ1PVRKD980GA1A5NU0"}
    response = requests.get(url=url, headers=headers, params=params)
    pprint(response.json())


def get_folders(space_id: int = 10852784):
    url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
    params = {"archived": False}
    headers = {"Authorization": "pk_4756058_ONQ9IB0O5VCG7RJ1PVRKD980GA1A5NU0"}
    response = requests.get(url=url, headers=headers, params=params)
    pprint(response.json())


def get_folderless_lists(space_id: int = 10852784):
    url = f"https://api.clickup.com/api/v2/space/{space_id}/list"
    params = {"archived": False}
    headers = {"Authorization": "pk_4756058_ONQ9IB0O5VCG7RJ1PVRKD980GA1A5NU0"}
    response = requests.get(url=url, headers=headers, params=params)
    pprint(response.json())


def create_click_up_task(
    task_name: str,
    task_description: str = "",
    list_id: int = 158334699,
    priority: int = 2,
    assignees: Optional[list[int]] = None,
    due_date_days: int = 1,
):
    """
    Creates a new task in ClickUp

    Params:
    Priority
    1 is Urgent     2 is High     3 is Normal     4 is Low
    """

    today = datetime.today()
    due_date = today + timedelta(days=due_date_days)
    due_epoch_ms = due_date.timestamp() * 1000

    body = {
        "name": task_name,
        "description": task_description,
        "priority": priority,
        "due_date": due_epoch_ms,
        "due_date_time": False,
    }

    if assignees:
        body["assignees"] = assignees

    # clickup_api_key = os.environ.get("CLICKUP_API_KEY")
    headers = {
        "Authorization": "pk_4756058_ONQ9IB0O5VCG7RJ1PVRKD980GA1A5NU0",
        "Content-Type": "application/json",
    }
    response = requests.post(
        url=f"https://api.clickup.com/api/v2/list/{list_id}/task",
        json=body,
        headers=headers,
    )


# create_click_up_task(task_name="New task for Ivan", assignees=[4756058])
