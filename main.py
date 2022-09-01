from datetime import datetime, timedelta

import requests as requests
from bs4 import BeautifulSoup
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

URLS = ["https://liquipedia.net/dota2/The_International/2022/Eastern_Europe"]

service = build(
    'calendar', 'v3',
    credentials=InstalledAppFlow
    .from_client_secrets_file('credentials.json', ['https://www.googleapis.com/auth/calendar'])
    .run_local_server(port=0)
)

for url in URLS:
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    for match in soup.find_all("div", class_="brkts-popup brkts-match-info-popup"):
        if len(match.find_all("span", class_="name")) == 2:
            team_1, team_2 = (team.text for team in match.find_all("span", class_="name"))
        else:
            team_1, team_2 = "команда", "команда"

        date = datetime.strptime(match.find("span", class_="timer-object").text, '%B %d, %Y - %H:%M UTC')
        event_data = {
            'summary': f"{team_1} vs {team_2}",
            'start': {'dateTime': date.isoformat(), 'timeZone': 'utc'},
            'end': {'dateTime': (date + timedelta(hours=2)).isoformat(), 'timeZone': 'utc'},
            'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 5}], },
        }

        event = service.events().insert(
            calendarId="pr1ej8epdlgiqviuaptfq7aupc@group.calendar.google.com",
            body=event_data
        ).execute()
        print(f"{team_1} vs {team_2} created: {event.get('htmlLink')}")
