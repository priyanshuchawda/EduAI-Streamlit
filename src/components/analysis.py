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
    
    # Add filters in a clean sidebar layout
    with st.sidebar:
        st.subheader("📋 Analysis Filters")
        time_range = st.selectbox(
            "Time Period",
            ["Last Week", "Last Month", "Last 3 Months", "All Time"],
            index=3
        )
        
        available_subjects = ["Mathematics", "Science", "English", "Physics", "Chemistry", "Biology", "History", "Computer Science"]
        subject_filter = st.multiselect(
            "Filter by Subjects",
            available_subjects,
            default=[]
        )
    
    # Add student name input
    student_name = st.text_input(
        "Student Name", 
        value=st.session_state.get('current_student', ''),
        help="Enter student name to view their performance analysis"
    )
    
    if student_name:
        st.session_state.current_student = student_name
        
        # Create tabs for different analysis views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Overall Performance", 
            "📚 Subject Performance", 
            "📋 Detailed Reports",
            "🎯 Improvement Plan"
        ])
        
        # Collect data from all subject sheets
        all_subjects_data = {}
        overall_performance = []
        
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
                            'Performance Trend': row['Previous Performance Trend']
                        })
            except Exception as e:
                st.warning(f"Could not load data for {subject}: {str(e)}")
        
        df_overall = pd.DataFrame(overall_performance)
        
        with tab1:
            if not df_overall.empty:
                col1, col2, col3 = st.columns(3)
                
                # Calculate overall metrics
                avg_score = df_overall['Percentage'].mean()
                recent_trend = df_overall.sort_values('Date').iloc[-1]['Performance Trend']
                consistency = df_overall['Percentage'].std()
                
                with col1:
                    st.metric(
                        "Overall Average",
                        f"{avg_score:.1f}%",
                        help="Average score across all subjects"
                    )
                
                with col2:
                    st.metric(
                        "Recent Trend",
                        recent_trend,
                        help="Based on recent performance across subjects"
                    )
                
                with col3:
                    st.metric(
                        "Consistency Score",
                        f"{(100 - consistency):.1f}%",
                        help="Higher score means more consistent performance"
                    )
                
                # Performance timeline
                st.subheader("📊 Performance Timeline")
                fig = go.Figure()
                
                for subject in df_overall['Subject'].unique():
                    subject_data = df_overall[df_overall['Subject'] == subject]
                    fig.add_trace(go.Scatter(
                        x=subject_data['Date'],
                        y=subject_data['Percentage'],
                        name=subject,
                        mode='lines+markers'
                    ))
                
                fig.update_layout(
                    title="Performance Across Subjects",
                    xaxis_title="Date",
                    yaxis_title="Score (%)",
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No performance data available yet. Complete some assignments to see analysis.")
        
        with tab2:
            if all_subjects_data:
                st.subheader("📚 Subject-wise Analysis")
                
                for subject, data in all_subjects_data.items():
                    with st.expander(f"{subject} Performance", expanded=True):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            # Create subject-specific performance chart
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=data['Date'],
                                y=[float(str(p).rstrip('%')) for p in data['Percentage']],
                                mode='lines+markers',
                                name='Score'
                            ))
                            fig.update_layout(
                                title=f"{subject} Progress",
                                xaxis_title="Date",
                                yaxis_title="Score (%)"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            # Show latest assessment details
                            latest = data.iloc[-1]
                            st.metric(
                                "Latest Score",
                                latest['Percentage'],
                                latest['Previous Performance Trend']
                            )
                            
                            st.write("**Recent Strengths:**")
                            strengths = latest['Strengths'].split(', ') if latest['Strengths'] else []
                            for strength in strengths[:3]:
                                st.success(f"✓ {strength}")
                            
                            st.write("**Areas to Focus:**")
                            improvements = latest['Areas for Improvement'].split(', ') if latest['Areas for Improvement'] else []
                            for improvement in improvements[:3]:
                                st.warning(f"! {improvement}")
            else:
                st.info("No subject-specific data available yet.")
        
        with tab3:
            if all_subjects_data:
                st.subheader("📋 Detailed Assessment Reports")
                
                # Sort options for reports
                sort_by = st.selectbox(
                    "Sort by",
                    ["Most Recent", "Subject", "Highest Score", "Lowest Score"]
                )
                
                # Combine all data and sort
                all_assessments = pd.concat([df.assign(Subject=subject) for subject, df in all_subjects_data.items()])
                
                if sort_by == "Most Recent":
                    all_assessments = all_assessments.sort_values('Date', ascending=False)
                elif sort_by == "Subject":
                    all_assessments = all_assessments.sort_values(['Subject', 'Date'], ascending=[True, False])
                elif sort_by == "Highest Score":
                    all_assessments['Score'] = all_assessments['Percentage'].str.rstrip('%').astype(float)
                    all_assessments = all_assessments.sort_values('Score', ascending=False)
                elif sort_by == "Lowest Score":
                    all_assessments['Score'] = all_assessments['Percentage'].str.rstrip('%').astype(float)
                    all_assessments = all_assessments.sort_values('Score', ascending=True)
                
                for _, row in all_assessments.iterrows():
                    with st.expander(f"📝 {row['Subject']} - {row['Assignment Title']} ({row['Date']})"):
                        st.write(f"**Grade:** {row['Grade']}")
                        st.write(f"**Score:** {row['Percentage']}")
                        st.write(f"**Summary:** {row['Summary']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Strengths:**")
                            for strength in row['Strengths'].split(', ') if row['Strengths'] else []:
                                st.success(f"✓ {strength}")
                        
                        with col2:
                            st.write("**Areas for Improvement:**")
                            for area in row['Areas for Improvement'].split(', ') if row['Areas for Improvement'] else []:
                                st.warning(f"! {area}")
                        
                        if row['AI Suggestions']:
                            st.write("**AI Suggestions:**")
                            st.info(row['AI Suggestions'])
            else:
                st.info("No assessment reports available yet.")
        
        with tab4:
            if all_subjects_data:
                st.subheader("🎯 Personalized Improvement Plan")
                
                # Aggregate data for overall analysis
                all_strengths = []
                all_weaknesses = []
                all_scores = []
                
                for subject_data in all_subjects_data.values():
                    latest = subject_data.iloc[-1]
                    if latest['Strengths']:
                        all_strengths.extend(latest['Strengths'].split(', '))
                    if latest['Areas for Improvement']:
                        all_weaknesses.extend(latest['Areas for Improvement'].split(', '))
                    all_scores.append(float(str(latest['Percentage']).rstrip('%')))
                
                # Generate improvement plan
                try:
                    analysis_results = analyze_student_performance(
                        student_name=student_name,
                        assignment_scores=all_scores,
                        strong_topics=list(set(all_strengths)),
                        weak_topics=list(set(all_weaknesses)),
                        pyq_performance={},  # This could be enhanced with PYQ data
                        syllabus_completion=len(all_scores) * 10
                    )
                    
                    if analysis_results:
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.subheader("📈 Performance Projection")
                            # Create projection chart using the analysis results
                            create_performance_projection_chart(df_overall, analysis_results)
                            
                            st.subheader("📚 Recommended Study Plan")
                            display_study_plan(analysis_results)
                        
                        with col2:
                            st.metric(
                                "Predicted Average Score",
                                f"{analysis_results['Predicted_Score']}%",
                                delta=f"{float(analysis_results['Predicted_Score']) - df_overall['Percentage'].mean():.1f}%"
                            )
                            
                            st.subheader("🎯 Quick Actions")
                            for i, tip in enumerate(analysis_results['Improvement_Plan'], 1):
                                st.info(f"{i}. {tip}")
                            
                            st.divider()
                            st.subheader("💭 AI Insights")
                            st.success(analysis_results['Motivational_Message'])
                except Exception as e:
                    st.error(f"Error generating improvement plan: {str(e)}")
            else:
                st.info("Complete some assignments to get a personalized improvement plan!")

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