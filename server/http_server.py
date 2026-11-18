
from server.core import create_server


if __name__ == "__main__":
    mcp = create_server()

    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
    )
