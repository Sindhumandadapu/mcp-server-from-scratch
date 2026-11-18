
import pytest


@pytest.mark.asyncio
async def test_calculator_tools(mcp_client):

    async with mcp_client() as client:
        cases = [
            ("add", {"a": 12, "b": 8}, 20),
            ("subtract", {"a": 12, "b": 8}, 4),
            ("multiply", {"a": 12, "b": 8}, 96),
            ("divide", {"a": 12, "b": 3}, 4),
        ]

        for name, arguments, expected in cases:
            result = await client.call_tool(name, arguments)

            assert not result.is_error
            assert result.structured_content["result"] == expected


@pytest.mark.asyncio
async def test_division_by_zero(mcp_client):

    async with mcp_client() as client:
        result = await client.call_tool(
            "divide",
            {"a": 10, "b": 0}
        )

        assert result.is_error


@pytest.mark.asyncio
async def test_all_twelve_tools_registered(mcp_client):

    async with mcp_client() as client:
        result = await client.list_tools()

        names = {tool.name for tool in result.tools}

        expected = {
            "add",
            "subtract",
            "multiply",
            "divide",
            "search_files",
            "read_file",
            "list_tables",
            "get_table_schema",
            "query_database",
            "get_weather",
            "convert_currency",
            "make_api_request",
        }

        assert names == expected
