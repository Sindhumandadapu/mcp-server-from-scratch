
from mcp.server import MCPServer

from tools.calculator import register_calculator_tools
from tools.file_search import register_file_search_tools
from tools.database import register_database_tools
from tools.api_tools import register_api_tools

from database.setup import initialize_database


def create_server() -> MCPServer:
    """Create and configure the SmartTools MCP server."""

    # Initialize the application database.
    initialize_database()

    # Create MCP server.
    mcp = MCPServer(
        "SmartTools MCP Server",
        instructions=(
            "A multi-tool MCP server providing calculator, file search, "
            "database, weather, currency conversion and controlled "
            "external API capabilities."
        ),
    )

    # Register existing MCP tool groups.
    register_calculator_tools(mcp)
    register_file_search_tools(mcp)
    register_database_tools(mcp)
    register_api_tools(mcp)

    return mcp
