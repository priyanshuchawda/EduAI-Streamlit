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

# Import configurations from the new structure
from src.config import APP_CONFIG, CUSTOM_CSS
from src.config.client import client, model

# Import components
from src.components.home import show_home_page
from src.components.grading import show_grading_page
from src.components.upload import show_upload_page
from src.components.analysis import show_analysis_page

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
from parent_report import generate_parent_report
from pyq_analysis import (
    analyze_pyq_patterns,
    generate_topic_visualizations,
    generate_practice_questions,
    get_exam_preparation_guide
)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"
    if 'uploaded_text' not in st.session_state:
        st.session_state.uploaded_text = None
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None
    if 'grading_history' not in st.session_state:
        st.session_state.grading_history = []
    if 'first_visit' not in st.session_state:
        st.session_state.first_visit = True
    if 'student_info' not in st.session_state:
        st.session_state.student_info = {
            'name': '',
            'grade_level': '',
            'teacher_contact': ''
        }
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pyq_analysis" not in st.session_state:
        st.session_state.pyq_analysis = None
    if "current_subject" not in st.session_state:
        st.session_state.current_subject = None

def setup_page():
    """Configure page settings and apply custom theme"""
    st.set_page_config(**APP_CONFIG)
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def show_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/yourusername/eduai-assistant/main/assets/logo.png", width=100)
        st.title("🎓 EduAI Assistant")
        
        # Navigation with tooltips
        pages = {
            "Home": {
                "icon": "🏠",
                "tooltip": "Overview and getting started guide"
            },
            "Upload Assignment": {
                "icon": "📝",
                "tooltip": "Upload and process PDF assignments"
            },
            "PYQ Analysis": {
                "icon": "🔍",
                "tooltip": "Analyze past year questions and predict patterns"
            },
            "Grading": {
                "icon": "✍️",
                "tooltip": "Grade assignments with AI assistance"
            },
            "Student Analysis": {
                "icon": "📊",
                "tooltip": "View student performance analytics"
            },
            "Parent Reports": {
                "icon": "📋",
                "tooltip": "Generate weekly summary reports for parents"
            },
            "Question Bank": {
                "icon": "❓",
                "tooltip": "Generate custom questions"
            },
            "Teacher Chat": {
                "icon": "💬",
                "tooltip": "Get teaching assistance and advice"
            }
        }
        
        st.session_state.current_page = st.radio(
            "Navigation",
            list(pages.keys()),
            format_func=lambda x: f"{pages[x]['icon']} {x}",
            help="Select a feature to use",
            key="navigation"
        )
        
        # Show tooltip for current page
        st.info(pages[st.session_state.current_page]["tooltip"])
        
        # Version and about information
        st.sidebar.divider()
        st.sidebar.caption("v1.0.0 | Made with ❤️ for educators")

def main():
    """Main application entry point"""
    # Initialize session state and setup page
    init_session_state()
    setup_page()
    
    # Show sidebar navigation
    show_sidebar()
    
    # Route to appropriate page based on navigation
    if st.session_state.current_page == "Home":
        show_home_page()
    elif st.session_state.current_page == "Upload Assignment":
        show_upload_page()
    elif st.session_state.current_page == "Grading":
        show_grading_page()
    elif st.session_state.current_page == "Student Analysis":
        show_analysis_page()
    elif st.session_state.current_page == "Parent Reports":
        show_parent_reports()
    elif st.session_state.current_page == "PYQ Analysis":
        show_pyq_analysis()
    elif st.session_state.current_page == "Question Bank":
        show_question_bank()
    elif st.session_state.current_page == "Teacher Chat":
        show_teacher_chat()

def show_parent_reports():
    """Display the parent reports page"""
    st.title("📋 Parent Report Generator")
    st.write("Generate detailed weekly progress reports for parents with QR codes for quick access.")

    # Student Information Form
    with st.form("student_info_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            student_name = st.text_input(
                "Student Name",
                value=st.session_state.student_info['name']
            )
            
        with col2:
            grade_level = st.text_input(
                "Grade Level",
                value=st.session_state.student_info['grade_level']
            )
        
        teacher_contact = st.text_input(
            "Teacher Contact Information (for QR code)",
            value=st.session_state.student_info['teacher_contact'],
            help="Enter email, phone, or any contact information to be encoded in QR code"
        )
        
        next_assignment_url = st.text_input(
            "Next Assignment URL (for QR code)",
            help="Enter the URL where parents can find the next assignment"
        )
        
        submitted = st.form_submit_button("Save Information")
        
        if submitted:
            st.session_state.student_info = {
                'name': student_name,
                'grade_level': grade_level,
                'teacher_contact': teacher_contact
            }
            st.success("✅ Student information saved!")
    
    # Check if we have grading history
    if st.session_state.grading_history and st.session_state.feedback:
        if st.button("Generate Weekly Report"):
            try:
                with st.spinner("Generating parent report..."):
                    # Convert grading history to the expected format
                    formatted_history = []
                    for entry in st.session_state.grading_history:
                        formatted_history.append({
                            'date': entry['timestamp'].strftime('%Y-%m-%d') if isinstance(entry['timestamp'], pd.Timestamp) else entry['timestamp'],
                            'percentage': entry['grade'],
                            'feedback': entry.get('feedback', {})
                        })
                    
                    # Generate the report
                    pdf_data = generate_parent_report(
                        student_name=st.session_state.student_info['name'],
                        grade_level=st.session_state.student_info['grade_level'],
                        grades_history=formatted_history,
                        latest_feedback=st.session_state.feedback,
                        teacher_contact=st.session_state.student_info['teacher_contact'],
                        next_assignment_url=next_assignment_url
                    )
                    
                    # Prepare the download button
                    st.download_button(
                        label="📥 Download Report PDF",
                        data=pdf_data,
                        file_name=f"progress_report_{student_name}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                    
                    st.success("✅ Report generated successfully!")
                    
                    # Preview section
                    with st.expander("📊 Report Preview", expanded=True):
                        st.write("### Report Contents:")
                        st.write("1. Student Information")
                        st.write("2. Performance Summary Graph")
                        st.write("3. Latest Assessment Results")
                        st.write("4. Strengths and Areas for Improvement")
                        st.write("5. Personalized Improvement Plan")
                        st.write("6. QR Codes for Quick Access")
                        
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
    else:
        st.warning("⚠️ No grading history available. Please grade some assignments first.")

def show_pyq_analysis():
    """Display the PYQ analysis page"""
    st.title("🔍 Past Year Questions Analysis")
    st.write("Upload past year question papers to analyze patterns and predict future questions.")
    
    # Subject selection
    subject = st.selectbox(
        "Select Subject",
        ["Mathematics", "Science", "English", "Physics", "Chemistry", "Biology", "History", "Computer Science"],
        help="Choose the subject to analyze"
    )
    
    # File upload section
    uploaded_files = st.file_uploader(
        "Upload Past Year Question Papers (PDF/Text)", 
        type=['pdf', 'txt'],
        accept_multiple_files=True,
        help="Upload one or more past year question papers"
    )
    
    if uploaded_files:
        analysis_status = st.empty()
        with st.spinner("Processing question papers..."):
            try:
                # Process each file
                for uploaded_file in uploaded_files:
                    analysis_status.info(f"Analyzing {uploaded_file.name}...")
                    
                    if uploaded_file.type == "application/pdf":
                        # Get PDF content and analyze directly
                        pdf_content = uploaded_file.getvalue()
                        analysis = analyze_pyq_patterns(pdf_content, subject, is_pdf=True)
                    else:
                        # For text files, read content normally
                        text_content = uploaded_file.read().decode()
                        analysis = analyze_pyq_patterns(text_content, subject, is_pdf=False)
                    
                    if analysis:
                        st.session_state.pyq_analysis = analysis
                        st.success(f"✅ Analysis completed for {uploaded_file.name}")
                        show_pyq_results(analysis)
                    else:
                        st.error(f"No analysis results for {uploaded_file.name}")
                        
            except Exception as e:
                st.error(f"Error in analysis: {str(e)}")
            finally:
                analysis_status.empty()
    
    # Add sample questions option
    if st.button("Load Sample Questions"):
        sample_text = """Mathematics Final Exam (2024)
        1. Solve the quadratic equation: 2x² + 5x - 3 = 0
        2. Find the derivative of f(x) = x³ + 2x² - 4x + 1
        3. Calculate the area under the curve y = x² from x = 0 to x = 2"""
        
        with st.spinner("Analyzing sample questions..."):
            try:
                analysis = analyze_pyq_patterns(sample_text, subject, is_pdf=False)
                if analysis:
                    st.session_state.pyq_analysis = analysis
                    st.success("✅ Sample questions analyzed!")
                    show_pyq_results(analysis)
            except Exception as e:
                st.error(f"Error in analysis: {str(e)}")

def show_pyq_results(analysis):
    """Display the results of PYQ analysis"""
    # Display analysis results in tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Pattern Analysis", 
        "🎯 Predicted Topics", 
        "✍️ Practice Questions",
        "📚 Exam Guide"
    ])
    
    with tab1:
        st.subheader("Question Pattern Analysis")
        
        # Display visualizations
        visualizations = generate_topic_visualizations(analysis)
        
        # Topic frequency and predictions
        st.subheader("Topic Analysis and Predictions")
        st.pyplot(visualizations['topics'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Difficulty Distribution")
            st.pyplot(visualizations['difficulty'])
        
        with col2:
            st.subheader("Question Types")
            st.pyplot(visualizations['question_types'])
        
        # Display common patterns
        st.subheader("📝 Common Question Patterns")
        for pattern in analysis['question_patterns']:
            with st.expander(f"Pattern: {pattern['pattern_type']} (Frequency: {pattern['frequency']})"):
                st.write("**Example:**", pattern['example'])
    
    with tab2:
        st.subheader("Most Likely Topics for Next Exam")
        
        # Display topics sorted by prediction probability
        topics_df = pd.DataFrame(analysis['topics'])
        # Convert percentage strings to float for sorting
        topics_df['predicted_probability_float'] = topics_df['predicted_probability'].apply(
            lambda x: float(str(x).strip('%')) if isinstance(x, str) else float(x)
        )
        topics_df = topics_df.sort_values('predicted_probability_float', ascending=False)
        
        for _, topic in topics_df.iterrows():
            prob = topic['predicted_probability_float']
            color = 'green' if prob > 75 else 'orange' if prob > 50 else 'red'
            with st.expander(
                f"🎯 {topic['name']} - {topic['predicted_probability']} likely",
                expanded=prob > 75
            ):
                st.markdown(f"**Importance Level:** {topic['importance_level']}")
                st.markdown(f"**Previous Frequency:** {topic['frequency']} times")
                st.progress(prob / 100)
    
    with tab3:
        st.subheader("📋 Practice Questions")
        num_questions = st.slider(
            "Number of questions to generate",
            min_value=3,
            max_value=10,
            value=5
        )
        
        if st.button("Generate Practice Set"):
            with st.spinner("Generating targeted practice questions..."):
                practice_questions = generate_practice_questions(
                    analysis,
                    st.session_state.get('current_subject', 'General'),
                    num_questions
                )
                
                for i, q in enumerate(practice_questions, 1):
                    with st.expander(
                        f"Question {i}: {q['topic']} ({q['difficulty']})",
                        expanded=i==1
                    ):
                        st.write("**Question:**", q['question'])
                        st.info(f"**Answer:** {q['answer']}")
                        st.success(f"**Explanation:** {q['explanation']}")
                        st.caption(f"Marks: {q['marks']} | Suggested Time: {q['time']}")
    
    with tab4:
        st.subheader("📚 Exam Preparation Guide")
        guide = get_exam_preparation_guide(analysis, st.session_state.get('current_subject', 'General'))
        
        # Create two columns for subject and pattern guides
        col1, col2 = st.columns(2)
        
        # Subject-specific guide
        with col1:
            st.markdown("### 📘 Subject Guide")
            
            # Display key topics
            st.subheader("🎯 Key Topics to Focus")
            for topic in guide['subject_guide']['key_topics']:
                with st.expander(f"📌 {topic['topic']} ({topic['preparation_time']})"):
                    st.write("**Focus Points:**")
                    for point in topic['focus_points']:
                        st.markdown(f"• {point}")
                    
                    st.write("**Practice Strategy:**", topic['practice_strategy'])
                    
                    st.write("**Common Mistakes to Avoid:**")
                    for mistake in topic['common_mistakes']:
                        st.warning(f"⚠️ {mistake}")
            
            # Time management section
            st.subheader("⏰ Time Management")
            st.metric(
                "Total Preparation Time", 
                f"{guide['subject_guide']['time_management']['total_preparation_hours']} hours"
            )
                
            st.write("**Topic-wise Time Distribution:**")
            for topic, hours in guide['subject_guide']['time_management']['topic_wise_distribution'].items():
                st.text(f"{topic}: {hours} hours")
            
            st.info(f"**Revision Strategy:** {guide['subject_guide']['time_management']['revision_strategy']}")
        
        # Question pattern guide
        with col2:
            st.markdown("### 📝 Question Pattern Guide")
            
            # Question types
            st.subheader("📋 Question Types")
            for qtype in guide['pattern_guide']['question_types']:
                with st.expander(f"🔍 {qtype['type']} ({qtype['typical_marks']} marks)"):
                    st.markdown(f"**Frequency:** {qtype['frequency']}")
                    st.markdown(f"**Approach Strategy:**\n{qtype['approach_strategy']}")
                    st.markdown(f"**Sample Structure:**\n{qtype['sample_structure']}")

def show_question_bank():
    """Display the question bank generation page with enhanced features"""
    st.title("❓ AI Question Bank Generator")
    st.write("Generate custom questions for your class based on subject, topic, and specific requirements.")
    
    # Question generation form
    with st.form("question_bank_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            subject = st.selectbox(
                "Select Subject",
                ["Mathematics", "Science", "English", "Physics", "Chemistry", 
                 "Biology", "History", "Computer Science"],
                help="Choose the subject for question generation"
            )
            
            topic = st.text_input(
                "Enter specific topic:", 
                help="Example: Quadratic Equations, Chemical Reactions, etc."
            )
            
            description = st.text_area(
                "Additional requirements:",
                placeholder="Example: Include real-world applications, focus on problem-solving, specific concepts to cover",
                help="Add any specific requirements or focus areas for the questions",
                height=100
            )
        
        with col2:
            difficulty = st.selectbox(
                "Difficulty Level",
                ["Easy", "Medium", "Hard", "Mixed"],
                help="Select the difficulty level for questions",
                index=1
            )
            
            num_questions = st.slider(
                "Number of Questions",
                min_value=1,
                max_value=15,
                value=5,
                help="Choose how many questions to generate"
            )
            
            question_types = st.multiselect(
                "Question Types",
                list(QUESTION_TYPES.keys()),
                default=["Short Answer", "Problem Solving"],
                help="Select the types of questions to include"
            )
            
            advanced_options = st.expander("Advanced Options")
            with advanced_options:
                include_visuals = st.checkbox(
                    "Include Visual Elements",
                    value=True,
                    help="Include diagrams, graphs, or visual aids where applicable"
                )
                
                include_prerequisites = st.checkbox(
                    "Include Prerequisites",
                    value=True,
                    help="List required concepts for each question"
                )
                
                include_mistakes = st.checkbox(
                    "Include Common Mistakes",
                    value=True,
                    help="Add warnings about common errors and misconceptions"
                )
                
                marking_details = st.checkbox(
                    "Include Marking Scheme",
                    value=True,
                    help="Add detailed marking guidelines for each question"
                )
        
        submit_button = st.form_submit_button("Generate Questions")
    
    # Store generated questions in session state to persist between form submissions
    if submit_button:
        if topic:
            questions = generate_and_display_questions(
                subject, topic, difficulty, num_questions, question_types, description
            )
            if questions:
                st.session_state.generated_questions = questions
                st.session_state.current_subject = subject
                st.session_state.current_topic = topic
                st.session_state.current_difficulty = difficulty
        else:
            st.warning("Please enter a topic to generate questions.")
    
    # Display download buttons outside the form if questions are available
    if 'generated_questions' in st.session_state and st.session_state.generated_questions:
        st.markdown("---")
        st.subheader("📥 Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            # Export as JSON
            if st.download_button(
                label="📑 Export as JSON",
                data=json.dumps(st.session_state.generated_questions, indent=2),
                file_name=f"questions_{st.session_state.current_subject}_{st.session_state.current_topic}.json",
                mime="application/json",
                help="Download questions in JSON format"
            ):
                st.success("Questions exported as JSON!")
        
        with col2:
            # Export as CSV
            csv_data = export_to_csv(
                st.session_state.generated_questions,
                st.session_state.current_subject,
                st.session_state.current_topic,
                st.session_state.current_difficulty
            )
            if st.download_button(
                label="📈 Export as CSV",
                data=csv_data,
                file_name=f"questions_{st.session_state.current_subject}_{st.session_state.current_topic}.csv",
                mime="text/csv",
                help="Download questions in CSV format"
            ):
                st.success("Questions exported as CSV!")

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
            st.markdown("""
            - Lesson planning strategies
            - Assessment techniques
            - Classroom management tips
            """)
        with cols[1]:
            st.markdown("""
            - Student engagement ideas
            - Differentiated instruction
            - Educational technology tools
            """)
    
    # Chat input
    user_question = st.chat_input("Ask a question about teaching:")
    if user_question:
        process_chat_message(user_question, context)

if __name__ == "__main__":
    main()