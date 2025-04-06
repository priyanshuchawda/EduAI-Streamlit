import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import sys
from pathlib import Path
import tempfile

# Add the project root to Python path
root_path = str(Path(__file__).parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

def setup_environment():
    """Setup environment variables from Streamlit secrets or .env file"""
    if hasattr(st, 'secrets'):
        # We're on Streamlit Cloud, use secrets
        for key, value in st.secrets.items():
            os.environ[key] = str(value)
            
        # Special handling for the service account credentials
        service_account_keys = {
            "type": "service_account",
            "project_id": os.environ.get("GOOGLE_PROJECT_ID"),
            "private_key_id": os.environ.get("GOOGLE_PRIVATE_KEY_ID"),
            "private_key": os.environ.get("GOOGLE_PRIVATE_KEY"),
            "client_email": os.environ.get("GOOGLE_CLIENT_EMAIL"),
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "auth_uri": os.environ.get("GOOGLE_AUTH_URI"),
            "token_uri": os.environ.get("GOOGLE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.environ.get("GOOGLE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.environ.get("GOOGLE_CLIENT_CERT_URL"),
            "universe_domain": os.environ.get("GOOGLE_UNIVERSE_DOMAIN", "googleapis.com")
        }
        
        # Create temporary credentials file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(service_account_keys, f)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
    else:
        # We're running locally, use python-dotenv
        from dotenv import load_dotenv
        load_dotenv()

# Setup environment before importing other modules
setup_environment()

# Import configurations from the new structure
from src.config import APP_CONFIG, CUSTOM_CSS
from src.config.client import client, model

# Import components
from src.components.home import show_home_page
from src.components.grading import show_grading_page
from src.components.upload import show_upload_page
from src.components.analysis import show_analysis_page
from src.components.calendar import show_calendar_sidebar
from src.components.calendar_page import show_calendar_page
from src.components.syllabus import show_syllabus_page
from src.components.pyq_analysis_page import show_pyq_analysis_page

# Import utilities
from utils.ai_grading import grade_assignment
from utils.feedback_display import display_feedback
from utils.sample_data import get_sample_assignments, get_sample_questions
from utils.chat_processing import (
    process_chat_message,
    TEACHING_CONTEXTS
)
from utils.question_generation import (
    generate_and_display_questions, 
    export_to_csv,
    QUESTION_TYPES
)

# Import other modules
from pdf_to_text import process_pdf_with_gemini

# Define all page functions first
def show_teacher_chat():
    """Display the enhanced teacher chat interface"""
    st.title("💬 Teacher Assistant Chat")
    st.write("Get expert guidance on teaching methods, assessment strategies, and educational resources.")
    
    # Add teaching context selector in sidebar
    with st.sidebar:
        st.subheader("🎯 Focus Area")
        context = st.selectbox(
            "Select teaching context",
            list(TEACHING_CONTEXTS.keys()),
            format_func=lambda x: TEACHING_CONTEXTS[x],
            help="Choose a specific area to focus the AI's responses"
        )
        
        # Display saved resources if any
        if 'teaching_resources' in st.session_state and st.session_state.teaching_resources:
            st.subheader("📚 Saved Resources")
            for resource in st.session_state.teaching_resources:
                st.markdown(f"- {resource}")
            
            if st.button("Clear Resources"):
                st.session_state.teaching_resources = []
    
    # Initialize chat history if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history with enhanced formatting
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(message["content"])
            else:
                st.write(message["content"])
    
    # Chat input with suggested prompts
    if not st.session_state.chat_history:
        st.info("Try asking about:")
        cols = st.columns(2)
        with cols[0]:
            st.markdown("""\
            - Lesson planning strategies
            - Assessment techniques
            - Classroom management tips
            """)
        with cols[1]:
            st.markdown("""\
            - Student engagement ideas
            - Differentiated instruction
            - Educational technology tools
            """)
    
    # Chat input
    user_question = st.chat_input("Ask a question about teaching:")
    if user_question:
        process_chat_message(user_question, context)

# Page configuration
st.set_page_config(
    page_title="EduAI Assistant",
    page_icon="🎓",
    layout="wide"
)

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Display calendar in sidebar for all pages
show_calendar_sidebar()

# Main navigation
st.sidebar.title("🎓 EduAI Assistant")
page = st.sidebar.radio(
    "Navigate to:",
    ["Home", "Grading", "Analysis", "Calendar", "Syllabus", "PYQ Analysis", "Teacher Chat"]
)

# Route to appropriate page based on navigation
if page == "Home":
    show_home_page()
elif page == "Grading":
    show_grading_page()
elif page == "Analysis":
    show_analysis_page()
elif page == "Calendar":
    show_calendar_page()
elif page == "Syllabus":
    show_syllabus_page()
elif page == "PYQ Analysis":
    show_pyq_analysis_page()
elif page == "Teacher Chat":
    show_teacher_chat()