import pytest

from mcp import Client


MCP_URL = "http://127.0.0.1:8000/mcp"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_mcp_connection():

    try:
        async with Client(MCP_URL) as client:

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

            # Calculator test
            result = await client.call_tool(
                "multiply",
                {"a": 10, "b": 5}
            )

            assert not result.is_error
            assert result.structured_content["result"] == 50.0

    except (ConnectionError, OSError):
        pytest.skip("MCP HTTP server is not running on port 8000.")