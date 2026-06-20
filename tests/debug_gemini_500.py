from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)
client = genai.Client()

system_prompt = (
    "You are a coding assistant providing a draft (叩き台) based on specific "
    "instructions.\nYour goal is to perform the heavy lifting of writing code "
    "so the Architect can refine it.\n"
    "RULES:\n"
    "- Output ONLY the code. No explanations, no markdown blocks.\n"
    "- Maintain existing indentation and style.\n"
    "- Provide the FULL replacement for the given snippet.\n"
    "- If unsure, provide the most likely draft; the Architect will handle "
    "final validation.\n"
)

instruction = "Add a divide(a, b) function to this calculator. Return the complete updated file."
snippet = """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""

prompt = (
    f"{system_prompt}\n### Instruction:\n{instruction}\n\n### Current Code Snippet:\n{snippet}\n\n"
)

print("--- PROMPT ---")
print(prompt)
print("--------------")

try:
    response = client.models.generate_content(
        model="models/gemma-4-31b-it",
        contents=prompt,
        config=genai.types.GenerateContentConfig(temperature=0.2),
    )
    print("SUCCESS")
    print(response.text)
except Exception as e:
    print(f"FAILED: {e}")
