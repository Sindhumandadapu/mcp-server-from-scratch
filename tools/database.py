
import json
import re
import sqlite3

from database.setup import DATABASE_PATH


def get_connection(read_only=True):
    """Create a SQLite database connection."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError("Database has not been initialized.")

    if read_only:
        connection = sqlite3.connect(
            f"{DATABASE_PATH.as_uri()}?mode=ro",
            uri=True
        )
    else:
        connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row
    return connection


def register_database_tools(mcp):
    """Register database tools with the MCP server."""

    @mcp.tool()
    def list_tables() -> str:
        """List all available user tables in the database."""

        with get_connection() as connection:
            rows = connection.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """).fetchall()

        tables = [row["name"] for row in rows]

        return json.dumps({
            "tables": tables,
            "count": len(tables)
        }, indent=2)

    @mcp.tool()
    def get_table_schema(table_name: str) -> str:
        """Get column names and data types for a database table."""

        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
            raise ValueError("Invalid table name.")

        with get_connection() as connection:

            exists = connection.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = ?
            """, (table_name,)).fetchone()

            if not exists:
                raise ValueError(f"Table '{table_name}' does not exist.")

            # The identifier is safe after the strict validation above.
            quoted_name = '"' + table_name + '"'

            columns = connection.execute(
                f"PRAGMA table_info({quoted_name})"
            ).fetchall()

        schema = [
            {
                "column": column["name"],
                "type": column["type"],
                "primary_key": bool(column["pk"]),
                "not_null": bool(column["notnull"])
            }
            for column in columns
        ]

        return json.dumps({
            "table": table_name,
            "columns": schema
        }, indent=2)

    @mcp.tool()
    def query_database(
        sql: str,
        max_rows: int = 50
    ) -> str:
        """
        Execute a read-only SELECT query against the database.

        Write operations and multiple SQL statements are not allowed.
        Results are limited to a maximum of 100 rows.
        """

        sql = sql.strip()

        if not sql:
            raise ValueError("SQL query cannot be empty.")

        if len(sql) > 5000:
            raise ValueError("SQL query is too long.")

        if not 1 <= max_rows <= 100:
            raise ValueError("max_rows must be between 1 and 100.")

        first_keyword = sql.split(None, 1)[0].upper()

        if first_keyword not in {"SELECT", "WITH"}:
            raise ValueError(
                "Only SELECT and read-only WITH queries are allowed."
            )

        denied_actions = {
            sqlite3.SQLITE_INSERT,
            sqlite3.SQLITE_UPDATE,
            sqlite3.SQLITE_DELETE,
            sqlite3.SQLITE_CREATE_INDEX,
            sqlite3.SQLITE_CREATE_TABLE,
            sqlite3.SQLITE_CREATE_TRIGGER,
            sqlite3.SQLITE_CREATE_VIEW,
            sqlite3.SQLITE_DROP_INDEX,
            sqlite3.SQLITE_DROP_TABLE,
            sqlite3.SQLITE_DROP_TRIGGER,
            sqlite3.SQLITE_DROP_VIEW,
            sqlite3.SQLITE_ALTER_TABLE,
            sqlite3.SQLITE_ATTACH,
            sqlite3.SQLITE_DETACH,
            sqlite3.SQLITE_PRAGMA,
            sqlite3.SQLITE_TRANSACTION,
            sqlite3.SQLITE_SAVEPOINT,
        }

        def authorize(action, arg1, arg2, database, trigger):
            if action in denied_actions:
                return sqlite3.SQLITE_DENY

            if (
                action == sqlite3.SQLITE_FUNCTION
                and (arg2 or "").lower() == "load_extension"
            ):
                return sqlite3.SQLITE_DENY

            return sqlite3.SQLITE_OK

        with get_connection() as connection:

            connection.set_authorizer(authorize)

            cursor = connection.execute(sql)

            columns = [
                description[0]
                for description in cursor.description or []
            ]

            rows = cursor.fetchmany(max_rows + 1)

            truncated = len(rows) > max_rows
            rows = rows[:max_rows]

            results = [
                dict(row)
                for row in rows
            ]

        return json.dumps({
            "columns": columns,
            "row_count": len(results),
            "truncated": truncated,
            "results": results
        }, indent=2, default=str)
