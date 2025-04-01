import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Any

from utils.feedback_display import display_grading_feedback  # Fixed function name
from utils.sheets_integration import analyze_student_performance, get_student_history, save_analysis_to_sheets

def extract_skill_from_feedback(feedback_text: str) -> str:
    """Extract the main skill from a feedback text"""
    # Common skill keywords to look for
    skill_keywords = {
        'problem solving': ['solve', 'solution', 'problem', 'analytical'],
        'critical thinking': ['analyze', 'evaluate', 'critical', 'reasoning'],
        'communication': ['explain', 'express', 'communicate', 'present'],
        'mathematics': ['calculate', 'compute', 'mathematical', 'numerical'],
        'writing': ['write', 'essay', 'composition', 'grammar'],
        'comprehension': ['understand', 'comprehend', 'interpret', 'grasp'],
        'application': ['apply', 'implement', 'use', 'practical'],
        'organization': ['organize', 'structure', 'systematic', 'planning']
    }
    
    feedback_lower = feedback_text.lower()
    
    # Check for each skill keyword
    for skill, keywords in skill_keywords.items():
        if any(keyword in feedback_lower for keyword in keywords):
            return skill.title()
    
    return 'General Skills'

def generate_skill_improvement_plan(skill: str) -> str:
    """Generate a personalized improvement plan for a specific skill"""
    improvement_plans = {
        'Problem Solving': [
            "Practice breaking down complex problems into smaller steps",
            "Work on additional practice problems with increasing difficulty",
            "Focus on understanding the problem before attempting solutions",
            "Review and analyze different solution approaches"
        ],
        'Critical Thinking': [
            "Analyze case studies and real-world scenarios",
            "Practice identifying assumptions and evaluating evidence",
            "Work on comparing and contrasting different viewpoints",
            "Develop skills in logical reasoning and argumentation"
        ],
        'Communication': [
            "Practice explaining concepts to others",
            "Work on writing clear and concise explanations",
            "Focus on using proper terminology and vocabulary",
            "Practice presenting ideas in different formats"
        ],
        'Mathematics': [
            "Review fundamental concepts and formulas",
            "Practice solving problems step by step",
            "Focus on understanding mathematical reasoning",
            "Work on applying concepts to real-world problems"
        ],
        'Writing': [
            "Practice organizing ideas before writing",
            "Focus on grammar and sentence structure",
            "Work on developing clear arguments",
            "Review and revise written work regularly"
        ],
        'Comprehension': [
            "Practice active reading strategies",
            "Focus on identifying main ideas and supporting details",
            "Work on summarizing and paraphrasing",
            "Develop note-taking skills"
        ],
        'Application': [
            "Work on applying concepts to new situations",
            "Practice identifying relevant concepts for problem-solving",
            "Focus on connecting theory to practice",
            "Develop skills in practical implementation"
        ],
        'Organization': [
            "Develop systematic study routines",
            "Practice creating outlines and study plans",
            "Focus on time management",
            "Work on organizing information effectively"
        ],
        'General Skills': [
            "Focus on developing consistent study habits",
            "Practice active learning techniques",
            "Work on time management and organization",
            "Seek help when needed and review feedback regularly"
        ]
    }
    
    skill_title = skill.title()
    if skill_title in improvement_plans:
        return "\n".join([
            f"**{skill_title} Improvement Plan:**",
            "",
            *[f"• {tip}" for tip in improvement_plans[skill_title]],
            "",
            "Remember to track your progress and regularly practice these strategies."
        ])
    
    return "Focus on general skill improvement and consistent practice."

def display_detailed_feedback(feedback: Dict[str, Any]):
    """Display detailed feedback in a structured format"""
    # Display grade and percentage
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Grade", feedback.get('grade', 'N/A'))
    with col2:
        st.metric("Score", feedback.get('percentage', '0%'))
    
    # Display strengths and weaknesses
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**💪 Strengths:**")
        for strength in feedback.get('strengths', []):
            st.success(f"✓ {strength}")
    
    with col2:
        st.markdown("**🎯 Areas for Improvement:**")
        for weakness in feedback.get('weaknesses', []):
            st.warning(f"• {weakness}")
    
    # Display detailed feedback if available
    if 'detailed_feedback' in feedback:
        st.markdown("**📝 Detailed Analysis:**")
        st.info(feedback['detailed_feedback'])
    
    # Display improvement suggestions
    if 'improvement_suggestions' in feedback:
        st.markdown("**🚀 Improvement Suggestions:**")
        for i, suggestion in enumerate(feedback['improvement_suggestions'], 1):
            st.write(f"{i}. {suggestion}")
    
    # Display related concepts if available
    if 'related_concepts_to_review' in feedback:
        st.markdown("**📚 Related Concepts to Review:**")
        for concept in feedback['related_concepts_to_review']:
            st.write(f"• {concept}")

def show_analysis_page():
    """Display the student analysis page"""
    st.title("📊 Student Performance Analysis")
    
    # Add filters in a clean sidebar layout
    with st.sidebar:
        st.subheader("📋 Analysis Filters")
        time_range = st.selectbox(
            "Time Period",
            ["Last Week", "Last Month", "Last 3 Months", "All Time"],
            index=3
        )
        
        subject_filter = st.multiselect(
            "Filter by Subjects",
            ["Mathematics", "Science", "English", "Physics", "Chemistry", "Biology", "History", "Computer Science"],
            default=[]
        )
    
    # Add student name input with autocomplete feature
    student_name = st.text_input(
        "Student Name", 
        value=st.session_state.get('current_student', ''),
        help="Enter student name to view their performance analysis"
    )
    
    if student_name:
        st.session_state.current_student = student_name
        
        # Create tabs for different analysis views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Performance Trends", 
            "💡 Skill Analysis", 
            "📋 Detailed Reports",
            "🎯 Improvement Plan"
        ])
        
        with tab1:
            if st.session_state.grading_history:
                col1, col2, col3 = st.columns(3)
                
                # Calculate metrics
                df = pd.DataFrame(st.session_state.grading_history)
                df["grade"] = pd.to_numeric(df["grade"], errors='coerce')
                avg_score = df["grade"].mean()
                trend = df["grade"].iloc[-1] - df["grade"].iloc[0] if len(df) > 1 else 0
                consistency = df["grade"].std() if len(df) > 1 else 0
                
                with col1:
                    st.metric(
                        "Average Performance",
                        f"{avg_score:.1f}%",
                        delta=f"{trend:+.1f}%"
                    )
                
                with col2:
                    st.metric(
                        "Performance Trend",
                        "Improving" if trend > 0 else "Declining" if trend < 0 else "Stable",
                        delta=f"{abs(trend):.1f}%"
                    )
                
                with col3:
                    st.metric(
                        "Consistency Score",
                        f"{(100 - consistency):.1f}%",
                        help="Higher score means more consistent performance"
                    )
                
                # Advanced performance visualization
                st.subheader("📊 Performance Over Time")
                fig = create_advanced_performance_chart(df)
                st.plotly_chart(fig, use_container_width=True)
                
                # Subject-wise performance
                if 'feedback' in df.columns:
                    st.subheader("📚 Subject-wise Performance")
                    subject_performance = analyze_subject_performance(df)
                    create_subject_heatmap(subject_performance)
            else:
                st.info("👋 Start by grading some assignments to see performance trends!")
        
        with tab2:
            if st.session_state.grading_history:
                # Skills matrix analysis
                st.subheader("🎯 Skills Matrix")
                skills_data = analyze_skills_matrix(st.session_state.grading_history)
                
                # Display skills in a circular progress chart
                col1, col2 = st.columns([2, 1])
                with col1:
                    create_skills_radar_chart(skills_data)
                
                with col2:
                    st.subheader("💪 Top Skills")
                    for skill, score in sorted(skills_data.items(), key=lambda x: x[1], reverse=True)[:5]:
                        st.progress(score/100, text=f"{skill}: {score}%")
                
                # Improvement opportunities
                st.subheader("🎯 Focus Areas")
                weak_skills = {k: v for k, v in skills_data.items() if v < 70}
                if weak_skills:
                    for skill, score in weak_skills.items():
                        with st.expander(f"📝 {skill} ({score}%)"):
                            st.write(generate_skill_improvement_plan(skill))
            else:
                st.info("Grade some assignments to see skills analysis!")
        
        with tab3:
            if st.session_state.grading_history:
                st.subheader("📋 Detailed Assessment Reports")
                
                # Filter and sort reports
                sort_order = st.selectbox(
                    "Sort by",
                    ["Most Recent", "Highest Score", "Lowest Score", "Most Improved"],
                    index=0
                )
                
                df_sorted = sort_assessment_reports(df, sort_order)
                
                for _, row in df_sorted.iterrows():
                    with st.expander(
                        f"📝 Assessment on {row['timestamp'].strftime('%Y-%m-%d')} - Score: {row['grade']}%",
                        expanded=False
                    ):
                        if 'feedback' in row:
                            display_detailed_feedback(row['feedback'])
                        st.divider()
            else:
                st.info("No assessment reports available yet.")
        
        with tab4:
            if st.session_state.grading_history and st.session_state.feedback:
                # Get AI analysis
                try:
                    with st.spinner("Generating personalized improvement plan..."):
                        # Extract strong and weak topics
                        strong_topics = []
                        weak_topics = []
                        if st.session_state.feedback:
                            strong_topics = st.session_state.feedback.get('strengths', [])
                            weak_topics = st.session_state.feedback.get('weaknesses', [])
                        
                        # Get PYQ performance if available
                        pyq_performance = {}
                        if st.session_state.pyq_analysis:
                            for topic in st.session_state.pyq_analysis.get('topics', []):
                                pyq_performance[topic['name']] = float(topic['predicted_probability'].strip('%'))
                        
                        # Calculate syllabus completion
                        syllabus_completion = len(st.session_state.grading_history) * 10
                        
                        analysis_results = analyze_student_performance(
                            student_name=student_name,
                            assignment_scores=df["grade"].tolist(),
                            strong_topics=strong_topics,
                            weak_topics=weak_topics,
                            pyq_performance=pyq_performance,
                            syllabus_completion=syllabus_completion
                        )
                        
                        # Display improvement plan
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.subheader("📈 Performance Projection")
                            create_performance_projection_chart(df, analysis_results)
                            
                            st.subheader("📚 Recommended Study Plan")
                            display_study_plan(analysis_results)
                        
                        with col2:
                            st.metric(
                                "Predicted Next Score",
                                f"{analysis_results['Predicted_Score']}%",
                                delta=f"{float(analysis_results['Predicted_Score']) - df['grade'].iloc[-1]:.1f}%"
                            )
                            
                            st.subheader("🎯 Quick Actions")
                            for i, tip in enumerate(analysis_results['Improvement_Plan'], 1):
                                st.info(f"{i}. {tip}")
                            
                            st.divider()
                            st.subheader("💭 AI Insights")
                            st.success(analysis_results['Motivational_Message'])
                            
                        # Save analysis button
                        if st.button("💾 Save Analysis to Sheets"):
                            try:
                                save_analysis_to_sheets(student_name, analysis_results)
                                st.success("✅ Analysis saved successfully!")
                            except Exception as e:
                                st.error(f"Error saving analysis: {str(e)}")
                                
                except Exception as e:
                    st.error(f"Error generating improvement plan: {str(e)}")
            else:
                st.info("Complete some assessments to get a personalized improvement plan!")
    else:
        st.warning("⚠️ Please enter a student name to begin the analysis")

def create_advanced_performance_chart(df):
    """Create an interactive performance chart using plotly"""
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add score line
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["grade"],
            name="Score",
            line=dict(color="#1f77b4", width=3),
            mode="lines+markers"
        ),
        secondary_y=False,
    )
    
    # Add trend line
    z = np.polyfit(range(len(df)), df["grade"], 1)
    p = np.poly1d(z)
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=p(range(len(df))),
            name="Trend",
            line=dict(color="#ff7f0e", dash="dash"),
        ),
        secondary_y=False,
    )
    
    # Calculate and add moving average
    df['MA5'] = df['grade'].rolling(window=5).mean()
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df['MA5'],
            name="5-Point Moving Average",
            line=dict(color="#2ca02c", dash="dot"),
        ),
        secondary_y=False,
    )
    
    # Update layout
    fig.update_layout(
        title="Performance Trends and Analysis",
        xaxis_title="Date",
        yaxis_title="Score (%)",
        hovermode="x unified",
        showlegend=True,
        template="plotly_white"
    )
    
    return fig

def analyze_subject_performance(df):
    """Analyze performance by subject"""
    subject_performance = {}
    for entry in df['feedback']:
        subject = entry.get('subject', 'General')
        score = float(entry.get('percentage', '0').strip('%'))
        if subject not in subject_performance:
            subject_performance[subject] = []
        subject_performance[subject].append(score)
    
    # Calculate averages
    return {k: sum(v)/len(v) for k, v in subject_performance.items()}

def create_subject_heatmap(subject_performance):
    """Create a heatmap of subject performance"""
    # Create heatmap data
    subjects = list(subject_performance.keys())
    scores = list(subject_performance.values())
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, 2))
    sns.heatmap(
        [scores],
        annot=True,
        cmap="RdYlGn",
        cbar=False,
        xticklabels=subjects,
        yticklabels=False,
        center=70,
        vmin=0,
        vmax=100,
        fmt=".1f"
    )
    plt.title("Subject Performance Heatmap")
    st.pyplot(fig)

def analyze_skills_matrix(grading_history):
    """Analyze student skills based on grading history"""
    skills = {}
    for entry in grading_history:
        if 'feedback' in entry:
            feedback = entry['feedback']
            # Extract skills from strengths
            for strength in feedback.get('strengths', []):
                skill = extract_skill_from_feedback(strength)
                if skill:
                    skills[skill] = skills.get(skill, 0) + 1
            
            # Consider weaknesses with lower weight
            for weakness in feedback.get('weaknesses', []):
                skill = extract_skill_from_feedback(weakness)
                if skill:
                    skills[skill] = skills.get(skill, 0) - 0.5
    
    # Normalize scores to 0-100 range
    max_score = max(skills.values()) if skills else 1
    return {k: min(100, max(0, (v/max_score) * 100)) for k, v in skills.items()}

def create_skills_radar_chart(skills_data):
    """Create an interactive radar chart for skills"""
    categories = list(skills_data.keys())
    values = list(skills_data.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Skills'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def sort_assessment_reports(df, sort_order):
    """Sort assessment reports based on selected order"""
    if sort_order == "Most Recent":
        return df.sort_values("timestamp", ascending=False)
    elif sort_order == "Highest Score":
        return df.sort_values("grade", ascending=False)
    elif sort_order == "Lowest Score":
        return df.sort_values("grade", ascending=True)
    elif sort_order == "Most Improved":
        df['improvement'] = df['grade'].diff()
        return df.sort_values("improvement", ascending=False)
    return df

def create_performance_projection_chart(df, analysis_results):
    """Create a performance projection chart"""
    # Historical data
    dates = df['timestamp']
    scores = df['grade']
    
    # Project future dates
    last_date = dates.iloc[-1]
    future_dates = pd.date_range(last_date, periods=5, freq='W')
    
    # Create projection line
    predicted_score = float(analysis_results['Predicted_Score'])
    current_score = scores.iloc[-1]
    projection = np.linspace(current_score, predicted_score, 5)
    
    fig = go.Figure()
    
    # Historical performance
    fig.add_trace(go.Scatter(
        x=dates,
        y=scores,
        name='Historical',
        line=dict(color='#1f77b4')
    ))
    
    # Projection
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=projection,
        name='Projection',
        line=dict(color='#ff7f0e', dash='dash')
    ))
    
    fig.update_layout(
        title="Performance Projection",
        xaxis_title="Date",
        yaxis_title="Score (%)",
        showlegend=True,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_study_plan(analysis_results):
    """Display the recommended study plan"""
    for i, plan in enumerate(analysis_results.get('Improvement_Plan', []), 1):
        with st.expander(f"Week {i} Focus"):
            st.write(plan)
            st.progress(1.0 - (i-1)*0.2, text="Priority Level")