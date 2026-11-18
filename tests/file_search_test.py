
import pytest

import tools.file_search as file_search


@pytest.fixture
def temporary_resources(tmp_path, monkeypatch):

    resources = tmp_path / "resources"
    resources.mkdir()

    sample_file = resources / "sample.txt"

    sample_file.write_text(
        "SmartTools MCP Server provides calculator and database tools.",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        file_search,
        "RESOURCE_ROOT",
        resources
    )

    return resources


@pytest.mark.asyncio
async def test_search_files(
    mcp_client,
    temporary_resources
):

    async with mcp_client() as client:
        result = await client.call_tool(
            "search_files",
            {
                "query": "calculator"
            }
        )

        assert not result.is_error
        assert result.content


@pytest.mark.asyncio
async def test_search_no_match(
    mcp_client,
    temporary_resources
):

    async with mcp_client() as client:
        result = await client.call_tool(
            "search_files",
            {
                "query": "something_not_present"
            }
        )

        assert not result.is_error
        assert result.content


@pytest.mark.asyncio
async def test_read_file(
    mcp_client,
    temporary_resources
):

    async with mcp_client() as client:
        result = await client.call_tool(
            "read_file",
            {
                "file_path": "sample.txt"
            }
        )

        assert not result.is_error
        assert result.content


@pytest.mark.asyncio
async def test_path_traversal_rejected(
    mcp_client,
    temporary_resources
):

    async with mcp_client() as client:
        result = await client.call_tool(
            "read_file",
            {
                "file_path": "../../.env"
            }
        )

        assert not result.is_error
        assert result.content

        # The tool returns a JSON error response for invalid paths.
        assert "error" in result.content[0].text.lower()


@pytest.mark.asyncio
async def test_unsupported_file_extension(
    mcp_client,
    temporary_resources
):

    (temporary_resources / "malicious.exe").write_text(
        "test content",
        encoding="utf-8"
    )

    async with mcp_client() as client:
        result = await client.call_tool(
            "read_file",
            {
                "file_path": "malicious.exe"
            }
        )

        assert not result.is_error
        assert result.content

        assert "error" in result.content[0].text.lower()
