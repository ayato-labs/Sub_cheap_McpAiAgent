import os
import pytest
from pathlib import Path
from sub_cheap_mcpaiagent.server import draft_code, SubLLMClient

# Mock the SubLLMClient to simulate a typical LLM response when asked to "add a divide function"
# We want to see how the pipeline handles both API responses and prompt building.

def test_calculator_add_divide(tmp_path):
    """
    Test the pipeline when adding a new function to an existing file.
    This simulates the exact scenario described in the feedback.
    """
    # 1. Prepare existing file
    calc_file = tmp_path / "calculator.py"
    original_code = '''def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
'''
    calc_file.write_text(original_code, encoding="utf-8")

    # 2. Setup environment for the test to use Genspark or a fast mock
    # For a true integration test, we will actually call the real backend (e.g. Gemini) 
    # to see if the 500 error comes from the API due to prompt structure.
    os.environ["AI_PROVIDER"] = "gemini"
    os.environ["DRAFTING_MODEL"] = "models/gemma-4-31b-it"
    
    # 3. Call the draft_code function directly
    # instruction: "既存のファイルに新しい関数を追加せよ (divide)"
    instruction = "Add a divide(a, b) function to this calculator. Return the complete updated file."
    
    try:
        result = draft_code(
            path=str(calc_file),
            instruction=instruction,
            # Intentionally omitting start_line/end_line to test full-file replacement behavior
        )
        print("Result Message:", result)
        
        # 4. Check the result
        updated_code = calc_file.read_text(encoding="utf-8")
        print("\n--- UPDATED CODE ---")
        print(updated_code)
        print("--------------------")
        
        assert "def divide" in updated_code, "Divide function was not added!"
        assert "def add" in updated_code, "Original add function was lost!"
        
    except Exception as e:
        pytest.fail(f"Pipeline crashed with error: {e}")
