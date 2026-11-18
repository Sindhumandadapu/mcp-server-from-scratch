
import pytest


@pytest.mark.asyncio
async def test_database_tools_registered(mcp_client):

    async with mcp_client() as client:
        result = await client.list_tools()

        names = {tool.name for tool in result.tools}

        expected = {
            "list_tables",
            "get_table_schema",
            "query_database",
        }

        assert expected.issubset(names)


@pytest.mark.asyncio
async def test_list_database_tables(mcp_client):

    async with mcp_client() as client:
        result = await client.call_tool(
            "list_tables",
            {}
        )

        assert not result.is_error
        assert result.content


@pytest.mark.asyncio
async def test_employee_table_schema(mcp_client):

    async with mcp_client() as client:
        result = await client.call_tool(
            "get_table_schema",
            {
                "table_name": "employees"
            }
        )

        assert not result.is_error
        assert result.content


@pytest.mark.asyncio
async def test_read_only_select_query(mcp_client):

    async with mcp_client() as client:
        result = await client.call_tool(
            "query_database",
            {
                "sql": "SELECT * FROM employees LIMIT 5"
            }
        )

        assert not result.is_error
        assert result.content


@pytest.mark.asyncio
async def test_delete_query_rejected(mcp_client):

    async with mcp_client() as client:
        result = await client.call_tool(
            "query_database",
            {
                "sql": "DELETE FROM employees"
            }
        )

        assert result.is_error


@pytest.mark.asyncio
async def test_invalid_table_rejected(mcp_client):

    async with mcp_client() as client:
        result = await client.call_tool(
            "get_table_schema",
            {
                "table_name": "non_existing_table"
            }
        )

        assert result.is_error


@pytest.mark.asyncio
async def test_invalid_table_identifier_rejected(mcp_client):

    async with mcp_client() as client:
        result = await client.call_tool(
            "get_table_schema",
            {
                "table_name": "employees; DROP TABLE employees"
            }
        )

        assert result.is_error


@pytest.mark.asyncio
async def test_update_inside_with_query_rejected(mcp_client):

    async with mcp_client() as client:
        result = await client.call_tool(
            "query_database",
            {
                "sql": """
                    WITH change AS (
                        SELECT 1
                    )
                    DELETE FROM employees
                """
            }
        )

        assert result.is_error
