"""Main MCP server entry point."""
import asyncio
import logging
import argparse

from src.config import load_config
from src.tools.generate import mcp, generate_image
from src.tools.edit import edit_image
from src.tools.info import get_server_info
# Note: Tool functions are imported for their side effect of registering with mcp instance


def setup_logging(level: str = "INFO", format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"):
    """
    Configure logging for the server.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_str: Log message format string
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_str
    )


async def main():
    """Main server entry point."""
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="GPT Image MCP Server")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--transport", type=str, default="stdio", help="Transport protocol (default: stdio)")
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
    config = load_config(config_file=args.config, cli_args=cli_args if cli_args else None)

    # Setup logging
    setup_logging(level=config.logging.level, format_str=config.logging.format)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {config.server.name} v{config.server.version}")

    # Validate API key at startup
    if not config.openai.api_key:
        logger.error("OpenAI API key is required. Set OPENAI__API_KEY environment variable or provide in config file.")
        raise ValueError("OpenAI API key is required")

    # Inject config into context
    mcp.context = {"config": config}

    # Run with configured transport
    if config.server.transport == "stdio":
        await mcp.run(transport="stdio")
    elif config.server.transport in ("sse", "http"):
        # Map "http" to "sse" for backward compatibility
        await mcp.run(
            transport="sse",
            sse_host=config.http.host,
            sse_port=config.http.port
        )
    else:
        logger.error(f"Unsupported transport: {config.server.transport}")
        raise ValueError(f"Unsupported transport: {config.server.transport}")


if __name__ == "__main__":
    asyncio.run(main())
