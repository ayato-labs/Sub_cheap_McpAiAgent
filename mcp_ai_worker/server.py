import os
import time
import uuid
import subprocess
import sys
import json
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP
from mcp_ai_worker.metrics import track_metrics
from mcp_ai_worker.logger import logger, setup_logger

# Import sub-modules
from mcp_ai_worker.client import SubLLMClient
from mcp_ai_worker.utils import (
    load_prompt_template,
    clean_json_output,
    generate_repo_map,
    extract_target_block,
    translate_to_english,
    compress_context,
    clean_code_output,
    fetch_and_clean_markdown,
    _load_target_snippet,
    _write_back_changes,
    extract_test_artifacts,
    validate_syntax,
)

# Load environment variables
load_dotenv(override=True)

# Initialize FastMCP
mcp = FastMCP("MCP-AIWorker")


@mcp.tool()
@track_metrics
def find_and_draft_edit(requirement: str, target_dir: str) -> str:
    """
    [Architect vs. Part-timer]
    Automatically finds areas to edit throughout the entire directory and creates a draft of the code corrections.
    Saves the token cost of the main AI reading the entire file.
    """
    run_id = str(uuid.uuid4())
    start_total_time = time.perf_counter()

    with logger.contextualize(run_id=run_id):
        logger.info(f"Starting auto-find and draft pipeline for dir: {target_dir}")

        # 1. Repo Map Generation
        repo_map = generate_repo_map(target_dir)
        if not repo_map:
            return "Error: Could not generate repository map."

        # 2. Target Inference (Sub-LLM Task 1)
        finder_prompt = load_prompt_template("target_finder_prompt.txt").format(
            requirement=requirement, repo_map=repo_map
        )
        provider = os.getenv("DRAFTING_PROVIDER")
        model_id = os.getenv("DRAFTING_MODEL", "models/gemini-3.1-flash-lite")

        logger.info("Identifying target file and entity...")
        target_json_str = SubLLMClient.call_any(model_id, finder_prompt, role_name="targeting", provider=provider)

        try:
            target_info = json.loads(clean_json_output(target_json_str))
            filepath = os.path.join(target_dir, target_info["target_file"])
            entity_name = target_info["target_entity"]
        except Exception:
            return f"Failed to parse target JSON from Sub-LLM. Raw output: {target_json_str}"

        # 3. Pinpoint Extraction
        snippet, start_line, end_line, full_content = extract_target_block(filepath, entity_name)
        if not snippet:
            return f"Error: Could not find entity '{entity_name}' in file '{filepath}'."

        # 4. Draft Generation and Writeback (Sub-LLM Task 2)
        # Reusing draft_code internal logic via final_prompt
        system_prompt = load_prompt_template("draft_system_prompt.txt")
        if not system_prompt:
            system_prompt = "You are a coding assistant providing a draft (叩き台) based on specific instructions."

        final_prompt = f"{system_prompt}\n\nInstruction: {requirement}\n\nCurrent Block:\n{snippet}"

        logger.info("Generating code draft...")
        draft_code_raw = SubLLMClient.call_any(model_id, final_prompt, role_name="drafting", provider=provider)
        cleaned_code = clean_code_output(draft_code_raw)

        # Write back changes
        msg = _write_back_changes(Path(filepath), cleaned_code, start_line, end_line, full_content, model_id)

        total_elapsed = time.perf_counter() - start_total_time
        logger.info(f"{msg} (Total pipeline time: {total_elapsed:.2f}s)")
        return msg


def is_command_safe(command: str) -> bool:
    """
    Checks if the command contains potentially destructive patterns.
    """
    import re

    # Patterns for highly destructive Windows commands
    dangerous_patterns = [
        r"\bformat\b",
        r"\bdiskpart\b",
        r"\breg\s+delete\b",
        r"\brm\s+-rf\s+/\b",  # Check for root rm -rf /
        r"\bdel\s+/f\s+/s\s+/q\s+c:\\\b",  # Destructive del on C drive
        r"\brmdir\s+/s\s+/q\s+c:\\\b",  # Destructive rmdir on C drive
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False
    return True


@mcp.tool()
@track_metrics
def execute_command(command: str, working_dir: Optional[str] = None, timeout_seconds: int = 90) -> str:
    """
    [Architect vs. Part-timer]
    Executes terminal commands and summarizes the resulting lengthy raw logs
    (standard output/error output) using an inexpensive sub-LLM,
    and returns only the important points (error causes and execution results) to YOU (main AI).

    ### CRITICAL WARNING FOR YOU (THE ARCHITECT)
    - This tool is for saving YOU tokens. Use it for building, testing, and running Lint.
    - [WARNING] This tool has limited security restrictions to prevent accidental damage.
    - Never issue commands that could lead to directory deletion or system corruption. You are solely responsible.
    """
    logger.info(f"Executing command: {command} in {working_dir or 'current dir'}")

    if not is_command_safe(command):
        return f"Security Error: The command '{command}' is blocked due to safety restrictions."

    try:
        # Execute the command (set a timeout as the only defense)
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        # Merge logs
        raw_log = f"--- STDOUT ---\n{result.stdout}\n\n--- STDERR ---\n{result.stderr}"

        # If the log is very short, return it directly without using LLM (optimize cost and latency)
        if len(raw_log.strip()) < 300:
            return f"Command completed (Exit code: {result.returncode}).\nRaw Output:\n{raw_log}"

        # Delegate log summarization to sub-LLM
        prompt = (
            "You are a log analysis assistant. Read the following terminal execution log.\n"
            f"The command exited with code {result.returncode}.\n"
            "Summarize what happened, focusing strictly on errors, warnings, or key outcomes.\n"
            "Keep the summary concise (a few lines to a dozen lines)."
            "Do NOT repeat the entire raw log. Provide actionable insights for the Architect AI.\n\n"
            f"### RAW LOG:\n{raw_log}"
        )

        provider = os.getenv("DRAFTING_PROVIDER")
        model_id = os.getenv("DRAFTING_MODEL", "models/gemini-3.1-flash-lite")

        logger.info("Delegating log summarization to Sub-LLM...")
        summary = SubLLMClient.call_any(model_id, prompt, role_name="summarization", provider=provider)

        return f"Command executed (Exit code: {result.returncode}).\n\n[Sub-LLM Log Summary]\n{summary}"
    except subprocess.TimeoutExpired as e:
        # Handling timeout exceptions (collect logs up to a certain point and summarize them)
        stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        partial_log = f"--- PARTIAL STDOUT ---\n{stdout}\n\n--- PARTIAL STDERR ---\n{stderr}"
        logger.warning(f"Command timed out after {timeout_seconds}s.")

        prompt = (
            f"The command timed out after {timeout_seconds} seconds."
            "Read the following partial log and summarize any errors or signs of an infinite loop/hang.\n\n"
            f"### PARTIAL LOG:\n{partial_log}"
        )
        provider = os.getenv("DRAFTING_PROVIDER")
        model_id = os.getenv("DRAFTING_MODEL", "models/gemini-3.1-flash-lite")
        summary = SubLLMClient.call_any(model_id, prompt, role_name="summarization", provider=provider)

        return f"Warning: Command timed out.\n\n[Sub-LLM Partial Log Summary]\n{summary}"

    except Exception as e:
        logger.exception("Failed to execute command")
        return f"System Error: Failed to execute command: {e}"


@mcp.tool()
@track_metrics
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

    ### CRITICAL: Path Requirement
    - **path** MUST be an **absolute path**. Relative paths will cause errors.

    ### Role: Architect vs. Part-timer
    - YOU (the Main AI) are the **Architect**: Responsible for high-level design and final QA.
    - SUB-LLM is the **Part-timer**: Responsible for localized typing and drafting.

    ### Strategy
    - Delegate tedious file modifications or first-draft generation to this tool.
    - Provide clear instructions and necessary context (reference_context).
    - **CRITICAL**: Expect a "draft" (叩き台). The result may have minor logical gaps.
    - **CRITICAL**: YOU must review the output and fix any integration issues.

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

            file_path = Path(path)
            # Allow creation if instruction contains "create"
            if not file_path.exists() and "create" not in instruction.lower():
                return "Error reading file."

            # --- 1. TRANSLATION PHASE ---
            instruction = translate_to_english(instruction)
            if reference_context:
                reference_context = translate_to_english(reference_context)

            # --- 2. DATA LOADING ---
            try:
                target_snippet, full_content = _load_target_snippet(file_path, start_line, end_line)
            except Exception:
                return "Error reading file."

            # --- 3. COMPRESSION PHASE (Conditional) ---
            provider = os.getenv("DRAFTING_PROVIDER")
            drafting_model_id = model or os.getenv("DRAFTING_MODEL", "models/gemini-3.1-flash-lite")
            backend = SubLLMClient.detect_backend(drafting_model_id, provider)

            # Load external system prompt
            try:
                prompt_path = Path("prompts/draft_system_prompt.txt")
                system_prompt = prompt_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"Failed to load prompt file: {e}")
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
                    count = client.models.count_tokens(model=drafting_model_id, contents=final_prompt).total_tokens

                    if count > (limit * 0.9) and reference_context:
                        reference_context = compress_context(instruction, reference_context)
                        final_prompt = build_draft_prompt(instruction, target_snippet, reference_context)
                except Exception as e:
                    logger.warning(f"Compression check failed: {e}")

            # --- 4. GENERATION PHASE ---
            try:
                generated_code = SubLLMClient.call_any(
                    drafting_model_id, final_prompt, role_name="drafting", provider=provider
                )
                generated_code = clean_code_output(generated_code)

                # --- 4.5. SYNTAX CHECK (Fail-Fast) ---
                validation_error_json = validate_syntax(generated_code, file_path)
                if validation_error_json:
                    error_data = json.loads(validation_error_json)
                    logger.warning(f"Syntax validation failed: {error_data.get('message')}. Attempting repair...")
                    repair_prompt = (
                        f"{final_prompt}\n\n### CRITICAL ERROR:\n{error_data.get('message')}\n\n"
                        "REPAIR THE CODE. Output ONLY the fixed code."
                    )

                    generated_code = SubLLMClient.call_any(
                        drafting_model_id, repair_prompt, role_name="repair", provider=provider
                    )
                    generated_code = clean_code_output(generated_code)

                    second_validation_error_json = validate_syntax(generated_code, file_path)
                    if second_validation_error_json:
                        second_error_data = json.loads(second_validation_error_json)
                        logger.error(f"Syntax repair failed: {second_error_data.get('message')}")
                        return (
                            f"Drafting failed due to syntax error: {error_data.get('message')}\n"
                            f"Repair failed: {second_error_data.get('message')}"
                        )
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


@mcp.tool()
@track_metrics
def generate_unit_tests(
    source_file_path: str,
    output_dir_path: str,
    test_framework: str = "pytest",
    additional_instruction: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    [Architect vs. Part-timer]
    Reads a specified source file, generates isolated unit tests based on strict AAA patterns,
    and saves the test file to the designated absolute directory.

    ### CRITICAL INSTRUCTION FOR ARCHITECT (YOU):
    - You MUST use `additional_instruction` to specify WHICH edge cases or specific methods to focus on.
    - Do NOT ask for integration tests. The Sub-LLM will explicitly mock all external dependencies.
    """
    run_id = str(uuid.uuid4())

    with logger.contextualize(run_id=run_id):
        # 1. Validation
        source_path = Path(source_file_path)
        if not source_path.is_absolute() or not Path(output_dir_path).is_absolute():
            return "Error: source_file_path and output_dir_path must be absolute."
        if not source_path.exists():
            return f"Error: Source file not found: {source_file_path}"

        # 2. Setup
        test_file_name = f"test_{source_path.name}"
        test_file_path = Path(output_dir_path) / test_file_name

        # 3. Prompt Assembly
        source_code = source_path.read_text(encoding="utf-8")
        system_prompt = load_prompt_template("unit_test_system_prompt.txt")

        prompt = f"{system_prompt}\n\n### SOURCE CODE:\n{source_code}"
        if additional_instruction:
            instruction_en = translate_to_english(additional_instruction)
            prompt += f"\n\n### ADDITIONAL INSTRUCTIONS:\n{instruction_en}"

        # 4. Execution
        provider = os.getenv("DRAFTING_PROVIDER")
        model_id = model or os.getenv("DRAFTING_MODEL", "models/gemini-2.0-flash-001")

        logger.info(f"Generating unit tests for {source_path.name}...")

        raw_output = SubLLMClient.call_any(model_id, prompt, role_name="testing", provider=provider)

        test_plan, test_code = extract_test_artifacts(raw_output)

        # 5. File I/O
        try:
            test_file_path.parent.mkdir(parents=True, exist_ok=True)
            test_file_path.write_text(test_code, encoding="utf-8")
            logger.info(f"Test plan generated: {test_plan}")
            return f"✅ Successfully generated unit tests in {test_file_path}.\n\n[Test Plan]\n{test_plan}"
        except Exception as e:
            logger.exception("Failed to write test file")
            return f"Error writing test file: {e}"


@mcp.tool()
@track_metrics
def fetch_and_summarize_url(url: str, instruction: Optional[str] = None) -> str:
    """
    [Architect vs. Part-timer]
    Extracts text content from a specified HTTPS URL and generates an accurate summary using a sub-LLM.
    This saves massive token overhead for YOU (the main AI) by avoiding reading large, raw web pages.

    CRITICAL WARNING: Pages utilizing client-side dynamic rendering (SPAs) will fail to parse.
    If a failure occurs, fall back to manual copy-pasting from your host browser.
    """
    run_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    with logger.contextualize(run_id=run_id):
        logger.info(f"Starting URL fetch and summarize pipeline for: {url}")

        # 1. Content fetching and structural cleansing
        try:
            markdown_content = fetch_and_clean_markdown(url)
        except ValueError as e:
            return f"Tool Execution Failed: {str(e)}"
        except Exception as e:
            logger.exception("Unexpected error during HTML fetching")
            return f"System Error: Failed to fetch the URL content. {e}"

        # 2. Construct strict, ground-truth anchored prompt
        summary_prompt = (
            "You are a strict factual summarization assistant.\n"
            "Read the following web page content provided in Markdown format.\n"
            "Summarize the core points accurately based ONLY on the provided text.\n"
            "Do NOT invent facts, do NOT assume or extrapolate.\n"
            "Structure the output in clean Markdown format using bullet points.\n\n"
            "CRITICAL INSTRUCTION:\n"
            "If the provided web content lacks substantive body text, consists mainly of "
            "navigation menus/footer links, or states that JavaScript is required, "
            "DO NOT attempt to summarize it.\n"
            "Instead, you MUST return EXACTLY the following string and nothing else:\n"
            "[ERROR: INSUFFICIENT_CONTENT_SPA]\n\n"
        )

        if instruction:
            # Leverage the existing translation pipeline
            instruction_en = translate_to_english(instruction)
            summary_prompt += f"### Specific Focus Request from Architect:\n{instruction_en}\n\n"

        summary_prompt += f"### WEB CONTENT (.md):\n{markdown_content}"

        provider = os.getenv("DRAFTING_PROVIDER")
        model_id = os.getenv("DRAFTING_MODEL", "models/gemini-3.1-flash-lite")

        logger.info("Delegating summary to Sub-LLM with deterministic constraints (temperature=0.0)...")

        # 3. Invoke Sub-LLM with a deterministic zero-temperature setting
        try:
            summary = SubLLMClient.call_any(
                model_id,
                summary_prompt,
                role_name="summarization",
                provider=provider,
                temperature=0.0,  # Rigidly enforce factual constraint
            )

            if "[ERROR: INSUFFICIENT_CONTENT_SPA]" in summary:
                raise ValueError("SPA Detection by Sub-LLM: Content insufficient.")

        except Exception as e:
            if "SPA Detection" in str(e):
                fail_message = (
                    "Tool Execution Aborted: The target URL appears to be a Single Page Application (SPA) "
                    "or requires JavaScript rendering. Text extraction yielded insufficient content.\n\n"
                    "CRITICAL DIRECTIVE FOR ARCHITECT:\n"
                    "- DO NOT retry fetching this URL.\n"
                    "- DO NOT attempt to use other search tools for this specific URL.\n"
                    "- You MUST explicitly ask the user to manually copy and paste the required content "
                    "from their browser into the chat."
                )
                return fail_message

            logger.exception("Failed to summarize content")
            return f"Summarization failed: {e}"

        elapsed = time.perf_counter() - start_time
        logger.info(f"URL successfully summarized. (Time: {elapsed:.2f}s)")

        return f"URL Successfully Summarized.\n\n[Sub-LLM Web Summary]\n{summary}"


def main():
    setup_logger()
    # We exclusively use Streamable HTTP for parallel support.
    # Hidden fallback: python -m mcp_ai_worker.server stdio (not recommended)
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
            config_example = json.dumps(
                {"mcpServers": {"mcp-ai-worker": {"url": f"http://{bind_host}:{port}/mcp"}}},
                indent=2,
            )
            startup_msg = (
                "\n"
                + "=" * 60
                + "\nMCP SERVER RUNNING (STREAMABLE HTTP)"
                + f"\nURL: http://{bind_host}:{port}/mcp"
                + "\n"
                + "-" * 60
                + "\nClaude Desktop Configuration Example:"
                + f"\n{config_example}"
                + "\n"
                + "=" * 60
                + "\n"
            )
            print(startup_msg)
            logger.info(startup_msg)
            mcp.run(transport="streamable-http", port=port, host=bind_host, stateless_http=True)
    except Exception:
        logger.exception("MCP Server crashed")
        if transport == "stdio":
            pass
        else:
            input("Press Enter to exit...")


if __name__ == "__main__":
    main()
