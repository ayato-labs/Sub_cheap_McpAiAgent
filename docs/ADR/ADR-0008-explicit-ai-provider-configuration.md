# ADR-0008: Explicit AI Provider Configuration via Environment Variables

- **Date**: 2026-06-17
- **Status**: Accepted
- **Deciders**: ayato-labs, Gemini Agent

## Context
Previously, the `Sub-cheap-McpAiAgent` determined whether to route an LLM request to the Gemini API or a local Ollama instance using a simple heuristic based on the model's name (e.g., if "gemini" was in the name, it routed to Gemini; otherwise, it assumed Ollama).

However, this heuristic-only approach presented a significant usability issue: users could not easily configure the system to run *exclusively* on Ollama if they provided model names that didn't strictly align with the heuristic, or if they wanted explicit control without relying on naming conventions. The lack of an explicit toggle meant the system might attempt to initialize the Gemini client (requiring `GOOGLE_API_KEY`) even when the user intended a fully local, offline execution.

## Decision
We introduced explicit configuration variables in the `.env` file to dictate the AI Provider routing:
1. `AI_PROVIDER`: A global setting (`gemini` or `ollama`) that explicitly routes all sub-LLM calls to the chosen backend.
2. Task-specific overrides (`TRANSLATION_PROVIDER`, `DRAFTING_PROVIDER`): Optional settings that allow users to override the global `AI_PROVIDER` for specific pipeline stages (e.g., using Ollama for translation and Gemini for complex drafting).

The heuristic detection remains in place *only* as a fallback if the explicit provider is not defined.

## Consequences
### Positive
- **Offline/Local First Support**: Users can now set `AI_PROVIDER=ollama` and run the entire MCP server locally without triggering Gemini client initialization errors, fully satisfying the requirement for pure-Ollama execution.
- **Flexibility**: The introduction of task-specific overrides allows advanced users to mix and match cloud and local models to optimize for cost, privacy, and performance.
- **Clarity**: The `.env.example` explicitly communicates how routing works, removing the "magic" from the previous heuristic-only approach.

### Negative / Risks
- **Configuration Overhead**: Adds slightly more configuration options to the `.env` file, though this is mitigated by keeping the task-specific overrides commented out by default.

## References
- Issue: None
- PR: None
