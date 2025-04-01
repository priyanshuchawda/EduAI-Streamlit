import streamlit as st
from datetime import datetime
from utils.calendar_integration import get_upcoming_events

def show_calendar_sidebar():
    """Display calendar events in the sidebar"""
    with st.sidebar:
        st.subheader("📅 Upcoming Events")
        
        try:
            events = get_upcoming_events()
            
            if not events:
                st.info("No upcoming events found")
            else:
                for event in events:
                    start_time = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                    
                    with st.expander(f"📌 {event['summary']}"):
                        st.write(f"**Date:** {start_time.strftime('%B %d, %Y')}")
                        st.write(f"**Time:** {start_time.strftime('%I:%M %p')}")
                        if event['description']:
                            st.write("**Details:**")
                            st.write(event['description'])
                
        except Exception as e:
            st.error(f"Could not load calendar events. Please check your Google Calendar integration.")