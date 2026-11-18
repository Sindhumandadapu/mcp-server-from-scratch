import pytest_asyncio

from mcp import Client
from server.core import create_server


@pytest_asyncio.fixture
async def mcp_client():
    """Create an isolated in-process MCP client for testing."""

    server = create_server()

    async with Client(server) as client:
        yield client