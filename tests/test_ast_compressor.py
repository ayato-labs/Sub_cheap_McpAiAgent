import ast
from mcp_ai_worker.utils import ast_compress_python

def test_ast_compress_python():
    code = """
def hello_world(name: str) -> str:
    print("Hello")
    return f"Hello, {name}"

class MyClass:
    def my_method(self, value: int):
        self.value = value
        return value * 2
"""
    compressed = ast_compress_python(code)
    
    assert "def hello_world(name: str) -> str:" in compressed
    assert "..." in compressed
    assert "class MyClass:" in compressed
    assert "def my_method(self, value: int):" in compressed
    assert 'print("Hello")' not in compressed
    assert 'return f"Hello, {name}"' not in compressed
    assert 'self.value = value' not in compressed
    
    # Verify syntax
    try:
        ast.parse(compressed)
    except SyntaxError:
        assert False, "Compressed code is invalid Python"

if __name__ == "__main__":
    test_ast_compress_python()
    print("Test passed!")
