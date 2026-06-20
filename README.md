# MCP-AIWorker

[![CI](https://github.com/ayato-labs/MCP-AIWorker/actions/workflows/ci.yml/badge.svg)](https://github.com/ayato-labs/MCP-AIWorker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/ayato-labs/MCP-AIWorker/pulls)

[日本語版はこちら (Japanese Version)](README_JA.md)

**MCP-AIWorker** is a Model Context Protocol (MCP) server built to slash API token consumption and development costs of high-performance "Frontier" models (like Claude 5 / Fable 5).

By delegating token-heavy, mechanical tasks—such as drafting repetitive code, JA-to-EN context translations, and summarizing massive log outputs—to inexpensive sub-LLMs (Google Gemini Flash, local Ollama, or Genspark Search AI), the Main AI remains focused on what it does best: acting as the high-level **System Architect**.

---

## 💸 Why MCP-AIWorker?

As AI agents perform file-wide analysis and compile-run-debug loops, they read and write large files and logs, quickly exhausting your context window and API budget. 

By splitting the workload into the **Architect-Worker Paradigm**, you get:
*   **Up to 90% Cost Reduction**: Offloads structural coding and translation tasks to free/low-cost tiers (such as Gemini Flash or local Ollama). *Note: The 90% reduction is a theoretical maximum achieved when leveraging prompt caching or local LLMs; single-turn workflows with duplicate full-file reads typically see around 30%-40% reduction.*
*   **Faster Iteration**: Reduces network payloads and speeds up the core planning loop.
*   **No Infinite Loops**: Explicitly rejects complex, token-wasting internal QA loops inside the sub-LLM. The Architect AI inspects the draft and corrects integrations directly, keeping it fast and predictable.

---

## 🏗️ The Architect-Worker Paradigm

```
                   +------------------------+
                   |    Main AI Agent       |
                   |      (Architect)       |  <-- High-level Reasoning & Design
                   +-----------+------------+
                               |
                       MCP Tool Calls
                               v
                   +-----------+------------+
                   |      MCP-AIWorker      |
                   +-----------+------------+
                               |
               +---------------+---------------+
               |               |               |
               v               v               v
        +------------+   +------------+  +------------+
        |   Gemini   |   |   Ollama   |  |  Genspark  |  <-- Cheap / Local LLMs
        |   (API)    |   |  (Local)   |  | (Search)   |      for Heavy Typing & Logs
        +------------+   +------------+  +------------+
```

---

## 🌟 Key Features

*   **Architect-Worker Separation**: Outsource tedious code drafting while keeping you (or the main AI) in absolute control.
*   **Streamable HTTP (SSE) Transport**: FastMCP-powered SSE transport allowing concurrent connections and parallel execution from multiple sub-agents, bypassing legacy stdio 1:1 constraints.
*   **Robust Code Extraction Engine**: Multi-stage parsing utilizing XML tag markers, recovery checks (rescuing truncated or unclosed model outputs), and fallback markdown parser.
*   **Translation Pipeline**: Seamless automatic translation of non-English prompts and reference contexts into clean English, enhancing sub-LLM comprehension.
*   **Context Compressor**: Intelligently compresses large reference contexts (classes, interfaces) to fit model limits while retaining structural logic.
*   **Log Summarization**: Runs terminal commands and summarizes hundreds of lines of raw test/build logs into small, actionable summaries for the main AI.

---

## 🚀 Quick Start (Windows)

### 1. Setup Environment
Run the setup batch file to install dependencies inside a local virtual environment managed by `uv`:
```bash
setup.bat
```

### 2. Configure `.env`
Create a `.env` file from the provided example:
```env
AI_PROVIDER=gemini
GOOGLE_API_KEY=your-api-key-here
```

### 3. Start the Server
Run the startup script:
```bash
run.bat
```
The server will boot on `http://127.0.0.1:10300/mcp`.

### 4. Connect to Claude Desktop
Add the server endpoint to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "mcp-ai-worker": {
      "url": "http://127.0.0.1:10300/mcp"
    }
  }
}
```

---

## 🛠️ MCP Tools Exposed

### `draft_code`
Delegates localized code drafting in a file to an inexpensive sub-LLM.
*   **path** (string): Absolute path to the file.
*   **instruction** (string): Code changes or feature requirements.
*   **start_line / end_line** (optional integer): Line range to replace.
*   **reference_context** (optional string): Surrounding class or utility code for the model to reference.

### `find_and_draft_edit`
Runs directory-wide targeting. It scans the repository using `grep-ast` to pinpoint classes or functions, maps them, and writes the draft modifications.

### `execute_command`
Executes terminal commands (e.g. testing, linting) and delegates the lengthy stdout/stderr output to a sub-LLM for a concise summary. Saves valuable context window tokens.

---

## 📄 Architecture Decision Records (ADRs)

We document our design trade-offs:
*   [ADR-0010: Architect-Worker Delegation Model](docs/ADR/ADR-0010-architect-parttimer-delegation-model.md)
*   [ADR-0011: Streamable HTTP Transport](docs/ADR/ADR-0011-switch-to-http-transport.md)
*   [ADR-0012: Output Control & XML Rescuing](docs/ADR/ADR-0012-robust-output-control-and-prompt-externalization.md)
*   [ADR-0013: Log Summarization Engine](docs/ADR/ADR-0013-terminal-execution-log-summarization.md)

---

## ⚖️ License

MIT License. See [LICENSE](LICENSE) for details.
