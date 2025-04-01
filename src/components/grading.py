import streamlit as st
from utils.ai_grading import grade_assignment
from utils.feedback_display import display_grading_feedback
import tempfile
import os
import time

def show_grading_page():
    """Display the grading interface with PDF upload and analysis"""
    st.title("Assignment Grading")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload an assignment PDF",
        type=["pdf"],
        help="Upload a PDF file containing the assignment to be graded"
    )
    
    # Subject selection for context-aware grading
    subject = st.selectbox(
        "Select Subject",
        ["General", "Mathematics", "Science", "English", "History", "Computer Science"],
        help="Select the subject to apply subject-specific grading criteria"
    )
    
    if uploaded_file is not None:
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
                    is_pdf=True
                )
                
                # Display comprehensive feedback
                display_grading_feedback(grading_result)
                
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