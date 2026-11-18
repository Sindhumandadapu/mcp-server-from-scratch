
from server.core import create_server


if __name__ == "__main__":
    mcp = create_server()
    mcp.run(transport="stdio")
