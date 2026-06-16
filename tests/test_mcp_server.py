import pytest
from mcp_server import clean_code_output, draft_code


def test_clean_code_output_removes_markdown():
    dirty = "```python\ndef hello():\n    pass\n```"
    clean = clean_code_output(dirty)
    assert clean == "def hello():\n    pass"


def test_clean_code_output_no_markdown():
    clean_input = "def hello():\n    pass"
    assert clean_code_output(clean_input) == clean_input


def test_clean_code_output_unclosed_markdown():
    dirty = "```python\ndef hello():\n    pass"
    clean = clean_code_output(dirty)
    assert clean == "def hello():\n    pass"


@pytest.fixture
def mock_backend(mocker):
    # Mock call_any to return different values based on the role or just a default
    return mocker.patch("mcp_server.SubLLMClient.call_any", return_value="def mock_func():\n    return 42")


def test_draft_code_full_overwrite(tmp_path, mock_backend):
    test_file = tmp_path / "test.py"
    test_file.write_text("old code\n")

    result = draft_code(path=str(test_file), instruction="rewrite", model="gemini")

    assert "Successfully wrote to" in result
    assert test_file.read_text() == "def mock_func():\n    return 42\n"
    # Might be called once for translation (if check is loose) and once for drafting
    assert mock_backend.called


def test_draft_code_translation_trigger(tmp_path, mock_backend):
    test_file = tmp_path / "test.py"
    # Instruction contains Japanese
    instruction = "日本語の指示"
    
    # Configure mock to return translation first, then code
    mock_backend.side_effect = ["Translated Instruction", "def translated_func(): pass"]

    result = draft_code(path=str(test_file), instruction=instruction, model="gemini")

    assert "Successfully wrote to" in result
    # First call should be translation
    args, kwargs = mock_backend.call_args_list[0]
    assert "Translate the following text" in args[1]
    assert "日本語の指示" in args[1]


def test_draft_code_partial_overwrite(tmp_path, mock_backend):
    test_file = tmp_path / "test.py"
    original_content = "line 1\nline 2\nline 3\nline 4\n"
    test_file.write_text(original_content)

    # Return some code to replace
    mock_backend.return_value = "new line 2\nnew line 3"

    result = draft_code(
        path=str(test_file), instruction="update lines", start_line=2, end_line=3, model="gemini"
    )

    assert "Updated lines 2-3" in result
    expected_content = "line 1\nnew line 2\nnew line 3\nline 4\n"
    assert test_file.read_text() == expected_content


def test_draft_code_new_directory(tmp_path, mock_backend):
    # Test file inside a directory that doesn't exist yet
    test_file = tmp_path / "new_dir" / "test.py"

    result = draft_code(path=str(test_file), instruction="create", model="ollama")

    assert "Successfully wrote to" in result
    assert test_file.exists()
    assert test_file.read_text() == "def mock_func():\n    return 42\n"



def test_draft_code_invalid_lines(tmp_path):
    test_file = tmp_path / "test.py"

    result = draft_code(path=str(test_file), instruction="update", start_line=5, end_line=2)

    assert result == "Error: start_line cannot be greater than end_line."
