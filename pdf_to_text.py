import os
import json
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

def process_pdf_with_gemini(pdf_path: str) -> Dict[str, Any]:
    """
    Process PDF with enhanced text extraction and formatting.
    Handles both typed and handwritten content with improved structure.
    """
    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Enhanced prompt for better text extraction with explicit JSON response requirement
        processing_prompt = """You are a PDF content processor. Your task is to extract and structure the content from this PDF document.

        CRITICAL REQUIREMENTS:
        1. You MUST return your response in valid JSON format ONLY
        2. Analyze the content type (handwriting vs typed)
        3. Identify the subject area and main topic
        4. Structure the content logically
        5. Format any mathematical content properly
        6. Extract teacher's notes and comments exactly as written

        Return ONLY a JSON object with this EXACT structure (no other text):
        {
            "title": "exact main title from document or clear topic description",
            "metadata": {
                "type": "typed/handwritten/mixed",
                "subject_area": "math/science/english/etc",
                "content_quality": "clear/legible/partially legible/etc"
            },
            "original_notes": {
                "teacher_comments": ["exact comment 1", "exact comment 2"],
                "margin_notes": ["note 1", "note 2"],
                "corrections": ["correction 1", "correction 2"]
            },
            "sections": [
                {
                    "heading": "clear section name",
                    "content": "formatted text content with proper spacing and line breaks",
                    "equations": ["equation 1", "equation 2"],
                    "key_points": ["key point 1", "key point 2"]
                }
            ],
            "summary": "brief content overview",
            "notes": ["important note 1", "important note 2"]
        }

        For handwritten content:
        - Clean up messy handwriting
        - Fix spelling/grammar while preserving meaning
        - Format equations properly
        - Maintain original structure
        - Preserve teacher's annotations exactly as written

        IMPORTANT: Your response must be ONLY the JSON object, no other text or explanation."""

        # Read and process the PDF file
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        # Create parts array for the request
        parts = [
            {"text": processing_prompt},
            {
                "inline_data": {
                    "mime_type": "application/pdf",
                    "data": base64.b64encode(pdf_bytes).decode('utf-8')
                }
            }
        ]
        
        # Generate content using the uploaded PDF
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{
                "role": "user",
                "parts": parts
            }],
            config=types.GenerateContentConfig(
                temperature=0.1,  # Lower temperature for more consistent formatting
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json"  # Enforce JSON response
            )
        )
        
        if response and response.text:
            try:
                # Remove any non-JSON text that might be in the response
                json_str = response.text.strip()
                # Find the first { and last } to extract just the JSON object
                start = json_str.find('{')
                end = json_str.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = json_str[start:end]
                
                # Parse the JSON response
                result = json.loads(json_str)
                
                # Validate required fields
                if not result.get('title'):
                    result['title'] = "Untitled Document"
                if not result.get('metadata'):
                    result['metadata'] = {
                        "type": "mixed",
                        "subject_area": "general",
                        "content_quality": "processed"
                    }
                if not result.get('original_notes'):
                    result['original_notes'] = {
                        "teacher_comments": [],
                        "margin_notes": [],
                        "corrections": []
                    }
                if not result.get('sections'):
                    # Create at least one section with the content
                    result['sections'] = [{
                        "heading": "Main Content",
                        "content": json_str,
                        "equations": [],
                        "key_points": []
                    }]
                
                return result
                
            except json.JSONDecodeError as e:
                # Create a structured response from unstructured text
                clean_text = response.text.strip()
                return {
                    "title": "Processed Document",
                    "metadata": {
                        "type": "processed",
                        "subject_area": "general",
                        "content_quality": "processed"
                    },
                    "original_notes": {
                        "teacher_comments": [],
                        "margin_notes": [],
                        "corrections": []
                    },
                    "sections": [{
                        "heading": "Main Content",
                        "content": clean_text,
                        "equations": [],
                        "key_points": []
                    }],
                    "summary": "Document has been processed and content extracted",
                    "notes": []
                }
        else:
            raise Exception("No text extracted from PDF")
            
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
    output.append(f"- Content Quality: {metadata.get('content_quality', 'unknown')}\n")
    
    # Add summary if available
    if 'summary' in structured_content:
        output.append("## Summary")
        output.append(structured_content['summary'] + "\n")
    
    # Add sections
    for section in structured_content.get('sections', []):
        output.append(f"## {section.get('heading', 'Section')}")
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
