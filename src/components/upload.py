import streamlit as st
import os
import tempfile
from pdf_to_text import process_pdf_with_gemini, format_structured_output
from utils.ai_grading import grade_assignment

def process_upload(uploaded_file, subject=None, student_name=None, roll_number=None):
    """Handle PDF upload and processing"""
    try:
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp.flush()
            
            # First process PDF with Gemini for text extraction
            extracted_content = process_pdf_with_gemini(tmp.name)
            st.session_state.uploaded_text = extracted_content
            
            # Then grade the assignment if subject is provided
            if subject and subject != "General":
                grading_result = grade_assignment(
                    content=uploaded_file.getvalue(),
                    subject=subject,
                    is_pdf=True,
                    student_name=student_name,
                    roll_number=roll_number
                )
                st.session_state.current_grading_result = grading_result
            
            return True
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return False
    finally:
        # Clean up temporary file
        if 'tmp' in locals() and os.path.exists(tmp.name):
            os.remove(tmp.name)

def display_structured_content(content):
    """Display structured content in a readable format"""
    # Document title and metadata
    st.markdown(f"# {content.get('title', 'Document Analysis')}")
    
    metadata = content.get('metadata', {})
    with st.expander("📝 Document Information", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"Type: {metadata.get('type', 'unknown')}")
        with col2:
            st.info(f"Subject: {metadata.get('subject_area', 'unknown')}")
        with col3:
            st.info(f"Quality: {metadata.get('content_quality', 'unknown')}")
    
    # Display original teacher notes
    original_notes = content.get('original_notes', {})
    if any(original_notes.values()):  # Check if there are any notes
        with st.expander("📓 Teacher's Original Notes", expanded=True):
            # Teacher comments
            if original_notes.get('teacher_comments'):
                st.markdown("### 👨‍🏫 Teacher Comments")
                for comment in original_notes['teacher_comments']:
                    st.success(f"💭 {comment}")
            
            # Margin notes
            if original_notes.get('margin_notes'):
                st.markdown("### 📝 Margin Notes")
                for note in original_notes['margin_notes']:
                    st.info(f"✏️ {note}")
            
            # Corrections
            if original_notes.get('corrections'):
                st.markdown("### ✍️ Corrections")
                for correction in original_notes['corrections']:
                    st.warning(f"📌 {correction}")
    
    # Summary section
    if 'summary' in content:
        st.markdown("## 📋 Summary")
        st.info(content['summary'])
    
    # Main content sections
    for section in content.get('sections', []):
        with st.expander(f"📚 {section.get('heading', 'Section')}", expanded=True):
            # Main content with proper formatting
            st.markdown(section.get('content', ''))
            
            # Display equations if present
            if section.get('equations'):
                st.markdown("### 📐 Equations")
                for eq in section['equations']:
                    st.latex(eq)
            
            # Display key points
            if section.get('key_points'):
                st.markdown("### 🎯 Key Points")
                for point in section['key_points']:
                    st.success(f"• {point}")
    
    # Important notes
    if content.get('notes'):
        with st.expander("📌 Important Notes", expanded=True):
            for note in content['notes']:
                st.info(note)

def show_upload_page():
    """Display the assignment upload page"""
    st.title("📝 Assignment Upload")
    st.write("Please enter student details and upload the assignment for grading.")
    
    # Add student information section
    with st.container():
        st.subheader("📋 Student Information")
        col1, col2 = st.columns(2)
        
        with col1:
            student_name = st.text_input(
                "Student Name*",
                value=st.session_state.get('current_student', ''),
                help="Enter the full name of the student"
            )
        
        with col2:
            roll_number = st.text_input(
                "Roll Number*",
                help="Enter the student's roll number"
            )
    
    # Store student info in session state
    if student_name:
        st.session_state.current_student = student_name
    
    # Add subject selection
    subject = st.selectbox(
        "Select Subject*",
        ["General", "Mathematics", "Science", "English", "History", "Computer Science"],
        help="Select the subject to apply subject-specific grading criteria"
    )
    
    uploaded_file = st.file_uploader(
        "Choose Assignment PDF*",
        type=["pdf"],
        help="Upload a student's completed assignment in PDF format"
    )
    
    # Validate inputs
    if uploaded_file:
        if not student_name or not roll_number:
            st.error("⚠️ Please enter both student name and roll number before uploading.")
            return
            
        with st.spinner("Processing PDF with AI..."):
            if process_upload(uploaded_file, subject, student_name, roll_number):
                st.success("✅ PDF processed successfully!")
                if st.session_state.uploaded_text:
                    st.markdown("### 📄 Processed Content")
                    display_structured_content(st.session_state.uploaded_text)
                
                # If grading result is available, show a preview
                if hasattr(st.session_state, 'current_grading_result') and st.session_state.current_grading_result:
                    st.markdown("### 📊 Initial Grading Preview")
                    st.write(f"Student: {student_name} (Roll No: {roll_number})")
                    st.write(f"Subject: {subject}")
                    st.write(f"Grade: {st.session_state.current_grading_result.get('grade', 'N/A')}")
                    st.write(f"Score: {st.session_state.current_grading_result.get('percentage', '0%')}")
                
                st.markdown("---")
                st.button(
                    "Continue to Detailed Grading",
                    on_click=lambda: setattr(st.session_state, 'current_page', 'Grading')
                )