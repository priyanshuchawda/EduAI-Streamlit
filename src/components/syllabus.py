import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.sheets_integration import get_syllabus_sheet, save_syllabus_topic, get_syllabus_data
from utils.topic_suggestion import get_topic_suggestion

def show_syllabus_page():
    """Display the syllabus management interface"""
    st.title("📚 Syllabus Management")
    
    # Initialize session state for syllabus data
    if "syllabus_data" not in st.session_state:
        st.session_state.syllabus_data = get_syllabus_data()
    
    # Create two columns - one for input form, one for current syllabus
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("Add New Topic")
        with st.form("syllabus_form"):
            topic = st.text_input("Topic Name", placeholder="e.g. Introduction to Calculus")
            duration = st.number_input("Duration (in days)", min_value=1, value=1)
            subject = st.selectbox("Subject", ["Mathematics", "Physics", "Chemistry", "Biology", "English"])
            planned_date = st.date_input("Planned Start Date", min_value=datetime.now().date())
            
            submitted = st.form_submit_button("Add Topic")
            if submitted:
                # Save the topic to Google Sheets
                save_syllabus_topic(topic, duration, subject, planned_date)
                st.session_state.syllabus_data = get_syllabus_data()  # Refresh data
                st.success(f"Added topic: {topic}")
    
    with col2:
        st.subheader("Current Syllabus")
        if st.session_state.syllabus_data.empty:
            st.info("No syllabus data available. Add topics using the form.")
        else:
            # Display syllabus data with editing capabilities
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
                # Handle changes in the dataframe
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
    
    # Topic Suggestions Section
    st.divider()
    st.subheader("📋 Topic Suggestions")
    
    if not st.session_state.syllabus_data.empty:
        suggested_topics = get_topic_suggestion(st.session_state.syllabus_data)
        
        if suggested_topics:
            st.write("Based on your syllabus progress, here are the suggested topics for the next few days:")
            for date, topics in suggested_topics.items():
                with st.expander(f"📅 {date}"):
                    for topic in topics:
                        st.write(f"- {topic}")
        else:
            st.info("All topics are completed! Time to add more topics to your syllabus.")