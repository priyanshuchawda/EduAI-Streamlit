from fpdf import FPDF
import qrcode
from datetime import datetime
import os
import json
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

class ParentReport(FPDF):
    def __init__(self):
        super().__init__()
        self.width = 210  # A4 width in mm
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.set_margins(20, 20, 20)
        
    def header(self):
        # Enhanced header with logo and school info
        self.set_font('Arial', 'B', 24)
        self.set_text_color(31, 119, 180)
        self.cell(0, 15, 'EduAI Assistant', align='C')
        self.ln(10)
        self.set_font('Arial', 'I', 12)
        self.set_text_color(128)
        self.cell(0, 10, 'Weekly Progress Report', align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')
        
    def add_student_info(self, student_name: str, grade_level: str):
        # Create an info box with border
        self.set_fill_color(240, 248, 255)  # Light blue background
        self.set_draw_color(31, 119, 180)   # Blue border
        
        self.rect(10, self.get_y(), self.width - 20, 40, 'DF')
        self.set_xy(15, self.get_y() + 5)
        
        self.set_font('Arial', 'B', 14)
        self.cell(40, 10, 'Student:', ln=0)
        self.set_font('Arial', '', 14)
        self.cell(0, 10, student_name, ln=1)
        
        self.set_x(15)
        self.set_font('Arial', 'B', 14)
        self.cell(40, 10, 'Grade:', ln=0)
        self.set_font('Arial', '', 14)
        self.cell(0, 10, grade_level, ln=1)
        
        self.ln(10)

    def add_performance_summary(self, grades_history: List[Dict[str, Any]]):
        self.add_section_title("📈 Performance Summary")
        
        if not grades_history:
            self.set_font('Arial', '', 12)
            self.cell(0, 10, 'No previous grades available', ln=True)
            return
            
        # Extract scores and create performance visualization
        scores = []
        dates = []
        for grade in grades_history:
            percentage = grade.get('percentage', 0)
            if isinstance(percentage, str):
                percentage = float(percentage.rstrip('%'))
            scores.append(float(percentage))
            dates.append(grade.get('date', datetime.now().strftime('%Y-%m-%d')))
        
        if scores:
            # Create performance graph
            plt.figure(figsize=(8, 4))
            plt.style.use('seaborn')
            
            # Plot actual scores
            plt.plot(range(len(scores)), scores, 'o-', linewidth=2, markersize=8, 
                    color='#1f77b4', label='Actual Scores')
            
            # Add trend line
            z = np.polyfit(range(len(scores)), scores, 1)
            p = np.poly1d(z)
            plt.plot(range(len(scores)), p(range(len(scores))), '--', 
                    color='#ff7f0e', label='Trend')
            
            # Customize the plot
            plt.title('Performance Trend', pad=15)
            plt.xlabel('Assessments')
            plt.ylabel('Score (%)')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Add score labels
            for i, score in enumerate(scores):
                plt.annotate(f'{score:.1f}%', 
                           (i, score),
                           textcoords="offset points",
                           xytext=(0,10),
                           ha='center',
                           bbox=dict(facecolor='white', edgecolor='none', alpha=0.8))
            
            # Save plot
            plt.savefig('temp_performance.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Add plot to PDF
            self.image('temp_performance.png', x=10, w=190)
            os.remove('temp_performance.png')
            self.ln(5)
            
            # Add summary statistics
            self.create_stats_box(scores)
            self.ln(10)

    def create_stats_box(self, scores: List[float]):
        """Create a statistics summary box"""
        avg_score = sum(scores) / len(scores)
        latest_score = scores[-1]
        improvement = latest_score - scores[0]
        consistency = np.std(scores) if len(scores) > 1 else 0
        
        # Create a box with statistics
        self.set_fill_color(240, 248, 255)
        self.set_draw_color(31, 119, 180)
        
        # Statistics box
        box_height = 40
        self.rect(10, self.get_y(), self.width - 20, box_height, 'DF')
        
        # Add statistics in columns
        col_width = (self.width - 20) / 4
        metrics = [
            ('Average', f'{avg_score:.1f}%'),
            ('Latest', f'{latest_score:.1f}%'),
            ('Improvement', f'{improvement:+.1f}%'),
            ('Consistency', f'{100-consistency:.1f}%')
        ]
        
        self.set_xy(10, self.get_y())
        for title, value in metrics:
            self.set_font('Arial', 'B', 10)
            self.cell(col_width, box_height/2, title, align='C')
            self.set_xy(self.get_x() - col_width, self.get_y() + box_height/2)
            self.set_font('Arial', '', 12)
            self.cell(col_width, box_height/2, value, align='C')
            self.set_xy(self.get_x(), self.get_y() - box_height/2)

    def add_latest_assessment(self, feedback: Dict[str, Any]):
        self.add_section_title("📝 Latest Assessment Details")
        
        # Grade and percentage
        self.create_grade_box(feedback.get('grade', 'N/A'), 
                            feedback.get('percentage', '0%'))
        self.ln(10)
        
        # Create two columns for strengths and weaknesses
        col_width = (self.width - 40) / 2
        y_position = self.get_y()
        
        # Strengths column
        self.set_xy(20, y_position)
        self.create_feedback_section("💪 Strengths", 
                                   feedback.get('strengths', []),
                                   col_width,
                                   background_color=(230, 255, 230))
        
        # Weaknesses column
        self.set_xy(20 + col_width + 10, y_position)
        self.create_feedback_section("🎯 Areas for Improvement",
                                   feedback.get('weaknesses', []),
                                   col_width,
                                   background_color=(255, 240, 240))
        
        # Move to bottom of columns
        self.set_y(max(self.get_y(), y_position + 60))
        self.ln(10)
        
        # Detailed feedback
        if 'detailed_feedback' in feedback:
            self.add_section_title("📋 Detailed Feedback")
            self.set_font('Arial', '', 11)
            self.multi_cell(0, 5, feedback['detailed_feedback'])
            self.ln(5)

    def create_grade_box(self, grade: str, percentage: str):
        """Create an attractive grade display box"""
        self.set_fill_color(240, 248, 255)
        self.set_draw_color(31, 119, 180)
        
        # Main grade box
        box_width = 60
        box_height = 40
        x_center = self.width / 2 - box_width
        
        # Grade box
        self.rect(x_center, self.get_y(), box_width, box_height, 'DF')
        self.set_xy(x_center, self.get_y())
        self.set_font('Arial', 'B', 24)
        self.cell(box_width, box_height, grade, align='C')
        
        # Percentage box
        self.rect(x_center + box_width, self.get_y(), box_width, box_height, 'DF')
        self.set_xy(x_center + box_width, self.get_y())
        self.cell(box_width, box_height, percentage, align='C')

    def create_feedback_section(self, title: str, items: List[str], width: float, 
                              background_color: tuple):
        """Create a feedback section with colored background"""
        self.set_fill_color(*background_color)
        self.set_draw_color(128, 128, 128)
        
        # Calculate box height based on content
        min_height = 60
        text_height = len(items) * 6 + 10  # 6 points per line + padding
        box_height = max(min_height, text_height)
        
        # Draw box
        self.rect(self.get_x(), self.get_y(), width, box_height, 'DF')
        
        # Add title
        self.set_xy(self.get_x() + 5, self.get_y() + 5)
        self.set_font('Arial', 'B', 12)
        self.cell(width - 10, 8, title, ln=True)
        
        # Add items
        self.set_font('Arial', '', 10)
        for item in items:
            self.set_x(self.get_x() + 5)
            self.multi_cell(width - 10, 6, f"• {item}")

    def add_improvement_plan(self, feedback: Dict[str, Any]):
        self.add_section_title("🎯 Improvement Plan")
        
        suggestions = feedback.get('improvement_suggestions', [])
        if not suggestions:
            self.set_font('Arial', '', 12)
            self.cell(0, 10, 'No improvement suggestions available', ln=True)
            return
        
        # Create boxes for each suggestion
        for i, suggestion in enumerate(suggestions, 1):
            self.create_suggestion_box(i, suggestion)
            self.ln(5)

    def create_suggestion_box(self, number: int, suggestion: str):
        """Create an attractive suggestion box"""
        self.set_fill_color(245, 245, 255)
        self.set_draw_color(31, 119, 180)
        
        # Calculate box dimensions
        margin = 10
        box_width = self.width - (2 * margin)
        
        # Draw box with rounded corners
        self.rounded_rect(margin, self.get_y(), box_width, 20, 3, 'DF')
        
        # Add suggestion number
        self.set_xy(margin + 5, self.get_y() + 2)
        self.set_font('Arial', 'B', 12)
        self.cell(20, 16, f"{number}.", ln=0)
        
        # Add suggestion text
        self.set_xy(margin + 25, self.get_y() + 2)
        self.set_font('Arial', '', 11)
        self.multi_cell(box_width - 30, 6, suggestion)

    def add_qr_codes(self, teacher_contact: str, next_assignment_url: str):
        self.add_section_title("📱 Quick Access")
        
        # Create QR codes
        qr_size = 40  # Size in mm
        margin = 20   # Margin from left
        spacing = 10  # Space between QR codes
        
        # Generate and save QR codes
        codes = [
            ("Contact Teacher", teacher_contact, 'temp_teacher_qr.png'),
            ("Next Assignment", next_assignment_url, 'temp_assignment_qr.png')
        ]
        
        # Calculate positions
        total_width = len(codes) * (qr_size + spacing) - spacing
        start_x = (self.width - total_width) / 2
        
        for i, (label, data, filename) in enumerate(codes):
            # Generate QR code
            qr = qrcode.make(data)
            qr.save(filename)
            
            # Calculate position
            x = start_x + i * (qr_size + spacing)
            y = self.get_y()
            
            # Add QR code to PDF
            self.image(filename, x=x, y=y, w=qr_size)
            
            # Add label
            self.set_xy(x, y + qr_size + 2)
            self.set_font('Arial', '', 10)
            self.cell(qr_size, 6, label, align='C')
            
            # Clean up
            os.remove(filename)
        
        self.ln(qr_size + 10)
        
        # Add scanning instructions
        self.set_font('Arial', 'I', 9)
        self.multi_cell(0, 5, "📱 Scan these QR codes with your phone's camera to quickly access important information.")

    def add_section_title(self, title: str):
        """Add a section title with consistent styling"""
        self.set_font('Arial', 'B', 16)
        self.set_fill_color(31, 119, 180)
        self.set_text_color(255, 255, 255)
        
        # Add colored background behind title
        self.rect(10, self.get_y(), self.width - 20, 10, 'F')
        self.set_xy(15, self.get_y())
        self.cell(0, 10, title, ln=True)
        
        # Reset text color
        self.set_text_color(0, 0, 0)
        self.ln(5)

def generate_parent_report(
    student_name: str,
    grade_level: str,
    grades_history: List[Dict[str, Any]],
    latest_feedback: Dict[str, Any],
    teacher_contact: str,
    next_assignment_url: str
) -> bytes:
    """Generate a complete parent report in PDF format"""
    report = ParentReport()
    
    # Add report sections
    report.add_student_info(student_name, grade_level)
    report.add_performance_summary(grades_history)
    report.add_latest_assessment(latest_feedback)
    report.add_improvement_plan(latest_feedback)
    report.add_qr_codes(teacher_contact, next_assignment_url)
    
    # Save to temporary file and return bytes
    temp_file = "temp_report.pdf"
    try:
        report.output(temp_file)
        with open(temp_file, 'rb') as f:
            pdf_bytes = f.read()
        return pdf_bytes
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)