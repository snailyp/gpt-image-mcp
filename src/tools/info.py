"""Server information tool for MCP."""

from typing import Any, Dict

from fastmcp import Context

from src.tools.generate import mcp


@mcp.tool()
def get_server_info(ctx: Context) -> Dict[str, Any]:
    """Get server metadata and configuration information.

    Returns server name, version, transport mode, supported models and formats,
    and current configuration defaults.

    Args:
        ctx: FastMCP context containing configuration

    Returns:
        Dictionary with:
            - name: Server name
            - version: Server version
            - transport: Transport mode (stdio or sse)
            - supported_models: List of supported OpenAI models
            - supported_formats: List of supported output formats
            - config: Current configuration defaults
    """
    config = ctx.fastmcp.context["config"]

    return {
        "name": config.server.name,
        "version": config.server.version,
        "transport": config.server.transport,
        "supported_models": ["gpt-image-1", "gpt-image-1.5", "gpt-image-2"],
        "supported_formats": ["url", "file", "base64"],
        "config": {
            "default_model": config.openai.default_model,
            "default_size": config.image.default_size,
        },
    }
