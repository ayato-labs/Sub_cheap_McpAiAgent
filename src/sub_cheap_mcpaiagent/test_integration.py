import os
from dotenv import load_dotenv
from mcp_server import draft_code

# Load environment to ensure GOOGLE_API_KEY is available for the tool
load_dotenv(override=True)


def test_draft():
    test_file = "test_output.py"
    instruction = "Write a simple python function that adds two numbers."

    print(f"Testing draft_code on {test_file}...")
    result = draft_code(path=test_file, instruction=instruction, model="gemini")
    print(f"Result: {result}")

    if os.path.exists(test_file):
        with open(test_file, "r") as f:
            print("--- Generated Content ---")
            print(f.read())
            print("-------------------------")
        os.remove(test_file)


if __name__ == "__main__":
    test_draft()
