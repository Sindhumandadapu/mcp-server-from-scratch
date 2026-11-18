
from contextlib import asynccontextmanager

import pytest

from mcp import Client
from server.core import create_server


@pytest.fixture
def mcp_client():
    """Provide an MCP client with a safe async lifecycle."""

    @asynccontextmanager
    async def client_context():
        server = create_server()

        async with Client(server) as client:
            yield client

    return client_context
