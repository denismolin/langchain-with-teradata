# LangChain with Teradata

An educational repository exploring two LLM application patterns — **Retrieval-Augmented Generation (RAG)** and **SQL assistance** — using LangChain as the orchestration layer and Teradata Vantage as the backend.

The notebooks are designed to be followed step by step. Each one builds on the previous, introducing one new concept or component at a time.

---

## Part 1 — RAG Pipelines (`notebooks-RAG/`)

This series starts from the simplest possible retrieval setup and progresses towards a fully Teradata-backed RAG pipeline.

| Notebook | What it introduces |
|---|---|
| 00 | RAG basics with in-memory BM25 keyword retrieval |
| 01 | Gradio chatbot interface on top of BM25 |
| 02 | Local semantic embeddings with `sentence-transformers` |
| 03 | API embeddings (OpenAI) + FAISS vector store + embedding space visualization |
| 04 | Swap FAISS for ChromaDB (persistent vector store) |
| 05 | Swap OpenAI embeddings for AWS Bedrock (Titan) |
| 06 | Move everything into **Teradata Vantage** — vector store + Bedrock embeddings |

Notebooks 03–05 include an **embedding inspection section** that goes beyond just running RAG: they visualize the vector space with PCA (Matplotlib and Plotly), compare cosine similarities between queries, and show how retrieved documents are ranked. This makes them useful for building intuition about how semantic search actually works.

All notebooks use a small set of toy documents on purpose — the focus is on understanding the mechanics, not on building a real document corpus.

---

## Part 2 — SQL Assistant (`notebook-SQL-assistant/`)

This part is inspired by the [LangChain SQL assistant with skills example](https://docs.langchain.com/oss/python/langchain/multi-agent/skills-sql-assistant#view-complete-runnable-script), adapted to use Teradata as the database backend. It shows how to build a LangGraph agent that can query a Teradata database in natural language. Three ideas are demonstrated together:

- **MCP (Model Context Protocol)** — the agent connects to the [Teradata MCP Server Community Edition](https://github.com/Teradata/teradata-mcp-server) to discover the schema and run queries, rather than having any hardcoded SQL knowledge.
- **Skills** — reusable Markdown files that inject domain rules and safe query patterns into the agent at runtime. The agent decides which skill to load based on the user's request.
- **On-premise LLMs** — the notebooks show how to plug in a locally-hosted model instead of relying on a cloud API. The demo uses `mistralai/Ministral-3-14B-Instruct-2512` served with [vLLM](https://github.com/vllm-project/vllm) on two NVIDIA RTX 4070 Ti Super (16 GB VRAM each), exposed via an OpenAI-compatible endpoint.

### Notebooks

- **`00 - Test MCP server`** — a minimal connectivity check to verify that the MCP server is reachable and exposes the expected tools.
- **`01 - Langchain SQL Assistant - Skill`** — the full agent demo: connects to MCP, loads skills dynamically, and answers questions about the database.

### How Skills Work

Skills live under `notebook-SQL-assistant/skills/<skill_name>/SKILL.md`. Each file has a short YAML frontmatter (`name`, `description`) and a Markdown body with rules and example SQL patterns.

At startup, `SkillMiddleware` reads all skill files and injects their names and descriptions into the agent's system prompt. When a user question matches a skill's domain, the agent calls the `load_skill` tool to pull in the full instructions before writing a query.

Three example skills are included:

| Skill | Domain |
|---|---|
| `transaction_analysis` | Aggregated queries on transactions (by customer, category, merchant, time) |
| `customer_spending_segmentation` | Customer behavior, spend tiers, category preferences |
| `transaction_anomaly_detection` | Heuristic detection of unusual spending patterns |

All three skills enforce the same safety rules: never return raw transaction rows, always aggregate results. This illustrates how skills can encode data governance constraints directly into the agent's behaviour — a pattern that is particularly relevant for Teradata SQL where controlling what gets returned matters.

---

## Getting Started

### Dependencies

```bash
pip install langchain langchain-community langchain-openai langchain-teradata \
            langchain-aws langchain-mcp-adapters langgraph \
            gradio faiss-cpu chromadb rank-bm25 sentence-transformers \
            python-dotenv pyyaml boto3 plotly scikit-learn
```

### Environment variables

Create a `.env` file at the root:

```env
# For RAG notebooks 00–04
OPENAI_API_KEY=...

# For RAG notebooks 05–06 and the SQL assistant (on-prem LLM)
AWS_ACCESS_KEY=...
AWS_SECRET_KEY=...
AWS_BEARER_TOKEN_BEDROCK=...

# For RAG notebook 06 and the SQL assistant
VANTAGE_HOST=...
VANTAGE_USER=...
VANTAGE_PASSWORD=...

# For the SQL assistant with a local LLM
LOCAL_TOKEN=...
```

Only the variables relevant to the notebook you are running are required.

---

## Adding Your Own Skill

Create a folder under `notebook-SQL-assistant/skills/` and add a `SKILL.md`:

```markdown
---
name: your_skill_name
description: One sentence describing when this skill should be used.
---

# Your Skill

Rules, table schema, and safe query patterns go here.
```

The agent will pick it up automatically at next startup.

---

## References

- [Teradata Package for LangChain — Function Reference](https://docs.teradata.com/r/Enterprise/Teradata-Package-for-LangChain-Function-Reference)
- [Teradata MCP Server Community Edition](https://github.com/Teradata/teradata-mcp-server)
- [LangChain SQL Assistant with Skills example](https://docs.langchain.com/oss/python/langchain/multi-agent/skills-sql-assistant#view-complete-runnable-script)
- [LangChain documentation](https://python.langchain.com/)
- [LangGraph documentation](https://langchain-ai.github.io/langgraph/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
