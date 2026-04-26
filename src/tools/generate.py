import logging
from typing import Literal, Dict, Any
from fastmcp import FastMCP, Context
from src.tools.common import process_image_request


logger = logging.getLogger(__name__)

mcp = FastMCP("gpt-image-mcp")


@mcp.tool()
async def generate_image(
    prompt: str,
    ctx: Context,
    model: str | None = None,
    size: str | None = None,
    quality: Literal["standard", "hd"] | None = None,
    output_format: Literal["url", "file", "base64"] | None = None,
    output_path: str | None = None,
) -> Dict[str, Any]:
    """Generate an image using OpenAI API based on a text prompt.

    Args:
        prompt: Text description of the image to generate
        model: Model to use for generation (default: gpt-4o)
        size: Image size (default: 1024x1024)
        quality: Image quality: standard or hd (default: standard)
        output_format: Output format: url, file, or base64 (default: url)
        output_path: Optional custom path for file output
        ctx: FastMCP context containing configuration

    Returns:
        Dictionary with:
            - success: bool indicating if operation succeeded
            - format: output format used
            - data: the image data (URL, file path, or base64 string)
            - metadata: dict with model, size, quality
            - error: error message if success is False
    """
    config = ctx.fastmcp.context["config"]

    # Apply defaults from config
    model = model or config.openai.default_model
    size = size or config.image.default_size
    quality = quality or config.image.default_quality
    output_format = output_format or config.image.default_output_format

    logger.info(f"Generating image with prompt: {prompt[:50]}...")

    # Construct CloudflareConfig if credentials provided
    cloudflare_config = None
    if config.cloudflare.auth_code and config.cloudflare.api_url:
        from src.config import CloudflareConfig

        cloudflare_config = CloudflareConfig(
            auth_code=config.cloudflare.auth_code,
            api_url=config.cloudflare.api_url,
            upload_folder=config.cloudflare.upload_folder,
        )

    async def api_call(client):
        return await client.generate_image(
            prompt=prompt, model=model, size=size, quality=quality
        )

    return await process_image_request(
        api_key=config.openai.api_key,
        base_url=config.openai.base_url,
        save_directory=config.image.save_directory,
        output_format=output_format,
        output_path=output_path,
        model=model,
        size=size,
        quality=quality,
        api_call=api_call,
        operation_name="Generating",
        cloudflare_config=cloudflare_config,
        auto_upload_to_cloudflare=config.image.auto_upload_to_cloudflare,
        timeout=config.openai.timeout,
    )
