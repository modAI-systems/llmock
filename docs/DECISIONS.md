# Key Decisions

## 2026-02-06 - LLMock3 Design

**Strategy Pattern**: Add new response behaviors (fixed, template, proxy) without changing core code.

**YAML Config**: Change API keys/models without rebuilding.

**Separate Streaming Adapter**: Strategies generate content; adapter handles SSE protocol.

**OpenAI Spec as Source of Truth**: Validate against official OpenAPI spec for drop-in compatibility.

**No Persistence (MVP)**: Stateless, simple. Add logging/metrics later if needed.

**Language TBD**: Go, Python, Rust, or Node.js. Choose after architecture approved.

---

## 2026-02-06 - Project Foundation

**AI-First Development**: Use `AGENTS.md` + `docs/` structure for clearer task boundaries.
