import os
import streamlit as st
from google import genai
from dotenv import load_dotenv

# Load environment variables only if not in Streamlit Cloud
if not hasattr(st, 'secrets'):
    load_dotenv()

# Initialize API client
def get_api_key():
    """Get Gemini API key from environment or Streamlit secrets"""
    if hasattr(st, 'secrets'):
        return st.secrets['GEMINI_API_KEY']
    return os.getenv('GEMINI_API_KEY')

GEMINI_API_KEY = get_api_key()
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables or Streamlit secrets")

client = genai.Client(api_key=GEMINI_API_KEY)
model = "gemini-2.0-flash"