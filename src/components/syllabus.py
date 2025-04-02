import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.sheets_integration import get_syllabus_sheet, save_syllabus_topic, get_syllabus_data
from utils.topic_suggestion import get_topic_suggestion
from utils.calendar_integration import get_free_time_slots
from utils.ai_scheduler import suggest_lesson_schedule, schedule_suggested_lesson

def show_syllabus_page():
    """Display the syllabus management interface"""
    # Initialize session states
    if "syllabus_data" not in st.session_state:
        st.session_state.syllabus_data = get_syllabus_data()
    if "current_suggestion" not in st.session_state:
        st.session_state.current_suggestion = None
    if "editing_suggestion" not in st.session_state:
        st.session_state.editing_suggestion = False
    if "manual_scheduling" not in st.session_state:
        st.session_state.manual_scheduling = False
    if "selected_dates" not in st.session_state:
        st.session_state.selected_dates = []
    if "recurring_schedule" not in st.session_state:
        st.session_state.recurring_schedule = {}
    if "schedule_suggestions" not in st.session_state:
        st.session_state.schedule_suggestions = []
    if "scheduled_classes" not in st.session_state:
        st.session_state.scheduled_classes = set()

    st.title("📚 Syllabus Management")
    
    # Create tabs
    syllabus_tab, scheduling_tab = st.tabs(["Syllabus Management", "AI Scheduling"])
    
    # Syllabus Management Tab
    with syllabus_tab:
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.subheader("Add New Topic")
            with st.form("syllabus_form"):
                topic = st.text_input("Topic Name", placeholder="e.g. Introduction to Calculus")
                duration = st.number_input("Duration (in days)", min_value=1, value=1)
                subject = st.selectbox("Subject", ["Mathematics", "Physics", "Chemistry", "Biology", "English"])
                planned_date = st.date_input("Planned Start Date", min_value=datetime.now().date())
                
                submitted = st.form_submit_button("Add Topic")
                if submitted and topic:
                    save_syllabus_topic(topic, duration, subject, planned_date)
                    st.session_state.syllabus_data = get_syllabus_data()
                    st.success(f"Added topic: {topic}")
        
        with col2:
            st.subheader("Current Syllabus")
            if st.session_state.syllabus_data.empty:
                st.info("No syllabus data available. Add topics using the form.")
            else:
                edited_df = st.data_editor(
                    st.session_state.syllabus_data,
                    column_config={
                        "Status": st.column_config.SelectboxColumn(
                            "Status",
                            options=["Not Started", "In Progress", "Completed"],
                            required=True
                        )
                    },
                    hide_index=True
                )
                
                if not edited_df.equals(st.session_state.syllabus_data):
                    for index, row in edited_df.iterrows():
                        save_syllabus_topic(
                            row['Topic'],
                            row['Duration'],
                            row['Subject'],
                            row['Planned Date'],
                            row['Status'],
                            update=True
                        )
                    st.session_state.syllabus_data = edited_df
    
    # AI Scheduling Tab
    with scheduling_tab:
        st.subheader("🤖 AI Lesson Scheduling")
        
        # Add recurring schedule section
        st.write("### 📅 Set Your Teaching Schedule")
        st.write("Add the dates and times when you regularly teach:")
        
        with st.form("recurring_schedule_form"):
            # Subject and Topic inputs
            subject = st.text_input("Subject Name", key="subject_input")
            topic = st.text_input("Topic Name (optional)", key="topic_input")
            duration = st.number_input("Duration (hours)", min_value=1, max_value=4, value=1, key="duration_input")
            
            dates = st.multiselect(
                "Select Teaching Days",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                default=st.session_state.recurring_schedule.get("days", [])
            )
            
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.time_input(
                    "Class Start Time",
                    value=datetime.strptime(st.session_state.recurring_schedule.get("start_time", "09:00"), "%H:%M").time() 
                    if "start_time" in st.session_state.recurring_schedule 
                    else datetime.now().replace(hour=9, minute=0).time()
                )
            
            with col2:
                end_time = st.time_input(
                    "Class End Time",
                    value=datetime.strptime(st.session_state.recurring_schedule.get("end_time", "17:00"), "%H:%M").time()
                    if "end_time" in st.session_state.recurring_schedule
                    else datetime.now().replace(hour=17, minute=0).time()
                )
            
            weeks_ahead = st.number_input("Schedule for how many weeks ahead?", min_value=1, max_value=12, value=4)
            
            if st.form_submit_button("Set Schedule"):
                if not dates:
                    st.error("Please select at least one teaching day")
                elif start_time >= end_time:
                    st.error("End time must be after start time")
                else:
                    st.session_state.recurring_schedule = {
                        "days": dates,
                        "start_time": start_time.strftime("%H:%M"),
                        "end_time": end_time.strftime("%H:%M")
                    }
                    
                    # Generate dates for the selected weeks
                    today = datetime.now().date()
                    all_dates = []
                    day_map = {
                        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                        "Friday": 4, "Saturday": 5, "Sunday": 6
                    }
                    
                    for week in range(weeks_ahead):
                        for day in dates:
                            day_num = day_map[day]
                            next_date = today + timedelta(days=(week * 7 + (day_num - today.weekday() + 7) % 7))
                            all_dates.append(next_date)
                    
                    st.session_state.selected_dates = sorted(all_dates)
                    st.success("Schedule set! Now you can get AI suggestions for topic distribution.")
        
        if st.session_state.selected_dates:
            st.write("### 📚 Topic Distribution")
            st.write(f"Planning for {len(st.session_state.selected_dates)} classes:")
            
            for date in st.session_state.selected_dates:
                st.write(f"- {date.strftime('%A, %B %d, %Y')}")
            
            get_suggestions = st.button("🤖 Get AI Topic Distribution")
            if get_suggestions:
                with st.spinner("Creating topic distribution plan..."):
                    schedule_suggestions = []
                    previous_topics = []  # Track previous topics
                    subject_preference = st.session_state.get('subject_input', '')
                    topic_preference = st.session_state.get('topic_input', '')
                    
                    for date in st.session_state.selected_dates:
                        # Create a simple time slot structure
                        start_time = datetime.strptime(st.session_state.recurring_schedule["start_time"], "%H:%M").time()
                        free_slots = [{"start": datetime.combine(date, start_time).isoformat()}]
                        
                        # Create topic dataframe with subject
                        topic_data = {
                            'Topic': [topic_preference] if topic_preference else [''],
                            'Subject': [subject_preference],  # Always use the subject from input
                            'Duration': [st.session_state.duration_input]
                        }
                        topic_df = pd.DataFrame(topic_data)
                        
                        # Get suggestion for this session, passing previous topics
                        suggestion = suggest_lesson_schedule(topic_df, free_slots, previous_topics)
                        
                        if suggestion:
                            suggestion['date'] = date
                            schedule_suggestions.append(suggestion)
                            # Track this topic for next suggestion
                            previous_topics.append(suggestion['topic'])
                    
                    # Store suggestions in session state
                    st.session_state.schedule_suggestions = schedule_suggestions
                    
                    if schedule_suggestions:
                        st.success("Topic distribution plan created!")
            
            # Always display suggestions if they exist in session state
            if st.session_state.schedule_suggestions:
                for suggestion in st.session_state.schedule_suggestions:
                    with st.expander(f"📅 {suggestion['date'].strftime('%A, %B %d, %Y')}", expanded=True):
                        st.markdown(f"### {suggestion['topic']}")
                        st.write("**Time:** " + suggestion['time_slot'])
                        st.write("**Duration:** " + str(suggestion['duration_hours']) + " hour")
                        st.markdown("#### 📝 Lesson Plan")
                        st.write(suggestion['lesson_plan'])
                        st.markdown("#### 🎯 Reasoning")
                        st.write(suggestion['reason'])
                        
                        key = suggestion['date'].strftime('%Y-%m-%d')
                        is_scheduled = key in st.session_state.scheduled_classes
                        
                        if not is_scheduled:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                schedule_button = st.button(
                                    f"📅 Schedule This Class ({suggestion['date'].strftime('%B %d')})",
                                    key=f"schedule_{key}"
                                )
                                if schedule_button:
                                    try:
                                        if schedule_suggested_lesson(suggestion):
                                            st.session_state.scheduled_classes.add(key)
                                            st.success(f"✅ Class scheduled for {suggestion['date'].strftime('%B %d, %Y')}")
                                        else:
                                            st.error("Failed to schedule the class. Please try again.")
                                    except Exception as e:
                                        st.error(f"Error scheduling class: {str(e)}")
                        else:
                            st.success("✅ This class has been scheduled")