import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import Dict, List, Any
import os
import json
from datetime import datetime, date
import os.path

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
            
        # Use credentials.json file
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        raise Exception(f"Error loading credentials: {str(e)}")

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

### Analysis Needed:
1. Strengths & Weaknesses: Identify key strong and weak areas based on assignment performance.
2. Predicted Score: Predict their next exam score based on trends.
3. Improvement Plan: Suggest 3 key actions to improve weak areas.
4. AI Insights: What learning strategies would be best for this student?
5. Motivational Message: Generate a custom motivational message for the student.

Return the insights in JSON format with the following structure exactly:
{{
    "Strengths": ["Topic 1", "Topic 2"],
    "Weaknesses": ["Topic 3", "Topic 4"],
    "Predicted_Score": 85,
    "Improvement_Plan": ["Tip 1", "Tip 2", "Tip 3"],
    "Learning_Strategy": "Strategy description",
    "Motivational_Message": "Motivational message"
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
        
        # Parse response and ensure it's valid JSON
        try:
            analysis = json.loads(response.text)
            
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
            raise Exception("Invalid JSON response from AI")
        
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