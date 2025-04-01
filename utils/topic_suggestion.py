import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from src.config.client import client, model
from google.genai import types
import json

def get_topic_suggestion(syllabus_df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Get topic suggestions based on current syllabus progress
    Returns a dictionary with dates as keys and lists of topics as values
    """
    if syllabus_df.empty:
        return {}

    # Convert planned dates to datetime
    syllabus_df['Planned Date'] = pd.to_datetime(syllabus_df['Planned Date'])
    
    # Get current progress
    completed = syllabus_df[syllabus_df['Status'] == 'Completed']
    in_progress = syllabus_df[syllabus_df['Status'] == 'In Progress']
    not_started = syllabus_df[syllabus_df['Status'] == 'Not Started']
    
    # Create prompt for Gemini
    prompt = f"""You are an AI curriculum planner helping a teacher organize their syllabus topics.

Current Syllabus Status:
- Completed Topics: {', '.join(completed['Topic'].tolist()) if not completed.empty else 'None'}
- In Progress: {', '.join(in_progress['Topic'].tolist()) if not in_progress.empty else 'None'}
- Not Started: {', '.join(not_started['Topic'].tolist()) if not not_started.empty else 'None'}

Based on this information, suggest a schedule for the next 5 days of topics to cover.
Consider:
1. Topics that are "In Progress" should be completed first
2. "Not Started" topics should be scheduled based on their planned dates
3. Topics should follow a logical sequence if possible

Return the suggestions in this exact JSON format:
{{
    "2025-04-02": ["Topic 1", "Topic 2"],
    "2025-04-03": ["Topic 3"],
    "2025-04-04": ["Topic 4"],
    "2025-04-05": ["Topic 5"],
    "2025-04-06": ["Topic 6"]
}}

Only include dates and topics that make sense based on the current syllabus data."""

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
        
        # Parse response and ensure it's valid JSON
        try:
            suggestions = json.loads(response.text)
            return suggestions
        except json.JSONDecodeError:
            return {}
            
    except Exception as e:
        print(f"Error getting topic suggestions: {str(e)}")
        return {}