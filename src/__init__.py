import sys
from pathlib import Path

# Add the project root to Python path
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Import components for easy access
from src.components.home import show_home_page
from src.components.grading import show_grading_page
from src.components.upload import show_upload_page
from src.components.analysis import show_analysis_page