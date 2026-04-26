import logging
from typing import Any, Dict, Literal

from fastmcp import Context

from src.tools.common import process_image_request
from src.tools.generate import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def edit_image(
    image_input: str,
    prompt: str,
    ctx: Context,
    model: str | None = None,
    quality: Literal["low", "medium", "high", "auto"] | None = None,
    output_format: Literal["url", "file", "base64"] | None = None,
    output_path: str | None = None,
) -> Dict[str, Any]:
    """Edit an existing image using OpenAI API based on a text prompt.

    Args:
        image_input: URL or file path of the image to edit
        prompt: Text description of the desired changes
        ctx: FastMCP context containing configuration
        model: Model to use for editing (default: gpt-image-2)
        quality: Image quality: low, medium, high, or auto (default: auto)
        output_format: Output format: url, file, or base64 (default: url)
        output_path: Optional custom path for file output

    Returns:
        Dictionary with:
            - success: bool indicating if operation succeeded
            - format: output format used
            - data: the image data (URL, file path, or base64 string)
            - metadata: dict with model, quality
            - error: error message if success is False
    """
    config = ctx.fastmcp.context["config"]

    # Validate image_input
    if not image_input:
        logger.error("Image input is required")
        return {"success": False, "error": "Image input is required"}

    # Apply defaults from config
    model = model or config.openai.default_model
    quality = quality or config.image.default_quality
    output_format = output_format or config.image.default_output_format

    logger.info(f"Editing image with prompt: {prompt[:50]}...")
    logger.debug(
        f"Parameters: image_input={image_input}, model={model}, quality={quality}, output_format={output_format}"
    )

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
        return await client.edit_image(
            image_url=image_input,
            prompt=prompt,
            model=model,
            quality=quality,
        )

    return await process_image_request(
        api_key=config.openai.api_key,
        base_url=config.openai.base_url,
        save_directory=config.image.save_directory,
        output_format=output_format,
        output_path=output_path,
        model=model,
        quality=quality,
        api_call=api_call,
        operation_name="Editing",
        cloudflare_config=cloudflare_config,
        auto_upload_to_cloudflare=config.image.auto_upload_to_cloudflare,
        timeout=config.openai.timeout,
    )
