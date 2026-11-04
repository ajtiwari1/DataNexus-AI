import pytest

from app.security.sql_guard import validate_readonly_query


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM customers",
        "WITH recent AS (SELECT * FROM orders) SELECT * FROM recent",
    ],
)
def test_valid_queries(query):
    valid, _ = validate_readonly_query(query)
    assert valid is True


@pytest.mark.parametrize(
    "query",
    [
        "DROP TABLE customers",
        "DELETE FROM customers",
        "UPDATE customers SET name = 'test'",
        "SELECT * FROM customers; DROP TABLE customers",
        "INSERT INTO customers VALUES (1, 'test')",
        "SELECT * FROM customers;",
        "SELECT * FROM customers -- comment",
    ],
)
def test_invalid_queries(query):
    valid, _ = validate_readonly_query(query)
    assert valid is False