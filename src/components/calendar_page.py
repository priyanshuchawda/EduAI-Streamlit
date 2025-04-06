import streamlit as st
import calendar
from datetime import datetime, timedelta
from utils.calendar_integration import get_upcoming_events, is_calendar_configured, get_calendar_credentials

def show_calendar_page():
    """Display the main calendar page with a full calendar view"""
    st.markdown("""
        <style>
        .calendar-day {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 10px;
            text-align: center;
            margin: 2px;
            cursor: pointer;
        }
        .calendar-day:hover {
            background-color: #e0e2e6;
        }
        .calendar-header {
            color: #0f52ba;
            text-align: center;
            padding: 5px;
            font-weight: bold;
        }
        .today {
            background-color: #0f52ba;
            color: white;
            border-radius: 10px;
        }
        .event-card {
            background-color: #0d1117;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #0f52ba;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("📅 Calendar")
    
    try:
        # Get credentials only once and store in session state
        if 'calendar_initialized' not in st.session_state:
            get_calendar_credentials()
            st.session_state.calendar_initialized = True
        
        # Initialize the current month/year if not in session state
        if 'current_month' not in st.session_state:
            today = datetime.now()
            st.session_state.current_month = today.month
            st.session_state.current_year = today.year
        
        # Calendar navigation with better styling
        st.markdown("---")
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        
        with nav_col1:
            if st.button("◀️", help="Previous Month", key="prev_month"):
                if st.session_state.current_month > 1:
                    st.session_state.current_month -= 1
                else:
                    st.session_state.current_month = 12
                    st.session_state.current_year -= 1
                    
        with nav_col2:
            st.markdown(f"<h2 style='text-align: center; color: #0f52ba;'>{calendar.month_name[st.session_state.current_month]} {st.session_state.current_year}</h2>", unsafe_allow_html=True)
            
        with nav_col3:
            if st.button("▶️", help="Next Month", key="next_month"):
                if st.session_state.current_month < 12:
                    st.session_state.current_month += 1
                else:
                    st.session_state.current_month = 1
                    st.session_state.current_year += 1

        # Create month calendar
        cal = calendar.monthcalendar(st.session_state.current_year, st.session_state.current_month)
        
        # Get events for the current month
        if not is_calendar_configured():
            st.error("Google Calendar is not configured. Please set up your credentials.")
            return

        start_of_month = datetime(st.session_state.current_year, st.session_state.current_month, 1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Calendar grid with improved styling
        st.markdown("---")
        
        # Create header row with day names
        cols = st.columns(7)
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            with cols[i]:
                st.markdown(f"<div class='calendar-header'>{day}</div>", unsafe_allow_html=True)
        
        # Get today's date for highlighting
        today = datetime.now()
        
        # Display calendar weeks with better styling
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day != 0:
                        date_str = f"{st.session_state.current_year}-{st.session_state.current_month:02d}-{day:02d}"
                        is_today = (day == today.day and 
                                  st.session_state.current_month == today.month and 
                                  st.session_state.current_year == today.year)
                        
                        # Create styled button with conditional today highlighting
                        button_style = "today" if is_today else "calendar-day"
                        if st.button(f"{day}", key=f"day_{date_str}"):
                            st.session_state.selected_date = date_str
                            
        # Display upcoming events section with improved styling
        st.markdown("---")
        events_col1, events_col2 = st.columns([1, 2])
        
        with events_col1:
            st.markdown("<h3 style='color: #0f52ba;'>📅 Upcoming Events</h3>", unsafe_allow_html=True)
        
        with events_col2:
            days_ahead = st.select_slider(
                "Show events for next",
                options=[7, 14, 30, 60, 90],
                value=30,
                help="Select how many days of upcoming events to show"
            )
        
        try:
            events = get_upcoming_events(days=days_ahead)
            if events:
                current_date = None
                for event in events:
                    start_dt = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                    
                    # Add date header if it's a new date
                    if current_date != start_dt.date():
                        current_date = start_dt.date()
                        st.markdown(f"<h4 style='color: #666; margin-top: 20px;'>{current_date.strftime('%A, %B %d')}</h4>", unsafe_allow_html=True)
                    
                    # Display event card
                    st.markdown(f"""
                        <div class='event-card'>
                            <h4 style='margin: 0; color: #0f52ba;'>{event['summary']}</h4>
                            <p style='margin: 5px 0; color: #666;'>🕒 {start_dt.strftime('%I:%M %p')}</p>
                            {f"<p style='margin: 5px 0;'>{event['description']}</p>" if event.get('description') else ""}
                            {f"<p style='margin: 5px 0; color: #666;'>📍 {event['location']}</p>" if event.get('location') else ""}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("🎉 No upcoming events found. Your schedule is clear!")
                
        except Exception as e:
            st.error(f"Error loading calendar events: {str(e)}")
            
    except Exception as e:
        st.error(f"Error loading calendar: {str(e)}")