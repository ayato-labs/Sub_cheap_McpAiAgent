import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from mcp_ai_worker.server import draft_code, find_and_draft_edit
from mcp_ai_worker.client import SubLLMClient

@pytest.fixture
def mock_llm(mocker):
    return mocker.patch("mcp_ai_worker.client.SubLLMClient.call_any")

def test_system_flow_full_rewrite(tmp_path, mock_llm):
    # GIVEN: A project with one file
    proj_dir = tmp_path / "project"
    proj_dir.mkdir()
    test_file = proj_dir / "main.py"
    test_file.write_text("print('old')\n", encoding="utf-8")
    
    # Mock LLM to return a full rewrite
    mock_llm.return_value = "print('new')\n"
    
    # WHEN: User requests a full rewrite
    result = draft_code(
        path=str(test_file),
        instruction="Change 'old' to 'new'",
        model="gemini"
    )
    
    # THEN: The file is updated and the user is notified
    assert "Successfully wrote to" in result
    assert test_file.read_text() == "print('new')\n"

def test_system_flow_add_method_to_class(tmp_path, mock_llm):
    # GIVEN: A project with a class
    proj_dir = tmp_path / "project"
    proj_dir.mkdir()
    test_file = proj_dir / "app.py"
    content = "class User:\n    def __init__(self):\n        pass\n"
    test_file.write_text(content, encoding="utf-8")
    
    # Mock LLM to return a replacement for the class block
    # We simulate adding a method 'save'
    mock_llm.return_value = "class User:\n    def __init__(self):\n        pass\n    def save(self):\n        print('saved')\n"
    
    # WHEN: User requests adding a method to the class (partial update)
    # Let's assume the Architect identifies the class range as lines 1-3
    result = draft_code(
        path=str(test_file),
        instruction="Add a save method to User class",
        start_line=1,
        end_line=3,
        model="gemini"
    )
    
    # THEN: The class is updated without losing other parts
    assert "Updated lines 1-3" in result
    assert "def save(self):" in test_file.read_text()
    assert "def __init__(self):" in test_file.read_text()

def test_system_flow_auto_find_and_fix(tmp_path, mock_llm):
    # GIVEN: A multi-file project
    proj_dir = tmp_path / "my_app"
    proj_dir.mkdir()
    
    file1 = proj_dir / "utils.py"
    file1.write_text("def helper():\n    return 'help'\n", encoding="utf-8")
    
    file2 = proj_dir / "main.py"
    file2.write_text("import utils\nprint(utils.helper())\n", encoding="utf-8")
    
    # Mock LLM Sequence:
    # 1. Targeting: returns utils.py helper
    # 2. Drafting: returns new implementation
    mock_llm.side_effect = [
        '{"target_file": "utils.py", "target_entity": "helper"}',
        "def helper():\n    return 'helped'\n"
    ]
    
    # Mock prompts and repo map
    with patch("mcp_ai_worker.server.generate_repo_map", return_value="utils.py: helper\nmain.py: main"), \
         patch("mcp_ai_worker.server.load_prompt_template", return_value="{requirement}\n{repo_map}"):
        
        # WHEN: User asks to change the helper function
        result = find_and_draft_edit(
            requirement="Change helper return value to 'helped'",
            target_dir=str(proj_dir)
        )
    
    # THEN: The correct file is updated
    assert "Updated lines" in result or "Successfully wrote" in result
    assert file1.read_text() == "def helper():\n    return 'helped'\n"
    assert file2.read_text() == "import utils\nprint(utils.helper())\n"
