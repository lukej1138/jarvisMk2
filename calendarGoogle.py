import datetime
import calendar
import os.path
import pytz
from rfc3339 import rfc3339

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIME_ZONE = 'America/Los_Angeles'
def parseEvent(inputText):
  splitUpInput = inputText.split(" ")
  # Name from _ AM/PM to _ AM/PM on DATE to my schedule
  start, end = get_start_end(splitUpInput)
  
  date = None

  for name in list(calendar.month_name):
    if name.lower() in splitUpInput:
      date = splitUpInput[splitUpInput.index(name.lower()): splitUpInput.index(name.lower())+2]
  try:
    text = " ".join(splitUpInput[:splitUpInput.index("break")])
  except:
    return "No Break", None, None, None
  # date = splitUpInput[splitUpInput.index("on")+1: splitUpInput.index("on")+3]
  # start = splitUpInput[splitUpInput.index("from")+1:splitUpInput.index("to")]
  # end = splitUpInput[splitUpInput.index("to")+1:splitUpInput.index("on")]
  # text = " ".join(splitUpInput[:splitUpInput.index("to")])

  if not start or not end or not date or not text:
    return None, None, None, None
  
  return start, end, date, text

def get_start_end(splitUpInput):
  l, r = 0, len(splitUpInput)-1
  start, end = [],[]
  while l < r:
    if(splitUpInput[l] == "a.m." or splitUpInput[l] == 'p.m.'):
      start = splitUpInput[l-1:l+1]
    else:
      l+=1
    
    if(splitUpInput[r] == "a.m." or splitUpInput[r] == 'p.m.'):
      end = splitUpInput[r-1:r+1]
    else:
      r-=1
    
    if start != [] and end != []:
      break
    
  if start == [] or end == []:
    return None, None
  
  return start, end



def get_service_events():
  creds = get_valid_creds()
  try:
    service = build("calendar", "v3", credentials=creds)

    # Get the calendar ID (usually 'primary')
    calendar_id = 'primary'

    # List events (you might need to adjust the time range)
    now = datetime.datetime.now(pytz.timezone(TIME_ZONE)).isoformat()
    events_result = service.events().list(calendarId=calendar_id, timeMin=now, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    return service, events
  except HttpError as error:
    print(f"An error occurred: {error}")
    return None, None

def get_valid_creds():
  creds = None
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file(
        "googlecls.json", SCOPES
    )
    creds = flow.run_local_server(port=8080, access_type="offline", prompt="consent")
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  return creds

def remove(name):
  search_name = " ".join(name).lower()
  try:
    service, events = get_service_events()
    if not service or not events:
      return

    if not events:
      print('No upcoming events found.')
      return

    for event in events:
      if event['summary'].lower() == search_name:  # Match event summary to the name
        event_id = event['id']
        print(f"Deleting event: {event['summary']} ({event_id})")
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        print("Event deleted successfully.")
        return  # Assuming you want to delete the first matching event

    print(f"Event with name '{name}' not found.")

  except HttpError as error:
    print(f"An error occurred: {error}")

def add(start, end, date, name):
  startTime = time_formatted(start, date)
  endTime = time_formatted(end, date)

  event = {
    'summary': name,
    'start': [{
      'dateTime': startTime,
      'timeZone': TIME_ZONE,
    }],
    'end': [{
      'dateTime': endTime,
      'timeZone': TIME_ZONE,
    }],
  }
  service, events = get_service_events()
  event = service.events().insert(calendarId='primary', body=event).execute()
  print("Successfully added item")

def time_formatted(time, date):
  time_items = time
  hour = int(time_items[0][0:time_items[0].index(":")])
  minutes = int(time_items[0][time_items[0].index(":")+1:])
  day= int(date[1][:2])
  indicator = time_items[1]
  if(indicator == "p.m."):
    hour+=12
  
  month = date[0]
  month = month.capitalize()
  month_num = 0
  try:
    month_num = list(calendar.month_name).index(month)
  except ValueError:
    print("Invalid month")
    return
  year = datetime.date.today().year
  final_date = datetime.datetime(year, month_num, day, hour, minutes)
  return rfc3339(final_date, utc=True, use_system_timezone=True)

def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = get_valid_creds()

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.now().isoformat() + "Z"  # 'Z' indicates UTC time
    print("Getting the upcoming 10 events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return
    
    pst_timezone = pytz.timezone(TIME_ZONE)  # Define the PST timezone
    # Prints the start and name of the next 10 events
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      start_utc = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))  # Convert UTC string to datetime object
      start_pst = start_utc.astimezone(pst_timezone)
      print(f"{event['summary']} ({start_pst.strftime('%Y-%m-%d %I:%M %p')})")

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  start, end, date, name = parseEvent("add to my schedule jack's birthday from 8:00 a.m. to 10:00 p.m. on march 31st")
  add(start, end, date, name)
  # start, end, date, text = parseEvent("goon goon gyatt from 7:30 a.m. to 8:00 p.m. on april 30th")
  # add(start, end, date, name=text)
  # main()