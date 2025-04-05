import os
import json
import re
import base64
from google import genai
from google.genai import types
from typing import Union, Dict, List, Any, Optional
import tempfile
from dotenv import load_dotenv
import time
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import fitz  # PyMuPDF

# Define the expected response structure using Pydantic with default values
class OriginalNotes(BaseModel):
    teacher_comments: List[str] = Field(default_factory=list)
    margin_notes: List[str] = Field(default_factory=list)
    corrections: List[str] = Field(default_factory=list)

class Evaluation(BaseModel):
    correctness: str = Field(default="N/A")
    score: str = Field(default="0")
    explanation: str = Field(default="No explanation available")

    @field_validator('correctness')
    def validate_correctness(cls, v):
        if not v or v not in ['correct', 'incorrect', 'partial', 'N/A']:
            return 'N/A'
        return v

    @field_validator('score')
    def validate_score(cls, v):
        if not v:
            return "0"
        return str(v)

    @field_validator('explanation')
    def validate_explanation(cls, v):
        if not v:
            return "No explanation available"
        return str(v)

class Feedback(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    solution: str = Field(default="Not available")

    @field_validator('strengths', 'improvements')
    def validate_lists(cls, v):
        if not v:
            return []
        return [str(item) for item in v if item]

    @field_validator('solution')
    def validate_solution(cls, v):
        if not v:
            return "Not available"
        return str(v)

class QuestionEvaluation(BaseModel):
    question_number: str
    question_text: str = Field(default="Unable to extract question")  
    student_answer: str = Field(default="Unable to extract answer")
    page_number: Optional[str] = Field(default=None)
    evaluation: Evaluation = Field(default_factory=Evaluation)
    feedback: Feedback = Field(default_factory=Feedback)

    @field_validator('question_number', 'question_text', 'student_answer', 'page_number')
    def validate_strings(cls, v):
        if v is None:
            return ""
        return str(v)

    model_config = {
        "validate_assignment": True,
        "extra": "allow"
    }

class GradingResponse(BaseModel):
    student_name: str = Field(default="Unknown Student")
    roll_number: str = Field(default="N/A")
    grade: str = Field(default="N/A")
    percentage: str = Field(default="0%")
    summary: str = Field(default="No summary available")
    questions: List[QuestionEvaluation] = Field(default_factory=lambda: [
        QuestionEvaluation(question_number="1")
    ])
    skills_analysis: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "mastered": [],
            "developing": [],
            "needs_work": []
        }
    )
    improvement_plan: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "topics_to_review": [],
            "recommended_practice": [],
            "resources": []
        }
    )

    @field_validator('student_name', 'roll_number', 'summary')
    def validate_strings(cls, v):
        if not v:
            return cls.model_fields[cls._get_field_name(v)].default
        return str(v)

    @field_validator('percentage')
    def ensure_percentage_format(cls, v):
        if not v:
            return "0%"
        if isinstance(v, (int, float)):
            return f"{v}%"
        v = str(v)
        if not v.endswith('%'):
            return f"{v}%"
        return v

    @field_validator('grade')
    def validate_grade(cls, v):
        valid_grades = ['A', 'B', 'C', 'D', 'F', 'N/A']
        if not v or v not in valid_grades:
            return 'N/A'
        return v

    @field_validator('questions', mode='before')
    def ensure_questions(cls, v):
        if not v:
            return [QuestionEvaluation(question_number="1")]
        return v

    @field_validator('skills_analysis', 'improvement_plan', mode='before')
    def ensure_dict_lists(cls, v):
        if not isinstance(v, dict):
            return cls.model_fields[cls._get_field_name(v)].default
        return v

    model_config = {
        "validate_assignment": True,
        "extra": "allow"
    }

    @classmethod
    def _get_field_name(cls, value):
        for field_name, field in cls.model_fields.items():
            if field.default == value:
                return field_name
        return None

def fix_incomplete_json(text: str) -> str:
    """Fix common JSON issues in the response"""
    if not text or not text.strip():
        return '{}'
        
    # Remove any markdown formatting
    if "```json" in text:
        text = text.split("```json", 1)[1]
    if "```" in text:
        text = text.split("```", 1)[0]
    
    # Clean up the text
    text = text.strip()
    
    # Ensure the text starts with an opening brace
    if not text.startswith('{'):
        if '{' in text:
            text = text[text.index('{'):]
        else:
            return '{}'
            
    # Try to complete truncated JSON by adding missing closing braces
    # Count opening and closing braces
    open_count = text.count('{')
    close_count = text.count('}')
    
    # If we have a truncated JSON, try to complete it
    if open_count > close_count:
        # First try to find the last complete object
        brace_count = 0
        in_string = False
        escape_next = False
        last_complete = 0
        has_complete_object = False
        
        for i, char in enumerate(text):
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        last_complete = i + 1
                        has_complete_object = True
        
        if has_complete_object:
            # We found a complete object, use it
            text = text[:last_complete].strip()
        else:
            # No complete object found, try to complete the JSON
            # Add any missing closing braces for objects
            missing_braces = open_count - close_count
            text += '}' * missing_braces
            
            # Try to fix any truncated string values
            text = re.sub(r'\"([^\"]*?)$', r'"\1"', text)
            
            # Add closing braces for any unclosed arrays
            open_arrays = text.count('[')
            close_arrays = text.count(']')
            if open_arrays > close_arrays:
                text += ']' * (open_arrays - close_arrays)
    
    # Fix missing quotes around property names
    text = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)
    
    # Replace null values for required string fields with their defaults
    text = re.sub(r'"grade"\s*:\s*null', '"grade": "N/A"', text)
    text = re.sub(r'"percentage"\s*:\s*null', '"percentage": "0%"', text)
    text = re.sub(r'"summary"\s*:\s*null', '"summary": "No summary available"', text)
    
    # Add missing required fields if they don't exist
    required_fields = {
        '"student_name"': '"Unknown Student"',
        '"roll_number"': '"N/A"',
        '"grade"': '"N/A"',
        '"percentage"': '"0%"',
        '"summary"': '"No summary available"',
        '"questions"': '[]',
        '"skills_analysis"': '{"mastered":[],"developing":[],"needs_work":[]}', 
        '"improvement_plan"': '{"topics_to_review":[],"recommended_practice":[],"resources":[]}' 
    }
    
    # Check for missing required fields and add them
    for field, default_value in required_fields.items():
        if field not in text:
            if text.endswith('}'):
                text = text[:-1]  # Remove closing brace
                if not text.endswith(','):
                    text += ','
                text += f'{field}:{default_value}}}'
    
    # Ensure text starts and ends with curly braces
    if not text.startswith('{'):
        text = '{' + text
    if not text.endswith('}'):
        text += '}'
        
    return text

def grade_assignment(
    content: Union[str, bytes], 
    subject: str = None, 
    is_pdf: bool = False,
    student_name: str = None,
    roll_number: str = None
) -> Dict[str, Any]:
    """Grade assignment using Gemini AI with comprehensive analysis"""
    try:
        # Initialize the Gemini client with API key from environment
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        if is_pdf:
            # Create temporary PDF file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(content)
                temp_file.flush()
                
                try:
                    # Upload PDF directly to Gemini
                    document_file = client.files.upload(file=temp_file.name)
                    
                    # Add retry mechanism for API calls
                    max_retries = 3
                    retry_delay = 2  # seconds
                    last_error = None
                    
                    for attempt in range(max_retries):
                        try:
                            # Create grading prompt with strict JSON format requirement
                            grading_prompt = f"""You are an expert teacher grading a student's assignment. Your task is to provide detailed evaluation in STRICT JSON format.

IMPORTANT: Return ONLY valid JSON - no other text or explanation.

Assignment Details:
- Student: {student_name or 'Unknown Student'}
- Roll Number: {roll_number or 'N/A'}
- Subject: {subject or 'General'}

Required Response Format:
{{
    "student_name": "{student_name or 'Unknown Student'}",
    "roll_number": "{roll_number or 'N/A'}",
    "grade": "A/B/C/D/F",
    "percentage": "85.5%",
    "summary": "Overall performance summary",
    "questions": [
        {{
            "question_number": "1",
            "question_text": "Complete question text",
            "student_answer": "Complete student answer",
            "page_number": "1",
            "evaluation": {{
                "correctness": "correct/incorrect/partial",
                "score": "points",
                "explanation": "Detailed explanation"
            }},
            "feedback": {{
                "strengths": ["point 1", "point 2"],
                "improvements": ["area 1", "area 2"],
                "solution": "Correct approach"
            }}
        }}
    ],
    "skills_analysis": {{
        "mastered": ["skill 1", "skill 2"],
        "developing": ["skill 3"],
        "needs_work": ["skill 4", "skill 5"]
    }},
    "improvement_plan": {{
        "topics_to_review": ["topic 1", "topic 2"],
        "recommended_practice": ["practice 1", "practice 2"],
        "resources": ["resource 1", "resource 2"]
    }}
}}"""

                            # Generate content using the uploaded PDF
                            response = client.models.generate_content(
                                model="gemini-2.0-flash",
                                contents=[grading_prompt, document_file],
                                config=types.GenerateContentConfig(
                                    temperature=0.1,
                                    top_p=0.95,
                                    top_k=40,
                                    max_output_tokens=30000,
                                    response_mime_type="application/json"
                                )
                            )

                            if response and response.text:
                                try:
                                    # Print raw response for debugging
                                    print(f"\nRaw response (first 500 chars):\n{response.text[:500]}")
                                    
                                    # Try to fix any JSON issues
                                    fixed_json = fix_incomplete_json(response.text)
                                    print(f"\nFixed JSON (first 500 chars):\n{fixed_json[:500]}")
                                    
                                    # Try to parse the JSON
                                    result = json.loads(fixed_json)
                                    
                                    # Validate with Pydantic model
                                    validated_response = GradingResponse(**result)
                                    return validated_response.model_dump()
                                    
                                except json.JSONDecodeError as e:
                                    print(f"\nJSON parsing error: {str(e)}")
                                    last_error = e
                                    if attempt < max_retries - 1:
                                        print(f"Retrying... Attempt {attempt + 2}/{max_retries}")
                                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                                        continue
                            else:
                                print("\nEmpty response from Gemini API")
                                if attempt < max_retries - 1:
                                    print(f"Retrying... Attempt {attempt + 2}/{max_retries}")
                                    time.sleep(retry_delay * (attempt + 1))
                                    continue
                                
                        except Exception as e:
                            print(f"\nAPI call error: {str(e)}")
                            last_error = e
                            if attempt < max_retries - 1:
                                print(f"Retrying... Attempt {attempt + 2}/{max_retries}")
                                time.sleep(retry_delay * (attempt + 1))
                            else:
                                print(f"All retry attempts failed. Last error: {str(last_error)}")
                                
                    # If we get here, all retries failed
                    print("\nFalling back to default response structure")
                    return GradingResponse(
                        student_name=student_name or "Unknown Student",
                        roll_number=roll_number or "N/A",
                        grade="N/A",
                        percentage="0%",
                        summary="Unable to grade assignment due to technical issues"
                    ).model_dump()

                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file.name):
                        try:
                            os.unlink(temp_file.name)
                        except Exception:
                            pass
        else:
            print("Text content grading not implemented in this version.")
            return GradingResponse().model_dump()

    except Exception as e:
        print(f"Error in grading assignment: {str(e)}")
        return GradingResponse().model_dump()

def calculate_grade(percentage: float) -> str:
    """Calculate letter grade from percentage"""
    if percentage >= 90:
        return 'A'
    elif percentage >= 80:
        return 'B'
    elif percentage >= 70:
        return 'C'
    elif percentage >= 60:
        return 'D'
    else:
        return 'F'

def generate_summary(questions: List[Dict], percentage: float) -> str:
    """Generate a comprehensive summary of the assignment performance"""
    total_questions = len(questions)
    correct = sum(1 for q in questions if q.get('evaluation', {}).get('correctness') == 'correct')
    partial = sum(1 for q in questions if q.get('evaluation', {}).get('correctness') == 'partial')
    
    summary = f"Assessment completed with {percentage:.1f}% overall score. "
    summary += f"Out of {total_questions} questions, {correct} were correct"
    if partial > 0:
        summary += f", {partial} were partially correct"
    summary += "."
    
    return summary

def generate_improvement_plan(improvements: List[str], subject: str) -> Dict[str, List[str]]:
    """Generate a structured improvement plan based on identified areas for improvement"""
    if not improvements:
        return {
            "topics_to_review": [],
            "recommended_practice": [],
            "resources": []
        }
    
    # Get unique improvements
    unique_improvements = list(set(improvements))
    
    # Generate specific practice recommendations
    practice_tasks = [
        f"Practice {imp.lower()}" for imp in unique_improvements[:3]
    ]
    
    # Generate subject-specific resources
    if subject:
        resources = [
            f"Review {subject} textbook chapter on {imp.lower()}" for imp in unique_improvements[:2]
        ]
        resources.extend([
            f"Complete practice problems in {subject} workbook",
            f"Watch video tutorials on {subject} topics"
        ])
    else:
        resources = [
            "Review relevant textbook chapters",
            "Complete practice workbook exercises",
            "Watch topic-specific video tutorials"
        ]
    
    return {
        "topics_to_review": unique_improvements[:5],
        "recommended_practice": practice_tasks,
        "resources": resources
    }