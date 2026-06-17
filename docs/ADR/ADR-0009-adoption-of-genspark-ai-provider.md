# ADR-0009: Adoption of Genspark CLI (gsk) as an AI Provider

- **Date**: 2026-06-17
- **Status**: Accepted
- **Deciders**: ayato-labs, Gemini Agent

## Context
The system already supports Google Gemini (Cloud) and Ollama (Local). There is a need for a third option that combines search-based reasoning with cloud-like ease of use. Genspark, via its `gsk` CLI, provides a unique Perplexity-like experience by automatically performing web searches and fact-checking before generating a response.

Integrating Genspark allows the `Sub-cheap-McpAiAgent` to benefit from high-quality, research-backed information, especially useful for tasks involving latest technical trends or complex documentation that might not be in the base model's training data.

## Decision
We implemented a new backend provider, `genspark`, within the `SubLLMClient` class:
1. **Implementation**: Uses `subprocess.run` to call the `gsk` CLI directly.
2. **Configuration**: Added `AI_PROVIDER=genspark` support. Users can also specify `GENSPARK_MODEL_TYPE` (default: `search`) in the `.env` file.
3. **Output Handling**: Uses the `--output text` flag of `gsk` to ensure response parity with other LLM providers (plain text output).

## Consequences
### Positive
- **Latest Information**: Automatically leverages web search, making it superior for research-heavy tasks.
- **Unified Interface**: Follows the same `call_any` pattern as Gemini and Ollama, allowing for easy task-based model switching.
- **Local Integration**: Since it runs via CLI, it doesn't require complex API client libraries in Python, keeping the server code lean.

### Negative / Risks
- **Latency**: Genspark is significantly slower (seconds to tens of seconds) due to its RAG/search process.
- **Credit Cost**: Unlike Ollama, Genspark consumes account credits per request.
- **Dependency**: Requires the `@genspark/cli` npm package to be installed globally on the host machine.
- **Context Management**: CLI-based interaction lacks native chat history support, though this is partially mitigated by the system's focus on single-shot code drafting.

## References
- Genspark CLI: `npm install -g @genspark/cli`
- Research Sources: Provided by user (YouTube, Medium, RealPython, etc.)
