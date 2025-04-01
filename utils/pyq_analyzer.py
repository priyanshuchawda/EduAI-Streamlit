import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any
from google.genai import types
from src.config import client

def analyze_question_patterns(questions: List[str], subject: str) -> Dict[str, Any]:
    """Analyze question patterns and predict likely topics"""
    instruction = f"""Analyze these {subject} questions and identify:
    1. Common patterns and structures
    2. Topic distribution and frequency
    3. Predicted topics for future exams
    4. Difficulty levels
    5. Question types (MCQ, essay, problem-solving, etc.)
    
    Format your response as a JSON object with:
    {{
        "patterns": [
            {{"type": "pattern type", "frequency": "occurrence count", "example": "example question"}}
        ],
        "topics": [
            {{"name": "topic name", "frequency": "count", "prediction": "likelihood %"}}
        ],
        "difficulty_distribution": {{"easy": "%", "medium": "%", "hard": "%"}},
        "question_types": ["list of identified types"],
        "recommended_focus": ["prioritized topics for preparation"]
    }}
    
    Questions to analyze:
    {questions}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role": "user", "parts": [{"text": instruction}]}],
            config=types.GenerateContentConfig(
                temperature=0.2,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json"
            )
        )
        
        return response.json()
    except Exception as e:
        print(f"Error analyzing questions: {str(e)}")
        return None

def predict_future_topics(historical_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Predict likely topics for future exams based on historical data"""
    # Calculate topic probabilities based on frequency and recency
    topics_data = {}
    for exam in historical_data:
        year = exam.get('year', 2024)  # Default to current year if not specified
        for topic in exam['topics']:
            if topic['name'] not in topics_data:
                topics_data[topic['name']] = {
                    'frequencies': [],
                    'years': [],
                    'total_frequency': 0
                }
            topics_data[topic['name']]['frequencies'].append(topic['frequency'])
            topics_data[topic['name']]['years'].append(year)
            topics_data[topic['name']]['total_frequency'] += topic['frequency']
    
    predictions = []
    current_year = 2024
    
    for topic, data in topics_data.items():
        # Calculate trend using weighted frequencies
        weights = [1 / (current_year - year + 1) for year in data['years']]
        weighted_freq = np.average(data['frequencies'], weights=weights)
        
        # Calculate probability based on frequency and trend
        probability = min(95, (weighted_freq / max(data['total_frequency'], 1)) * 100)
        
        predictions.append({
            'topic': topic,
            'probability': round(probability, 2),
            'trend': 'increasing' if weighted_freq > np.mean(data['frequencies']) else 'decreasing',
            'suggested_focus': probability > 60
        })
    
    return sorted(predictions, key=lambda x: x['probability'], reverse=True)

def generate_preparation_guide(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a detailed exam preparation guide based on analysis"""
    predicted_topics = analysis_results.get('topics', [])
    patterns = analysis_results.get('patterns', [])
    difficulty = analysis_results.get('difficulty_distribution', {})
    
    # Prioritize topics based on predictions
    high_priority = [t for t in predicted_topics if float(t['prediction'].rstrip('%')) > 70]
    medium_priority = [t for t in predicted_topics if 40 < float(t['prediction'].rstrip('%')) <= 70]
    
    # Create a structured study plan
    study_plan = {
        'high_priority_topics': [
            {
                'topic': topic['name'],
                'focus_time': '3-4 hours',
                'practice_questions': int(float(topic['prediction'].rstrip('%')) / 10)
            } for topic in high_priority
        ],
        'medium_priority_topics': [
            {
                'topic': topic['name'],
                'focus_time': '2-3 hours',
                'practice_questions': int(float(topic['prediction'].rstrip('%')) / 15)
            } for topic in medium_priority
        ],
        'question_patterns': [
            {
                'pattern': p['type'],
                'practice_strategy': f"Focus on {p['type']} type questions with {p['frequency']} practice attempts"
            } for p in patterns
        ],
        'time_allocation': {
            'topics': '60%',
            'practice': '30%',
            'revision': '10%'
        },
        'difficulty_focus': {
            'easy': f"Allocate {difficulty.get('easy', '30%')} of practice time",
            'medium': f"Allocate {difficulty.get('medium', '40%')} of practice time",
            'hard': f"Allocate {difficulty.get('hard', '30%')} of practice time"
        }
    }
    
    return study_plan

def analyze_difficulty(questions: List[str], subject: str) -> Dict[str, Any]:
    """Analyze question difficulty and provide insights"""
    instruction = f"""Analyze these {subject} questions and assess their difficulty levels. Consider:
    1. Cognitive complexity (Bloom's taxonomy)
    2. Time required to solve
    3. Required prerequisite knowledge
    4. Number of steps/concepts involved
    
    Format response as JSON:
    {{
        "questions": [
            {{
                "text": "question text",
                "difficulty_level": "easy/medium/hard",
                "cognitive_level": "remember/understand/apply/analyze/evaluate/create",
                "time_estimate": "minutes",
                "complexity_factors": ["list of factors that make it difficult"],
                "prerequisites": ["required knowledge"],
                "suggested_preparation": "preparation advice"
            }}
        ],
        "overall_analysis": {{
            "average_difficulty": "score out of 10",
            "difficulty_distribution": {{"easy": "%", "medium": "%", "hard": "%"}},
            "cognitive_levels": ["dominant levels"],
            "common_prerequisites": ["frequently needed concepts"],
            "preparation_recommendations": ["study suggestions"]
        }}
    }}"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role": "user", "parts": [{"text": instruction}]}],
            config=types.GenerateContentConfig(
                temperature=0.2,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json"
            )
        )
        
        return response.json()
    except Exception as e:
        print(f"Error analyzing difficulty: {str(e)}")
        return None

def generate_difficulty_insights(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate insights and recommendations based on difficulty analysis"""
    overall = analysis_results.get('overall_analysis', {})
    questions = analysis_results.get('questions', [])
    
    # Calculate difficulty trends
    difficulty_counts = {'easy': 0, 'medium': 0, 'hard': 0}
    cognitive_levels = {}
    prerequisites = {}
    
    for q in questions:
        difficulty_counts[q['difficulty_level'].lower()] += 1
        
        # Count cognitive levels
        cog_level = q['cognitive_level'].lower()
        cognitive_levels[cog_level] = cognitive_levels.get(cog_level, 0) + 1
        
        # Track prerequisites
        for prereq in q['prerequisites']:
            prerequisites[prereq] = prerequisites.get(prereq, 0) + 1
    
    # Generate insights
    insights = {
        'difficulty_profile': {
            'distribution': {
                level: (count / len(questions)) * 100 
                for level, count in difficulty_counts.items()
            },
            'average_difficulty': float(overall['average_difficulty']),
            'dominant_cognitive_levels': sorted(
                cognitive_levels.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3],
        },
        'key_prerequisites': sorted(
            prerequisites.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5],
        'recommendations': {
            'study_focus': overall['preparation_recommendations'],
            'time_management': generate_time_allocation(difficulty_counts),
            'skill_development': [
                f"Focus on {level} thinking skills" 
                for level, _ in sorted(cognitive_levels.items(), key=lambda x: x[1], reverse=True)[:2]
            ]
        }
    }
    
    return insights

def generate_time_allocation(difficulty_counts: Dict[str, int]) -> Dict[str, str]:
    """Generate recommended time allocation based on difficulty distribution"""
    total = sum(difficulty_counts.values())
    if total == 0:
        return {
            'easy': '30%',
            'medium': '40%',
            'hard': '30%'
        }
    
    allocations = {}
    for level, count in difficulty_counts.items():
        if level == 'easy':
            allocations[level] = f"{max(20, min(40, (count/total) * 100))}%"
        elif level == 'medium':
            allocations[level] = f"{max(30, min(50, (count/total) * 100))}%"
        else:  # hard
            allocations[level] = f"{max(20, min(40, (count/total) * 100))}%"
    
    return allocations

def analyze_topic_trends(historical_data: List[Dict[str, Any]], subject: str) -> Dict[str, Any]:
    """Analyze topic trends and predict future exam focus areas"""
    instruction = f"""Analyze historical {subject} exam data for topic prediction. Consider:
    1. Topic frequency over time
    2. Recent changes in topic emphasis
    3. Current curriculum trends
    4. Related topics that often appear together
    
    Format response as JSON:
    {{
        "predicted_topics": [
            {{
                "topic": "topic name",
                "likelihood": "percentage",
                "reasoning": "explanation for prediction",
                "related_topics": ["list of related topics"],
                "preparation_focus": ["specific areas to focus on"]
            }}
        ],
        "trend_analysis": {{
            "emerging_topics": ["topics gaining importance"],
            "declining_topics": ["topics becoming less common"],
            "stable_topics": ["consistently important topics"]
        }},
        "recommendations": {{
            "high_priority": ["topics to focus most on"],
            "medium_priority": ["topics to cover well"],
            "low_priority": ["topics to be familiar with"]
        }}
    }}
    
    Historical data to analyze:
    {json.dumps(historical_data, indent=2)}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role": "user", "parts": [{"text": instruction}]}],
            config=types.GenerateContentConfig(
                temperature=0.2,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json"
            )
        )
        
        return response.json()
    except Exception as e:
        print(f"Error analyzing topic trends: {str(e)}")
        return None

def generate_topic_visualizations(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate visualizations for topic analysis results"""
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Create visualizations dictionary to store figures
    visualizations = {}
    
    # Topic prediction visualization
    plt.figure(figsize=(10, 6))
    topics = [t['topic'] for t in analysis_results['predicted_topics']]
    likelihoods = [float(t['likelihood'].rstrip('%')) for t in analysis_results['predicted_topics']]
    
    sns.barplot(x=likelihoods, y=topics)
    plt.title('Topic Prediction Likelihood')
    plt.xlabel('Likelihood (%)')
    plt.ylabel('Topics')
    visualizations['topics'] = plt.gcf()
    plt.close()
    
    # Trend analysis visualization
    plt.figure(figsize=(12, 6))
    trend_data = {
        'Emerging': len(analysis_results['trend_analysis']['emerging_topics']),
        'Stable': len(analysis_results['trend_analysis']['stable_topics']),
        'Declining': len(analysis_results['trend_analysis']['declining_topics'])
    }
    
    colors = {'Emerging': '#2ecc71', 'Stable': '#3498db', 'Declining': '#e74c3c'}
    plt.pie(trend_data.values(), labels=trend_data.keys(), colors=[colors[key] for key in trend_data.keys()],
            autopct='%1.1f%%', startangle=90)
    plt.title('Topic Trends Distribution')
    visualizations['trends'] = plt.gcf()
    plt.close()
    
    return visualizations

def get_topic_preparation_guide(topic_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a focused preparation guide based on topic analysis"""
    guide = {
        'priority_topics': {
            'high': [{
                'topic': topic,
                'study_hours': '4-5',
                'focus_areas': topic_analysis['predicted_topics'][i]['preparation_focus']
            } for i, topic in enumerate(topic_analysis['recommendations']['high_priority'])],
            'medium': [{
                'topic': topic,
                'study_hours': '2-3',
                'focus_areas': []
            } for topic in topic_analysis['recommendations']['medium_priority']],
            'low': [{
                'topic': topic,
                'study_hours': '1-2',
                'focus_areas': []
            } for topic in topic_analysis['recommendations']['low_priority']]
        },
        'study_schedule': {
            'week1': {
                'focus': 'High priority topics',
                'hours_per_day': '2-3',
                'activities': ['Concept review', 'Practice problems', 'Self-assessment']
            },
            'week2': {
                'focus': 'Medium priority topics',
                'hours_per_day': '1-2',
                'activities': ['Topic overview', 'Key problem types', 'Quick practice']
            },
            'week3': {
                'focus': 'Low priority topics and revision',
                'hours_per_day': '1',
                'activities': ['Basic concepts', 'Important formulas', 'Brief practice']
            }
        },
        'recommended_resources': [
            'Topic-specific practice questions',
            'Video tutorials for complex concepts',
            'Summary sheets for quick revision',
            'Past year questions by topic'
        ]
    }
    
    return guide