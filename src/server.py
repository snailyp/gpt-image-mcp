"""Main MCP server entry point."""

import argparse
import asyncio
import logging

# Import tool modules to register them with mcp instance
import src.tools.edit  # noqa: F401
import src.tools.info  # noqa: F401
from src.config import load_config
from src.tools.generate import mcp
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn


def setup_logging(
    level: str = "INFO",
    format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
):
    """
    Configure logging for the server.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_str: Log message format string
    """
    logging.basicConfig(level=getattr(logging, level.upper()), format=format_str)


async def main():
    """Main server entry point."""
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="GPT Image MCP Server")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument("--port", type=int, help="Port for HTTP transport")
    parser.add_argument("--host", type=str, help="Host for HTTP transport")
    args = parser.parse_args()

    # Build CLI args dict for config
    cli_args = {}
    if args.transport:
        cli_args["server.transport"] = args.transport
    if args.port:
        cli_args["http.port"] = args.port
    if args.host:
        cli_args["http.host"] = args.host

    # Load configuration
    config = load_config(
        config_file=args.config, cli_args=cli_args if cli_args else None
    )

    # Setup logging
    setup_logging(level=config.logging.level, format_str=config.logging.format)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {config.server.name} v{config.server.version}")

    # Validate API key at startup
    if not config.openai.api_key:
        logger.error(
            "OpenAI API key is required. Set OPENAI__API_KEY environment variable or provide in config file."
        )
        raise ValueError("OpenAI API key is required")

    # Inject config into context
    mcp.context = {"config": config}

    # Run with configured transport
    if config.server.transport == "stdio":
        await mcp.run_async(transport="stdio")
    elif config.server.transport in ("sse", "http"):
        # Determine actual transport type
        actual_transport = "sse" if config.server.transport == "sse" else "http"

        # Create HTTP app with CORS support
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount
        from starlette.responses import Response

        # Create the base MCP app with specified transport
        mcp_app = mcp.http_app(
            transport=actual_transport,
        )

        # Create CORS preflight handler
        async def cors_preflight(request):
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Max-Age": "86400",
                },
            )

        # Wrap the MCP app with CORS middleware
        cors_middleware = Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Get the endpoint path based on transport type
        endpoint_path = "/sse" if actual_transport == "sse" else "/mcp"

        # Create wrapper app with OPTIONS route and MCP app's lifespan
        app = Starlette(
            routes=[
                Route(endpoint_path, cors_preflight, methods=["OPTIONS"]),
                Mount("/", app=mcp_app),
            ],
            middleware=[cors_middleware],
            lifespan=mcp_app.lifespan,  # CRITICAL: Pass MCP app's lifespan
        )

        # Run with uvicorn
        config_kwargs = {
            "host": config.http.host,
            "port": config.http.port,
            "log_level": config.logging.level.lower(),
        }

        logger.info(f"Starting MCP server with {actual_transport} transport on http://{config.http.host}:{config.http.port}{endpoint_path}")
        await uvicorn.Server(uvicorn.Config(app, **config_kwargs)).serve()
    else:
        logger.error(f"Unsupported transport: {config.server.transport}")
        raise ValueError(f"Unsupported transport: {config.server.transport}")


if __name__ == "__main__":
    asyncio.run(main())
