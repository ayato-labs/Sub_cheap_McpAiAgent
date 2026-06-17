# Sub-cheap-McpAiAgent

[![CI](https://github.com/ayato-labs/Sub_cheap_McpAiAgent/actions/workflows/ci.yml/badge.svg)](https://github.com/ayato-labs/Sub_cheap_McpAiAgent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[日本語版はこちら (Japanese Version)](README_JA.md)

**Sub-cheap-McpAiAgent** is a Model Context Protocol (MCP) server designed to drastically reduce the token consumption and costs of high-performance "Frontier" models (like Claude 3.5 Sonnet). 

It delegates token-heavy tasks—such as drafting code or translating context—to inexpensive sub-LLMs (Google Gemini, local Ollama, or Genspark), while keeping the Main AI in control as the **Architect**.

## 🌟 Key Features

- **Architect-Part-timer Division of Labor**: Specifically designed for a workflow where the Main AI (Architect) designs and the Sub-LLM (Part-timer) drafts code.
- **Streamable HTTP (SSE) Transport**: Supports parallel execution by multiple AI agents, breaking the 1:1 limitation of Stdio.
- **Multi-Backend Support**: Seamlessly switch between **Google Gemini**, **local Ollama**, or **Genspark (Search AI)** via `.env`.
- **Draft-First Pipeline**:
    1. **Translation**: Auto-converts JA instructions to English.
    2. **Compression**: Dynamically shrinks large code contexts.
    3. **Drafting**: Generates "Draft-quality" (叩き台) code snippets for the Architect to refine.
- **Enterprise-Ready**: Stateless HTTP mode for robustness, hostname-based endpoints, and 100 char line limit code style.

## 🏗️ Architecture Philosophy

The core philosophy is **"The Architect and the Part-timer"**:
- **The Main AI (YOU) is the Architect**: You do the heavy thinking and design.
- **The Sub-LLM is the Part-timer**: It does the heavy lifting of typing code.
- **"Draft" Quality is Okay**: We explicitly accept that the Sub-LLM output is a "draft" (叩き台). The Architect (Main AI) is responsible for final QA and integration. This prevents expensive internal QA loops and keeps the system simple and fast.

## 🚀 Quick Start (Windows)

1.  **Setup Environment**:
    Run `setup.bat` to install dependencies (uses `uv`).

2.  **Configure `.env`**:
    Create `.env` based on `.env.example`.
    ```env
    AI_PROVIDER=gemini
    GOOGLE_API_KEY=your_key
    ```

3.  **Run the Server**:
    Execute `run.bat`. The server will start on `http://127.0.0.1:10300/mcp`. **Keep this window open.**

4.  **Register with Claude Desktop**:
    Add the URL to your `claude_desktop_config.json`:
    ```json
    {
      "mcpServers": {
        "sub-cheap-mcp": {
          "url": "http://127.0.0.1:10300/mcp"
        }
      }
    }
    ```

## 📄 Decision Records (ADR)

- [ADR-0008: Explicit AI Provider Config](docs/ADR/ADR-0008-explicit-ai-provider-configuration.md)
- [ADR-0009: Genspark CLI Integration](docs/ADR/ADR-0009-adoption-of-genspark-ai-provider.md)
- [ADR-0010: Architect-Part-timer Model](docs/ADR/ADR-0010-architect-parttimer-delegation-model.md)
- [ADR-0011: Switch to Streamable HTTP](docs/ADR/ADR-0011-switch-to-http-transport.md)
- [View all ADRs](docs/ADR/)


## 🗺️ Roadmap & Future Vision

**Current Phase (MVP for Individual Developers):**
The project currently relies on explicit `.env` settings for model routing. This is an intentional design choice for a "Bring Your Own Key" (BYOK) environment and local executions. We do not use automated "Task Routers" that might silently upgrade to expensive models or load local models that exceed your hardware's VRAM. This ensures you maintain 100% control over your API costs and local resources.

**Future SaaS Phase:**
When evolving into a managed SaaS platform, we plan to implement:
- **Intelligent Task Router**: Automatically assessing prompt complexity to route between Tier 1 (Flash) and Tier 2 (Pro/Opus) models to maximize margin and performance.
- **Automated QA Retry Loops**: Re-rolling failed generation attempts based on static analysis (e.g., Semgrep) before returning the payload to the Main AI.

## 🏢 Commercial & Business Use Ready

This project is built entirely on permissive open-source licenses (MIT, Apache 2.0, BSD), ensuring it can be safely integrated into commercial, enterprise, or proprietary workflows without copyleft (GPL) contamination risks.

**Dependency License Map:**
*   **[Ollama](https://github.com/ollama/ollama/blob/main/LICENSE)** (Local LLM Server): `MIT License`
*   **[FastMCP](https://github.com/jlowin/fastmcp/blob/main/LICENSE)** (MCP Framework): `MIT License`
*   **[google-genai](https://github.com/googleapis/python-genai/blob/main/LICENSE)** (Gemini SDK): `Apache License 2.0`
*   **[requests](https://github.com/psf/requests/blob/main/LICENSE)** (HTTP Client): `Apache License 2.0`
*   **[loguru](https://github.com/Delgan/loguru/blob/master/LICENSE)** (Logging): `MIT License`
*   **[python-dotenv](https://github.com/theskumar/python-dotenv/blob/main/LICENSE)** (Env Config): `BSD-3-Clause`

> **⚠️ Important Disclaimer: AI Model Weights, API Terms, and License Verification**
> 1. **AI Models & APIs**: While this MCP server and its software dependencies are commercially viable, **the licenses and terms of service (TOS) for the actual AI models (weights) and external APIs you connect to are governed by their respective providers.** For example, if you load models via Ollama (e.g., Llama 3, Gemma) or use Google AI Studio APIs, you must ensure your use case complies with Meta's, Google's, or the respective creator's commercial licensing terms.
> 2. **Final Verification**: While we have made every effort to list the correct licenses for our dependencies, **the ultimate responsibility for verifying and complying with all software and model licenses for your specific business use case rests entirely with you (the user).**

## ⚖️ License

MIT License. See [LICENSE](LICENSE) for details.
