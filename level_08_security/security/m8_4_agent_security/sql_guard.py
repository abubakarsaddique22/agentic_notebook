"""Treat model-generated SQL as untrusted (roadmap M8.4).

If an agent ever builds a SQL query, never run the raw string. Parse it with
sqlglot and allow it only if it is a single, read-only SELECT on an allow-listed
table, with no stacked statements and no dangerous keywords.

    pip install sqlglot
"""
from __future__ import annotations

ALLOWED_TABLES = {"orders", "products"}
BANNED = {"insert", "update", "delete", "drop", "alter", "create", "truncate",
          "grant", "revoke", "attach", "pragma", "exec", "execute"}


class UnsafeSQL(Exception):
    pass


def validate_select(sql: str, allowed_tables: set[str] = ALLOWED_TABLES) -> str:
    """Return the SQL if it is a safe single read-only SELECT, else raise."""
    try:
        # sqlglot: SQL ko sirf string ki tarah nahi, balke proper "parse" karta hai,
        #          yani query ko tukron (SELECT, table, WHERE) mein tor kar samajhta hai.
        #          Is se hum pakka check kar sakte hain ke yeh sach-much read-only SELECT hai.
        import sqlglot
        # exp: sqlglot ke "expression" types (jaise exp.Select = SELECT statement,
        #      exp.Table = table ka naam). Inse hum query ki qisam aur tables pehchante hain.
        from sqlglot import exp
    except ImportError as e:
        raise UnsafeSQL("sqlglot not installed. Run: pip install sqlglot") from e

    statements = [s for s in sqlglot.parse(sql, read="sqlite") if s]
    if len(statements) != 1:
        raise UnsafeSQL("Only a single statement is allowed (no stacked queries).")

    stmt = statements[0]
    if not isinstance(stmt, exp.Select):
        raise UnsafeSQL("Only SELECT statements are allowed.")

    lowered = sql.lower()
    for word in BANNED:
        if word in lowered:
            raise UnsafeSQL(f"Banned keyword in query: {word}")

    tables = {t.name.lower() for t in stmt.find_all(exp.Table)}
    bad = tables - allowed_tables
    if bad:
        raise UnsafeSQL(f"Query touches tables that are not allowed: {sorted(bad)}")

    return sql


if __name__ == "__main__":
    samples = [
        "SELECT status FROM orders WHERE order_id = 'ORD-1001'",
        "SELECT * FROM orders; DROP TABLE orders;",
        "DELETE FROM orders",
        "SELECT * FROM internal_secrets",
    ]
    for s in samples:
        try:
            validate_select(s)
            print(f"ALLOW | {s}")
        except UnsafeSQL as e:
            print(f"DENY  | {s}  ->  {e}")
