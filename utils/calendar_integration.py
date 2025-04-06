from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
from datetime import datetime, timedelta, time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import pytz
from dotenv import load_dotenv
import os
import streamlit as st

# Load environment variables
load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar'
]

# Get calendar ID from environment variables
AI_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')

def get_calendar_credentials():
    """Get Google Calendar credentials using OAuth 2.0 with offline access"""
    # Check if credentials are already in session state
    if 'calendar_creds' in st.session_state and st.session_state.calendar_creds:
        creds = st.session_state.calendar_creds
        if creds.valid:
            return creds
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                st.session_state.calendar_creds = creds
                return creds
            except Exception:
                del st.session_state.calendar_creds
    
    # If no valid credentials in session, check token file
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            if creds and creds.valid:
                st.session_state.calendar_creds = creds
                return creds
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                st.session_state.calendar_creds = creds
                return creds
        except Exception as e:
            if os.path.exists('token.json'):
                os.remove('token.json')
    
    # No valid credentials found, start new OAuth flow
    if 'oauth_state' not in st.session_state:
        st.session_state.oauth_state = os.urandom(16).hex()
    
    client_config = {
        "installed": {
            "client_id": os.getenv('GOOGLE_CALENDAR_CLIENT_ID'),
            "project_id": os.getenv('GOOGLE_CALENDAR_PROJECT_ID'),
            "auth_uri": os.getenv('GOOGLE_CALENDAR_AUTH_URI'),
            "token_uri": os.getenv('GOOGLE_CALENDAR_TOKEN_URI'),
            "auth_provider_x509_cert_url": os.getenv('GOOGLE_CALENDAR_AUTH_PROVIDER_CERT_URL'),
            "client_secret": os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET'),
            "redirect_uris": [os.getenv('GOOGLE_CALENDAR_REDIRECT_URIS')]
        }
    }
    
    try:
        flow = InstalledAppFlow.from_client_config(
            client_config,
            SCOPES,
            state=st.session_state.oauth_state
        )
        creds = flow.run_local_server(
            port=8080,
            access_type='offline',
            state=st.session_state.oauth_state
        )
        
        # Save credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        st.session_state.calendar_creds = creds
        return creds
        
    except Exception as e:
        print(f"Error in authorization flow: {e}")
        raise Exception(f"Failed to get calendar credentials: {str(e)}")

def get_free_time_slots(start_datetime=None, end_datetime=None):
    """Get available time slots for the specified date range"""
    try:
        creds = get_calendar_credentials()
        service = build('calendar', 'v3', credentials=creds)
        
        # Use UTC for all datetime operations
        utc = pytz.UTC
        
        if start_datetime is None:
            # Default to today
            start_datetime = datetime.now(utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif isinstance(start_datetime, datetime) and not start_datetime.tzinfo:
            start_datetime = start_datetime.replace(tzinfo=utc)
            
        if end_datetime is None:
            # Default to end of today
            end_datetime = start_datetime.replace(
                hour=23, minute=59, second=59
            )
        elif isinstance(end_datetime, datetime) and not end_datetime.tzinfo:
            end_datetime = end_datetime.replace(tzinfo=utc)
        
        # Get busy periods from both primary and AI calendars
        body = {
            "timeMin": start_datetime.isoformat(),
            "timeMax": end_datetime.isoformat(),
            "items": [
                {"id": "primary"},
                {"id": AI_CALENDAR_ID}
            ]
        }
        
        eventsResult = service.freebusy().query(body=body).execute()
        
        # Combine busy periods from both calendars
        busy_periods = []
        if 'primary' in eventsResult['calendars']:
            busy_periods.extend(eventsResult['calendars']['primary']['busy'])
        if AI_CALENDAR_ID in eventsResult['calendars']:
            busy_periods.extend(eventsResult['calendars'][AI_CALENDAR_ID]['busy'])
        
        # Convert busy periods to timezone-aware datetime objects
        busy_slots = []
        for period in busy_periods:
            start = datetime.fromisoformat(period['start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
            if not start.tzinfo:
                start = start.replace(tzinfo=utc)
            if not end.tzinfo:
                end = end.replace(tzinfo=utc)
            busy_slots.append((start, end))
        
        # Find free slots (1-hour intervals)
        free_slots = []
        current_time = start_datetime
        
        while current_time < end_datetime:
            slot_end = current_time + timedelta(hours=1)
            is_free = True
            
            # Check if slot overlaps with any busy period
            for busy_start, busy_end in busy_slots:
                if not (slot_end <= busy_start or current_time >= busy_end):
                    is_free = False
                    break
            
            if is_free:
                free_slots.append({
                    'start': current_time.isoformat(),
                    'end': slot_end.isoformat()
                })
            
            current_time += timedelta(hours=1)
        
        return free_slots
        
    except Exception as e:
        raise Exception(f"Error getting free time slots: {str(e)}")

def schedule_lesson(topic: str, start_time: str, end_time: str, subject: str, description: str = ""):
    """Schedule a lesson in the AI-Scheduled-Lessons calendar"""
    try:
        creds = get_calendar_credentials()
        if not creds:
            print("No credentials found - attempting to refresh")
            creds = get_calendar_credentials()
            if not creds:
                raise Exception("Could not obtain calendar credentials")
            
        service = build('calendar', 'v3', credentials=creds)
        
        # Get local timezone
        local_tz = pytz.timezone('Asia/Kolkata')  # Using IST for India
        
        # Parse times and make them timezone-aware
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
        except ValueError as e:
            print(f"Error parsing dates: {e}")
            print(f"start_time: {start_time}, end_time: {end_time}")
            raise Exception("Invalid date format")
        
        if not start_dt.tzinfo:
            start_dt = local_tz.localize(start_dt)
        if not end_dt.tzinfo:
            end_dt = local_tz.localize(end_dt)
        
        print(f"Scheduling event from {start_dt} to {end_dt}")
            
        event = {
            'summary': f"{subject}: {topic}",
            'description': description,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                    {'method': 'email', 'minutes': 60},
                ],
            }
        }

        # First try to find existing AI calendar
        calendar_list = service.calendarList().list().execute()
        ai_calendar = None
        for calendar_item in calendar_list.get('items', []):
            if calendar_item.get('summary') == 'AI-Scheduled-Lessons':
                ai_calendar = calendar_item
                break
                
        # Create AI calendar if it doesn't exist
        if not ai_calendar:
            calendar_body = {
                'summary': 'AI-Scheduled-Lessons',
                'timeZone': 'Asia/Kolkata',
                'description': 'Calendar for AI-scheduled teaching lessons'
            }
            try:
                ai_calendar = service.calendars().insert(body=calendar_body).execute()
                print("Created new AI-Scheduled-Lessons calendar")
            except Exception as e:
                print(f"Error creating calendar: {e}")
                raise e
        
        # Schedule the event
        if ai_calendar:
            print(f"Scheduling in calendar: {ai_calendar['id']}")
            try:
                event = service.events().insert(
                    calendarId=ai_calendar['id'],
                    body=event
                ).execute()
                print(f"Event created: {event.get('htmlLink')}")
                return event['id']
            except Exception as e:
                print(f"Error creating event: {e}")
                raise e
        else:
            raise Exception("Could not find or create AI calendar")
            
    except Exception as e:
        print(f"Error in schedule_lesson: {str(e)}")
        return None

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

def is_calendar_configured():
    """Check if calendar credentials are properly configured"""
    required_vars = [
        'GOOGLE_CALENDAR_CLIENT_ID',
        'GOOGLE_CALENDAR_CLIENT_SECRET',
        'GOOGLE_CALENDAR_PROJECT_ID',
        'GOOGLE_CALENDAR_AUTH_URI',
        'GOOGLE_CALENDAR_TOKEN_URI',
        'GOOGLE_CALENDAR_AUTH_PROVIDER_CERT_URL',
        'GOOGLE_CALENDAR_REDIRECT_URIS',
        'GOOGLE_CALENDAR_ID'
    ]
    return all(os.getenv(var) for var in required_vars)