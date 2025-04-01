import sys
from pathlib import Path

# Add the project root to Python path
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Import utility functions for easy access
from utils.ai_grading import grade_assignment
from utils.feedback_display import display_grading_feedback
from utils.sample_data import get_sample_assignments, get_sample_questions
from utils.chat_processing import process_chat_message
from utils.question_generation import generate_and_display_questions

