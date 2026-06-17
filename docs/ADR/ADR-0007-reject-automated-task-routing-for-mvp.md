# ADR-0007: Rejection of Automated Task Routing for MVP

- **Date**: 2026-06-15
- **Status**: Accepted
- **Deciders**: ayato-labs (User), Gemini CLI (Agent)

## Context
During an external expert review, it was strongly suggested that the project's "biggest weakness" is the lack of an automated "Task Router"—a mechanism that dynamically analyzes prompt complexity and automatically routes the task to either a cheap model (e.g., Gemini Flash) or an expensive one (e.g., Claude Opus) without user intervention.

## Decision
**Reject** the implementation of an automated Task Router for the current Minimum Viable Product (MVP) phase. The system will continue to rely on manual, hardcoded model selection via `.env` variables (`TRANSLATION_MODEL`, `DRAFTING_MODEL`). 
Automated task routing is reclassified as a "Future Roadmap" feature, specifically reserved for a potential SaaS-based business model.

## Rationale
1. **BYOK (Bring Your Own Key) Reality**: The current target audience consists of personal developers using their own API keys. Automatically upgrading a task to an expensive model without explicit user consent risks unexpected billing (bill shock). Users must maintain absolute control over their spend.
2. **Local Hardware Constraints**: For local execution (Ollama), a router might decide to load a heavier model (e.g., Qwen 32B) for a complex task. However, the system cannot reliably predict if the user's local VRAM can handle it, potentially causing system crashes. Model selection must remain tied to the user's understanding of their own hardware.
3. **Product-Market Fit Boundaries**: An automated Task Router is a feature designed to maximize profit margins for an infrastructure provider (SaaS) by balancing cost and performance behind the scenes. It provides little value—and significant risk—to a developer running an open-source tool locally.

## Consequences
### Positive
- Prevents unexpected API charges for users.
- Keeps the MCP server extremely lightweight and predictable.
- Avoids over-engineering during the MVP phase.

### Negative / Risks
- The user is fully responsible for matching the right model to the right task in their `.env` file. If they set a model that is too weak for their needs, they may experience lower quality outputs.

## References
- External Expert Review Feedback
- README.md (Roadmap section)
