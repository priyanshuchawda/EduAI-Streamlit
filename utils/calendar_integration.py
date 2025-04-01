from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Update SCOPES to include all needed permissions
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events.readonly'
]

def is_calendar_configured():
    """Check if calendar credentials are properly configured"""
    credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')
    return os.path.exists(credentials_path)

def get_calendar_credentials():
    """Get or refresh Google Calendar credentials"""
    if not is_calendar_configured():
        raise Exception("Google Calendar credentials not found. Please set up credentials.json first.")
        
    creds = None
    token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'token.pickle')
    
    try:
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, 
                    SCOPES,
                    redirect_uri='http://localhost'
                )
                creds = flow.run_local_server(port=8080)
            
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
                
        return creds
    except Exception as e:
        raise Exception(f"Error with calendar credentials: {str(e)}")

def get_upcoming_events(days=7):
    """Fetch upcoming calendar events"""
    try:
        creds = get_calendar_credentials()
        service = build('calendar', 'v3', credentials=creds)

        now = datetime.utcnow()
        end_date = now + timedelta(days=days)

        events_result = service.events().list(
            calendarId='primary',
            timeMin=now.isoformat() + 'Z',
            timeMax=end_date.isoformat() + 'Z',
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return [format_event(event) for event in events]
        
    except HttpError as e:
        raise Exception(f"Error accessing Google Calendar API: {str(e)}")
    except Exception as e:
        raise Exception(f"Error fetching calendar events: {str(e)}")

def format_event(event):
    """Format a calendar event for display"""
    start = event['start'].get('dateTime', event['start'].get('date'))
    end = event['end'].get('dateTime', event['end'].get('date'))
    
    return {
        'summary': event['summary'],
        'start': start,
        'end': end,
        'description': event.get('description', ''),
        'id': event['id'],
        'location': event.get('location', ''),
        'colorId': event.get('colorId', ''),
        'all_day': 'date' in event['start']
    }