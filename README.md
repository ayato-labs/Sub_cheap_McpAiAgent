# Sub-cheap-McpAiAgent

[![CI](https://github.com/ayato-labs/Sub_cheap_McpAiAgent/actions/workflows/ci.yml/badge.svg)](https://github.com/ayato-labs/Sub_cheap_McpAiAgent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[日本語版はこちら (Japanese Version)](README_JA.md)

**Sub-cheap-McpAiAgent** is a Model Context Protocol (MCP) server designed to drastically reduce the token consumption and costs of high-performance "Frontier" models (like Claude 3.5 Sonnet). 

It delegates the most token-heavy tasks—such as drafting initial code, rewriting large files, or translating technical context—to inexpensive sub-LLMs (Google Gemini Flash or local Ollama), while keeping the Main AI in control as the "Architect."

## 🌟 Key Features

- **Multi-Stage Optimization Pipeline**:
    1. **Translation**: Automatically converts non-English instructions/context into English (using chunked processing) to optimize token density and inference quality.
    2. **Compression**: Dynamically summarizes large code contexts if they exceed the sub-LLM's window, ensuring logic preservation while fitting into small models.
    3. **Drafting**: Generates pinpoint code diffs or full drafts based on optimized English context.
- **Dynamic Context Management**: Automatically detects model limits for Gemini API and Ollama models to prevent runtime overflows.
- **Multi-Backend Support**: Seamlessly switch between Google AI Studio (Gemini) and local host (Ollama) via simple model ID configuration.
- **High Traceability**: Structured JSON logging with `Loguru`, performance tracking, and unique `run_id` for every request.
- **Enterprise-Ready Error Isolation**: Dedicated `error.log` for troubleshooting and crash-prevention logic for stable CLI operations.

## 🏗️ Architecture Philosophy

The core philosophy is **"Intentional Context Disconnection"**:
- Information (code, requirements) is passed thoroughly from the Main AI to the Sub-agent.
- However, the Sub-agent only returns the **result**. 
- The internal reasoning process (the "how") of the sub-agent is discarded to keep the Main AI's context clean and focused on high-level orchestration.

## 🚀 Quick Start (Windows)

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/ayato-labs/Sub_cheap_McpAiAgent.git
    cd Sub_cheap_McpAiAgent
    ```

2.  **Setup Environment**:
    Run the automated setup script. This will create a virtual environment and install all dependencies using `uv`.
    ```cmd
    setup.bat
    ```

3.  **Configure `.env`**:
    Create a `.env` file based on `.env.example` and add your API keys.
    ```env
    GOOGLE_API_KEY=your_gemini_api_key
    TRANSLATION_MODEL=gemini-2.5-flash
    DRAFTING_MODEL=gemma2:9b
    ```

4.  **Register with Claude Desktop**:
    Add the following to your `claude_desktop_config.json`:
    ```json
    {
      "mcpServers": {
        "sub-cheap-mcp": {
          "command": "uv",
          "args": [
            "--directory",
            "C:/path/to/Sub_cheap_McpAiAgent",
            "run",
            "sub-cheap-mcp"
          ]
        }
      }
    }
    ```

5.  **Run**:
    ```cmd
    run.bat
    ```

## 🛠️ Configuration

Detailed configuration options for different models and behaviors can be found in [docs/MCP_CONFIGURATION.md](docs/MCP_CONFIGURATION.md).

## 📄 Decision Records (ADR)

Our architectural choices are documented to ensure transparency:
- [ADR-0001: Sub-LLM Selection Strategy](docs/ADR/ADR-0001-selection-of-sub-llm-and-edit-strategy.md)
- [ADR-0004: Adoption of Google AI Studio API](docs/ADR/ADR-0004-use-google-ai-studio-api.md)
- [ADR-0005: Rejection of Local MT Models for KISS](docs/ADR/ADR-0005-reject-dedicated-local-translation-models.md)

## ⚖️ License

MIT License. See [LICENSE](LICENSE) for details.
