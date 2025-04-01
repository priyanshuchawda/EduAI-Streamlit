import streamlit as st
import base64
import os
from google import genai
from google.genai import types
from typing import Dict, Any, List
import json

TEACHING_CONTEXTS = {
    "lesson_planning": "Help with creating effective lesson plans",
    "assessment": "Guidance on assessment methods and rubrics",
    "methodology": "Teaching methodology and best practices",
    "differentiation": "Strategies for differentiated instruction",
    "feedback": "How to provide effective feedback",
    "resources": "Educational resources and materials"
}

def process_chat_message(user_question: str, context: str = None):
    """Process a chat message and generate AI response with teaching context"""
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_question})
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_question)
        
    # Display assistant response with a spinner
    with st.chat_message("assistant"):
        with st.spinner("AI is thinking..."):
            # Create prompt with role context
            prompt = f"""As an expert teacher assistant, help with this question: {user_question}

Key areas of expertise:
1. Educational pedagogy and teaching methodologies
2. Assessment strategies and feedback techniques
3. Curriculum development and lesson planning
4. Student engagement and classroom management
5. Educational technology and resources
6. Differentiated instruction strategies

Provide practical, actionable advice based on modern educational research.
Include specific examples and resources when relevant.
Format your response in clear paragraphs with proper spacing."""

            if context:
                prompt += f"\n\nFocus area: {TEACHING_CONTEXTS[context]}"

            try:
                # Create Gemini client
                client = genai.Client(
                    api_key=os.environ.get("GEMINI_API_KEY"),
                )

                # Configure the model and content
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                        ],
                    ),
                ]

                # Configure generation parameters
                generate_content_config = types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=8192,
                    response_mime_type="text/plain",
                )

                # Initialize placeholder for streaming response
                placeholder = st.empty()
                response_text = ""
                formatted_text = ""
                buffer = ""

                # Stream the response with better formatting
                for chunk in client.models.generate_content_stream(
                    model="gemini-2.0-flash",
                    contents=contents,
                    config=generate_content_config,
                ):
                    if chunk.text:
                        buffer += chunk.text
                        # Process complete sentences or paragraphs
                        if any(char in buffer for char in ['.', '!', '?', '\n']):
                            formatted_chunk = format_teaching_response(buffer)
                            response_text += buffer
                            formatted_text += formatted_chunk
                            # Update the display with the complete formatted text
                            placeholder.markdown(formatted_text)
                            buffer = ""
                
                # Handle any remaining text in buffer
                if buffer:
                    formatted_chunk = format_teaching_response(buffer)
                    response_text += buffer
                    formatted_text += formatted_chunk
                    placeholder.markdown(formatted_text)
                
                # Add complete response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                
                # Save relevant teaching resources if provided
                if "resources:" in response_text.lower():
                    save_teaching_resources(response_text)
                
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")

def format_teaching_response(response: str) -> str:
    """Format the AI response with proper markdown and structure"""
    # Remove extra newlines
    response = response.strip()
    
    # Split into paragraphs
    paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
    formatted_paragraphs = []
    
    for paragraph in paragraphs:
        # Add headers
        if paragraph.startswith(('How to', 'Tips for', 'Steps to')):
            paragraph = f"### {paragraph}"
        # Add bullet points
        elif paragraph.strip().startswith(('-', '•')):
            # Ensure proper spacing for bullet points
            lines = paragraph.split('\n')
            paragraph = '\n'.join(line.strip() for line in lines)
            paragraph = paragraph.replace('•', '-')
        # Highlight important points
        paragraph = paragraph.replace('[Important]', '**Important:**')
        paragraph = paragraph.replace('[Tip]', '**Tip:**')
        paragraph = paragraph.replace('[Example]', '**Example:**')
        
        formatted_paragraphs.append(paragraph)
    
    # Join paragraphs with proper spacing
    formatted_text = '\n\n'.join(formatted_paragraphs)
    
    # Clean up any remaining multiple newlines
    formatted_text = '\n'.join(line for line in formatted_text.splitlines() if line.strip())
    
    return formatted_text

def save_teaching_resources(response: str) -> None:
    """Save teaching resources mentioned in the response"""
    if 'st.session_state.teaching_resources' not in st.session_state:
        st.session_state.teaching_resources = []
    
    # Extract resources section
    if "resources:" in response.lower():
        resources_section = response.lower().split("resources:")[1].split("\n\n")[0]
        resources = [r.strip() for r in resources_section.split("\n") if r.strip()]
        st.session_state.teaching_resources.extend(resources)
