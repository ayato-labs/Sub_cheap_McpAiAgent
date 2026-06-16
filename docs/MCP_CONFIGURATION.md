# MCP Configuration Guide

This guide explains how to configure and use the **Sub-cheap-McpAiAgent** server with your AI client (e.g., Claude Desktop).

## 1. Prerequisites
- **Python 3.10+**
- **uv**: The recommended package manager for this project.
- **Google AI Studio API Key**: For Gemini access. [Get one here](https://aistudio.google.com/app/apikey).
- **Ollama (Optional)**: For local LLM support.

## 2. Environment Variables (.env)
Create a `.env` file in the project root with the following settings. The system uses a multi-phase LLM approach to optimize tokens:

```env
# Google AI Studio
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Ollama (Local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2:9b

# Role-based Model Selection ('gemini' or 'ollama')
TRANSLATION_MODEL=gemini  # Used for translating Japanese to English and chunking
DRAFTING_MODEL=gemini     # Used for context compression and actual code drafting
```

## 3. Claude Desktop Configuration
To use this server with Claude Desktop, add it to your `claude_desktop_config.json`:

### Windows
Typically located at: `%APPDATA%\Claude\claude_desktop_config.json`

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
*Note: Replace `C:/path/to/Sub_cheap_McpAiAgent` with the absolute path to your repository.*

## 4. Usage
Once configured, restart Claude Desktop. You will see the `sub-cheap-mcp` tools available (e.g., `draft_code`).

### Example Tool Call
The Main AI (Claude) will call the tool as follows:
- **path**: `src/main.py`
- **instruction**: `Add a docstring to the add_numbers function.`
- **start_line**: 10
- **end_line**: 15

## 5. Traceability & Logs
- **mcp_server.log**: Contains structured JSON logs of the last 2 runs.
- **error.log**: Dedicated log file for error isolation.
- **run_id**: Each request is tagged with a unique UUID for easy tracking.
