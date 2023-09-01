import json
import os
import requests
import time
from datetime import datetime
from datetime import timedelta

# Site codes can be found here: https://kontests.net/api
SITES = ['codeforces', 'at_coder', 'code_chef', 'codeforces_gym', 'top_coder', 'cs_academy', 'hacker_rank', 'hacker_earth',
         'leet_code']
SLEEP_TIME = 10800

# Notion Internal Integration Token
token = os.getenv("TOKEN")

# Notion Dataset/Database ID
database_id = os.getenv("DATASET_ID")


def clear_data():
    """Deletes all rows of the table."""
    global database_id
    url = f'https://api.notion.com/v1/databases/{database_id}/query'
    r = requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-02-22"
    })
    result_dict = r.json()
    rows = result_dict['results']
    for row in rows:
        url = f'https://api.notion.com/v1/pages/{row["id"]}'

        payload = {
            'archived': True,
            'properties': {
                'Start - End': {
                    'id': '%3C%5Bd%5E',
                    'type': 'date',
                    'date': None
                },
                'Duration': {
                    'id': '_Fsx',
                    'type': 'rich_text',
                    'rich_text': []
                },
                'Name': {
                    'id': 'title',
                    'type': 'title',
                    'title': []
                }
            }
        }

        r = requests.patch(url, headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2021-08-16",
            "Content-Type": "application/json"
        }, data=json.dumps(payload))

        time.sleep(1)


def add_contest(name, link, start, end, duration):
    """Adds a new row to the table containing the data passed as arguments."""
    global database_id
    url = f'https://api.notion.com/v1/pages'

    payload = {
        "parent": {
            "database_id": database_id
        },
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": name,
                            "link": {
                                "url": link,
                            }
                        }
                    }
                ]
            },
            "Start - End": {
                "date": {
                    "start": start,
                    "end": end
                }
            },
            "Duration": {
                "rich_text": [
                    {
                        "text": {
                            "content": duration
                        }
                    }
                ]
            }
        }
    }

    r = requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-02-22",
        "Content-Type": "application/json"
    }, data=json.dumps(payload))

    return r


def enter_data():
    """Fetches all contests data of the sites specified in SITES and parses the data into add_contest()."""
    for site in SITES:
        for i in requests.get(f'https://kontests.net/api/v1/{site}').json():
            if i['in_24_hours'] == 'Yes' or i['status'] == 'CODING':
                try:
                    i['start_time'] = datetime.strptime(i['start_time'][:19], '%Y-%m-%d %H:%M:%S') \
                                      + timedelta(minutes=30, hours=5)

                    i['end_time'] = datetime.strptime(i['end_time'][:19], '%Y-%m-%d %H:%M:%S') \
                                    + timedelta(minutes=30, hours=5)
                except ValueError:
                    i['start_time'] = datetime.strptime(i['start_time'][:19], '%Y-%m-%dT%H:%M:%S') \
                                      + timedelta(minutes=30, hours=5)

                    i['end_time'] = datetime.strptime(i['end_time'][:19], '%Y-%m-%dT%H:%M:%S') \
                                    + timedelta(minutes=30, hours=5)

                i['start_time'] = i['start_time'].strftime('%Y-%m-%dT%H:%M:%S.000+05:30')
                i['end_time'] = i['end_time'].strftime('%Y-%m-%dT%H:%M:%S.000+05:30')

                i['duration'] = float(i['duration']) / 3600
                if i['duration'] > 1:
                    days = int(i['duration'] // 24)
                    if days > 0:
                        hours = ''
                        if int(i["duration"] % 24) > 0:
                            hours = f'{int(i["duration"] % 24)} hour{"s" if int(i["duration"] % 24) > 1 else ""}'
                        i['duration'] = f'{days} day{"s" if days > 1 else ""} ' + hours
                    else:
                        i['duration'] = f'{int(i["duration"])} hour{"s" if i["duration"] % 24 > 1 else ""}'
                i['name'] = " ".join([i.capitalize() for i in site.split("_")]) + ": " + i['name']
                add_contest(i['name'], i['url'], i['start_time'], i['end_time'], i['duration'])


while True:
    clear_data()
    enter_data()
    time.sleep(SLEEP_TIME)
