import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import streamlit as st          # <-- new import for streamlit UI
import tempfile                # <-- new import for temporary file handling

# Load environment variables from .env file
load_dotenv()

# Initialize the API client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_pdf(pdf_path: str, query: str = "Please summarize this document."):
    """
    Upload and analyze a PDF file using Gemini API
    
    Args:
        pdf_path (str): Path to the PDF file
        query (str): Question or instruction for analyzing the PDF
    
    Returns:
        str: Gemini's response
    """
    try:
        # Upload the PDF file to Gemini
        document_file = client.files.upload(file=pdf_path)
        print(f"Document uploaded successfully: {document_file}")

        # Generate content using the uploaded PDF
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # Using the fast version
            contents=[query, document_file],  # Combining question with the document
            config=types.GenerateContentConfig(
                temperature=0.4,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,  # Maximum length for detailed analysis
            )
        )
        
        return response.text
        
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

if __name__ == "__main__":
    st.title("PDF Analysis with Gemini API")
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    # Removed text_input for query; using automatic extraction query
    if uploaded_file is not None:
        query = "Extract text from this PDF automatically."  # new automatic query
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp.flush()
            result = analyze_pdf(tmp.name, query)
        st.write("Result:")
        st.write(result)