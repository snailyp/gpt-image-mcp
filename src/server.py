"""Main MCP server entry point."""
import asyncio
import logging
import argparse
import json
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent

from src.config import load_config
from src.tools.generate import generate_image_tool
from src.tools.edit import edit_image_tool
from src.tools.info import get_server_info_tool
from src.transports.stdio import run_stdio_server


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

    # Create MCP server instance
    server = Server(config.server.name)

    # Register list_tools handler
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available MCP tools."""
        return [
            Tool(
                name="generate_image",
                description="Generate an image using OpenAI API based on a text prompt",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Text description of the image to generate"
                        },
                        "model": {
                            "type": "string",
                            "description": "Model to use for generation",
                            "default": config.openai.default_model
                        },
                        "size": {
                            "type": "string",
                            "description": "Image size (e.g., 1024x1024, 1792x1024, 1024x1792)",
                            "default": config.image.default_size
                        },
                        "quality": {
                            "type": "string",
                            "description": "Image quality: standard or hd",
                            "enum": ["standard", "hd"],
                            "default": config.image.default_quality
                        },
                        "output_format": {
                            "type": "string",
                            "description": "Output format: url, file, or base64",
                            "enum": ["url", "file", "base64"],
                            "default": config.image.default_output_format
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Optional custom path for file output"
                        }
                    },
                    "required": ["prompt"]
                }
            ),
            Tool(
                name="edit_image",
                description="Edit an existing image using OpenAI API based on a text prompt",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_input": {
                            "type": "string",
                            "description": "URL or file path to the image to edit"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Text description of the edits to make"
                        },
                        "model": {
                            "type": "string",
                            "description": "Model to use for editing",
                            "default": config.openai.default_model
                        },
                        "size": {
                            "type": "string",
                            "description": "Image size (e.g., 1024x1024, 1792x1024, 1024x1792)",
                            "default": config.image.default_size
                        },
                        "quality": {
                            "type": "string",
                            "description": "Image quality: standard or hd",
                            "enum": ["standard", "hd"],
                            "default": config.image.default_quality
                        },
                        "output_format": {
                            "type": "string",
                            "description": "Output format: url, file, or base64",
                            "enum": ["url", "file", "base64"],
                            "default": config.image.default_output_format
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Optional custom path for file output"
                        }
                    },
                    "required": ["image_input", "prompt"]
                }
            ),
            Tool(
                name="get_server_info",
                description="Get server metadata and configuration information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]

    # Register call_tool handler
    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Handle tool calls."""
        logger.info(f"Tool called: {name}")

        # Sanitize sensitive data before logging
        sanitized_args = {k: v for k, v in arguments.items() if k not in ["api_key", "token", "password"]}
        logger.debug(f"Arguments: {sanitized_args}")

        try:
            if name == "generate_image":
                result = await generate_image_tool(
                    prompt=arguments["prompt"],
                    model=arguments.get("model", config.openai.default_model),
                    size=arguments.get("size", config.image.default_size),
                    quality=arguments.get("quality", config.image.default_quality),
                    output_format=arguments.get("output_format", config.image.default_output_format),
                    output_path=arguments.get("output_path"),
                    api_key=config.openai.api_key,
                    base_url=config.openai.base_url,
                    save_directory=config.image.save_directory
                )
                return [TextContent(type="text", text=json.dumps(result))]

            elif name == "edit_image":
                result = await edit_image_tool(
                    image_input=arguments["image_input"],
                    prompt=arguments["prompt"],
                    model=arguments.get("model", config.openai.default_model),
                    size=arguments.get("size", config.image.default_size),
                    quality=arguments.get("quality", config.image.default_quality),
                    output_format=arguments.get("output_format", config.image.default_output_format),
                    output_path=arguments.get("output_path"),
                    api_key=config.openai.api_key,
                    base_url=config.openai.base_url,
                    save_directory=config.image.save_directory
                )
                return [TextContent(type="text", text=json.dumps(result))]

            elif name == "get_server_info":
                result = get_server_info_tool(
                    server_name=config.server.name,
                    server_version=config.server.version,
                    transport=config.server.transport,
                    default_model=config.openai.default_model,
                    default_size=config.image.default_size
                )
                return [TextContent(type="text", text=json.dumps(result))]

            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Run server with configured transport
    if config.server.transport == "stdio":
        await run_stdio_server(server)
    else:
        logger.error(f"Unsupported transport: {config.server.transport}")
        raise ValueError(f"Unsupported transport: {config.server.transport}")


if __name__ == "__main__":
    asyncio.run(main())
