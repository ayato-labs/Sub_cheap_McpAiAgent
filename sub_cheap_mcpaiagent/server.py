import os
import time
import uuid
import requests
import subprocess
import sys
import json
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP
from loguru import logger
from google import genai

# Load environment variables
load_dotenv(override=True)

# Initialize FastMCP
mcp = FastMCP("Sub-cheap-McpAiAgent")

# Configure logger
logger.remove()
logger.add("mcp_server.log", rotation="10 MB", retention=2, serialize=True, level="DEBUG")
logger.add("error.log", rotation="10 MB", retention=2, serialize=True, level="ERROR")


# Sub-LLM Clients
class SubLLMClient:
    @staticmethod
    def get_gemini_client():
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in .env")
        return genai.Client(api_key=api_key)

    @staticmethod
    def detect_backend(model_id: str, specific_provider: Optional[str] = None) -> str:
        """Determines the backend based on explicit configuration or fallback heuristic."""
        if specific_provider:
            return specific_provider.lower()

        global_provider = os.getenv("AI_PROVIDER", "").lower()
        if global_provider in ["gemini", "ollama", "genspark"]:
            return global_provider

        # Fallback heuristic if not explicitly set
        low_id = model_id.lower()
        if "gemini" in low_id:
            return "gemini"
        if "genspark" in low_id or low_id in ["search", "crawl"]:
            return "genspark"
        return "ollama"

    @staticmethod
    def call_any(
        model_id: str, prompt: str, role_name: str = "task", provider: Optional[str] = None
    ) -> str:
        """Call the appropriate backend based on configuration or model_id."""
        backend = SubLLMClient.detect_backend(model_id, provider)
        if backend == "gemini":
            return SubLLMClient.call_gemini(model_id, prompt, role_name)
        elif backend == "genspark":
            return SubLLMClient.call_genspark(model_id, prompt, role_name)
        else:
            return SubLLMClient.call_ollama(model_id, prompt, role_name)

    @staticmethod
    def call_gemini(model_name: str, prompt: str, role_name: str = "task") -> str:
        client = SubLLMClient.get_gemini_client()

        # Dynamic context check
        try:
            model_info = client.models.get(model=model_name)
            max_tokens = model_info.input_token_limit

            token_count_resp = client.models.count_tokens(model=model_name, contents=prompt)
            current_tokens = token_count_resp.total_tokens

            logger.info(
                f"Gemini [{role_name}] ({model_name}) Tokens: {current_tokens}/{max_tokens}"
            )

            if current_tokens > max_tokens:
                raise ValueError(
                    f"Prompt exceeds Gemini context limit: {current_tokens} > {max_tokens}"
                )
        except Exception as e:
            logger.warning(f"Could not verify Gemini context limit for {model_name}: {e}")

        logger.info(f"Calling Gemini ({model_name}) for {role_name}...")
        try:
            start_time = time.perf_counter()
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.1 if role_name != "drafting" else 0.2,
                ),
            )
            elapsed = time.perf_counter() - start_time
            logger.info(f"Gemini [{role_name}] completed in {elapsed:.2f}s")
            return response.text.strip()
        except Exception:
            logger.exception(f"Gemini [{role_name}] call failed")
            raise

    @staticmethod
    def call_ollama(model_name: str, prompt: str, role_name: str = "task") -> str:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Dynamic context check for Ollama
        try:
            show_resp = requests.post(f"{base_url}/api/show", json={"name": model_name}, timeout=5)
            if show_resp.status_code == 200:
                context_limit = 4096  # Conservative default
                estimated_tokens = len(prompt) // 4
                logger.info(
                    f"Ollama [{role_name}] ({model_name}) "
                    f"Est. Tokens: ~{estimated_tokens}/{context_limit}"
                )
                if estimated_tokens > context_limit:
                    logger.warning(
                        f"Prompt might exceed Ollama limit: "
                        f"~{estimated_tokens} > {context_limit}"
                    )
        except Exception as e:
            logger.warning(f"Could not verify Ollama context limit for {model_name}: {e}")

        logger.info(f"Calling Ollama ({model_name}) for {role_name}...")
        try:
            start_time = time.perf_counter()
            response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1 if role_name != "drafting" else 0.2},
                },
                timeout=90,
            )
            response.raise_for_status()
            elapsed = time.perf_counter() - start_time
            logger.info(f"Ollama [{role_name}] completed in {elapsed:.2f}s")
            return response.json().get("response", "").strip()
        except Exception:
            logger.exception(f"Ollama [{role_name}] call failed")
            raise

    @staticmethod
    def call_genspark(model_name: str, prompt: str, role_name: str = "task") -> str:
        """Call Genspark CLI (gsk) to get an answer."""
        gsk_cmd = (
            model_name
            if model_name in ["search", "crawl", "img", "video"]
            else os.getenv("GENSPARK_MODEL_TYPE", "search")
        )
        logger.info(f"Calling Genspark ({gsk_cmd}) for {role_name}...")

        command = ["gsk", gsk_cmd, prompt, "--output", "text"]

        try:
            start_time = time.perf_counter()
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            elapsed = time.perf_counter() - start_time
            logger.info(f"Genspark [{role_name}] completed in {elapsed:.2f}s")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.exception(f"Genspark [{role_name}] call failed: {e.stderr}")
            raise


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
    """Removes markdown code blocks and common preamble/postamble."""
    # Remove markdown blocks
    if "```" in text:
        # Extract content between first and last triple backticks
        import re

        match = re.search(r"```(?:\w+)?\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            text = match.group(1)
        else:
            # Fallback: just strip the marks if they exist at ends
            text = text.replace("```python", "").replace("```", "").strip()

    # Remove common AI phrases if they leaked
    noise_phrases = ["Here is the updated code", "I have modified", "The following code"]
    for phrase in noise_phrases:
        if (
            phrase in text and len(text.splitlines()) < 5
        ):  # Only if it's very short/likely a preamble
            text = text.replace(phrase, "")

    return text.strip()


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


@mcp.tool()
def draft_code(
    path: str,
    instruction: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    reference_context: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Delegates heavy-lifting code drafting to an inexpensive sub-LLM to save YOUR tokens.
    
    ### Role: Architect vs. Part-timer
    - YOU (the Main AI) are the **Architect**: Responsible for high-level design and final QA.
    - SUB-LLM is the **Part-timer**: Responsible for localized typing and drafting.
    
    ### Strategy
    1. Delegate tedious file modifications or first-draft generation to this tool.
    2. Provide clear instructions and necessary context (reference_context).
    3. **CRITICAL**: Expect a "draft" (叩き台). The result may have minor logical gaps.
    4. **CRITICAL**: YOU must review the output and fix any integration issues.
    
    The pipeline includes auto-translation (JA->EN) and context compression.
    """
    run_id = str(uuid.uuid4())
    start_total_time = time.perf_counter()

    with logger.contextualize(run_id=run_id):
        logger.info(f"Started draft_code pipeline for path: {path}")
        try:
            # --- PRE-FLIGHT ---
            if start_line is not None and end_line is not None and start_line > end_line:
                return "Error: start_line cannot be greater than end_line."

            # --- 1. TRANSLATION PHASE ---
            instruction = translate_to_english(instruction)
            if reference_context:
                reference_context = translate_to_english(reference_context)

            # --- 2. DATA LOADING ---
            file_path = Path(path)
            try:
                target_snippet, full_content = _load_target_snippet(
                    file_path, start_line, end_line
                )
            except Exception:
                return "Error reading file."

            # --- 3. COMPRESSION PHASE (Conditional) ---
            provider = os.getenv("DRAFTING_PROVIDER")
            drafting_model_id = model or os.getenv("DRAFTING_MODEL", "models/gemma-4-31b-it")
            backend = SubLLMClient.detect_backend(drafting_model_id, provider)

            system_prompt = (
                "You are a coding assistant providing a draft (叩き台) based on specific "
                "instructions.\nYour goal is to perform the heavy lifting of writing code "
                "so the Architect can refine it.\n"
                "RULES:\n"
                "- Output ONLY the code. No explanations, no markdown blocks.\n"
                "- Maintain existing indentation and style.\n"
                "- Provide the FULL replacement for the given snippet.\n"
                "- If unsure, provide the most likely draft; the Architect will handle "
                "final validation.\n"
            )

            def build_draft_prompt(instr, snippet, context):
                p = f"{system_prompt}\n### Instruction:\n{instr}\n\n"
                if snippet:
                    p += f"### Current Code Snippet:\n{snippet}\n\n"
                if context:
                    p += f"### Reference Context:\n{context}\n\n"
                return p

            final_prompt = build_draft_prompt(instruction, target_snippet, reference_context)

            # Compression check for Gemini
            if backend == "gemini":
                try:
                    client = SubLLMClient.get_gemini_client()
                    limit = client.models.get(model=drafting_model_id).input_token_limit
                    count = client.models.count_tokens(
                        model=drafting_model_id, contents=final_prompt
                    ).total_tokens

                    if count > (limit * 0.9) and reference_context:
                        reference_context = compress_context(instruction, reference_context)
                        final_prompt = build_draft_prompt(
                            instruction, target_snippet, reference_context
                        )
                except Exception as e:
                    logger.warning(f"Compression check failed: {e}")

            # --- 4. GENERATION PHASE ---
            try:
                generated_code = SubLLMClient.call_any(
                    drafting_model_id, final_prompt, role_name="drafting", provider=provider
                )
                generated_code = clean_code_output(generated_code)
            except Exception as e:
                logger.exception("Final generation failed")
                return f"Drafting failed: {e}"

            # --- 5. WRITE BACK ---
            try:
                msg = _write_back_changes(
                    file_path,
                    generated_code,
                    start_line,
                    end_line,
                    full_content,
                    drafting_model_id,
                )
                total_elapsed = time.perf_counter() - start_total_time
                logger.info(f"{msg} (Total pipeline time: {total_elapsed:.2f}s)")
                return msg
            except Exception:
                logger.exception("Failed to write file")
                return "Error writing file."

        except Exception as e:
            logger.exception("Unexpected fatal error in pipeline")
            return f"Fatal error: {e}"

def main():
    # We exclusively use Streamable HTTP for parallel support.
    # Hidden fallback: python -m sub_cheap_mcpaiagent.server stdio (not recommended)
    transport = "http"
    if len(sys.argv) > 1:
        transport = sys.argv[1]

    port = 10300
    # Force IPv4 localhost to prevent IPv6/mDNS connection refused errors on Windows
    bind_host = "127.0.0.1"

    try:
        if transport == "stdio":
            logger.info("Starting MCP Server with transport: stdio")
            mcp.run(transport="stdio")
        else:
            logger.info(f"Starting MCP Server on {bind_host}:{port} with transport: streamable-http")
            print("\n" + "=" * 60)
            print("MCP SERVER RUNNING (STREAMABLE HTTP)")
            print(f"URL: http://{bind_host}:{port}/mcp")
            print("-" * 60)
            print("Claude Desktop Configuration Example:")
            config_example = {
                "mcpServers": {
                    "sub-cheap-mcp": {
                        "url": f"http://{bind_host}:{port}/mcp"
                    }
                }
            }
            print(json.dumps(config_example, indent=2))
            print("=" * 60 + "\n")
            mcp.run(transport="streamable-http", port=port, host=bind_host, stateless_http=True)
    except Exception:
        logger.exception("MCP Server crashed")
        if transport == "stdio":
            pass
        else:
            input("Press Enter to exit...")

if __name__ == "__main__":
    main()
