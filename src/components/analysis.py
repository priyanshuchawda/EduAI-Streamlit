import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Any

from utils.feedback_display import display_grading_feedback
from utils.sheets_integration import (
    analyze_student_performance, 
    get_student_history,
    get_student_subject_history,
    save_analysis_to_sheets
)

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
    
    # Add student information section
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input(
            "Student Name*", 
            value=st.session_state.get('current_student', ''),
            help="Enter student name to view their performance analysis"
        )
    with col2:
        roll_number = st.text_input(
            "Roll Number*",
            value=st.session_state.get('current_roll_number', ''),
            help="Enter student roll number"
        )

    if student_name and roll_number:
        st.session_state.current_student = student_name
        st.session_state.current_roll_number = roll_number
        
        # Create tabs for different analysis views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Overall Performance", 
            "📚 Subject-wise Analysis", 
            "📋 Assessment History",
            "🎯 Personalized Plan"
        ])
        
        # Fetch data from all subject sheets
        all_subjects_data = {}
        overall_performance = []
        available_subjects = ["Mathematics", "Science", "English", "Physics", "Chemistry", "Biology", "History", "Computer Science", "General"]
        
        with st.spinner("Analyzing student data..."):
            for subject in available_subjects:
                try:
                    subject_data = get_student_subject_history(student_name, subject)
                    if not subject_data.empty:
                        all_subjects_data[subject] = subject_data
                        # Convert data for overall analysis
                        for _, row in subject_data.iterrows():
                            overall_performance.append({
                                'Date': row['Date'],
                                'Subject': subject,
                                'Grade': row['Grade'],
                                'Percentage': float(str(row['Percentage']).rstrip('%')),
                                'Strengths': row['Strengths'].split(', ') if row['Strengths'] else [],
                                'Areas for Improvement': row['Areas for Improvement'].split(', ') if row['Areas for Improvement'] else [],
                                'Performance Trend': row['Previous Performance Trend'],
                                'Resources': row['Recommended Resources'].split(', ') if row['Recommended Resources'] else []
                            })
                except Exception as e:
                    st.warning(f"Could not load data for {subject}: {str(e)}")
            
            df_overall = pd.DataFrame(overall_performance)
            
            # Generate comprehensive analysis using Gemini
            if not df_overall.empty:
                try:
                    all_strengths = list(set([s for p in overall_performance for s in p['Strengths']]))
                    all_weaknesses = list(set([w for p in overall_performance for w in p['Areas for Improvement']]))
                    all_scores = [p['Percentage'] for p in overall_performance]
                    
                    analysis_results = analyze_student_performance(
                        student_name=student_name,
                        assignment_scores=all_scores,
                        strong_topics=all_strengths,
                        weak_topics=all_weaknesses,
                        pyq_performance={},  # Can be enhanced with PYQ data
                        syllabus_completion=len(all_scores) * 10
                    )
                    
                    # Save analysis to sheets
                    save_analysis_to_sheets(student_name, analysis_results)
                except Exception as e:
                    st.error(f"Error generating analysis: {str(e)}")
                    analysis_results = None

            # Display Overall Performance (Tab 1)
            with tab1:
                if not df_overall.empty:
                    st.subheader("📊 Performance Overview")
                    
                    # Key metrics
                    col1, col2, col3 = st.columns(3)
                    avg_score = df_overall['Percentage'].mean()
                    recent_trend = df_overall.sort_values('Date').iloc[-1]['Performance Trend']
                    consistency = df_overall['Percentage'].std()
                    
                    with col1:
                        st.metric(
                            "Overall Average",
                            f"{avg_score:.1f}%", 
                            delta=None,
                            help="Average score across all subjects"
                        )
                    
                    with col2:
                        st.metric(
                            "Recent Trend",
                            recent_trend,
                            help="Based on recent performance"
                        )
                    
                    with col3:
                        st.metric(
                            "Consistency Score",
                            f"{(100 - consistency):.1f}%", 
                            help="Higher score means more consistent performance"
                        )
                    
                    # Performance timeline
                    st.subheader("📈 Performance Timeline")
                    timeline_fig = create_advanced_performance_chart(df_overall)
                    st.plotly_chart(timeline_fig, use_container_width=True)
                    
                    if analysis_results:
                        st.subheader("🤖 AI Analysis")
                        st.info(f"**Overall Assessment:** {analysis_results.get('Overall_Assessment', 'Not available')}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**💪 Key Strengths:**")
                            for strength in analysis_results.get('Strengths', []):
                                st.success(f"✓ {strength}")
                        
                        with col2:
                            st.write("**🎯 Areas for Improvement:**")
                            for weakness in analysis_results.get('Weaknesses', []):
                                st.warning(f"• {weakness}")
                else:
                    st.info("No performance data available yet. Complete some assignments to see analysis.")

            # Display Subject Performance (Tab 2)
            with tab2:
                if all_subjects_data:
                    for subject, data in all_subjects_data.items():
                        with st.expander(f"{subject} Analysis", expanded=True):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                # Simple subject performance chart
                                subject_fig = go.Figure()
                                # Convert dates and ensure they're in ascending order
                                data = data.sort_values('Date')
                                # Convert percentages to float values
                                percentages = [float(str(p).rstrip('%')) for p in data['Percentage']]
                                
                                subject_fig.add_trace(go.Scatter(
                                    x=pd.to_datetime(data['Date']),
                                    y=percentages,
                                    mode='lines+markers',
                                    name='Score',
                                    line=dict(color="#1f77b4", width=3)
                                ))
                                
                                subject_fig.update_layout(
                                    title=f"{subject} Progress",
                                    xaxis=dict(
                                        title="Date",
                                        type='date',
                                        tickformat='%Y-%m-%d',
                                        dtick='D1'  # Show daily ticks
                                    ),
                                    yaxis_title="Score (%)",
                                    showlegend=False,
                                    template="plotly_white",
                                    hovermode="x unified"
                                )
                                # Add this line to display the chart
                                st.plotly_chart(subject_fig, use_container_width=True)
                            
                            with col2:
                                latest = data.iloc[-1]
                                st.metric(
                                    "Latest Score",
                                    latest['Percentage'],
                                    delta=latest['Previous Performance Trend']
                                )
                                
                                # Recent performance details with proper data handling
                                st.write("**Recent Performance:**")
                                
                                # Handle strengths
                                strengths = []
                                if isinstance(latest['Strengths'], str) and latest['Strengths'].strip():
                                    strengths = [s.strip() for s in latest['Strengths'].split(',') if s.strip()]
                                elif isinstance(latest['Strengths'], list):
                                    strengths = latest['Strengths']
                                
                                if strengths:
                                    st.write("✓ Strengths:")
                                    for strength in strengths[:3]:  # Show top 3 strengths
                                        st.success(f"• {strength}")
                                else:
                                    st.info("Complete more assignments to see strengths")
                                
                                # Handle areas to focus
                                improvements = []
                                if isinstance(latest['Areas for Improvement'], str) and latest['Areas for Improvement'].strip():
                                    improvements = [i.strip() for i in latest['Areas for Improvement'].split(',') if i.strip()]
                                elif isinstance(latest['Areas for Improvement'], list):
                                    improvements = latest['Areas for Improvement']
                                
                                if improvements:
                                    st.write("! Areas to Focus:")
                                    for improvement in improvements[:3]:  # Show top 3 areas
                                        st.warning(f"• {improvement}")
                                else:
                                    st.info("Complete more assignments to see areas for improvement")
                else:
                    st.info("No subject-wise data available yet.")

            # Display Assessment History (Tab 3)
            with tab3:
                if all_subjects_data:
                    st.subheader("📋 Assessment History")
                    
                    # Sort options
                    sort_by = st.selectbox(
                        "Sort by",
                        ["Most Recent", "Subject", "Highest Score", "Lowest Score"]
                    )
                    
                    # Combine and sort all assessments
                    all_assessments = []
                    for subject, data in all_subjects_data.items():
                        for _, row in data.iterrows():
                            all_assessments.append({
                                'Date': pd.to_datetime(row['Date']),
                                'Subject': subject,
                                'Grade': row['Grade'],
                                'Score': float(str(row['Percentage']).rstrip('%')),
                                'Details': row
                            })
                    
                    df_assessments = pd.DataFrame(all_assessments)
                    if sort_by == "Most Recent":
                        df_assessments = df_assessments.sort_values('Date', ascending=False)
                    elif sort_by == "Subject":
                        df_assessments = df_assessments.sort_values(['Subject', 'Date'], ascending=[True, False])
                    elif sort_by == "Highest Score":
                        df_assessments = df_assessments.sort_values('Score', ascending=False)
                    else:  # Lowest Score
                        df_assessments = df_assessments.sort_values('Score', ascending=True)
                    
                    # Display assessments
                    for _, assessment in df_assessments.iterrows():
                        with st.expander(
                            f"{assessment['Subject']} - {assessment['Date'].strftime('%Y-%m-%d')} "
                            f"(Grade: {assessment['Grade']}, Score: {assessment['Score']}%)"
                        ):
                            details = assessment['Details']
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**📝 Assessment Details:**")
                                st.write(f"• Assignment: {details['Assignment Title']}")
                                st.write(f"• Performance Trend: {details['Previous Performance Trend']}")
                            
                            with col2:
                                st.write("**💡 Key Takeaways:**")
                                if details['Strengths']:
                                    strengths = details['Strengths'].split(', ') if isinstance(details['Strengths'], str) else details['Strengths']
                                    st.write("**Strengths:**")
                                    for strength in strengths:
                                        st.success(f"✓ {strength}")
                                
                                if details['Areas for Improvement']:
                                    improvements = details['Areas for Improvement'].split(', ') if isinstance(details['Areas for Improvement'], str) else details['Areas for Improvement']
                                    st.write("**Areas for Improvement:**")
                                    for improvement in improvements:
                                        st.warning(f"• {improvement}")
                else:
                    st.info("No assessment history available yet.")

            # Display Personalized Plan (Tab 4)
            with tab4:
                if analysis_results:
                    st.subheader("🎯 Personalized Improvement Plan")
                    
                    # Study plan and recommendations
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write("**📚 Recommended Study Plan:**")
                        for i, action in enumerate(analysis_results.get('Improvement_Plan', []), 1):
                            st.info(f"{i}. {action}")
                        
                        st.write("**🎓 Learning Strategy:**")
                        st.success(analysis_results.get('Learning_Strategy', 'Not available'))
                    
                    with col2:
                        st.metric(
                            "Predicted Next Score",
                            f"{analysis_results.get('Predicted_Score', '0')}%",
                            delta=f"{float(analysis_results.get('Predicted_Score', 0)) - avg_score:.1f}%"
                        )
                        
                        st.write("**💭 Motivational Message:**")
                        st.info(analysis_results.get('Motivational_Message', 'Keep working hard!'))
                    
                    # Resources and next steps
                    st.subheader("📚 Recommended Resources")
                    resources = []
                    for subject_data in all_subjects_data.values():
                        latest = subject_data.iloc[-1]
                        if latest['Recommended Resources']:
                            resources.extend(latest['Recommended Resources'].split(', '))
                    
                    if resources:
                        for resource in list(set(resources)):
                            st.write(f"• {resource}")
                    else:
                        st.info("Complete more assignments to get personalized resource recommendations.")
                else:
                    st.info("Complete more assignments to get a personalized improvement plan.")
    else:
        st.warning("Please enter both student name and roll number to view analysis.")

def create_advanced_performance_chart(df):
    """Create an interactive performance chart using plotly"""
    fig = go.Figure()
    
    # Convert Date to datetime if it's not already
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Add score line
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Percentage"],
            name="Score",
            line=dict(color="#1f77b4", width=3),
            mode="lines+markers"
        )
    )
    
    # Update layout with proper date formatting
    fig.update_layout(
        title="Performance Trends",
        xaxis=dict(
            title="Date",
            type='date',
            tickformat='%Y-%m-%d',
            dtick='D1'  # Show daily ticks
        ),
        yaxis_title="Score (%)",
        hovermode="x unified",
        showlegend=False,
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
    dates = pd.to_datetime(df['Date'])
    scores = df['Percentage']
    
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
        xaxis=dict(
            title="Date",
            type='date',
            tickformat='%Y-%m-%d',
            dtick='D1'  # Show daily ticks
        ),
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