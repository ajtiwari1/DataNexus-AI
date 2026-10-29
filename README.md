# DataNexus AI — Phase 1

Local starter for an enterprise data intelligence multi-agent platform.

## Services
- FastAPI: http://localhost:8000
- PostgreSQL: localhost:5432
- Qdrant: http://localhost:6333
- PostgreSQL MCP (Streamable HTTP): http://localhost:8001/mcp

## Start
```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:6333/healthz
```
API docs: http://localhost:8000/docs

Connect an MCP-compatible client to `http://localhost:8001/mcp`.
Tools: `list_tables`, `describe_table`, `run_readonly_query`.

## Tests
Requires Python 3.12:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Operations
```bash
docker compose logs -f api mcp postgres qdrant
docker compose down
docker compose down -v  # Deletes local database and Qdrant data
```

This is local-development scaffolding. Before exposing it beyond localhost, add MCP authentication, network restrictions, authorization, auditing, and managed secrets. Never commit `.env`.
