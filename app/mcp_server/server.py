import os
import re
from typing import Any

import psycopg
from psycopg.rows import dict_row
from mcp.server.fastmcp import FastMCP
from app.security.sql_guard import validate_readonly_query
from app.security.pii_guard import mask_pii

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8001"))
DATABASE_URL = os.getenv(
    "MCP_DATABASE_URL",
    "postgresql://datanexus_reader:local_reader_change_me@localhost:5432/datanexus",
)
MAX_ROWS_HARD_LIMIT = 200
STATEMENT_TIMEOUT_MS = 5000

mcp = FastMCP("DataNexus PostgreSQL MCP", host=MCP_HOST, port=MCP_PORT)


def _connect() -> psycopg.Connection[Any]:
    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=3,
        options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS}",
        row_factory=dict_row,
    )

def _validate_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", identifier):
        raise ValueError("Invalid table identifier")
    return identifier

@mcp.tool()
def list_tables() -> list[dict[str, str]]:
    """List base tables in the public schema."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        ).fetchall()
    return [{"table_name": row["table_name"]} for row in rows]

@mcp.tool()
def describe_table(table_name: str) -> list[dict[str, Any]]:
    """Return columns and types for a public-schema table."""
    safe_name = _validate_identifier(table_name)
    with _connect() as conn:
        exists = conn.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s AND table_type = 'BASE TABLE'
            """,
            (safe_name,),
        ).fetchone()
        if not exists:
            raise ValueError("Table not found in public schema")
        rows = conn.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (safe_name,),
        ).fetchall()
    return [dict(row) for row in rows]

@mcp.tool()
def run_readonly_query(query: str, max_rows: int = 100) -> dict[str, Any]:
    """
    Execute one read-only SELECT or WITH query. Results are capped.
    Do not use for writes, DDL, multiple statements, or transaction commands.
    """
    if not 1 <= max_rows <= MAX_ROWS_HARD_LIMIT:
        raise ValueError(f"max_rows must be between 1 and {MAX_ROWS_HARD_LIMIT}")
    cleaned = query.strip()
    if not cleaned:
        raise ValueError("Query must not be empty")
    if ";" in cleaned or "--" in cleaned or "/*" in cleaned or "*/" in cleaned:
        raise ValueError("Only one query without SQL comments is allowed")
    if not re.match(r"(?is)^(SELECT|WITH)\b", cleaned):
        raise ValueError("Only SELECT or WITH queries are allowed")
    is_valid, reason = validate_readonly_query(query)

    if not is_valid:
        return {
        "success": False,
        "error": reason,
        }

    with _connect() as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            cursor = conn.execute(cleaned)
            if cursor.description is None:
                raise ValueError("Query did not return rows")
            columns = [col.name for col in cursor.description]
            rows = cursor.fetchmany(max_rows + 1)
            truncated = len(rows) > max_rows
            rows = rows[:max_rows]
            output_rows = []
            for row in rows:
                converted = {}
                for key, value in row.items():
                    if value is None or isinstance(value, (str, int, float, bool)):
                        converted[key] = value
                    elif hasattr(value, "isoformat"):
                        converted[key] = value.isoformat()
                    else:
                        converted[key] = str(value)
                output_rows.append(converted)

    return {
        "columns": columns,
        "rows": output_rows,
        "row_count": len(output_rows),
        "truncated": truncated,
        "max_rows": max_rows,
    }

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
