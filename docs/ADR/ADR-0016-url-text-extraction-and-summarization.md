# ADR 0016: URL Text Extraction and Summarization

## Status
Accepted

## Context
The main AI (Architect) often needs to process information from external URLs. Reading raw HTML or very large web pages directly consumes massive amounts of tokens, increasing costs and potentially exceeding context limits. There is a need for a tool that can extract the core text content from a URL and provide a concise, factual summary using a sub-LLM, thereby reducing token overhead for the Architect.

## Decision
We implement a local, self-contained extraction and summarization pipeline within `MCP-AIWorker`.

### Implementation Details
1.  **Fetching & Cleaning**: 
    - Use `httpx` for static HTML fetching.
    - Use `BeautifulSoup4` to narrow down the content to the most relevant containers (`<article>`, `<main>`, or `<body>`).
    - Decompose noisy elements (`<script>`, `<style>`, `<nav>`, `<footer>`, etc.) to strip irrelevant data.
    - Convert the cleaned HTML subtree to Markdown using `markdownify`.
2.  **Security**:
    - Strictly restrict input URLs to the `https://` scheme.
    - Implement SSRF protection by blocking requests to loopback and private IP ranges.
3.  **Summarization**:
    - Delegate the summarization task to a sub-LLM with a strict, ground-truth anchored system prompt.
    - Fix the `temperature` to `0.0` to ensure deterministic and factual summaries, preventing hallucinations.
4.  **SPA Handling**:
    - To maintain a lightweight infrastructure, headless browsers are rejected. 
    - Implement a "fail-fast" mechanism: if the extracted content is too short (e.g., < 100 characters), the tool reports a potential SPA/empty content error, signaling the Architect to fall back to manual input.

## Consequences
### Positive
- **Token Efficiency**: Drastically reduces the token cost for the main AI.
- **Data Sovereignty**: Processing is done locally within the MCP server without external proxy APIs.
- **Reliability**: Deterministic summarization ensures high factual accuracy.

### Negative/Trade-offs
- **No SPA Support**: Pages that require JavaScript rendering (Single Page Applications) cannot be processed.
- **Static Fetching**: Limited to static HTML content.
