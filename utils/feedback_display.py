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
    st.title("Assignment Grading Analysis")
    
    # Top-level metrics in a neat row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Grade", feedback.get('grade', 'N/A'))
    with col2:
        st.metric("Score", f"{feedback.get('percentage', '0')}%")
    with col3:
        total_questions = len(feedback.get('questions', []))
        st.metric("Questions", str(total_questions))

    # Teacher's Original Notes section (before summary)
    if 'original_notes' in feedback:
        with st.expander("📓 Teacher's Original Notes", expanded=True):
            notes = feedback['original_notes']
            
            # Teacher comments section
            if notes.get('teacher_comments'):
                st.markdown("### 👨‍🏫 Teacher Comments")
                for comment in notes['teacher_comments']:
                    st.success(f"💭 {comment}")
            
            # Margin notes section
            if notes.get('margin_notes'):
                st.markdown("### 📝 Margin Notes")
                for note in notes['margin_notes']:
                    st.info(f"✏️ {note}")
            
            # Corrections section
            if notes.get('corrections'):
                st.markdown("### ✍️ Corrections")
                for correction in notes['corrections']:
                    st.warning(f"📌 {correction}")

    # Executive Summary
    st.header("Executive Summary")
    st.markdown(format_explanation_text(feedback.get('summary', 'No summary available')))

    # Skills Analysis with Radar Chart
    st.header("Skills Analysis")
    if 'skills_analysis' in feedback:
        # Display radar chart
        fig = create_skill_radar_chart(feedback['skills_analysis'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed skills breakdown
        cols = st.columns(3)
        with cols[0]:
            st.subheader("✨ Mastered")
            for skill in feedback['skills_analysis'].get('mastered', []):
                st.success(f"• {skill}")
        
        with cols[1]:
            st.subheader("🔄 Developing")
            for skill in feedback['skills_analysis'].get('developing', []):
                st.info(f"• {skill}")
        
        with cols[2]:
            st.subheader("🎯 Need Work")
            for skill in feedback['skills_analysis'].get('needs_work', []):
                st.warning(f"• {skill}")

    # Detailed Question Analysis
    st.header("Question-by-Question Analysis")
    if 'questions' in feedback:
        # Create tabs for each question
        question_tabs = st.tabs([f"Question {idx+1}" for idx in range(len(feedback['questions']))])
        
        for idx, (tab, question) in enumerate(zip(question_tabs, feedback['questions'])):
            with tab:
                # Question content
                st.markdown(f"### Question {idx+1}")
                st.markdown("**Question Text:**")
                st.write(format_math_text(question.get('question_text', 'Question text not available')))
                
                # Student's answer
                st.markdown("**Student's Response:**")
                st.markdown('```\n' + format_math_text(question.get('student_answer', 'Answer not available')) + '\n```')
                
                # Evaluation details
                st.markdown("---")
                eval_col1, eval_col2 = st.columns(2)
                with eval_col1:
                    st.markdown("**Evaluation:**")
                    correctness = question.get('evaluation', {}).get('correctness', 'not evaluated')
                    score = question.get('evaluation', {}).get('score', 'N/A')
                    
                    if correctness == 'correct':
                        st.success(f"✓ Status: {correctness.title()}\n📊 Score: {score}")
                    elif correctness == 'partial':
                        st.warning(f"⚠️ Status: {correctness.title()}\n📊 Score: {score}")
                    else:
                        st.error(f"✗ Status: {correctness.title()}\n📊 Score: {score}")
                
                with eval_col2:
                    st.markdown("**Explanation:**")
                    explanation = question.get('evaluation', {}).get('explanation', 'No explanation provided')
                    st.markdown(format_explanation_text(explanation))
                
                # Feedback section
                st.markdown("---")
                st.markdown("**Detailed Feedback**")
                feedback_cols = st.columns(2)
                with feedback_cols[0]:
                    st.markdown("*Strengths:*")
                    for strength in question.get('feedback', {}).get('strengths', []):
                        st.success(f"✓ {strength}")
                
                with feedback_cols[1]:
                    st.markdown("*Areas for Improvement:*")
                    for improvement in question.get('feedback', {}).get('improvements', []):
                        st.warning(f"• {improvement}")
                
                # Solution - formatted in a code block with proper spacing
                st.markdown("---")
                st.markdown("**📝 Correct Solution:**")
                solution = question.get('feedback', {}).get('solution', 'Solution not provided')
                # Format the solution with proper spacing and LaTeX
                formatted_solution = format_math_text(format_explanation_text(solution))
                st.markdown(formatted_solution)

    # Improvement Plan
    st.header("📈 Improvement Plan")
    if 'improvement_plan' in feedback:
        # Create three columns for a more organized layout
        plan_cols = st.columns(3)
        
        with plan_cols[0]:
            st.subheader("📚 Topics to Review")
            for topic in feedback['improvement_plan'].get('topics_to_review', []):
                st.info(f"• {topic}")
        
        with plan_cols[1]:
            st.subheader("✍️ Practice Tasks")
            for practice in feedback['improvement_plan'].get('recommended_practice', []):
                st.success(f"• {practice}")
        
        with plan_cols[2]:
            st.subheader("📖 Resources")
            for resource in feedback['improvement_plan'].get('resources', []):
                st.markdown(f"• {resource}")

    # Export options
    st.markdown("---")
    st.header("📑 Export Options")
    if st.button("Generate PDF Report"):
        st.info("PDF report generation in progress...")

# Create an alias for the display_grading_feedback function
display_feedback = display_grading_feedback