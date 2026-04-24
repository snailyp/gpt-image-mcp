"""Server information tool for MCP."""


def get_server_info_tool(
    server_name: str = "gpt-image-mcp",
    server_version: str = "1.0.0",
    transport: str = "stdio",
    default_model: str = "gpt-4o",
    default_size: str = "1024x1024"
) -> dict:
    """
    Get server metadata and configuration information.

    Args:
        server_name: Name of the MCP server
        server_version: Version of the server
        transport: Transport protocol (stdio, http, etc.)
        default_model: Default model to use for image generation
        default_size: Default image size

    Returns:
        Dictionary containing server metadata, supported models, formats, and config
    """
    return {
        "name": server_name,
        "version": server_version,
        "transport": transport,
        "supported_models": ["gpt-4o", "gpt-4-turbo"],
        "supported_formats": ["url", "file", "base64"],
        "config": {
            "default_model": default_model,
            "default_size": default_size
        }
    }
