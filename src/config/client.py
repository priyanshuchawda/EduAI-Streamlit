import os
import streamlit as st
from google import genai
from dotenv import load_dotenv

# Load environment variables only if not in Streamlit Cloud
if not hasattr(st, 'secrets'):
    load_dotenv()

# Initialize API client
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] if hasattr(st, 'secrets') else os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables or Streamlit secrets")

client = genai.Client(api_key=GEMINI_API_KEY)
model = "gemini-2.0-flash"