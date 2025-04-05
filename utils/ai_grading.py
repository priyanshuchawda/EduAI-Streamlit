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
from pydantic import BaseModel, Field, validator, field_validator
from datetime import datetime
import fitz

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
    # Remove any markdown formatting
    if "```json" in text:
        text = text.split("```json", 1)[1]
    if "```" in text:
        text = text.split("```", 1)[0]
    
    # Clean up the text
    text = text.strip()
    
    # Find the last complete object by checking balanced braces
    brace_count = 0
    last_complete = 0
    in_string = False
    escape_next = False
    
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

    # Get the complete JSON object
    text = text[:last_complete].strip()
    
    # Fix missing quotes around property names
    text = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)
    
    # Replace null values for required string fields with their defaults
    text = re.sub(r'"grade"\s*:\s*null', '"grade": "N/A"', text)
    text = re.sub(r'"percentage"\s*:\s*null', '"percentage": "0%"', text)
    text = re.sub(r'"summary"\s*:\s*null', '"summary": "No summary available"', text)
    
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
        
        # Extract assignment title from content
        assignment_title = "Assignment " + datetime.now().strftime("%Y-%m-%d")
        if isinstance(content, str) and len(content) > 50:
            first_line = content.split('\n')[0][:50]
            if first_line.strip():
                assignment_title = first_line.strip()

        # Process PDF in chunks for larger documents
        if is_pdf:
            # Handle PDF content
            temp_file = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(content)
                    temp_file.flush()
                    
                    # Process PDF and extract text from all pages
                    pdf_document = fitz.open(temp_file.name)
                    total_pages = pdf_document.page_count
                    
                    # Process pages in chunks of 5 to stay within token limits
                    chunks = []
                    for i in range(0, total_pages, 5):
                        chunk_content = ""
                        end_page = min(i + 5, total_pages)
                        
                        for page_num in range(i, end_page):
                            page = pdf_document[page_num]
                            chunk_content += f"\n=== Page {page_num + 1} ===\n"
                            chunk_content += page.get_text()
                        
                        chunks.append(chunk_content)
                    
                    pdf_document.close()

                    # Process each chunk and combine results
                    all_questions = []
                    all_strengths = set()
                    all_improvements = set()
                    total_score = 0
                    total_evaluated = 0

                    for chunk_num, chunk in enumerate(chunks):
                        chunk_prompt = f"""You are an expert teacher grading a section of an assignment (Part {chunk_num + 1} of {len(chunks)}).
                        Process ALL questions in this section thoroughly.

                        Student: {student_name or 'Unknown Student'}
                        Roll Number: {roll_number or 'N/A'}
                        Subject: {subject or 'General'}

                        Instructions:
                        1. Extract and grade ALL questions and answers
                        2. Provide detailed evaluation for each
                        3. Return in exact JSON format

                        Return ONLY a JSON object with this structure:
                        {{
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
                            "chunk_summary": {{
                                "strengths": ["strength 1", "strength 2"],
                                "improvements": ["improvement 1", "improvement 2"],
                                "total_points": 0,
                                "max_points": 0
                            }}
                        }}"""

                        # Process chunk with Gemini
                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=[{
                                "role": "user",
                                "parts": [
                                    {"text": chunk_prompt},
                                    {"text": chunk}
                                ]
                            }],
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
                                chunk_result = json.loads(fix_incomplete_json(response.text))
                                
                                # Accumulate questions
                                if 'questions' in chunk_result:
                                    all_questions.extend(chunk_result['questions'])
                                
                                # Accumulate strengths and improvements
                                if 'chunk_summary' in chunk_result:
                                    all_strengths.update(chunk_result['chunk_summary'].get('strengths', []))
                                    all_improvements.update(chunk_result['chunk_summary'].get('improvements', []))
                                    total_score += chunk_result['chunk_summary'].get('total_points', 0)
                                    total_evaluated += chunk_result['chunk_summary'].get('max_points', 0)
                            
                            except json.JSONDecodeError:
                                print(f"Error parsing chunk {chunk_num + 1}")
                                continue

                    # Calculate overall grade
                    if total_evaluated > 0:
                        percentage = (total_score / total_evaluated) * 100
                        grade = calculate_grade(percentage)
                    else:
                        percentage = 0
                        grade = 'N/A'

                    # Combine all results
                    final_result = {
                        "student_name": student_name or "Unknown Student",
                        "roll_number": roll_number or "N/A",
                        "grade": grade,
                        "percentage": f"{percentage:.1f}%",
                        "summary": generate_summary(all_questions, percentage),
                        "questions": all_questions,
                        "skills_analysis": {
                            "mastered": list(all_strengths)[:5],
                            "developing": list(all_strengths)[5:8] if len(all_strengths) > 5 else [],
                            "needs_work": list(all_improvements)[:5]
                        },
                        "improvement_plan": generate_improvement_plan(list(all_improvements), subject)
                    }

                    return final_result

            finally:
                if temp_file and os.path.exists(temp_file.name):
                    try:
                        os.unlink(temp_file.name)
                    except Exception:
                        pass

        else:
            # Handle text content (existing code)
            print("Text content grading not implemented in this version.")
            return {}

    except Exception as e:
        print(f"Error in grading assignment: {str(e)}")
        return {}

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