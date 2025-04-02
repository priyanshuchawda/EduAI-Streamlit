import os
from google import genai
from google.genai import types
from typing import Dict, Any, List, Union
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import tempfile

def analyze_pyq_patterns(content: Union[str, bytes], subject: str, is_pdf: bool = False) -> Dict[str, Any]:
    """Analyze past year questions using Gemini AI with direct PDF support"""
    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Prepare the analysis prompt
        analysis_prompt = """
        Analyze these past year questions in detail. Consider all content including text, diagrams, tables, and equations.
        
        Provide a comprehensive analysis with:
        1. Question patterns and their frequency
        2. Topic distribution and predictions
        3. Difficulty levels analysis
        4. Visual elements analysis (diagrams, graphs, tables)
        5. Mathematical/technical complexity assessment
        6. Practice questions based on patterns
        
        Format the response in JSON with these exact fields:
        {
            "question_patterns": [
                {
                    "pattern_type": "pattern description",
                    "frequency": "occurrence rate",
                    "example": "example question"
                }
            ],
            "topics": [
                {
                    "name": "topic name",
                    "frequency": "number of occurrences",
                    "predicted_probability": "likelihood for next exam",
                    "importance_level": "HIGH/MEDIUM/LOW"
                }
            ],
            "difficulty_distribution": {
                "easy": "percentage",
                "medium": "percentage",
                "hard": "percentage"
            },
            "visual_elements_analysis": {
                "diagrams": ["analysis of diagram types and complexity"],
                "tables": ["analysis of table types and usage"],
                "graphs": ["analysis of graph types and complexity"]
            }
        }"""

        if subject:
            analysis_prompt += f"\n\nThis is for the subject: {subject}. Analyze according to {subject}-specific criteria."

        # Build the list of content items
        if is_pdf:
            # Save the PDF bytes to a temporary file and upload it
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf.write(content)
                temp_pdf.flush()
                temp_pdf_path = temp_pdf.name
            try:
                uploaded_file = client.files.upload(file=temp_pdf_path)
            finally:
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
            # Pass a list containing the prompt and the uploaded file directly
            contents = [analysis_prompt, uploaded_file]
        else:
            # For text, simply use the prompt and the text content
            contents = [analysis_prompt, content]

        # Generate content using Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # Using flash model for fast diagram/table understanding
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json"
            )
        )
        
        if response and response.text:
            return json.loads(response.text)
        
        return {}
    except Exception as e:
        raise Exception(f"Error analyzing questions: {str(e)}")


def generate_practice_questions(analysis: Dict[str, Any], subject: str, num_questions: int = 5) -> List[Dict[str, Any]]:
    """Generate practice questions based on analysis patterns"""
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Create prompt for generating questions
        generation_prompt = f"""
        Based on this analysis of past questions, generate {num_questions} practice questions for {subject}.
        Follow the detected patterns and difficulty distribution.
        Include questions with diagrams or visual elements if they were present in the original papers.
        
        For each question, provide:
        1. The question text
        2. Topic covered
        3. Difficulty level
        4. Expected time
        5. Marks allocation
        6. Detailed answer
        7. Step-by-step explanation
        
        Format each question as a JSON object in a list:
        [
            {{
                "question": "question text",
                "topic": "topic name",
                "difficulty": "EASY/MEDIUM/HARD",
                "time": "expected time in minutes",
                "marks": "marks allocated",
                "answer": "detailed answer",
                "explanation": "step-by-step explanation"
            }}
        ]
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=generation_prompt),
                        types.Part.from_text(text=json.dumps(analysis))
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json"
            )
        )
        
        if response and response.text:
            return json.loads(response.text)
        
        return []
    except Exception as e:
        raise Exception(f"Error generating practice questions: {str(e)}")


def get_exam_preparation_guide(analysis: Dict[str, Any], subject: str) -> Dict[str, Any]:
    """Generate exam preparation guide based on analysis"""
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Create prompt for generating study guide
        guide_prompt = f"""
        Based on the analysis of past questions for {subject}, create a comprehensive exam preparation guide.
        Consider the pattern frequency, topic importance, and difficulty distribution.
        
        Format the guide as a JSON with this structure:
        {{
            "subject_guide": {{
                "key_topics": [
                    {{
                        "topic": "topic name",
                        "preparation_time": "recommended hours",
                        "focus_points": ["key points to study"],
                        "practice_strategy": "detailed approach",
                        "common_mistakes": ["mistakes to avoid"]
                    }}
                ],
                "time_management": {{
                    "total_preparation_hours": "total hours needed",
                    "topic_wise_distribution": {{
                        "topic": "hours"
                    }},
                    "revision_strategy": "detailed revision approach"
                }}
            }},
            "pattern_guide": {{
                "question_types": [
                    {{
                        "type": "question type",
                        "typical_marks": "marks allocated",
                        "frequency": "how often it appears",
                        "approach_strategy": "how to tackle this type",
                        "sample_structure": "expected answer structure"
                    }}
                ]
            }}
        }}
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(
                role="user", 
                parts=[
                    types.Part.from_text(text=guide_prompt),
                    types.Part.from_text(text=json.dumps(analysis))
                ]
            )],
            config=types.GenerateContentConfig(
                temperature=0.5,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json"
            )
        )
        
        if response and response.text:
            return json.loads(response.text)
            
        return {}
    except Exception as e:
        raise Exception(f"Error generating exam guide: {str(e)}")
    
def safe_float(val):
    try:
        # Remove any percentage signs if present
        if isinstance(val, str):
            val = val.strip().replace('%', '')
        return float(val)
    except Exception:
        return 0.0

def generate_topic_visualizations(analysis: Dict[str, Any]) -> Dict[str, plt.Figure]:
    """Generate visualizations for PYQ analysis results"""
    visualizations = {}
    
    # Set theme for all plots using seaborn
    sns.set_theme(style="whitegrid")
    
    # 1. Topic frequency and predictions visualization
    fig_topics = plt.figure(figsize=(12, 6))
    topics_data = analysis.get('topics', [])
    
    # Use safe_float for conversion; if conversion fails, default to 0.0.
    topics = [t.get('name', 'Unknown') for t in topics_data]
    frequencies = [safe_float(t.get('frequency', 0)) for t in topics_data]
    predictions = [
        safe_float(t.get('predicted_probability', 0)) 
        for t in topics_data
    ]
    
    x = np.arange(len(topics))
    width = 0.35
    
    ax = fig_topics.add_subplot(111)
    ax.bar(x - width/2, frequencies, width, label='Past Frequency', color='skyblue')
    ax.bar(x + width/2, predictions, width, label='Predicted Probability', color='lightcoral')
    
    ax.set_title('Topic Analysis: Past Frequency vs Future Prediction')
    ax.set_xticks(x)
    ax.set_xticklabels(topics, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    visualizations['topics'] = fig_topics
    
    # 2. Difficulty distribution pie chart
    fig_difficulty = plt.figure(figsize=(8, 8))
    difficulty_data = analysis.get('difficulty_distribution', {})
    difficulties = list(difficulty_data.keys())
    percentages = [safe_float(v) for v in difficulty_data.values()]
    
    plt.pie(percentages, labels=difficulties, autopct='%1.1f%%',
            colors=['lightgreen', 'gold', 'lightcoral'])
    plt.title('Question Difficulty Distribution')
    visualizations['difficulty'] = fig_difficulty
    
    # 3. Question types analysis
    fig_types = plt.figure(figsize=(10, 6))
    patterns = analysis.get('question_patterns', [])
    pattern_types = [p.get('pattern_type', 'Unknown') for p in patterns]
    pattern_freqs = [safe_float(p.get('frequency', 0)) for p in patterns]
    
    plt.barh(pattern_types, pattern_freqs, color='lightblue')
    plt.title('Question Pattern Distribution')
    plt.xlabel('Frequency (%)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    visualizations['question_types'] = fig_types
    
    return visualizations
