import os
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize API client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

client = genai.Client(api_key=GEMINI_API_KEY)
model = "gemini-2.0-flash"