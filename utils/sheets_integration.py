import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import Dict, List, Any
import os
import json
from datetime import datetime, date
import streamlit as st
from dotenv import load_dotenv

# Load environment variables only if not in Streamlit Cloud
if not hasattr(st, 'secrets'):
    load_dotenv()

def get_google_sheets_client():
    """Initialize and return Google Sheets client"""
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        # Get path to credentials file in the same directory as app.py
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        credentials_path = os.path.join(current_dir, 'credentials1.json')  # Changed to credentials1.json
        
        if not os.path.exists(credentials_path):
            raise Exception(f"Credentials file not found at {credentials_path}")
            
        # Validate required fields
        required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email"]
        missing_fields = [field for field in required_fields if not credentials_info.get(field)]
        if missing_fields:
            raise Exception(f"Missing required Google credentials fields: {', '.join(missing_fields)}")

        creds = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
        return gspread.authorize(creds)
        
    except Exception as e:
        st.error("⚠️ Failed to initialize Google Sheets client. Please check your credentials.")
        raise Exception(f"Error initializing Google Sheets client: {str(e)}")

def get_or_create_student_sheet(student_name: str) -> gspread.Worksheet:
    """Get or create a sheet for the student"""
    try:
        client = get_google_sheets_client()
        
        # Use the specific spreadsheet ID
        spreadsheet = client.open_by_key('1XsVFDulZvVm48TufEaVoNMkEj6-wA583lIuQz5odDiM')
        
        # Try to get the Teacher worksheet
        try:
            worksheet = spreadsheet.worksheet('Teacher')
        except gspread.WorksheetNotFound:
            # Create Teacher worksheet if it doesn't exist
            worksheet = spreadsheet.add_worksheet(
                title='Teacher',
                rows=1000,  # Initial row count
                cols=10     # Initial column count
            )
            # Set up headers
            headers = [
                'Date', 'Student Name', 'Assignment Score', 'Strengths', 'Weaknesses', 
                'Predicted Score', 'Improvement Plan', 'Learning Strategy',
                'Motivational Message', 'Notes'
            ]
            worksheet.update('A1:J1', [headers])
        
        return worksheet
        
    except Exception as e:
        raise Exception(f"Error accessing Google Sheets: {str(e)}")

def get_syllabus_sheet() -> gspread.Worksheet:
    """Get or create the syllabus worksheet"""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_key('1XsVFDulZvVm48TufEaVoNMkEj6-wA583lIuQz5odDiM')
        
        try:
            worksheet = spreadsheet.worksheet('Syllabus')
        except gspread.WorksheetNotFound:
            # Create Syllabus worksheet if it doesn't exist
            worksheet = spreadsheet.add_worksheet(
                title='Syllabus',
                rows=1000,
                cols=6
            )
            # Set up headers
            headers = ['Topic', 'Duration', 'Subject', 'Planned Date', 'Status', 'Last Updated']
            worksheet.update('A1:F1', [headers])
        
        return worksheet
    except Exception as e:
        raise Exception(f"Error accessing Google Sheets: {str(e)}")

def get_syllabus_data() -> pd.DataFrame:
    """Get all syllabus data as a pandas DataFrame"""
    try:
        worksheet = get_syllabus_sheet()
        records = worksheet.get_all_records()
        if not records:
            return pd.DataFrame(columns=['Topic', 'Duration', 'Subject', 'Planned Date', 'Status', 'Last Updated'])
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        raise Exception(f"Error retrieving syllabus data: {str(e)}")

def save_syllabus_topic(
    topic: str, 
    duration: int, 
    subject: str, 
    planned_date: date,
    status: str = "Not Started",
    update: bool = False
) -> bool:
    """Save or update a syllabus topic"""
    try:
        worksheet = get_syllabus_sheet()
        
        # Format data
        row_data = [
            topic,
            duration,
            subject,
            planned_date.strftime('%Y-%m-%d'),
            status,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        if update:
            # Find the row with matching topic and update it
            cell = worksheet.find(topic)
            if cell:
                worksheet.update(f'A{cell.row}:F{cell.row}', [row_data])
        else:
            # Append new row
            worksheet.append_row(row_data)
            
        return True
        
    except Exception as e:
        raise Exception(f"Error saving syllabus topic: {str(e)}")

def save_student_analysis(
    student_name: str,
    analysis_results: Dict[str, Any],
    assignment_score: float,
    syllabus_completion: float
) -> bool:
    """Save student analysis results to Google Sheets"""
    try:
        worksheet = get_or_create_student_sheet(student_name)
        
        # Prepare row data
        row_data = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            student_name,  # Added student name column
            assignment_score,
            ', '.join(analysis_results['Strengths']),
            ', '.join(analysis_results['Weaknesses']),
            analysis_results['Predicted_Score'],
            ', '.join(analysis_results['Improvement_Plan']),
            analysis_results['Learning_Strategy'],
            analysis_results['Motivational_Message'],
            ''  # Empty notes column
        ]
        
        # Append new row
        worksheet.append_row(row_data)
        return True
        
    except Exception as e:
        raise Exception(f"Error saving to Google Sheets: {str(e)}")

def get_student_history(student_name: str) -> pd.DataFrame:
    """Retrieve student's historical data as a pandas DataFrame"""
    try:
        worksheet = get_or_create_student_sheet(student_name)
        records = worksheet.get_all_records()
        return pd.DataFrame(records)
    except Exception as e:
        raise Exception(f"Error retrieving student history: {str(e)}")

def analyze_student_performance(
    student_name: str,
    assignment_scores: List[float],
    strong_topics: List[str],
    weak_topics: List[str],
    pyq_performance: Dict[str, float],
    syllabus_completion: float
) -> Dict[str, Any]:
    """Generate AI analysis of student performance using Gemini"""
    from src.config.client import client, model
    from google.genai import types
    
    # Create the analysis prompt
    prompt = f"""You are an advanced AI tutor specializing in student performance analysis.

### Student Data:
- Name: {student_name}
- Past Assignment Scores: {assignment_scores}
- Strong Topics: {strong_topics}
- Weak Topics: {weak_topics}
- Past Year Question Performance: {json.dumps(pyq_performance)}
- Syllabus Completion: {syllabus_completion}%

### Required Analysis Format:
Please provide a detailed analysis in the following JSON structure:
{{
    "Overall_Assessment": "A detailed 2-3 sentence overview of the student's performance",
    "Strengths": [
        "List 3-4 specific strengths with clear examples",
        "Each strength should be concrete and actionable"
    ],
    "Weaknesses": [
        "List 3-4 specific areas for improvement",
        "Each weakness should be accompanied by improvement potential"
    ],
    "Predicted_Score": "A number between 0-100 based on trend analysis",
    "Improvement_Plan": [
        "3-4 specific action items",
        "Each should be detailed and actionable"
    ],
    "Learning_Strategy": "A paragraph explaining recommended learning approach",
    "Motivational_Message": "A personalized encouraging message"
}}

### Analysis Guidelines:
1. Be specific and actionable in feedback
2. Focus on observable patterns
3. Provide constructive criticism
4. Include positive reinforcement
5. Base predictions on historical data
6. Keep feedback professional and encouraging

Please analyze the student's performance and provide the response in the exact JSON format specified above."""

    contents = [
        types.Content(
            role="user",
            parts=[{"text": prompt}]  # Changed this line to use dictionary format
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
            analysis = json.loads(response.text)
            
            # Ensure all required fields are present
            required_fields = [
                'Overall_Assessment', 'Strengths', 'Weaknesses',
                'Predicted_Score', 'Improvement_Plan',
                'Learning_Strategy', 'Motivational_Message'
            ]
            
            # Add default values for any missing fields
            for field in required_fields:
                if field not in analysis:
                    if field in ['Strengths', 'Weaknesses', 'Improvement_Plan']:
                        analysis[field] = ["Needs more data to analyze"]
                    elif field == 'Predicted_Score':
                        analysis[field] = '70'
                    else:
                        analysis[field] = "More data needed for detailed analysis"
            
            # Save analysis to Google Sheets
            current_score = assignment_scores[-1] if assignment_scores else 0
            save_student_analysis(
                student_name=student_name,
                analysis_results=analysis,
                assignment_score=current_score,
                syllabus_completion=syllabus_completion
            )
            
            return analysis
            
        except json.JSONDecodeError:
            return {
                'Overall_Assessment': 'Unable to generate analysis at this time',
                'Strengths': ['More data needed'],
                'Weaknesses': ['More data needed'],
                'Predicted_Score': '70',
                'Improvement_Plan': ['Complete more assignments for detailed analysis'],
                'Learning_Strategy': 'Continue working on assignments to receive personalized strategy',
                'Motivational_Message': 'Keep up the good work! Every assignment helps build a better analysis.'
            }
        
    except Exception as e:
        raise Exception(f"Error analyzing student performance: {str(e)}")

def save_analysis_to_sheets(student_name: str, analysis_results: Dict[str, Any]) -> bool:
    """
    Save the complete analysis results to Google Sheets
    
    Args:
        student_name (str): Name of the student
        analysis_results (Dict[str, Any]): Complete analysis results including performance metrics
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        # Calculate overall progress and completion metrics
        latest_score = float(analysis_results['Predicted_Score'])
        
        # Save to Google Sheets using existing function
        return save_student_analysis(
            student_name=student_name,
            analysis_results=analysis_results,
            assignment_score=latest_score,
            syllabus_completion=0  # This can be updated when syllabus tracking is implemented
        )
        
    except Exception as e:
        raise Exception(f"Error saving analysis to sheets: {str(e)}")