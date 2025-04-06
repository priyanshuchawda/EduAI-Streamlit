import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

def process_pdf_with_gemini(pdf_path: str) -> Dict[str, Any]:
    """Process PDF with enhanced learning analysis"""
    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Upload the PDF file to Gemini
        document_file = client.files.upload(file=pdf_path)
        
        # Enhanced learning-focused prompt
        processing_prompt = """Analyze this document comprehensively and return a detailed JSON response with the following structure:

        {
            "title": "Main document title",
            "main_topics": {
                "theoretical_concepts": ["concept1", "concept2"],
                "formulas": ["formula1", "formula2"]
            },
            "learning_analysis": {
                "difficulty_level": "Beginner/Intermediate/Advanced",
                "prerequisites": ["prereq1", "prereq2"],
                "study_tips": ["tip1", "tip2"],
                "common_misconceptions": ["misconception1", "misconception2"]
            },
            "content_breakdown": [
                {
                    "title": "Section title",
                    "analysis": "Detailed analysis",
                    "examples": [
                        {
                            "title": "Example title",
                            "problem": "Problem statement",
                            "solution": "Step-by-step solution",
                            "explanation": "Detailed explanation"
                        }
                    ],
                    "key_points": ["point1", "point2"]
                }
            ],
            "practice_material": {
                "exercises": [
                    {
                        "question": "Exercise question",
                        "hint": "Optional hint",
                        "solution": "Complete solution"
                    }
                ],
                "common_mistakes": ["mistake1", "mistake2"]
            },
            "additional_resources": {
                "related_topics": ["topic1", "topic2"],
                "reference_materials": ["reference1", "reference2"]
            },
            "summary": "Overall document summary",
            "key_takeaways": ["takeaway1", "takeaway2"],
            "notes": ["important note1", "important note2"]
        }

        Instructions:
        1. Extract and organize all content according to this structure
        2. Identify main concepts and formulas
        3. Provide detailed analysis of each section
        4. Include practice exercises with solutions
        5. Add learning tips and common misconceptions
        6. Suggest related topics and resources
        7. Keep mathematical formulas in proper LaTeX format

        Your response must be valid JSON.
        """
        
        # Generate content using the uploaded PDF
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[processing_prompt, document_file],
            config=types.GenerateContentConfig(
                temperature=0.1,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192
            )
        )
        
        if not response or not response.text:
            raise Exception("No response from Gemini")
            
        try:
            # Clean and parse the JSON response
            json_str = response.text.strip()
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = json_str[start:end]
            
            result = json.loads(json_str)
            
            # Ensure minimum required structure with learning focus
            if not isinstance(result, dict):
                result = {
                    "title": "Document Analysis",
                    "content": str(result),
                    "learning_analysis": {
                        "difficulty_level": "Not analyzed",
                        "prerequisites": [],
                        "study_tips": []
                    }
                }
            
            # Add default learning sections if missing
            if "learning_analysis" not in result:
                result["learning_analysis"] = {
                    "difficulty_level": "Not analyzed",
                    "prerequisites": [],
                    "study_tips": []
                }
            
            if "practice_material" not in result:
                result["practice_material"] = {
                    "examples": [],
                    "exercises": [],
                    "common_mistakes": []
                }
            
            if "additional_resources" not in result:
                result["additional_resources"] = {
                    "related_topics": [],
                    "reference_materials": []
                }
                
            return result
            
        except json.JSONDecodeError:
            return {
                "title": "Document Analysis",
                "content": response.text,
                "learning_analysis": {
                    "difficulty_level": "Not analyzed",
                    "prerequisites": [],
                    "study_tips": []
                }
            }
            
    except Exception as e:
        raise Exception(f"Error processing PDF with Gemini: {str(e)}")

def format_structured_output(structured_content: Dict[str, Any]) -> str:
    """Format the structured content into a readable string format"""
    output = []
    
    # Add title
    output.append(f"# {structured_content.get('title', 'Document Analysis')}\n")
    
    # Add metadata
    metadata = structured_content.get('metadata', {})
    output.append("## Document Information")
    output.append(f"- Type: {metadata.get('type', 'unknown')}")
    output.append(f"- Subject Area: {metadata.get('subject_area', 'unknown')}")
    output.append(f"- Content Quality: {metadata.get('content_quality', 'unknown')}")
    output.append(f"- Total Pages: {metadata.get('total_pages', 'unknown')}\n")
    
    # Add summary if available
    if 'summary' in structured_content:
        output.append("## Summary")
        output.append(structured_content['summary'] + "\n")
    
    # Add pages and sections
    for page in structured_content.get('pages', []):
        output.append(f"### Page {page.get('page_number', 'unknown')}")
        for section in page.get('sections', []):
            output.append(f"#### {section.get('heading', 'Section')}")
            output.append(section.get('content', ''))
            
            # Add equations if present
            if section.get('equations'):
                output.append("\nEquations:")
                for eq in section['equations']:
                    output.append(f"  {eq}")
            
            # Add key points if present
            if section.get('key_points'):
                output.append("\nKey Points:")
                for point in section['key_points']:
                    output.append(f"- {point}")
            output.append("")  # Add spacing between sections
    
    # Add notes if present
    if structured_content.get('notes'):
        output.append("## Important Notes")
        for note in structured_content['notes']:
            output.append(f"- {note}")
    
    return "\n".join(output)

def main():
    pdf_path = "new1.pdf"
    print("Processing PDF with enhanced formatting...")
    try:
        structured_content = process_pdf_with_gemini(pdf_path)
        formatted_output = format_structured_output(structured_content)
        print("\nProcessed Content:")
        print(formatted_output)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
