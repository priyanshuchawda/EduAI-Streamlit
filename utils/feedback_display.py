import streamlit as st
from typing import Dict, Any
import plotly.graph_objects as go
import pandas as pd
import re

def format_math_text(text: str) -> str:
    """Format mathematical expressions with proper spacing and LaTeX rendering"""
    # Add LaTeX formatting for common math symbols
    text = re.sub(r'(\d+)\^(\d+)', r'$\1^\2$', text)  # Format exponents
    text = text.replace('∫', '$\\int$')  # Integrals
    text = text.replace('Σ', '$\\Sigma$')  # Summation
    text = text.replace('√', '$\\sqrt$')  # Square root
    text = text.replace('±', '$\\pm$')  # Plus-minus
    text = text.replace('∞', '$\\infty$')  # Infinity
    
    # Add proper spacing around mathematical operators
    text = re.sub(r'(\d+)([+\-*/=])(\d+)', r'\1 \2 \3', text)
    
    return text

def format_explanation_text(text: str) -> str:
    """Format explanation text with proper spacing and structure"""
    # Add bullet points for lists
    text = re.sub(r'^-\s*(.+)$', r'• \1', text, flags=re.MULTILINE)
    
    # Format numbered steps
    text = re.sub(r'^(\d+)\.\s*(.+)$', r'**Step \1:** \2', text, flags=re.MULTILINE)
    
    # Add emphasis to key terms (words in quotes)
    text = re.sub(r'"([^"]+)"', r'**\1**', text)
    
    return text

def create_skill_radar_chart(skills_data: Dict[str, list]) -> go.Figure:
    """Create a radar chart for skills analysis"""
    categories = []
    values = []
    colors = []
    
    # Process skills by category
    if 'mastered' in skills_data:
        categories.extend(skills_data['mastered'])
        values.extend([100] * len(skills_data['mastered']))
        colors.extend(['#00CC96'] * len(skills_data['mastered']))
    
    if 'developing' in skills_data:
        categories.extend(skills_data['developing'])
        values.extend([65] * len(skills_data['developing']))
        colors.extend(['#FFA15A'] * len(skills_data['developing']))
    
    if 'needs_work' in skills_data:
        categories.extend(skills_data['needs_work'])
        values.extend([30] * len(skills_data['needs_work']))
        colors.extend(['#EF553B'] * len(skills_data['needs_work']))

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(99, 110, 250, 0.5)',
        line=dict(color='rgb(99, 110, 250)'),
        name='Skills Assessment'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        title="Skills Assessment Radar"
    )
    
    return fig

def display_grading_feedback(feedback: Dict[str, Any]):
    """Display comprehensive grading feedback"""
    if not feedback:
        st.error("No grading feedback available")
        return

    # Store the feedback in session state for persistence
    st.session_state.last_feedback = feedback
        
    st.title("Assignment Grading Analysis")
    
    # Display student information
    with st.container():
        st.subheader("📋 Student Information")
        student_col1, student_col2 = st.columns(2)
        with student_col1:
            st.info(f"**Student Name:** {feedback.get('student_name', 'Unknown Student')}")
        with student_col2:
            st.info(f"**Roll Number:** {feedback.get('roll_number', 'N/A')}")
        st.divider()
    
    try:
        # Top-level metrics in a neat row
        col1, col2, col3 = st.columns(3)
        with col1:
            grade = feedback.get('grade')
            if grade and grade.strip() and grade != 'N/A':
                st.metric("Grade", grade)
            else:
                st.metric("Grade", "N/A")
                
        with col2:
            percentage = feedback.get('percentage', '0')
            if isinstance(percentage, (int, float)):
                percentage = f"{percentage}%"
            elif not str(percentage).endswith('%'):
                percentage = f"{percentage}%"
            st.metric("Score", percentage)
                
        with col3:
            questions = feedback.get('questions', [])
            total_questions = len(questions) if questions else 0
            st.metric("Questions", str(total_questions))

        # Executive Summary
        st.header("Executive Summary")
        summary = feedback.get('summary')
        if summary and summary.strip() and summary != 'Unable to process assignment':
            st.markdown(format_explanation_text(summary))
        else:
            st.warning("The assignment has been processed but no detailed summary is available yet.")

        # Skills Analysis
        st.header("Skills Analysis")
        skills_analysis = feedback.get('skills_analysis', {})
        if skills_analysis and any(skills_analysis.values()):
            # Create radar chart if there are skills
            fig = create_skill_radar_chart(skills_analysis)
            st.plotly_chart(fig, use_container_width=True)
            
            cols = st.columns(3)
            with cols[0]:
                st.subheader("✨ Mastered")
                mastered = skills_analysis.get('mastered', [])
                if mastered:
                    for skill in mastered:
                        st.success(f"✓ {skill}")
                else:
                    st.info("Currently working on mastering skills")
            
            with cols[1]:
                st.subheader("🔄 Developing")
                developing = skills_analysis.get('developing', [])
                if developing:
                    for skill in developing:
                        st.info(f"• {skill}")
                else:
                    st.info("No skills currently in development")
            
            with cols[2]:
                st.subheader("🎯 Need Work")
                needs_work = skills_analysis.get('needs_work', [])
                if needs_work:
                    for skill in needs_work:
                        st.warning(f"! {skill}")
                else:
                    st.info("No critical skill gaps identified")
        else:
            st.info("A skills analysis will be generated after grading more assignments")

        # Question-by-Question Analysis
        st.header("Question-by-Question Analysis")
        questions = feedback.get('questions', [])
        if questions and len(questions) > 0:
            for idx, question in enumerate(questions):
                with st.expander(f"Question {idx + 1}", expanded=idx == 0):
                    # Question content
                    st.markdown("**Question Text:**")
                    question_text = question.get('question_text', '')
                    if question_text and question_text != 'Unable to extract question':
                        st.write(format_math_text(question_text))
                        if question.get('page_number'):
                            st.caption(f"Page {question['page_number']}")
                    else:
                        st.warning("Question text not available")
                    
                    # Student's answer
                    st.markdown("**Student's Response:**")
                    answer = question.get('student_answer', '')
                    if answer and answer != 'Unable to extract answer':
                        st.markdown('```\n' + format_math_text(answer) + '\n```')
                    else:
                        st.warning("Student answer not available")
                    
                    # Evaluation details
                    st.markdown("---")
                    eval_col1, eval_col2 = st.columns(2)
                    with eval_col1:
                        st.markdown("**Evaluation:**")
                        evaluation = question.get('evaluation', {})
                        correctness = evaluation.get('correctness', '')
                        score = evaluation.get('score', '')
                        
                        if correctness and correctness != 'N/A':
                            status_icon = "✓" if correctness == "correct" else "⚠️" if correctness == "partial" else "✗"
                            if correctness == "correct":
                                st.success(f"{status_icon} Status: {correctness.title()}\n📊 Score: {score}")
                            elif correctness == "partial":
                                st.warning(f"{status_icon} Status: {correctness.title()}\n📊 Score: {score}")
                            else:
                                st.error(f"{status_icon} Status: {correctness.title()}\n📊 Score: {score}")
                        else:
                            st.info("Evaluation in progress...")
                    
                    with eval_col2:
                        st.markdown("**Explanation:**")
                        explanation = evaluation.get('explanation', '')
                        if explanation and explanation != 'Unable to evaluate':
                            st.markdown(format_explanation_text(explanation))
                        else:
                            st.info("Explanation will be provided after evaluation")
                    
                    # Feedback section
                    if 'feedback' in question:
                        st.markdown("---")
                        st.markdown("**Detailed Feedback**")
                        feedback_cols = st.columns(2)
                        with feedback_cols[0]:
                            st.markdown("*Strengths:*")
                            strengths = question['feedback'].get('strengths', [])
                            if strengths:
                                for strength in strengths:
                                    st.success(f"✓ {strength}")
                            else:
                                st.info("Working on identifying strengths")
                        
                        with feedback_cols[1]:
                            st.markdown("*Areas for Improvement:*")
                            improvements = question['feedback'].get('improvements', [])
                            if improvements:
                                for improvement in improvements:
                                    st.warning(f"• {improvement}")
                            else:
                                st.info("Working on identifying areas for improvement")
                        
                        # Solution
                        solution = question['feedback'].get('solution')
                        if solution and solution != "Not available":
                            st.markdown("---")
                            st.markdown("**📝 Correct Solution:**")
                            st.markdown(format_math_text(format_explanation_text(solution)))
                            
        else:
            st.info("Processing questions... This may take a moment.")

        # Improvement Plan
        improvement_plan = feedback.get('improvement_plan', {})
        if improvement_plan and any(improvement_plan.values()):
            st.header("📈 Improvement Plan")
            plan_cols = st.columns(3)
            
            with plan_cols[0]:
                st.subheader("📚 Topics to Review")
                topics = improvement_plan.get('topics_to_review', [])
                if topics:
                    for topic in topics:
                        st.info(f"• {topic}")
                else:
                    st.info("Topics will be suggested after evaluation")
            
            with plan_cols[1]:
                st.subheader("✍️ Practice Tasks")
                tasks = improvement_plan.get('recommended_practice', [])
                if tasks:
                    for task in tasks:
                        st.success(f"• {task}")
                else:
                    st.info("Practice tasks will be suggested after evaluation")
            
            with plan_cols[2]:
                st.subheader("📖 Resources")
                resources = improvement_plan.get('resources', [])
                if resources:
                    for resource in resources:
                        st.markdown(f"• {resource}")
                else:
                    st.info("Resources will be suggested after evaluation")
        
    except Exception as e:
        st.error(f"Error displaying feedback: {str(e)}")
        st.info("Please try uploading the assignment again.")

# Create an alias for the display_grading_feedback function
display_feedback = display_grading_feedback