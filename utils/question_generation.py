import streamlit as st
import json
from google.genai import types
import sys
from pathlib import Path
from typing import List, Dict, Any
import json
from io import BytesIO
import csv
import os

# Add the project root to Python path
root_path = str(Path(__file__).parent.parent)
if (root_path not in sys.path):
    sys.path.insert(0, root_path)

from src.config import client, model

QUESTION_TYPES = {
    "Short Answer": {
        "structure": "direct question requiring concise response",
        "cognitive_level": "comprehension, application",
        "format": "brief answer format"
    },
    "Essay": {
        "structure": "open-ended analytical question",
        "cognitive_level": "analysis, synthesis, evaluation",
        "format": "extended response with arguments"
    },
    "Problem Solving": {
        "structure": "scenario-based question with steps",
        "cognitive_level": "application, analysis",
        "format": "structured solution approach"
    },
    "True/False": {
        "structure": "statement to evaluate",
        "cognitive_level": "knowledge",
        "format": "binary choice with explanation"
    },
    "Fill in the Blanks": {
        "structure": "sentence with missing words",
        "cognitive_level": "recall, comprehension",
        "format": "completion task"
    },
    "Diagram Based": {
        "structure": "visual with related questions",
        "cognitive_level": "application, analysis",
        "format": "interpretation of visuals"
    }
}

DIFFICULTY_LEVELS = {
    "Easy": {
        "cognitive_demand": "Basic recall and understanding",
        "time_allocation": "1-2 minutes",
        "marks_range": "1-2 marks",
        "complexity": "Single concept, straightforward application"
    },
    "Medium": {
        "cognitive_demand": "Application and analysis",
        "time_allocation": "3-5 minutes",
        "marks_range": "3-4 marks",
        "complexity": "Multiple concepts, some problem-solving"
    },
    "Hard": {
        "cognitive_demand": "Analysis, synthesis, evaluation",
        "time_allocation": "5-10 minutes",
        "marks_range": "5-8 marks",
        "complexity": "Complex problem-solving, multiple steps"
    },
    "Mixed": {
        "cognitive_demand": "Varied levels",
        "time_allocation": "Varied",
        "marks_range": "1-8 marks",
        "complexity": "Combination of different levels"
    }
}

def generate_and_display_questions(subject: str, topic: str, difficulty: str, num_questions: int, 
                                question_types: list, description: str = "") -> List[Dict[str, Any]]:
    """Generate and display questions based on the given parameters"""
    with st.spinner("Generating questions..."):
        instruction = f"""Create {num_questions} {difficulty.lower()} difficulty {subject} questions about '{topic}'.
        
Question Types to Include ({', '.join(question_types)}):
{json.dumps([QUESTION_TYPES[qt] for qt in question_types], indent=2)}

Difficulty Level Parameters:
{json.dumps(DIFFICULTY_LEVELS[difficulty], indent=2)}

Additional Requirements:
1. Each question should match the specified difficulty parameters
2. Include a mix of theoretical and practical questions
3. Incorporate real-world applications where relevant
4. For mathematical/scientific topics, include step-by-step solutions
5. Add diagrams/visual descriptions where appropriate
6. Include misconception warnings in explanations
7. Provide marking scheme guidelines

Additional Context: {description}

Format each question as a JSON object with:
{{
    "question": "detailed question text",
    "type": "question type from the specified list",
    "difficulty": "actual difficulty level",
    "expected_time": "time in minutes",
    "marks": "marks allocated",
    "answer": "complete answer",
    "explanation": "detailed explanation with steps",
    "common_mistakes": ["list of common errors to avoid"],
    "marking_scheme": ["points allocation details"],
    "prerequisites": ["concepts needed to answer"],
    "visual_aids": "description of any diagrams/visuals needed"
}}"""
        
        contents = [
            types.Content(
                role="user",
                parts=[{"text": instruction}]
            )
        ]

        config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="application/json"
        )
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=config
            )
            
            # Clean and validate JSON response
            try:
                response_text = response.text.strip()
                # Handle case where response might be wrapped in ```json ... ```
                if response_text.startswith('```json'):
                    response_text = response_text.split('```json')[1]
                if response_text.endswith('```'):
                    response_text = response_text.rsplit('```', 1)[0]
                    
                questions = json.loads(response_text.strip())
                
                # Ensure response is a list
                if not isinstance(questions, list):
                    if isinstance(questions, dict):
                        questions = [questions]
                    else:
                        raise ValueError("Response must be a list of questions or a single question object")
                
                # Force generation of multiple questions if only one was returned
                if len(questions) < num_questions:
                    st.warning(f"Only {len(questions)} question(s) were generated. Generating more...")
                    # Make another API call to get remaining questions
                    remaining = num_questions - len(questions)
                    instruction_remaining = instruction.replace(str(num_questions), str(remaining))
                    contents_remaining = [
                        types.Content(
                            role="user",
                            parts=[{"text": instruction_remaining}]
                        )
                    ]
                    response_remaining = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=contents_remaining,
                        config=config
                    )
                    
                    # Parse and validate remaining questions
                    remaining_text = response_remaining.text.strip()
                    if remaining_text.startswith('```json'):
                        remaining_text = remaining_text.split('```json')[1]
                    if remaining_text.endswith('```'):
                        remaining_text = remaining_text.rsplit('```', 1)[0]
                        
                    remaining_questions = json.loads(remaining_text.strip())
                    if not isinstance(remaining_questions, list):
                        if isinstance(remaining_questions, dict):
                            remaining_questions = [remaining_questions]
                        else:
                            raise ValueError("Response must be a list of questions or a single question object")
                            

                    questions.extend(remaining_questions)
                
                # Validate required fields
                required_fields = ['question', 'type', 'difficulty', 'expected_time', 'marks', 'answer', 'explanation']
                for q in questions:
                    missing_fields = [field for field in required_fields if field not in q]
                    if missing_fields:
                        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            except json.JSONDecodeError as je:
                st.error(f"Invalid JSON response: {str(je)}")
                return []
            except ValueError as ve:
                st.error(f"Invalid question format: {str(ve)}")
                return []
            
            # Display generated questions
            st.success(f"✅ Generated {len(questions)} questions on {topic} ({difficulty})")
            
            # Display questions in an enhanced format
            for i, q in enumerate(questions, 1):
                with st.expander(f"Question {i}: {q['type']}", expanded=i==1):
                    # Create tabs for different sections
                    question_tab, answer_tab, details_tab = st.tabs(["Question", "Answer", "Additional Details"])
                    
                    with question_tab:
                        st.markdown("### Question")
                        st.write(q['question'])
                        
                        # Question metadata
                        meta_col1, meta_col2, meta_col3 = st.columns(3)
                        with meta_col1:
                            st.info(f"⏱️ Time: {q['expected_time']}")
                        with meta_col2:
                            st.info(f"📊 Marks: {q['marks']}")
                        with meta_col3:
                            st.info(f"📈 Difficulty: {q['difficulty']}")
                        
                        # Visual aids if present
                        if q.get('visual_aids'):
                            st.markdown("### Visual Aid")
                            st.info(q['visual_aids'])
                    
                    with answer_tab:
                        st.markdown("### Answer")
                        st.success(q['answer'])
                        
                        st.markdown("### Detailed Explanation")
                        st.write(q['explanation'])
                    
                    with details_tab:
                        # Common mistakes
                        if q.get('common_mistakes'):
                            st.markdown("### ⚠️ Common Mistakes to Avoid")
                            for mistake in q['common_mistakes']:
                                st.warning(mistake)
                        
                        # Marking scheme
                        if q.get('marking_scheme'):
                            st.markdown("### 📝 Marking Scheme")
                            for point in q['marking_scheme']:
                                st.info(point)
                        
                        # Prerequisites
                        if q.get('prerequisites'):
                            st.markdown("### 📚 Prerequisites")
                            for prereq in q['prerequisites']:
                                st.write(f"- {prereq}")

            return questions

        except Exception as e:
            st.error(f"Error generating questions: {str(e)}")
            return []

def export_to_csv(questions: list, subject: str, topic: str, difficulty: str) -> bytes:
    """Convert questions to CSV format with enhanced fields"""
    from io import StringIO
    output = StringIO()
    writer = csv.writer(output, lineterminator='\n')
    
    # Enhanced header with all fields
    headers = [
        'Subject', 'Topic', 'Difficulty', 'Question Type', 'Question', 
        'Expected Time', 'Marks', 'Answer', 'Explanation', 
        'Common Mistakes', 'Marking Scheme', 'Prerequisites', 'Visual Aids'
    ]
    writer.writerow(headers)
    
    # Write questions with all available data
    for q in questions:
        row = [
            subject,
            topic,
            q['difficulty'],
            q['type'],
            q['question'],
            q['expected_time'],
            q['marks'],
            q['answer'],
            q['explanation'],
            '; '.join(str(x) for x in q.get('common_mistakes', [])),
            '; '.join(str(x) for x in q.get('marking_scheme', [])),
            '; '.join(str(x) for x in q.get('prerequisites', [])),
            q.get('visual_aids', '')
        ]
        # Convert all values to strings
        row = [str(value) for value in row]
        writer.writerow(row)
    
    # Get the value and encode as UTF-8 with BOM for Excel compatibility
    return b'\xef\xbb\xbf' + output.getvalue().encode('utf-8')