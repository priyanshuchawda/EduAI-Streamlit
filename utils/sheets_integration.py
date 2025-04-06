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
        if hasattr(st, 'secrets'):
            credentials_info = json.loads(st.secrets['GOOGLE_APPLICATION_CREDENTIALS'])
        else:
            credentials_info = {
                "type": os.getenv('GOOGLE_TYPE'),
                "project_id": os.getenv('GOOGLE_PROJECT_ID'),
                "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
                "private_key": os.getenv('GOOGLE_PRIVATE_KEY'),
                "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
                "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                "auth_uri": os.getenv('GOOGLE_AUTH_URI'),
                "token_uri": os.getenv('GOOGLE_TOKEN_URI'),
                "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER_CERT_URL'),
                "client_x509_cert_url": os.getenv('GOOGLE_CLIENT_CERT_URL')
            }

        creds = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        raise Exception(f"Error initializing Google Sheets client: {str(e)}")

def get_or_create_student_sheet(student_name: str) -> gspread.Worksheet:
    """Get or create a sheet for the student"""
    try:
        client = get_google_sheets_client()
        
        # Use the specific spreadsheet ID
        spreadsheet = client.open_by_key(os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID'))
        
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
        spreadsheet = client.open_by_key(os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID'))
        
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

def get_or_create_subject_sheet(subject: str) -> gspread.Worksheet:
    """Get or create a sheet for a specific subject"""
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_key(os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID'))
        
        # Try to get the subject worksheet
        try:
            worksheet = spreadsheet.worksheet(subject)
        except gspread.WorksheetNotFound:
            # Create subject worksheet if it doesn't exist
            worksheet = spreadsheet.add_worksheet(
                title=subject,
                rows=1000,
                cols=16  # Added column for roll number
            )
            # Set up headers for comprehensive student tracking
            headers = [
                'Date',
                'Student Name',
                'Roll Number',  # New column
                'Assignment Title',
                'Grade',
                'Percentage',
                'Summary',
                'Strengths',
                'Areas for Improvement',
                'Key Topics Mastered',
                'Topics Needing Work',
                'Teacher Comments',
                'AI Suggestions',
                'Previous Performance Trend',
                'Recommended Resources',
                'Notes'
            ]
            worksheet.update('A1:P1', [headers])
            
            # Format header row
            worksheet.format('A1:P1', {
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                "horizontalAlignment": "CENTER",
                "textFormat": {"bold": True}
            })
            
            # Set column widths using resize_column
            try:
                worksheet.resize(cols=16)  # Ensure we have enough columns
                # Set specific column widths (pixel values are approximate)
                col_widths = {
                    'B': 250,  # Student Name
                    'C': 150,  # Roll Number
                    'D': 300,  # Assignment Title
                    'G': 400,  # Summary
                    'H': 300,  # Strengths
                    'I': 300   # Areas for Improvement
                }
                
                for col, width in col_widths.items():
                    col_index = ord(col) - ord('A') + 1
                    worksheet.update_column_properties(col_index, {
                        "pixelSize": width
                    })
            except Exception as e:
                print(f"Warning: Could not set column widths: {str(e)}")
                # Continue even if column resizing fails
            
        return worksheet
        
    except Exception as e:
        raise Exception(f"Error accessing Google Sheets for subject {subject}: {str(e)}")

def save_grading_result(
    student_name: str,
    roll_number: str,
    subject: str,
    grading_data: Dict[str, Any],
    assignment_title: str
) -> bool:
    """Save assignment grading results to subject-specific sheet"""
    try:
        worksheet = get_or_create_subject_sheet(subject)
        
        # Get student's previous performance data
        previous_data = get_student_subject_history(student_name, subject)
        performance_trend = analyze_performance_trend(previous_data) if not previous_data.empty else "First submission"
        
        # Prepare row data
        row_data = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            student_name,
            roll_number,
            assignment_title,
            grading_data.get('grade', 'N/A'),
            grading_data.get('percentage', '0%'),
            grading_data.get('summary', 'No summary available'),
            ', '.join([s for s in grading_data.get('strengths', []) if s]),
            ', '.join([i for i in grading_data.get('improvements', []) if i]),
            ', '.join([q['question_text'] for q in grading_data.get('questions', []) 
                      if q.get('evaluation', {}).get('correctness') == 'correct']),
            ', '.join([q['question_text'] for q in grading_data.get('questions', []) 
                      if q.get('evaluation', {}).get('correctness') == 'incorrect']),
            '',  # Teacher comments (blank initially)
            ', '.join(grading_data.get('improvement_plan', {}).get('recommended_practice', [])),
            performance_trend,
            ', '.join(grading_data.get('improvement_plan', {}).get('resources', [])),
            ''   # Notes (blank initially)
        ]
        
        # Append new row
        worksheet.append_row(row_data)
        return True
        
    except Exception as e:
        raise Exception(f"Error saving grading results to sheets: {str(e)}")

def get_student_subject_history(student_name: str, subject: str) -> pd.DataFrame:
    """Retrieve student's historical data for a specific subject"""
    try:
        worksheet = get_or_create_subject_sheet(subject)
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        if not df.empty:
            # Filter by both student name and roll number if available
            return df[df['Student Name'] == student_name]
        return df
    except Exception as e:
        raise Exception(f"Error retrieving student subject history: {str(e)}")

def analyze_performance_trend(history_df: pd.DataFrame) -> str:
    """Analyze student's performance trend from historical data"""
    if history_df.empty:
        return "No previous data"
        
    try:
        # Convert percentage strings to float values
        percentages = history_df['Percentage'].str.rstrip('%').astype(float)
        
        if len(percentages) < 2:
            return "Not enough data for trend analysis"
            
        # Calculate trend
        recent_avg = percentages.tail(2).mean()
        older_avg = percentages.head(len(percentages) - 2).mean() if len(percentages) > 2 else percentages.iloc[0]
        
        diff = recent_avg - older_avg
        if diff > 5:
            return "Improving"
        elif diff < -5:
            return "Declining"
        else:
            return "Stable"
            
    except Exception:
        return "Unable to calculate trend"