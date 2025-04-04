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
from pydantic import BaseModel, Field, validator

# Define the expected response structure using Pydantic with default values
class OriginalNotes(BaseModel):
    teacher_comments: List[str] = Field(default_factory=list)
    margin_notes: List[str] = Field(default_factory=list)
    corrections: List[str] = Field(default_factory=list)

class Evaluation(BaseModel):
    correctness: Optional[str] = None
    score: Optional[str] = None
    explanation: Optional[str] = None

class Feedback(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    solution: Optional[str] = None

class QuestionEvaluation(BaseModel):
    question_number: str
    question_text: str
    student_answer: str
    evaluation: Evaluation = Field(default_factory=Evaluation)
    feedback: Feedback = Field(default_factory=Feedback)

    @validator('question_number', 'question_text', 'student_answer', pre=True)
    def ensure_string(cls, v):
        if v is None:
            return ""
        return str(v)

class GradingResponse(BaseModel):
    grade: str = Field(default="N/A")  # Default value for grade
    percentage: str = Field(default="0%")  # Default value for percentage
    summary: str = Field(default="No summary available")  # Default value for summary
    original_notes: OriginalNotes = Field(default_factory=OriginalNotes)
    questions: List[QuestionEvaluation]
    skills_analysis: Dict[str, List[str]] = Field(default_factory=lambda: {"mastered": [], "developing": [], "needs_work": []})
    improvement_plan: Dict[str, List[str]] = Field(default_factory=lambda: {"topics_to_review": [], "recommended_practice": [], "resources": []})

    @validator('grade', 'percentage', 'summary', pre=True)
    def set_default_if_none(cls, v):
        if v is None:
            return cls.__fields__[cls._get_field_name(v)].default
        return v

    @classmethod
    def _get_field_name(cls, value):
        # Helper method to get the field name from the validator context
        for name, field in cls.__fields__.items():
            if field.default == value:
                return name
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

def grade_assignment(content: Union[str, bytes], subject: str = None, is_pdf: bool = False) -> Dict[str, Any]:
    """Grade assignment using Gemini AI with comprehensive analysis"""
    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Create a default response structure
        default_response = {
            "grade": "N/A",
            "percentage": "0%",
            "summary": "Unable to process assignment",
            "original_notes": {
                "teacher_comments": [],
                "margin_notes": [],
                "corrections": []
            },
            "questions": [{
                "question_number": "1",
                "question_text": "Unable to extract question",
                "student_answer": "Unable to extract answer",
                "evaluation": {
                    "correctness": "N/A",
                    "score": "N/A",
                    "explanation": "Unable to evaluate"
                },
                "feedback": {
                    "strengths": [],
                    "improvements": [],
                    "solution": "Not available"
                }
            }],
            "skills_analysis": {
                "mastered": [],
                "developing": [],
                "needs_work": []
            },
            "improvement_plan": {
                "topics_to_review": [],
                "recommended_practice": [],
                "resources": []
            }
        }
        
        # Enhanced grading prompt for better structure
        grading_prompt = """You are an expert teacher grading an assignment. Analyze this assignment comprehensively and provide detailed feedback in JSON format. Follow these rules:

        1. Return ONLY a valid JSON object
        2. Include ALL fields shown in the example format
        3. Ensure grade is A/B/C/D/F
        4. Ensure percentage is a number with % symbol
        5. Provide detailed explanations and specific feedback
        6. Never return null values

        Format exactly like this:
        {
            "grade": "A/B/C/D/F",
            "percentage": "85%",
            "summary": "Clear executive summary of performance",
            "original_notes": {
                "teacher_comments": ["Comment 1", "Comment 2"],
                "margin_notes": ["Note 1", "Note 2"],
                "corrections": ["Correction 1", "Correction 2"]
            },
            "questions": [
                {
                    "question_number": "1",
                    "question_text": "Actual question text",
                    "student_answer": "Student's answer",
                    "evaluation": {
                        "correctness": "correct/partial/incorrect",
                        "score": "85",
                        "explanation": "Detailed explanation"
                    },
                    "feedback": {
                        "strengths": ["Specific strength 1", "Specific strength 2"],
                        "improvements": ["Specific improvement 1", "Specific improvement 2"],
                        "solution": "Step-by-step solution"
                    }
                }
            ],
            "skills_analysis": {
                "mastered": ["Skill 1", "Skill 2"],
                "developing": ["Skill 3", "Skill 4"],
                "needs_work": ["Skill 5", "Skill 6"]
            },
            "improvement_plan": {
                "topics_to_review": ["Topic 1", "Topic 2"],
                "recommended_practice": ["Practice 1", "Practice 2"],
                "resources": ["Resource 1", "Resource 2"]
            }
        }"""

        if subject:
            grading_prompt += f"\n\nThis is a {subject} assignment. Apply subject-specific criteria for {subject}."

        try:
            if is_pdf:
                # Handle PDF content
                temp_file = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                        temp_file.write(content)
                        temp_file.flush()
                        
                        with open(temp_file.name, 'rb') as f:
                            pdf_bytes = f.read()
                        
                        parts = [
                            {"text": grading_prompt},
                            {
                                "inline_data": {
                                    "mime_type": "application/pdf",
                                    "data": base64.b64encode(pdf_bytes).decode('utf-8')
                                }
                            }
                        ]

                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[{
                            "role": "user",
                            "parts": parts
                        }],
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            top_p=0.95,
                            top_k=40,
                            max_output_tokens=30000,
                            stop_sequences=[],
                            response_mime_type="application/json"
                        )
                    )

                finally:
                    if temp_file:
                        try:
                            os.unlink(temp_file.name)
                        except Exception:
                            pass
            else:
                # Handle text content
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[{
                        "role": "user",
                        "parts": [
                            {"text": grading_prompt},
                            {"text": str(content)}
                        ]
                    }],
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=30000,
                        stop_sequences=[],
                        response_mime_type="application/json"
                    )
                )

            if not response or not hasattr(response, 'text') or not response.text:
                print("Empty response from Gemini API")
                return default_response

            try:
                # Clean and process the response
                clean_text = response.text.strip()
                
                # Extract JSON from response
                json_start = clean_text.find('{')
                json_end = clean_text.rfind('}') + 1
                if json_start >= 0 and json_end > 0:
                    clean_text = clean_text[json_start:json_end]
                
                # Remove markdown formatting
                clean_text = re.sub(r'```json\s*|\s*```', '', clean_text)
                
                # Fix JSON formatting issues
                clean_text = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', clean_text)
                clean_text = re.sub(r':\s*None\s*([,}])', r': null\1', clean_text)
                clean_text = re.sub(r':\s*True\s*([,}])', r': true\1', clean_text)
                clean_text = re.sub(r':\s*False\s*([,}])', r': false\1', clean_text)
                
                # Parse JSON
                try:
                    result = json.loads(clean_text)
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {str(e)}")
                    return default_response
                
                # Validate and ensure required fields
                result['grade'] = result.get('grade', 'N/A')
                result['percentage'] = result.get('percentage', '0%')
                if not str(result['percentage']).endswith('%'):
                    result['percentage'] = f"{result['percentage']}%"
                result['summary'] = result.get('summary', 'No summary available')
                
                # Ensure questions array exists
                if 'questions' not in result or not result['questions']:
                    result['questions'] = default_response['questions']
                
                # Validate using Pydantic model
                validated_response = GradingResponse(**result)
                return validated_response.dict()

            except Exception as e:
                print(f"Error processing response: {str(e)}")
                return default_response

        except Exception as e:
            print(f"Error in Gemini processing: {str(e)}")
            return default_response

    except Exception as e:
        print(f"Error in grading assignment: {str(e)}")
        return default_response
