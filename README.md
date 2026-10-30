# DataNexus AI

### Enterprise Data Intelligence Multi-Agent Platform

DataNexus AI is a production-oriented multi-agent platform for answering enterprise questions using structured databases and unstructured documents. It combines SQL-based data access, retrieval-augmented generation (RAG), and supervisor-driven agent orchestration in a single API.

The project is being developed incrementally, with a focus on reliability, observability, evaluation, and extensible agent architecture.

## Key Features

- **Supervisor-based orchestration:** Uses LangGraph to classify incoming questions and route them to specialized agents.
- **SQL agent:** Answers natural-language questions using structured PostgreSQL data through a read-only database tool.
- **Document RAG agent:** Retrieves relevant document chunks from Qdrant and generates grounded answers using an LLM.
- **Hybrid question handling:** Supports questions that require both structured database results and document context, with parallel agent execution.
- **MCP integration:** Exposes database tools through a Model Context Protocol server.
- **Document ingestion API:** Accepts document text, splits it into chunks, generates embeddings, and indexes the chunks in Qdrant.
- **LLM provider configuration:** Supports an OpenAI-compatible API endpoint, configured for OpenRouter in the current setup.
- **Evaluation and observability:** Langfuse tracing and automated evaluation are being developed.

## Architecture

```mermaid
flowchart TD
    U[Client] --> API[FastAPI]
    API --> S[LangGraph Supervisor]

    S -->|SQL question| SQL[SQL Agent]
    S -->|Document question| RAG[RAG Agent]
    S -->|Both sources| SQL
    S -->|Both sources| RAG
    S -->|General question| G[General Response Node]

    SQL --> MCP[MCP Database Tools]
    MCP --> DB[(PostgreSQL)]

    RAG --> RET[Qdrant Retrieval]
    RET --> V[(Qdrant Vector Store)]
    RAG --> LLM[OPENAI LLM]

    SQL --> F[Final Response]
    RAG --> F
    G --> END[API Response]
    F --> END
```

### Request lifecycle

1. The client sends a question to the FastAPI `/chat` endpoint.
2. The supervisor classifies the question as `sql`, `documents`, `both`, or `general`.
3. The graph invokes the appropriate agent or agents.
4. The SQL agent accesses PostgreSQL through read-only MCP tools.
5. The RAG agent retrieves relevant chunks from Qdrant and generates an answer grounded in the retrieved context.
6. The workflow combines the available results and returns the answer with the selected intent and any reported errors.

## Technology Stack

| Component | Technology |
|---|---|
| API | FastAPI |
| Agent orchestration | LangGraph |
| LLM integration | LangChain OpenAI-compatible client |
| LLM provider | OpenRouter |
| Structured data | PostgreSQL |
| Database tool integration | Model Context Protocol (MCP) |
| Vector database | Qdrant |
| Embeddings | FastEmbed, BGE-small-en-v1.5 |
| Containers | Docker Compose |
| Observability | Langfuse — integration in progress |
| Evaluation | Custom regression runner — in progress |

## Project Structure

```text
datanexus-ai/
├── app/
│   ├── agents/
│   │   ├── rag_agent.py
│   │   └── ...
│   ├── core/
│   ├── graph/
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── workflow.py
│   ├── mcp_server/
│   │   └── server.py
│   ├── observability/
│   │   └── tracing.py
│   ├── rag/
│   │   └── store.py
│   └── main.py
├── sql/
├── tests/
├── evals/
│   ├── dataset.json
│   ├── run_eval.py
│   └── results/
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

The exact contents may evolve as implementation progresses.

## Prerequisites

- Docker Desktop with Docker Compose
- An OpenRouter API key and a supported model ID
- A Langfuse project and API keys if enabling tracing
- Internet access for pulling container images and downloading the embedding model on first use

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd datanexus-ai
```

### 2. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Configure the relevant values in `.env`:

```dotenv
POSTGRES_DB=datanexus
POSTGRES_USER=datanexus_admin
POSTGRES_PASSWORD=replace_with_a_strong_password

POSTGRES_READER_USER=datanexus_reader
POSTGRES_READER_PASSWORD=replace_with_a_reader_password

MCP_DATABASE_URL=postgresql://datanexus_reader:replace_with_a_reader_password@postgres:5432/datanexus

OPENAI_API_KEY=your_openrouter_api_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=your_exact_openrouter_model_id

QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=datanexus_documents

LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

Use the actual environment variables expected by your current code. Keep `.env` out of version control and never commit API keys or production credentials.

### 3. Start the services

```bash
docker compose up --build -d
```

Check the running containers:

```bash
docker compose ps
docker compose logs --tail=100 api
```

### 4. Open the API documentation

Visit:

- Swagger UI: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health
- Readiness endpoint: http://localhost:8000/ready

These URLs assume the default local port mappings are configured.

## API Usage

### Ask a question

**Endpoint:** `POST /chat`

Example request:

```json
{
  "question": "What factors does the Q3 product strategy recommend considering when prioritizing products?"
}
```

The response includes the question, detected intent, generated answer, and any reported errors.

### Ingest a document

**Endpoint:** `POST /documents/ingest`

Example request:

```json
{
  "title": "Product Strategy Q3",
  "text": "Product teams should consider customer satisfaction, sales performance, customer feedback, and product reliability when prioritizing products."
}
```

The service chunks the text, generates embeddings, and indexes the chunks in Qdrant.

### Query structured data

**Endpoint:** `POST /chat/sql`

Use this endpoint for natural-language questions about the seeded PostgreSQL data. The SQL agent should operate through a read-only database role.

## Multi-Agent Design

The current graph uses a shared state to pass information between nodes. Its main fields include:

- `question`: original user query
- `intent`: supervisor routing decision
- `sql_result`: structured-data result
- `document_result`: document-grounded result
- `final_answer`: response returned by the workflow
- `errors`: errors reported by individual agents

For questions requiring both SQL and document context, the graph can execute the two specialized agents in parallel. The state reducer for `errors` supports combining error lists from parallel branches.

## Security and Reliability

Current design goals include:

- Read-only database credentials for SQL access
- Restricted SQL execution through database tools
- Environment-based secret configuration
- Error reporting from individual agent branches
- Grounding document answers in retrieved context
- Automated regression tests for routing and answer behavior

A production deployment should additionally validate SQL restrictions, enforce query timeouts and resource limits, authenticate API clients, redact sensitive trace data, and test failure handling before exposing the service to untrusted users.

## Evaluation and Observability

The evaluation framework is being built to measure:

- Supervisor routing accuracy
- Retrieval precision and recall
- Answer faithfulness and correctness
- Execution success rate
- Regressions after prompt, model, or retrieval changes

Langfuse integration is intended to provide trace-level visibility into workflow execution, model calls, latency, and failures.

Keyword coverage is used only as an initial regression signal; it is not a substitute for semantic correctness or groundedness evaluation.

## Roadmap

- [x] FastAPI service and Docker-based development environment
- [x] PostgreSQL database and MCP tool integration
- [x] Supervisor-driven LangGraph workflow
- [x] SQL and document RAG agent paths
- [x] Qdrant document indexing and retrieval
- [x] Verified end-to-end Langfuse tracing
- [ ] Expanded RAG and answer-quality evaluation
- [ ] CI-based evaluation regression checks
- [ ] Authentication, rate limiting, and production hardening
- [ ] More advanced agent interoperability using A2A where independently deployed agents require it

## Development Philosophy

DataNexus AI is designed to evolve from a local multi-agent application into a scalable enterprise platform. Development prioritizes clear agent boundaries, explicit shared state, controlled tool access, measurable quality, and observable execution over simply adding more agents.

## License

Add a license before publishing the repository for reuse. Until then, usage and redistribution rights are governed by the repository owner's terms.
