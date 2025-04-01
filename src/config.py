import os
from google import genai
from google.genai import types

# Initialize the Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Use flash model for faster processing
model = "gemini-2.0-flash"  # Using flash model for faster responses

# Default configuration for Gemini
default_generation_config = types.GenerateContentConfig(
    temperature=0.7,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,  # Set to 8192 token limit
    response_mime_type="text/plain"
)