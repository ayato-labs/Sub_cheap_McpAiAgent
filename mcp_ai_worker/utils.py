import os
import re
import subprocess
from pathlib import Path
from typing import Optional
from loguru import logger
from mcp_ai_worker.client import SubLLMClient

def load_prompt_template(filename: str) -> str:
    """Loads a prompt template from the prompts directory."""
    try:
        prompt_path = Path("prompts") / filename
        return prompt_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to load prompt template {filename}: {e}")
        return ""

def clean_json_output(text: str) -> str:
    """Extracts JSON block from LLM response."""
    json_pattern = re.compile(r"```json\s*\n?(.*?)\n?```", re.DOTALL)
    match = json_pattern.search(text)
    if match:
        return match.group(1).strip()
    # Fallback: try to find first { and last }
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1:
        return text[start_idx : end_idx + 1]
    return text.strip()

import ast
import os
import subprocess

def generate_repo_map(directory: str) -> str:
    """Generates a signature map of the entire directory using grep-ast"""
    try:
        result = subprocess.run(
            ["grep-ast", ".", "--encoding", "utf-8"],
            cwd=directory,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        logger.error(f"Failed to generate repo map with grep-ast, using AST fallback: {e}")
        repo_map = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, directory)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                                repo_map.append(f"{rel_path}:{node.lineno}: {node.name}")
                    except Exception:
                        continue
        return "\n".join(repo_map)
def extract_target_block(filepath: str, target_name: str) -> tuple[str, int, int, list[str]]:
    """
    Extracts blocks matching the function/class name from the specified file.
    Simple regex implementation for Python.
    Return value: (code snippet string, start line, end line, full_content)
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            full_content = f.readlines()

        content_str = "".join(full_content)
        # Match 'def function_name(' or 'class ClassName('
        pattern = rf"^(?:def|class)\s+({re.escape(target_name)})(?:\s*\(|:)"
        match = re.search(pattern, content_str, re.MULTILINE)

        if not match:
            return "", 0, 0, full_content

        start_line = content_str.count("\n", 0, match.start()) + 1
        
        # Heuristic: find end of block by looking for next definition at same indentation or EOF
        # This is simplified. In a real scenario, we'd use tree-sitter.
        start_pos = match.start()
        # Find the indentation of the matched line
        current_line_start = content_str.rfind("\n", 0, start_pos) + 1
        
        # We just take a reasonable chunk or use a simple regex to find next top-level def/class
        # For now, let's find the next line that starts with 'def ' or 'class ' at 0 indentation
        # or the end of the file.
        remaining_text = content_str[match.end():]
        next_block = re.search(r"^\s*(?:def|class)\s+", remaining_text, re.MULTILINE)
        
        if next_block:
            end_pos = next_block.start()
        else:
            end_pos = len(content_str)

        # More accurate line count for end_line
        snippet = content_str[match.start() : (match.end() + next_block.start()) if next_block else len(content_str)]
        
        # Re-calculate end_line based on snippet
        end_line = start_line + snippet.count("\n")
        
        return snippet, start_line, end_line, full_content
    except Exception as e:
        logger.exception(f"Failed to extract target block: {e}")
        return "", 0, 0, []
def translate_to_english(text: str) -> str:
    """Chunks text and translates it to English."""
    if not text or text.isascii():
        return text

    provider = os.getenv("TRANSLATION_PROVIDER")
    model_id = os.getenv("TRANSLATION_MODEL", "models/gemma-4-31b-it")
    chunk_size = 3000
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    translated_chunks = []

    for i, chunk in enumerate(chunks):
        prompt = (
            "Translate the following text to English. If it is already in English, return it exactly as is.\n"
            "Maintain technical terms and code structure. Output ONLY the translated text.\n\n"
            f"TEXT:\n{chunk}"
        )
        logger.info(f"Translating chunk {i + 1}/{len(chunks)}...")
        translated_chunks.append(
            SubLLMClient.call_any(model_id, prompt, role_name="translation", provider=provider)
        )

    return "\n".join(translated_chunks)

def compress_context(instruction: str, context: str) -> str:
    """Compresses the reference context to fit into the model's window."""
    provider = os.getenv("DRAFTING_PROVIDER")
    model_id = os.getenv("DRAFTING_MODEL", "models/gemma-4-31b-it")
    prompt = (
        "You are a context compression expert. Your goal is to shrink the following reference code\n"
        "to be as concise as possible while retaining all structural information (function signatures,\n"
        "class definitions, key variable types) and logic necessary for the instruction below.\n"
        "Remove unnecessary comments, long strings, or unrelated logic. Output ONLY the compressed code.\n\n"
        f"### Instruction:\n{instruction}\n\n"
        f"### Reference Code:\n{context}"
    )
    logger.info("Compressing long context...")
    return SubLLMClient.call_any(model_id, prompt, role_name="compression", provider=provider)

def clean_code_output(text: str) -> str:
    """
    A robust code parsing function.
    It performs multi-stage extraction of XML tags, removal of Markdown, and cleansing of noise (explanatory text).
    """
    if not text:
        return ""

    cleaned = text.strip()

    # 1. Extraction by XML tag (<draft_output>)
    xml_pattern = re.compile(r"<draft_output>\s*\n?(.*?)\n?\s*</draft_output>", re.DOTALL | re.IGNORECASE)
    match = xml_pattern.search(cleaned)
    if match:
        cleaned = match.group(1).strip()
    else:
        # Fallback: Recovery when tags are not closed due to token restrictions, etc.
        partial_xml_pattern = re.compile(r"<draft_output>\s*\n?(.*)", re.DOTALL | re.IGNORECASE)
        partial_match = partial_xml_pattern.search(cleaned)
        if partial_match:
            logger.warning("Unclosed <draft_output> tag detected. Rescuing partial content.")
            cleaned = partial_match.group(1).strip()

    # 2. Removing Markdown Code Blocks
    md_pattern = re.compile(r"```(?:\w+)?\n?(.*?)\n?```", re.DOTALL)
    md_match = md_pattern.search(cleaned)
    if md_match:
        cleaned = md_match.group(1).strip()
    else:
        # Fallback: simple stripping if not properly wrapped
        cleaned = cleaned.replace("```python", "").replace("```", "").strip()

    # 3. Final noise cleansing (only if the result is short and contains common phrases)
    noise_phrases = ["Here is the updated code", "I have modified", "The following code"]
    for phrase in noise_phrases:
        if phrase in cleaned and len(cleaned.splitlines()) < 5:
            cleaned = cleaned.replace(phrase, "")

    return cleaned.strip()

def _load_target_snippet(
    file_path: Path, start_line: Optional[int], end_line: Optional[int]
) -> tuple[str, list[str]]:
    """Reads the target file and extracts the snippet to be modified."""
    if not file_path.exists():
        return "", []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            full_content = f.readlines()

        if start_line is not None and end_line is not None:
            s_idx = max(0, start_line - 1)
            e_idx = min(len(full_content), end_line)
            return "".join(full_content[s_idx:e_idx]), full_content
        return "".join(full_content), full_content
    except Exception:
        logger.exception(f"Failed to read existing file: {file_path}")
        raise

def _write_back_changes(
    file_path: Path,
    generated_code: str,
    start_line: Optional[int],
    end_line: Optional[int],
    full_content: list[str],
    model_id: str,
) -> str:
    """Writes the generated code back to the file, either fully or as a snippet."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if start_line is not None and end_line is not None and full_content:
        s_idx = max(0, start_line - 1)
        e_idx = min(len(full_content), end_line)
        new_lines = generated_code.splitlines(keepends=True)
        if generated_code and not generated_code.endswith("\n"):
            new_lines[-1] += "\n"
        updated_content = full_content[:s_idx] + new_lines + full_content[e_idx:]
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(updated_content)
        return f"✅ Updated lines {start_line}-{end_line} in '{file_path.name}' using {model_id}."
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(generated_code + ("\n" if not generated_code.endswith("\n") else ""))
        return f"✅ Successfully wrote to '{file_path.name}' using {model_id}."
