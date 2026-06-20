import os
import pytest
from mcp_ai_worker.server import draft_code


def test_calculator_add_divide(tmp_path, mocker):
    """
    Test the pipeline when adding a new function to an existing file.
    This simulates the exact scenario described in the feedback.
    """
    # Mock the LLM call to avoid needing API keys and to ensure predictability
    mock_llm = mocker.patch("mcp_ai_worker.client.SubLLMClient.call_any")
    mock_llm.return_value = """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b
"""

    # 1. Prepare existing file
    calc_file = tmp_path / "calculator.py"
    original_code = """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""
    calc_file.write_text(original_code, encoding="utf-8")

    # 2. Setup environment
    os.environ["AI_PROVIDER"] = "gemini"
    os.environ["DRAFTING_MODEL"] = "models/gemma-4-31b-it"

    # 3. Call the draft_code function directly
    instruction = (
        "Add a divide(a, b) function to this calculator. Return the complete updated file."
    )

    try:
        draft_code(
            path=str(calc_file),
            instruction=instruction,
        )

        # 4. Check the result
        updated_code = calc_file.read_text(encoding="utf-8")

        assert "def divide" in updated_code, "Divide function was not added!"
        assert "def add" in updated_code, "Original add function was lost!"

    except Exception as e:
        pytest.fail(f"Pipeline crashed with error: {e}")
