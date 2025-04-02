import streamlit as st
import pandas as pd
from utils.pyq_analysis import analyze_pyq_patterns, generate_practice_questions, get_exam_preparation_guide, generate_topic_visualizations

def show_pyq_analysis_page():
    """Display the Previous Year Questions Analysis interface"""
    st.title("📝 Previous Year Questions Analysis")
    
    # File upload section
    uploaded_file = st.file_uploader("Upload Previous Year Question Paper (PDF/Text)", type=['pdf', 'txt'])
    
    # Subject selection
    subject = st.selectbox(
        "Select Subject",
        ["Mathematics", "Physics", "Chemistry", "Biology", "English"]
    )
    
    if uploaded_file is not None:
        # Read file content
        is_pdf = uploaded_file.type == 'application/pdf'
        content = uploaded_file.read()
        
        with st.spinner("Analyzing question patterns..."):
            try:
                # Analyze the questions
                analysis = analyze_pyq_patterns(content, subject, is_pdf)
                
                # Display analysis results in tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 Pattern Analysis", 
                    "📈 Visualizations", 
                    "✍️ Practice Questions",
                    "📚 Exam Guide"
                ])
                
                with tab1:
                    st.subheader("Question Patterns")
                    for pattern in analysis.get('question_patterns', []):
                        with st.expander(f"📌 {pattern['pattern_type']}"):
                            st.write(f"**Frequency:** {pattern['frequency']}")
                            st.write(f"**Example:** {pattern['example']}")
                    
                    st.subheader("Topic Distribution")
                    for topic in analysis.get('topics', []):
                        with st.expander(f"📚 {topic['name']}"):
                            st.write(f"**Frequency:** {topic['frequency']}")
                            st.write(f"**Predicted Probability:** {topic['predicted_probability']}")
                            st.write(f"**Importance:** {topic['importance_level']}")
                
                with tab2:
                    st.subheader("Analysis Visualizations")
                    visualizations = generate_topic_visualizations(analysis)
                    
                    # Display each visualization
                    st.write("### Topic Analysis")
                    st.pyplot(visualizations['topics'])
                    
                    st.write("### Difficulty Distribution")
                    st.pyplot(visualizations['difficulty'])
                    
                    st.write("### Question Pattern Types")
                    st.pyplot(visualizations['question_types'])
                
                with tab3:
                    st.subheader("Practice Questions")
                    num_questions = st.slider("Number of questions to generate", 3, 10, 5)
                    
                    if st.button("Generate Practice Questions"):
                        with st.spinner("Generating questions..."):
                            practice_questions = generate_practice_questions(analysis, subject, num_questions)
                            
                            for i, q in enumerate(practice_questions, 1):
                                with st.expander(f"Question {i}"):
                                    st.write(f"**Question:** {q['question']}")
                                    st.write(f"**Topic:** {q['topic']}")
                                    st.write(f"**Difficulty:** {q['difficulty']}")
                                    st.write(f"**Time:** {q['time']} minutes")
                                    st.write(f"**Marks:** {q['marks']}")
                                    with st.expander("View Answer"):
                                        st.write(f"**Answer:** {q['answer']}")
                                        st.write("**Explanation:**")
                                        st.write(q['explanation'])
                
                with tab4:
                    st.subheader("Exam Preparation Guide")
                    exam_guide = get_exam_preparation_guide(analysis, subject)
                    
                    # Display key topics
                    st.write("### 📚 Key Topics")
                    for topic in exam_guide.get('subject_guide', {}).get('key_topics', []):
                        with st.expander(f"📖 {topic['topic']}"):
                            st.write(f"**Preparation Time:** {topic['preparation_time']} hours")
                            st.write("**Focus Points:**")
                            for point in topic['focus_points']:
                                st.write(f"- {point}")
                            st.write(f"**Practice Strategy:** {topic['practice_strategy']}")
                            st.write("**Common Mistakes to Avoid:**")
                            for mistake in topic['common_mistakes']:
                                st.write(f"- {mistake}")
                    
                    # Display time management
                    time_mgmt = exam_guide.get('subject_guide', {}).get('time_management', {})
                    st.write("### ⏰ Time Management")
                    st.write(f"**Total Preparation Hours:** {time_mgmt.get('total_preparation_hours')}")
                    st.write("**Topic-wise Time Distribution:**")
                    for topic, hours in time_mgmt.get('topic_wise_distribution', {}).items():
                        st.write(f"- {topic}: {hours} hours")
                    st.write(f"**Revision Strategy:** {time_mgmt.get('revision_strategy')}")
                    
            except Exception as e:
                st.error(f"Error analyzing questions: {str(e)}")
    else:
        st.info("Upload a question paper to start the analysis")