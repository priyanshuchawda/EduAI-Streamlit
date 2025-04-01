import os
import json
import base64
from google import genai
from google.genai import types
from typing import Union, Dict, List, Any
import tempfile
from dotenv import load_dotenv
import time
from pydantic import BaseModel
from typing import List, Optional

# Define the expected response structure using Pydantic
class OriginalNotes(BaseModel):
    teacher_comments: List[str]
    margin_notes: List[str]
    corrections: List[str]

class QuestionEvaluation(BaseModel):
    question_number: str
    question_text: str
    student_answer: str
    evaluation: Dict[str, str]
    feedback: Dict[str, Union[List[str], str]]

class GradingResponse(BaseModel):
    grade: str
    percentage: str
    summary: str
    original_notes: OriginalNotes
    questions: List[QuestionEvaluation]
    skills_analysis: Dict[str, List[str]]
    improvement_plan: Dict[str, List[str]]

# Load environment variables
load_dotenv()

def grade_assignment(content: Union[str, bytes], subject: str = None, is_pdf: bool = False) -> Dict[str, Any]:
    """Grade assignment using Gemini AI with comprehensive analysis"""
    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        grading_prompt = """You are an expert teacher grading an assignment. Analyze this assignment comprehensively and extract ALL questions and content. Return the results in the exact JSON format specified below.

        Text Formatting Requirements:
        1. Extract and process ALL questions from the document
        2. Do not skip any content or questions
        3. Use proper line breaks to separate ideas
        4. Format mathematical content properly
        5. Include all teacher's notes and comments

        YOU MUST FORMAT THE RESPONSE AS VALID JSON with this exact structure:
        {
            "grade": "A/B/C/D/F",
            "percentage": "numeric_score%",
            "summary": "executive_summary_text",
            "original_notes": {
                "teacher_comments": ["comment1", "comment2"],
                "margin_notes": ["note1", "note2"],
                "corrections": ["correction1", "correction2"]
            },
            "questions": [
                {
                    "question_number": "1",
                    "question_text": "extracted_question",
                    "student_answer": "extracted_answer",
                    "evaluation": {
                        "correctness": "correct/partial/incorrect",
                        "score": "numeric_score",
                        "explanation": "detailed_explanation"
                    },
                    "feedback": {
                        "strengths": ["point1", "point2"],
                        "improvements": ["point1", "point2"],
                        "solution": "step_by_step_solution"
                    }
                }
            ],
            "skills_analysis": {
                "mastered": ["skill1", "skill2"],
                "developing": ["skill1", "skill2"],
                "needs_work": ["skill1", "skill2"]
            },
            "improvement_plan": {
                "topics_to_review": ["topic1", "topic2"],
                "recommended_practice": ["practice1", "practice2"],
                "resources": ["resource1", "resource2"]
            }
        }"""

        if subject:
            grading_prompt += f"\n\nThis is a {subject} assignment. Apply subject-specific criteria for {subject}."

        try:
            if is_pdf:
                # Create a new temporary file with a unique name
                temp_file = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                        temp_file.write(content)
                        temp_file.flush()
                        
                        # Read the PDF file as bytes
                        with open(temp_file.name, 'rb') as f:
                            pdf_bytes = f.read()
                        
                        # Create parts array for the request
                        parts = [
                            {"text": grading_prompt},
                            {
                                "inline_data": {
                                    "mime_type": "application/pdf",
                                    "data": base64.b64encode(pdf_bytes).decode('utf-8')
                                }
                            }
                        ]
                        
                        # Generate content using the uploaded PDF with increased tokens
                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=[{
                                "role": "user",
                                "parts": parts
                            }],
                            config=types.GenerateContentConfig(
                                temperature=0.3,  # Lower temperature for more consistent output
                                top_p=0.95,
                                top_k=40,
                                max_output_tokens=90000,  # Increased from 8192
                                candidate_count=1,
                                stop_sequences=[],
                                response_mime_type="application/json",
                            )
                        )
                finally:
                    # Ensure temporary file is cleaned up
                    if temp_file:
                        try:
                            os.unlink(temp_file.name)
                        except Exception:
                            time.sleep(0.1)
                            try:
                                os.unlink(temp_file.name)
                            except Exception:
                                pass
            else:
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
                        max_output_tokens=30000,  # Increased from 8192
                        candidate_count=1,
                        stop_sequences=[],
                        response_mime_type="application/json"
                    )
                )

            if response and response.text:
                try:
                    # Parse and validate the response against our schema
                    result = json.loads(response.text)
                    
                    # Validate with Pydantic
                    validated_response = GradingResponse(**result)
                    return validated_response.dict()
                    
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON response: {response.text}")
                    raise Exception(f"Failed to parse AI response: {str(e)}")
                except Exception as e:
                    print(f"Response validation error: {str(e)}")
                    raise Exception(f"Invalid response format: {str(e)}")
            else:
                raise Exception("Empty response from Gemini API")

        except Exception as e:
            raise Exception(f"Error processing with Gemini: {str(e)}")

    except Exception as e:
        raise Exception(f"Error in grading assignment: {str(e)}")
