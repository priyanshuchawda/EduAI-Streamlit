from fpdf import FPDF
import os

def create_math_assignment():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Mathematics Assignment - Algebra", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    questions = [
        "1. Solve the quadratic equation: x² + 5x + 6 = 0",
        "2. Factor the expression: 2x² - 7x + 3",
        "3. Find the value of x: 3(x + 2) = 21",
        "4. Simplify: (2x + 3)(x - 4)",
        "5. Solve the system of equations:\n   y = 2x + 1\n   y = -x + 7"
    ]
    
    for q in questions:
        pdf.multi_cell(0, 10, q)
        pdf.ln(5)
    
    pdf.output("sample_data/assignments/math_assignment.pdf")

def create_science_assignment():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Science Assignment - Basic Chemistry", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    questions = [
        "1. Balance the chemical equation: H2 + O2 -> H2O",
        "2. Define and explain the difference between atoms and molecules.",
        "3. What is the atomic number of Carbon? Describe its electron configuration.",
        "4. List three examples of physical changes in matter.",
        "5. Explain the process of photosynthesis in simple terms."
    ]
    
    for q in questions:
        pdf.multi_cell(0, 10, q)
        pdf.ln(5)
    
    pdf.output("sample_data/assignments/science_assignment.pdf")

def create_english_assignment():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "English Assignment - Literature Analysis", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 12)
    text = """Read the following excerpt and answer the questions below:

    "It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness..."
    - Charles Dickens, A Tale of Two Cities

    Questions:
    1. What literary device is being used in this opening passage?
    2. Explain the significance of the contrasting pairs in this excerpt.
    3. How does this opening set the tone for the rest of the novel?
    4. What historical period is being referenced?
    5. Write a paragraph analyzing the author's purpose in using these contrasts."""
    
    pdf.multi_cell(0, 10, text)
    pdf.output("sample_data/assignments/english_assignment.pdf")

def main():
    # Create assignments directory if it doesn't exist
    os.makedirs("sample_data/assignments", exist_ok=True)
    
    # Generate sample assignments
    create_math_assignment()
    create_science_assignment()
    create_english_assignment()

if __name__ == "__main__":
    main()