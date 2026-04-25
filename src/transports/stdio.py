"""stdio transport implementation for MCP server."""
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server


logger = logging.getLogger(__name__)


async def run_stdio_server(server: Server):
    """
    Run the MCP server with stdio transport.

    Args:
        server: The MCP Server instance to run
    """
    logger.info("Starting MCP server with stdio transport")
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Error running stdio server: {e}", exc_info=True)
        raise
