# ADR-0010: Embrace "Draft Quality" and Architect-Part-timer Division of Labor

- **Date**: 2026-06-17
- **Status**: Accepted
- **Deciders**: ayato-labs, Gemini Agent

## Context
When designing an MCP tool that leverages inexpensive or local sub-LLMs (like Gemini Flash or Ollama) to assist a high-performance main AI (like Claude 3.5 Sonnet or GPT-4o), there is a temptation to build complex QA loops, retry mechanisms, and validations into the sub-LLM pipeline to ensure it returns "perfect, working code."

However, this approach inflates the complexity of the MCP server, increases latency, and often fails because cheap LLMs struggle with complex self-correction. 

## Decision
We explicitly adopt the **"Architect vs. Part-timer (Programmer)" delegation model**:
1. **The Main AI acts as the Architect/System Architect**: It performs all the high-level reasoning, design, context gathering, and final quality assurance.
2. **The Sub-LLM acts as a Part-time Worker/Programmer**: It takes explicit instructions and context, and performs the heavy "typing" or localized modifications.

Crucially, **we explicitly accept that the sub-LLM is only expected to produce a "draft" (叩き台) rather than perfectly working code**. Errors, missing imports, or slight logical oversights are *acceptable* because the result is merely an outsourced draft that the Architect (Main AI) or a human will review and refine.

## Consequences
### Positive
- **Simplicity & Speed**: The MCP server remains a pure, stateless execution engine without the need for complex, token-heavy internal reflection or QA loops.
- **Cost Efficiency**: We maximize the utility of cheap models by treating them as rapid draft generators.
- **Clear Boundaries**: Future agents using this tool understand that they should not blindly trust the output. They must read the returned draft and fix any integration issues themselves, maintaining system integrity.

### Negative / Risks
- **Rework (手戻り)**: The Main AI may occasionally need to spend a turn fixing a silly mistake made by the sub-LLM. However, we deem this cost acceptable and far cheaper than having the Main AI write the entire code block from scratch.

## References
- `docs/概念的要件定義書.md` (Conceptual Requirements Document) - Updated to reflect this core philosophy.
