from typing import Dict, Any

def get_sample_assignments() -> Dict[str, Dict[str, str]]:
    """Return pre-defined sample assignments for demo purposes"""
    return {
        "Mathematics": {
            "text": """Solution to Quadratic Equation Problem:
            
For the equation x² + 5x + 6 = 0:
1. Using the quadratic formula: x = [-b ± √(b² - 4ac)] / 2a
2. Here, a = 1, b = 5, c = 6
3. x = [-5 ± √(25 - 24)] / 2
4. x = [-5 ± √1] / 2
5. x = [-5 ± 1] / 2
Therefore, x = -3 or x = -2

The solutions can be verified by substituting back:
For x = -3: (-3)² + 5(-3) + 6 = 9 - 15 + 6 = 0
For x = -2: (-2)² + 5(-2) + 6 = 4 - 10 + 6 = 0""",
            "subject": "Mathematics"
        },
        "Science": {
            "text": """Chemical Reactions Lab Report

Experiment: Observing the reaction between baking soda and vinegar

Materials:
- Sodium bicarbonate (NaHCO₃)
- Acetic acid (CH₃COOH)
- Beaker
- Thermometer
- Scale

Procedure:
1. Measured 50mL of vinegar into beaker
2. Added 1 tablespoon of baking soda
3. Recorded temperature change and observations

Results:
- Initial temperature: 22°C
- Final temperature: 19°C
- Observed bubbling and gas formation
- Reaction was exothermic

Chemical equation:
NaHCO₃ + CH₃COOH → CH₃COONa + H₂O + CO₂

Conclusion:
The reaction produced sodium acetate, water, and carbon dioxide gas. The temperature decrease indicates it was an endothermic reaction.""",
            "subject": "Science"
        },
        "English": {
            "text": """Literary Analysis: Romeo and Juliet

Theme Analysis: Love vs. Hate

Shakespeare's Romeo and Juliet masterfully explores the conflict between love and hate through the feuding Montague and Capulet families. The play demonstrates how their hatred destroys the pure love between Romeo and Juliet.

Key Evidence:
1. The prologue introduces "two households, both alike in dignity" but consumed by "ancient grudge."
2. Romeo and Juliet's love blooms despite family hatred
3. Tybalt's death shows how hatred leads to tragedy
4. The final scene reconciles the families, but at great cost

Literary Devices:
- Foreshadowing in the prologue
- Metaphors comparing love to light and hatred to darkness
- Dramatic irony throughout the play
- Symbolism in the balcony scene

Conclusion:
Shakespeare shows that love has the power to overcome hatred, but at a tragic cost. The death of the young lovers finally ends the feud, suggesting that love ultimately triumphs over hate, though sometimes too late.""",
            "subject": "English"
        }
    }

def get_sample_questions(subject: str) -> list:
    """Return pre-defined sample questions for demo purposes"""
    sample_questions = {
        "Mathematics": [
            {
                "question": "What is the derivative of f(x) = x² + 3x + 2?",
                "answer": "f'(x) = 2x + 3",
                "explanation": "Using the power rule for derivatives: the derivative of x² is 2x, and the derivative of 3x is 3. Constants (2) become 0."
            },
            {
                "question": "Solve the system of equations: 2x + y = 7, x - y = 1",
                "answer": "x = 3, y = 1",
                "explanation": "Using substitution method: From second equation, y = x - 1. Substitute into first equation: 2x + (x - 1) = 7. Solve: 3x - 1 = 7, so x = 3. Then y = 3 - 1 = 1"
            }
        ],
        "Science": [
            {
                "question": "Explain the difference between mitosis and meiosis.",
                "answer": "Mitosis produces 2 identical cells, meiosis produces 4 genetically diverse cells",
                "explanation": "Mitosis is for growth and repair, creating identical daughter cells. Meiosis is for reproduction, creating gametes with half the chromosomes and genetic variation."
            },
            {
                "question": "What are the three states of matter? Give an example of each.",
                "answer": "Solid (ice), Liquid (water), Gas (water vapor)",
                "explanation": "Matter exists in three main states based on molecular arrangement and energy. Examples show how H2O can exist in all three states."
            }
        ],
        "English": [
            {
                "question": "Identify and explain three different types of figurative language.",
                "answer": "Metaphor, Simile, Personification",
                "explanation": "Metaphor directly compares two unlike things. Simile compares using 'like' or 'as'. Personification gives human qualities to non-human things."
            },
            {
                "question": "What are the elements of a Shakespearean sonnet?",
                "answer": "14 lines, iambic pentameter, rhyme scheme ABAB CDCD EFEF GG",
                "explanation": "Shakespearean sonnets have a specific structure with three quatrains and a couplet, using iambic pentameter throughout."
            }
        ]
    }
    return sample_questions.get(subject, [])