import os
from dotenv import load_dotenv
import google.generativeai as genai

# Use override=True to ensure .env values take precedence over system environment
load_dotenv(override=True)
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env")
else:
    # Print key prefix for debugging
    print(f"Key begins with: {api_key[:10]}...")
    genai.configure(api_key=api_key)
    print("Listing available models...")
    try:
        models = genai.list_models()
        found = False
        for m in models:
            if "generateContent" in m.supported_generation_methods:
                print(f"Name: {m.name}, Display Name: {m.display_name}")
                if "gemma" in m.name.lower():
                    found = True
        if not found:
            print("No gemma models found in the list.")
    except Exception as e:
        print(f"Error: {e}")
