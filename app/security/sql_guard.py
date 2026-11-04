import re


FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|"
    r"TRUNCATE|GRANT|REVOKE|COPY|CALL|EXECUTE)\b",
    re.IGNORECASE,
)


def validate_readonly_query(query: str) -> tuple[bool, str]:
    normalized = query.strip()

    if not normalized:
        return False, "Empty SQL query"

    # Allow only SELECT and WITH queries
    if not re.match(r"^(SELECT|WITH)\b", normalized, re.IGNORECASE):
        return False, "Only SELECT queries are allowed"

    if ";" in normalized:
        return False, "Semicolons are not allowed"

    if any(marker in normalized for marker in ("--", "/*", "*/")):
        return False, "SQL comments are not allowed"

    # Reject write or administrative operations
    if FORBIDDEN_SQL.search(normalized):
        return False, "Forbidden SQL operation detected"

    return True, "Query accepted"