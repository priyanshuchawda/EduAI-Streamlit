from setuptools import setup, find_packages

setup(
    name="eduai_assistant",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "PyMuPDF>=1.23.0",
        "Pillow>=10.0.0",
        "google-generativeai>=0.3.0",
        "python-dotenv>=1.0.0",
        "google-genai>=0.1.0",
        "pandas>=2.1.0",
        "matplotlib>=3.8.0",
        "seaborn>=0.13.0",
        "fpdf2>=2.8.2",
        "qrcode>=7.4.0",
        "python-barcode>=0.15.1",
        "numpy>=1.24.0"
    ],
    python_requires=">=3.8",
)