
def register_calculator_tools(mcp):
    """Register calculator tools with the MCP server."""

    @mcp.tool()
    def add(a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    @mcp.tool()
    def subtract(a: float, b: float) -> float:
        """Subtract the second number from the first."""
        return a - b

    @mcp.tool()
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    @mcp.tool()
    def divide(a: float, b: float) -> float:
        """Divide the first number by the second."""
        if b == 0:
            raise ValueError("Division by zero is not allowed.")

        return a / b
