"""HTTP transport implementation for MCP server using SSE."""
import logging
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.responses import Response


logger = logging.getLogger(__name__)


async def run_http_server(server: Server, host: str = "0.0.0.0", port: int = 8000):
    """
    Run the MCP server with HTTP transport using Server-Sent Events (SSE).

    Args:
        server: The MCP Server instance to run
        host: Host address to bind to (default: 0.0.0.0)
        port: Port number to listen on (default: 8000)
    """
    logger.info(f"Starting MCP server with HTTP transport on {host}:{port}")

    try:
        from starlette.applications import Starlette
        from starlette.routing import Route
        import uvicorn

        # Create SSE transport
        sse = SseServerTransport("/messages")

        async def handle_sse(request):
            """Handle SSE connection requests."""
            async with sse.connect_sse(
                request.scope,
                request.receive,
                request.send
            ) as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options()
                )

        async def handle_messages(request):
            """Handle POST messages from the client."""
            await sse.handle_post_message(
                request.scope,
                request.receive,
                request.send
            )
            return Response(status_code=204)

        app = Starlette(
            routes=[
                Route("/mcp", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"])
            ]
        )

        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server_instance = uvicorn.Server(config)
        await server_instance.serve()

    except Exception as e:
        logger.error(f"Error running HTTP server: {e}", exc_info=True)
        raise
