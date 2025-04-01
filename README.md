# EduAI Assistant 🎓

An AI-powered teaching assistant platform built with Streamlit and Google Gemini.

## Features

- 📝 **Assignment Processing**
  - PDF upload and text extraction
  - Multi-page document support
  - Advanced OCR using Google Gemini

- ✍️ **AI Grading System**
  - Automated assignment evaluation
  - Subject-specific grading
  - Detailed feedback with:
    - Letter grades and percentage scores
    - Strengths and weaknesses analysis
    - Improvement suggestions
    - Related concepts review
    - Real-world applications

- 🔍 **Past Year Questions Analysis**
  - Pattern recognition
  - Topic prediction
  - Difficulty analysis
  - Custom practice question generation

- 📊 **Student Analytics**
  - Performance tracking
  - Grade history visualization
  - Trend analysis with charts
  - Detailed feedback history

- ❓ **Question Bank Generator**
  - Custom question generation
  - Multiple subjects and topics
  - Adjustable difficulty levels
  - Various question types
  - Export to PDF, CSV, JSON

- 📋 **Parent Reports**
  - Weekly progress summaries
  - Performance visualizations
  - QR codes for quick access
  - Personalized feedback

- 💬 **Teacher Chat Assistant**
  - Interactive AI chat
  - Teaching methodology assistance
  - Assessment guidance
  - Educational query support

## Project Structure

```
├── src/                    # Source code
│   ├── components/         # UI components
│   │   ├── home.py        # Home page
│   │   ├── upload.py      # File upload
│   │   ├── grading.py     # Assignment grading
│   │   └── analysis.py    # Student analysis
│   └── config.py          # Configuration
├── utils/                  # Utility functions
│   ├── ai_grading.py      # AI grading logic
│   ├── chat_processing.py # Chat functionality
│   ├── feedback_display.py # Feedback UI
│   ├── question_generation.py # Question gen
│   └── sample_data.py     # Sample content
├── static/                # Static assets
├── templates/            # HTML templates
├── pdf_to_text.py       # PDF processing
├── parent_report.py     # Report generation
├── pyq_analysis.py      # Question analysis
└── app.py               # Main application
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - Create a `.env` file
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## Dependencies

- streamlit
- PyMuPDF
- Pillow
- google-generativeai
- python-dotenv
- google-genai
- pandas
- matplotlib
- seaborn
- fpdf2>=2.8.2
- qrcode
- python-barcode

## Development

The application is organized into modular components for better maintainability:

- Components are in `src/components/`
- Utility functions are in `utils/`
- Main configuration in `src/config.py`
- PDF processing in `pdf_to_text.py`
- Past year question analysis in `pyq_analysis.py`
- Parent report generation in `parent_report.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.