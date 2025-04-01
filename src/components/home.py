import streamlit as st

def show_home_page():
    """Display the home page with introduction and features"""
    # Initialize first_visit in session state if not present
    if "first_visit" not in st.session_state:
        st.session_state.first_visit = True
        
    st.title("🎓 Welcome to EduAI Assistant")
    
    # Introduction
    st.markdown("""
    <div style='text-align: center; padding: 2rem;'>
        <h3>Your AI-Powered Teaching Assistant</h3>
        <p>Streamline your teaching workflow with advanced AI assistance</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick start guide for first-time users
    if st.session_state.first_visit:
        with st.info("👋 Welcome! Let's get you started with EduAI Assistant"):
            st.markdown("""
            1. **Upload Assignment**: Convert PDF assignments to text
            2. **Grading**: Get AI-powered grading and feedback
            3. **Student Analysis**: Track performance over time
            4. **Question Bank**: Generate custom questions
            5. **Teacher Chat**: Get instant teaching assistance
            """)
            if st.button("Got it!"):
                st.session_state.first_visit = False
    
    # Feature cards in grid layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📝 Assignment Processing
        - Upload PDF assignments
        - Automatic text extraction
        - Multi-page support
        """)
        
        st.markdown("""
        ### 📊 Student Analytics
        - Track performance trends
        - Visual progress reports
        - Detailed feedback history
        """)
    
    with col2:
        st.markdown("""
        ### ✍️ AI Grading
        - Automated assessment
        - Detailed feedback
        - Subject-specific evaluation
        """)
        
        st.markdown("""
        ### ❓ Question Generation
        - Custom question banks
        - Multiple formats
        - Export options
        """)
    
    # Getting started section
    st.divider()
    st.subheader("🚀 Getting Started")
    
    tab1, tab2, tab3 = st.tabs(["Upload", "Grade", "Analyze"])
    
    with tab1:
        st.markdown("""
        1. Click on **Upload Assignment** in the sidebar
        2. Choose a PDF file
        3. Wait for text extraction
        """)
    
    with tab2:
        st.markdown("""
        1. Navigate to **Grading**
        2. Select a subject (optional)
        3. Get AI-powered feedback
        """)
    
    with tab3:
        st.markdown("""
        1. View **Student Analysis**
        2. Track performance trends
        3. Export reports
        """)