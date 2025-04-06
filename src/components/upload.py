import streamlit as st
import os
import tempfile
from pdf_to_text import process_pdf_with_gemini, format_structured_output
from utils.ai_grading import grade_assignment

def process_upload(uploaded_file, subject=None, student_name=None, roll_number=None):
    """Handle PDF upload and processing"""
    try:
        # Create a temporary file that stays open during processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp.flush()
            
            # First process PDF with Gemini for text extraction
            extracted_content = process_pdf_with_gemini(tmp.name)
            st.session_state.uploaded_text = extracted_content
            
            # Then grade the assignment if subject is provided
            if subject and subject != "General":
                # Use the temporary file path directly
                grading_result = grade_assignment(
                    content=tmp.name,  # Pass the file path instead of content
                    subject=subject,
                    is_pdf=True,
                    student_name=student_name,
                    roll_number=roll_number
                )
                st.session_state.current_grading_result = grading_result
            
            # Clean up temporary file after all processing is complete
            try:
                os.unlink(tmp.name)
            except Exception:
                pass  # If file is locked, let OS handle cleanup
                
            return True
            
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return False

def display_structured_content(content):
    """Display structured content in a readable format with enhanced learning focus"""
    # Document title and overview
    st.markdown(f"# {content.get('title', 'Document Analysis')}")
    
    # Main Topics & Concepts
    with st.expander("📚 Main Topics & Concepts", expanded=True):
        st.markdown("### Core Concepts")
        topics = content.get('main_topics', {})
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Key Theoretical Concepts")
            for concept in topics.get('theoretical_concepts', []):
                st.info(f"• {concept}")
                
        with col2:
            st.markdown("#### 📐 Important Formulas")
            for formula in topics.get('formulas', []):
                st.latex(formula)
    
    # Learning Analysis
    with st.expander("🎓 Learning Analysis", expanded=True):
        learning = content.get('learning_analysis', {})
        
        # Create columns for difficulty and prerequisites
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📊 Difficulty Assessment")
            st.info(f"**Level:** {learning.get('difficulty_level', 'Not analyzed')}")
        with col2:
            st.markdown("#### 📋 Prerequisites")
            for prereq in learning.get('prerequisites', []):
                st.info(f"• {prereq}")
        
        # Study tips and misconceptions
        st.markdown("#### 💡 Study Tips")
        tips_col1, tips_col2 = st.columns(2)
        with tips_col1:
            for tip in learning.get('study_tips', []):
                st.success(f"• {tip}")
        with tips_col2:
            st.markdown("#### ⚠️ Common Misconceptions")
            for misconception in learning.get('common_misconceptions', []):
                st.warning(f"• {misconception}")
    
    # Content Breakdown
    with st.expander("📖 Detailed Content Analysis", expanded=True):
        if content.get('content_breakdown'):
            for section in content['content_breakdown']:
                with st.expander(f"📝 {section.get('title', 'Section')}"):
                    st.write(section.get('analysis', ''))
                    
                    # Examples with solutions
                    if section.get('examples'):
                        st.markdown("#### 📚 Examples")
                        for idx, example in enumerate(section['examples'], 1):
                            with st.expander(f"Example {idx}: {example.get('title', '')}"):
                                st.markdown("**Problem:**")
                                st.markdown(example.get('problem', ''))
                                with st.expander("View Solution"):
                                    st.markdown("**Solution:**")
                                    st.markdown(example.get('solution', ''))
                                    if example.get('explanation'):
                                        st.info(f"**Explanation:** {example['explanation']}")
                    
                    # Key points from the section
                    if section.get('key_points'):
                        st.markdown("#### 🎯 Key Points")
                        for point in section['key_points']:
                            st.success(f"• {point}")
        else:
            st.info("No detailed content analysis available.")
    
    # Practice Material
    with st.expander("✍️ Practice Material", expanded=True):
        practice = content.get('practice_material', {})
        
        # Practice Exercises
        if practice.get('exercises'):
            st.markdown("### 📝 Practice Exercises")
            for idx, exercise in enumerate(practice['exercises'], 1):
                with st.expander(f"Exercise {idx}"):
                    st.markdown(exercise.get('question', ''))
                    if exercise.get('hint'):
                        with st.expander("Need a hint?"):
                            st.info(exercise['hint'])
                    if exercise.get('solution'):
                        with st.expander("View Solution"):
                            st.markdown(exercise['solution'])
        
        # Common mistakes and tips
        if practice.get('common_mistakes'):
            st.markdown("### ⚠️ Watch Out For These Common Mistakes")
            for mistake in practice['common_mistakes']:
                st.warning(f"• {mistake}")
    
    # Additional Resources
    with st.expander("📚 Additional Learning Resources", expanded=True):
        resources = content.get('additional_resources', {})
        
        col1, col2 = st.columns(2)
        with col1:
            if resources.get('related_topics'):
                st.markdown("#### 🔄 Related Topics")
                for topic in resources['related_topics']:
                    st.info(f"• {topic}")
                    
        with col2:
            if resources.get('reference_materials'):
                st.markdown("#### 📚 Recommended Reading")
                for ref in resources['reference_materials']:
                    st.success(f"• {ref}")
    
    # Summary and Key Takeaways
    if content.get('summary'):
        with st.expander("📌 Summary & Key Takeaways", expanded=True):
            st.markdown("### 📝 Document Summary")
            st.write(content['summary'])
            
            if content.get('key_takeaways'):
                st.markdown("### 🎯 Key Takeaways")
                for takeaway in content['key_takeaways']:
                    st.success(f"• {takeaway}")
    
    # Important Notes
    if content.get('notes'):
        with st.expander("📢 Important Notes & Annotations", expanded=True):
            for note in content['notes']:
                st.info(note)

def show_upload_page():
    """Display the assignment upload page"""
    st.info("📢 Assignment upload feature is currently unavailable.")
    return  # Early return to prevent showing the upload interface