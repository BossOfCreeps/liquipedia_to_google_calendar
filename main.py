import os
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()
CALENDAR_ID = os.getenv("CALENDAR_ID")
URLS = os.getenv("URLS").split(",")

service = build(
    "calendar",
    "v3",
    credentials=InstalledAppFlow.from_client_secrets_file(
        "credentials.json", ["https://www.googleapis.com/auth/calendar"]
    ).run_local_server(port=0),
).events()


def parse_liquidpedia():
    result = []
    for url in URLS:
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        for match in soup.find_all("div", class_="brkts-popup brkts-match-info-popup"):
            teams, team_1, team_2 = match.find_all("span", class_="name"), "команда", "команда"
            if len(teams) == 1:
                team_1 = teams[0].text
            elif len(teams) == 2:
                team_1, team_2 = (t.text for t in teams)

            datetime_obj = match.find("span", class_="timer-object")
            if datetime_obj is None:
                continue
            datetime_str = datetime_obj.text
            date = None

            for tz, hour in {"CEST": -2, "EEST": -3, "SGT": -8, "CET": -1, "EST": 5, "AST": -3, "PDT": 7}.items():
                if tz in datetime_str:
                    date = datetime.strptime(datetime_str, f"%B %d, %Y - %H:%M {tz}") + timedelta(hours=hour)
                    break

            if date is None:
                raise Exception(datetime_str)

            data = {
                "summary": f"{team_1} vs {team_2}",
                "start": {"dateTime": date.isoformat(), "timeZone": "utc"},
                "end": {"dateTime": (date + timedelta(hours=2)).isoformat(), "timeZone": "utc"},
                "reminders": {
                    "useDefault": False,
                    "overrides": [{"method": "popup", "minutes": 5}],
                },
            }
            result.append([date, f"{team_1} vs {team_2}", data])

    return result


if __name__ == "__main__":
    exists = []
    for e in service.list(calendarId=CALENDAR_ID).execute().get("items", []):
        if "команда" in e["summary"]:
            service.delete(calendarId=CALENDAR_ID, eventId=e["id"]).execute()
        else:
            if "dateTime" in e["start"]:
                event_date = datetime.fromisoformat(e["start"]["dateTime"]).replace(tzinfo=None) - timedelta(hours=7)
                exists.append([event_date, e["summary"]])
    for event_date, summary, event_data in parse_liquidpedia():
        if [event_date, summary] not in exists and event_date > datetime.now():
            created_event = service.insert(calendarId=CALENDAR_ID, body=event_data).execute()
            print(f"{event_data['summary']} created: {created_event.get('htmlLink')}")
