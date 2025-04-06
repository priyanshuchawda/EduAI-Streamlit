# EduAI Assistant 🎓

An intelligent teaching assistant powered by Google's Gemini AI

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

- 📅 **Calendar & Scheduling**
  - Google Calendar integration
  - AI-powered lesson scheduling
  - Recurring schedule support
  - Topic distribution planning
  - Schedule conflict detection
  - Visual calendar interface

- 📚 **Syllabus Management**
  - Topic tracking and organization
  - Progress monitoring
  - AI-suggested topic distribution
  - Smart scheduling recommendations
  - Subject-specific planning
  - Real-time progress tracking

- 📋 **Parent Reports**
  - Weekly progress summaries
  - Performance visualizations
  - Trend analysis
  - Improvement suggestions
  - Subject-wise breakdown

## Tech Stack
- Frontend: Streamlit
- AI: Google Gemini 2.0
- Data Processing: Pandas, PyMuPDF
- Visualization: Matplotlib
- Calendar: Google Calendar API
- Storage: Google Sheets API

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`:
   ```
   GEMINI_API_KEY=your_api_key
   GOOGLE_CREDENTIALS_PATH=path_to_credentials.json
   ```
4. Run the application: `streamlit run app.py`

## Deployment on Streamlit Cloud

1. Fork this repository to your GitHub account
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Click "New app" and select this repository
4. Set the following environment variables in Streamlit Cloud settings:
   - GEMINI_API_KEY
   - GOOGLE_CREDENTIALS_PATH
   - GOOGLE_APPLICATION_CREDENTIALS
5. Deploy the app

### Required Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key
- `GOOGLE_CREDENTIALS_PATH`: Path to Google Cloud credentials JSON
- `GOOGLE_APPLICATION_CREDENTIALS`: Full Google Cloud service account JSON

## Key Innovations
1. Advanced AI-powered assignment grading with subject-specific criteria
2. Smart syllabus management with AI-suggested topic distribution
3. Intelligent lesson scheduling with Google Calendar integration
4. Custom question generation with varied difficulty levels
5. Comprehensive performance analytics and visualization

## Development Status
- Core Features: ✅ Completed
- Testing: 🟡 In Progress
- Documentation: ✅ Completed
- Deployment: 🟡 In Progress

## Future Roadmap
1. Mobile application development
2. LMS integration capabilities
3. Multi-language support
4. Real-time collaboration features
5. Advanced analytics dashboard