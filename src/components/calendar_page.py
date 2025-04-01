import streamlit as st
import calendar
from datetime import datetime, timedelta
from utils.calendar_integration import get_upcoming_events, is_calendar_configured

def show_calendar_page():
    """Display the main calendar page with a full calendar view"""
    st.title("📅 Calendar")
    
    # Initialize the current month/year if not in session state
    if 'current_month' not in st.session_state:
        today = datetime.now()
        st.session_state.current_month = today.month
        st.session_state.current_year = today.year
    
    # Calendar navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀️ Previous Month"):
            if st.session_state.current_month > 1:
                st.session_state.current_month -= 1
            else:
                st.session_state.current_month = 12
                st.session_state.current_year -= 1
                
    with col2:
        st.header(f"{calendar.month_name[st.session_state.current_month]} {st.session_state.current_year}")
        
    with col3:
        if st.button("Next Month ▶️"):
            if st.session_state.current_month < 12:
                st.session_state.current_month += 1
            else:
                st.session_state.current_month = 1
                st.session_state.current_year += 1

    # Create month calendar
    cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)
    
    # Get events for the current month
    try:
        if not is_calendar_configured():
            st.error("Google Calendar is not configured. Please set up your credentials.json file.")
            st.markdown("""
            To set up Google Calendar integration:
            1. Go to Google Cloud Console
            2. Create a new project or select existing one
            3. Enable Google Calendar API
            4. Create OAuth 2.0 credentials
            5. Download the credentials and save as 'credentials.json' in the project root
            """)
            return

        start_of_month = datetime(st.session_state.current_year, st.session_state.current_month, 1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        days_in_month = (end_of_month - start_of_month).days + 1
        
        events = get_upcoming_events(days=days_in_month)
        events_by_date = {}
        
        for event in events:
            event_date = datetime.fromisoformat(event['start'].replace('Z', '+00:00')).date()
            if event_date not in events_by_date:
                events_by_date[event_date] = []
            events_by_date[event_date].append(event)
        
        # Display calendar grid
        st.write("### 📅 Monthly View")
        
        # Display weekday headers
        cols = st.columns(7)
        for idx, day in enumerate(calendar.day_abbr):
            cols[idx].write(f"**{day}**")
        
        # Display calendar days
        today = datetime.now().date()
        
        for week in cal:
            cols = st.columns(7)
            for idx, day in enumerate(week):
                if day == 0:
                    cols[idx].write("")
                    continue
                    
                date = datetime(st.session_state.current_year, st.session_state.current_month, day).date()
                
                # Highlight current day
                if date == today:
                    day_display = f"**{day}** 📍"
                else:
                    day_display = str(day)
                
                # Display events for this day
                if date in events_by_date:
                    with cols[idx]:
                        st.write(day_display)
                        for event in events_by_date[date]:
                            if event['all_day']:
                                st.info(f"🕒 {event['summary']}")
                            else:
                                time = datetime.fromisoformat(event['start'].replace('Z', '+00:00')).strftime('%I:%M %p')
                                st.info(f"🕒 {time}\n{event['summary']}")
                else:
                    cols[idx].write(day_display)
        
        # List view of upcoming events
        st.write("### 📋 Upcoming Events")
        upcoming_events = get_upcoming_events(days=30)
        
        if not upcoming_events:
            st.info("No upcoming events found for the next 30 days")
        else:
            for event in upcoming_events:
                start_time = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                with st.expander(f"📌 {event['summary']} - {start_time.strftime('%B %d, %Y')}"):
                    if not event['all_day']:
                        st.write(f"**Time:** {start_time.strftime('%I:%M %p')}")
                    else:
                        st.write("**All day event**")
                    if event['location']:
                        st.write(f"**Location:** {event['location']}")
                    if event['description']:
                        st.write("**Details:**")
                        st.write(event['description'])
                        
    except Exception as e:
        st.error(f"Error loading calendar events: {str(e)}")
        st.info("Please make sure your Google Calendar integration is properly configured.")