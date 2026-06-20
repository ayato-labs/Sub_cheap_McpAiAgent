import pytest
from unittest.mock import patch
from mcp_ai_worker.server import draft_code, execute_command, find_and_draft_edit


@pytest.fixture
def mock_llm(mocker):
    return mocker.patch("mcp_ai_worker.client.SubLLMClient.call_any")


def test_draft_code_invalid_range(tmp_path, mock_llm):
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hi')\n", encoding="utf-8")

    # Start line > end line
    result = draft_code(
        path=str(test_file), instruction="update", start_line=10, end_line=5, model="gemini"
    )
    assert "Error: start_line cannot be greater than end_line." in result


def test_draft_code_missing_file(mock_llm):
    # Non-existent path
    mock_llm.return_value = "translated instruction"
    result = draft_code(path="C:/non_existent_file_12345.py", instruction="update", model="gemini")
    assert "Error reading file." in result or "Error writing file." in result


def test_draft_code_llm_failure(tmp_path, mock_llm):
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hi')\n", encoding="utf-8")

    # Simulate LLM API exception
    mock_llm.side_effect = Exception("API Key Expired")

    result = draft_code(path=str(test_file), instruction="update", model="gemini")
    assert "Drafting failed" in result
    assert "API Key Expired" in result


def test_find_and_draft_edit_malformed_json(tmp_path, mock_llm):
    proj_dir = tmp_path / "my_proj"
    proj_dir.mkdir()
    src_file = proj_dir / "main.py"
    src_file.write_text("def hello(): pass\n", encoding="utf-8")

    # Mock 1: Repo Map
    # Mock 2: Targeting LLM returns malformed JSON
    mock_llm.return_value = (
        "I cannot find the file, but here is a guess: { 'file': 'main.py' }"
    )  # Invalid JSON (single quotes)

    with (
        patch("mcp_ai_worker.server.generate_repo_map", return_value="main.py: hello"),
        patch(
            "mcp_ai_worker.server.load_prompt_template", return_value="{requirement}\n{repo_map}"
        ),
    ):
        result = find_and_draft_edit(requirement="update", target_dir=str(proj_dir))

    assert "Failed to parse target JSON" in result


def test_execute_command_timeout(tmp_path, mock_llm):
    # Use a python script that sleeps, and use the venv python
    sleep_script = tmp_path / "sleep.py"
    sleep_script.write_text("import time\ntime.sleep(10)", encoding="utf-8")

    # Use the current python executable to ensure it's found
    import sys

    python_exe = sys.executable

    result = execute_command(
        command=f'"{python_exe}" {sleep_script}', working_dir=str(tmp_path), timeout_seconds=1
    )

    assert "Warning: Command timed out" in result
    mock_llm.assert_called()


def test_execute_command_system_error(tmp_path):
    # Command that doesn't exist
    result = execute_command(command="non_existent_command_12345", working_dir=str(tmp_path))
    assert "Command completed" in result
    assert "Exit code: 1" in result
