import streamlit as st
from utils.ai_grading import grade_assignment
from utils.feedback_display import display_grading_feedback
import tempfile
import os
import time
from datetime import datetime

def show_grading_page():
    """Display the grading interface with PDF upload and analysis"""
    st.title("Assignment Grading")
    
    # Initialize session state if needed
    if 'current_grading_result' not in st.session_state:
        st.session_state.current_grading_result = None
    
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
    
    # Subject selection for context-aware grading
    subject = st.selectbox(
        "Select Subject*",
        ["General", "Mathematics", "Science", "English", "History", "Computer Science"],
        help="Select the subject to apply subject-specific grading criteria"
    )
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Assignment PDF*",
        type=["pdf"],
        help="Upload a PDF file containing the assignment to be graded"
    )
    
    if uploaded_file is not None:
        # Validate required fields
        if not student_name or not roll_number:
            st.error("⚠️ Please enter both student name and roll number before uploading.")
            return
            
        # Create a unique temporary file
        temp_file = None
        try:
            # Create temp file with a unique name
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                # Write the uploaded file content
                temp_file.write(uploaded_file.getvalue())
                temp_file.flush()
                temp_path = temp_file.name

            with st.spinner("Analyzing assignment..."):
                # Grade the assignment using the temporary file path
                grading_result = grade_assignment(
                    content=uploaded_file.getvalue(),
                    subject=subject if subject != "General" else None,
                    is_pdf=True,
                    student_name=student_name,
                    roll_number=roll_number
                )
                
                # Store the result in session state
                st.session_state.current_grading_result = grading_result
                
                # Display comprehensive feedback
                if grading_result:
                    display_grading_feedback(grading_result)
                    
                    # Add save to sheets button
                    st.divider()
                    st.subheader("💾 Save Results")
                    save_col1, save_col2 = st.columns([3, 1])
                    with save_col1:
                        st.info("Click the button to save these results to Google Sheets for tracking and analysis.")
                    with save_col2:
                        if st.button("Save to Sheets", type="primary"):
                            try:
                                from utils.sheets_integration import save_grading_result
                                success = save_grading_result(
                                    student_name=student_name,
                                    roll_number=roll_number,
                                    subject=subject,
                                    grading_data=grading_result,
                                    assignment_title=f"{subject} Assignment - {datetime.now().strftime('%Y-%m-%d')}"
                                )
                                if success:
                                    st.success("✅ Results saved successfully to Google Sheets!")
                                else:
                                    st.error("❌ Failed to save results. Please try again.")
                            except Exception as e:
                                st.error(f"Error saving to sheets: {str(e)}")
                                st.info("Check your Google Sheets credentials in the .env file.")
                else:
                    st.error("Unable to process the assignment. Please try again.")
                
        except Exception as e:
            st.error(f"Error analyzing assignment: {str(e)}")
            st.info("Please try uploading the file again or contact support if the issue persists.")
        
        finally:
            # Cleanup: Make sure the temporary file is deleted
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    # If file is still locked, wait briefly and try again
                    time.sleep(0.1)
                    try:
                        os.unlink(temp_file.name)
                    except Exception:
                        pass  # If still can't delete, let the OS handle it later