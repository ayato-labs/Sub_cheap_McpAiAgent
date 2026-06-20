import mcp_ai_worker.utils
from mcp_ai_worker.utils import clean_code_output



# Mocking the logger to capture warnings for the test
class MockLogger:
    def __init__(self):
        self.warnings = []

    def warning(self, msg):
        self.warnings.append(msg)


mock_logger = MockLogger()
mcp_ai_worker.utils.logger = mock_logger
# Test cases
test_cases = [
    {
        "name": "Perfect XML",
        "input": (
            "Here is the result:\n<draft_output>"
            "\ndef hello():\n    print('world')\n</draft_output>"
            "\nHope this helps!"
        ),
        "expected": "def hello():\n    print('world')",
    },
    {
        "name": "Partial XML (Truncated)",
        "input": "Some text\n<draft_output>\ndef hello():\n    print('world'",
        "expected": "def hello():\n    print('world'",
    },
    {
        "name": "Markdown Only",
        "input": "Sure, here is the code:\n```python\ndef hello():\n    print('world')\n```",
        "expected": "def hello():\n    print('world')",
    },
    {
        "name": "Mixed XML and Markdown",
        "input": "<draft_output>\n```python\ndef hello():\n    print('world')\n```\n</draft_output>",
        "expected": "def hello():\n    print('world')",
    },
    {
        "name": "Noise phrase alone",
        "input": "Here is the updated code\ndef hello():\n    print('world')",
        "expected": "def hello():\n    print('world')",
    },
    {"name": "Empty input", "input": "", "expected": ""},
]

for tc in test_cases:
    result = clean_code_output(tc["input"])
    if result == tc["expected"]:
        print(f"✅ {tc['name']} passed")
    else:
        print(f"❌ {tc['name']} failed")
        print(f"   Input: {tc['input']!r}")
        print(f"   Expected: {tc['expected']!r}")
        print(f"   Result: {result!r}")

if "Unclosed <draft_output> tag detected. Rescuing partial content." in mock_logger.warnings:
    print("✅ Partial XML warning verified")
else:
    print("❌ Partial XML warning NOT verified")
