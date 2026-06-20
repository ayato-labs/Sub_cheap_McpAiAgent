import pytest
from unittest.mock import patch
from mcp_ai_worker.server import draft_code, execute_command, find_and_draft_edit


@pytest.fixture
def mock_llm(mocker):
    return mocker.patch("mcp_ai_worker.client.SubLLMClient.call_any")


def test_draft_code_integration_success(tmp_path, mock_llm):
    test_file = tmp_path / "app.py"
    test_file.write_text("def old_func():\n    pass\n", encoding="utf-8")
    mock_llm.return_value = "def new_func():\n    return True\n"
    result = draft_code(path=str(test_file), instruction="Replace old_func with new_func", model="gemini")
    assert "Successfully wrote to" in result
    assert "def new_func():" in test_file.read_text()
    assert "def old_func():" not in test_file.read_text()


def test_draft_code_integration_partial_success(tmp_path, mock_llm):
    test_file = tmp_path / "app.py"
    content = "line 1\nline 2\nline 3\nline 4\n"
    test_file.write_text(content, encoding="utf-8")
    mock_llm.return_value = "new 2\nnew 3"
    result = draft_code(path=str(test_file), instruction="Update middle", start_line=2, end_line=3, model="gemini")
    assert "Updated lines 2-3" in result
    assert test_file.read_text() == "line 1\nnew 2\nnew 3\nline 4\n"


def test_execute_command_integration_short_log(tmp_path, mock_llm):
    # Use a command that is guaranteed to be very short
    result = execute_command(command="echo hello", working_dir=str(tmp_path))
    assert "Command completed" in result
    assert "Raw Output" in result
    mock_llm.assert_not_called()


def test_execute_command_integration_long_log_summarization(tmp_path, mock_llm):
    # Force a long log via a loop
    long_cmd = "python -c \"for i in range(1, 51): print(f'line {i}')\""
    mock_llm.return_value = "Summarized: 50 lines of output."
    result = execute_command(command=long_cmd, working_dir=str(tmp_path))
    assert "[Sub-LLM Log Summary]" in result
    assert "Summarized: 50 lines of output." in result
    mock_llm.assert_called()


def test_draft_code_integration_translation_trigger(tmp_path, mock_llm):
    test_file = tmp_path / "app.py"
    test_file.write_text("pass", encoding="utf-8")
    instruction = "関数を追加して"
    mock_llm.side_effect = ["Add a function", "def mock(): pass"]
    result = draft_code(path=str(test_file), instruction=instruction, model="gemini")
    assert "Successfully wrote to" in result
    assert mock_llm.call_count == 2


def test_find_and_draft_edit_integration(tmp_path, mock_llm):
    # Setup a mock project
    proj_dir = tmp_path / "my_proj"
    proj_dir.mkdir()
    src_file = proj_dir / "main.py"
    src_file.write_text("def hello():\n    print('hi')\n", encoding="utf-8")

    # Mock 1: Repo Map (not LLM) - handled by grep-ast. Let's mock SubLLMClient calls
    # Call 1: targeting LLM -> returns JSON
    # Call 2: drafting LLM -> returns code
    mock_llm.side_effect = [
        '{"target_file": "main.py", "target_entity": "hello"}',
        "def hello():\n    print('hello world')\n",
    ]

    # We need to make sure generate_repo_map works or is mocked.
    # Since grep-ast might not be installed in venv, we might need to mock it.
    with (
        patch("mcp_ai_worker.server.generate_repo_map", return_value="main.py: hello"),
        patch("mcp_ai_worker.server.load_prompt_template", return_value="{requirement}\n{repo_map}"),
    ):
        result = find_and_draft_edit(requirement="Change hello to print hello world", target_dir=str(proj_dir))

    assert "Updated lines" in result or "Successfully wrote" in result
    assert "print('hello world')" in src_file.read_text()
