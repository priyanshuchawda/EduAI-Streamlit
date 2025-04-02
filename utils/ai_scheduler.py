from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
from src.config.client import client, model
from google.genai import types
from utils.calendar_integration import get_free_time_slots, schedule_lesson
import json

def suggest_lesson_schedule(syllabus_df: pd.DataFrame, free_slots: List[Dict[str, str]], previous_topics: List[str] = None) -> Dict[str, Any]:
    """
    Use Gemini to suggest the best topic and time slot for scheduling.
    """
    if syllabus_df.empty:
        return None
        
    # Use the topic and subject provided from the website input
    full_topic = syllabus_df['Topic'].iloc[0]
    subject = syllabus_df['Subject'].iloc[0]  # Get subject from dataframe
    
    # Format time slots for better readability
    formatted_slots = []
    for slot in free_slots:
        start = datetime.fromisoformat(slot['start'])
        formatted_slots.append(f"{start.strftime('%I:%M %p')}")
    
    # Get user-specified duration
    user_duration = 1
    if 'Duration' in syllabus_df.columns and not syllabus_df.empty:
        user_duration = syllabus_df['Duration'].iloc[0]

    # Determine the current session number based on previous topics
    session_num = len(previous_topics) + 1 if previous_topics else 1
    
    # Create a dynamic prompt that uses the entered topic without assuming a fixed breakdown
    prompt = f"""You are an AI teaching assistant helping schedule lessons for a teacher.

Full Topic to Schedule: {full_topic}
Subject: {subject}

Current Session: {session_num}/6
Previous Topics Covered: {', '.join(previous_topics) if previous_topics else 'None'}
Time Slot: {formatted_slots[0] if formatted_slots else '09:00 AM'}
Duration: Exactly {user_duration} hour

Task: Break down and schedule the provided topic across 6 one-hour sessions.

For this specific session #{session_num}, provide:
1. The appropriate subtopic or section of the full topic based on a logical progression.
2. A detailed lesson plan that can be completed in EXACTLY {user_duration} hour.
3. Specific examples and practice problems appropriate for {subject} class.
4. Clear learning objectives and outcomes.

Return your suggestions in this exact JSON format:
{{
    "topic": "Specific subtopic with clear scope",
    "subject": "{subject}",
    "time_slot": "{formatted_slots[0] if formatted_slots else '09:00 AM'}",
    "duration_hours": {user_duration},
    "lesson_plan": "Detailed breakdown including examples and exercises",
    "reason": "Why this subtopic was chosen and how it fits in the overall sequence",
    "section": "Subsection of the topic",
    "sequence_number": "{session_num}"
}}"""

    # Create content using Gemini API format
    contents = [
        types.Content(
            role="user",
            parts=[{"text": prompt}]
        )
    ]
    
    config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        max_output_tokens=2048,
        response_mime_type="application/json"
    )
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        
        suggestion = json.loads(response.text)
        
        # Ensure subject is set correctly
        suggestion['subject'] = subject
        
        # Format the topic display to show progression
        suggestion['topic'] = f"[{suggestion.get('sequence_number', '1')}/6] {suggestion.get('section', '')}: {suggestion['topic']}"
        
        return suggestion
            
    except Exception as e:
        print(f"Error getting schedule suggestions: {str(e)}")
        return None

def schedule_suggested_lesson(suggestion: Dict[str, Any]) -> bool:
    """
    Schedule a lesson based on AI suggestions
    """
    try:
        if not suggestion:
            return False
            
        # Handle date if provided in suggestion
        if 'date' in suggestion:
            # Parse the time from time_slot (e.g. "9:00 AM")
            start_time = datetime.strptime(suggestion['time_slot'], '%I:%M %p').time()
            # Combine with the date
            start_datetime = datetime.combine(suggestion['date'], start_time)
            # Add duration for end time
            end_datetime = start_datetime + timedelta(hours=float(suggestion['duration_hours']))
        else:
            # Fallback if no date provided
            start_time = datetime.strptime(suggestion['time_slot'], '%I:%M %p').time()
            today = datetime.now().date()
            start_datetime = datetime.combine(today, start_time)
            end_datetime = start_datetime + timedelta(hours=float(suggestion['duration_hours']))
        
        # Create event description from lesson plan
        description = f"""📝 Lesson Plan:
{suggestion['lesson_plan']}

🎯 Teaching Focus:
{suggestion['reason']}"""
        
        # Schedule the lesson
        event_id = schedule_lesson(
            topic=suggestion['topic'],
            start_time=start_datetime.isoformat(),
            end_time=end_datetime.isoformat(),
            subject=suggestion['subject'],
            description=description
        )
        
        return bool(event_id)
        
    except Exception as e:
        print(f"Error scheduling suggested lesson: {str(e)}")
        return False
