import pytest
import os
from pathlib import Path
from mcp_ai_worker.utils import (
    clean_json_output,
    extract_target_block,
    clean_code_output,
    _load_target_snippet,
    _write_back_changes
)

def test_clean_json_output():
    # Case 1: Standard markdown JSON block
    text = "Here is the result:\n```json\n{\"key\": \"value\"}\n```\nHope this helps!"
    assert clean_json_output(text) == '{"key": "value"}'

    # Case 2: No markdown, just JSON
    text = '{"key": "value"}'
    assert clean_json_output(text) == '{"key": "value"}'

    # Case 3: JSON with noise around it (fallback to { } search)
    text = "The response is: {\"key\": \"value\"} but not formatted."
    assert clean_json_output(text) == '{"key": "value"}'

    # Case 4: Completely invalid content
    text = "Nothing here"
    assert clean_json_output(text) == "Nothing here"

def test_clean_code_output():
    # Case 1: XML tags
    text = "<draft_output>\ndef hello():\n    pass\n</draft_output>"
    assert clean_code_output(text) == "def hello():\n    pass"

    # Case 2: Unclosed XML tags
    text = "<draft_output>\ndef hello():\n    pass"
    assert clean_code_output(text) == "def hello():\n    pass"

    # Case 3: Markdown blocks
    text = "```python\ndef hello():\n    pass\n```"
    assert clean_code_output(text) == "def hello():\n    pass"

    # Case 4: No tags, no markdown
    text = "def hello():\n    pass"
    assert clean_code_output(text) == "def hello():\n    pass"

    # Case 5: Noise phrases (short result)
    text = "Here is the updated code\ndef hello():\n    pass"
    assert "Here is the updated code" not in clean_code_output(text)

def test_extract_target_block(tmp_path):
    content = (
        "import os\n\n"
        "def add(a, b):\n"
        "    return a + b\n\n"
        "def subtract(a, b):\n"
        "    return a - b\n\n"
        "class Calc:\n"
        "    def run(self):\n"
        "        print('running')\n"
    )
    filepath = tmp_path / "test_code.py"
    filepath.write_text(content, encoding="utf-8")

    # Test finding a function
    snippet, start, end, full = extract_target_block(str(filepath), "add")
    assert "def add(a, b):" in snippet
    assert start == 3
    assert "return a + b" in snippet

    # Test finding a class
    snippet, start, end, full = extract_target_block(str(filepath), "Calc")
    assert "class Calc:" in snippet
    assert start == 9

    # Test not finding anything
    snippet, start, end, full = extract_target_block(str(filepath), "missing")
    assert snippet == ""
    assert start == 0

def test_load_target_snippet(tmp_path):
    content = ["line 1\n", "line 2\n", "line 3\n", "line 4\n", "line 5\n"]
    filepath = tmp_path / "test.txt"
    filepath.write_text("".join(content), encoding="utf-8")

    # Case 1: Full file
    snippet, full = _load_target_snippet(filepath, None, None)
    assert snippet == "".join(content)
    assert full == content

    # Case 2: Partial range
    snippet, full = _load_target_snippet(filepath, 2, 3)
    assert snippet == "line 2\nline 3\n"

    # Case 3: Out of bounds range (clamped)
    snippet, full = _load_target_snippet(filepath, 1, 100)
    assert snippet == "".join(content)

    # Case 4: Non-existent file
    snippet, full = _load_target_snippet(Path("missing.txt"), None, None)
    assert snippet == ""
    assert full == []

def test_write_back_changes(tmp_path):
    content = ["line 1\n", "line 2\n", "line 3\n", "line 4\n"]
    filepath = tmp_path / "test.txt"
    filepath.write_text("".join(content), encoding="utf-8")

    # Case 1: Full write
    msg = _write_back_changes(filepath, "new content", None, None, content, "model-1")
    assert filepath.read_text() == "new content\n"
    assert "Successfully wrote" in msg

    # Case 2: Partial update (lines 2-3)
    # Reset file
    filepath.write_text("".join(content), encoding="utf-8")
    msg = _write_back_changes(filepath, "new 2\nnew 3", 2, 3, content, "model-1")
    expected = "line 1\nnew 2\nnew 3\nline 4\n"
    assert filepath.read_text() == expected
    assert "Updated lines 2-3" in msg

    # Case 3: Partial update ensuring newline at end of generated code
    filepath.write_text("".join(content), encoding="utf-8")
    msg = _write_back_changes(filepath, "new 2", 2, 2, content, "model-1")
    # "new 2" does not end in \n, _write_back_changes should add it.
    assert "line 1\nnew 2\nline 3\nline 4\n" == filepath.read_text()
