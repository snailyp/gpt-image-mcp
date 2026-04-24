import logging
from typing import Optional, Literal, Dict, Any
from src.tools.common import process_image_request


logger = logging.getLogger(__name__)


async def edit_image_tool(
    image_input: str,
    prompt: str,
    model: str = "gpt-4o",
    size: str = "1024x1024",
    quality: str = "standard",
    output_format: Literal["url", "file", "base64"] = "url",
    output_path: Optional[str] = None,
    api_key: str = "",
    base_url: str = "https://api.openai.com/v1",
    save_directory: str = "./images"
) -> Dict[str, Any]:
    """
    Edit an image using OpenAI API and return it in the specified format.

    Args:
        image_input: URL or path to the image to edit
        prompt: Text description of the edits to make
        model: Model to use for editing (default: "gpt-4o")
        size: Image size (default: "1024x1024")
        quality: Image quality "standard" or "hd" (default: "standard")
        output_format: Output format - "url", "file", or "base64" (default: "url")
        output_path: Optional custom path for file output
        api_key: OpenAI API key
        base_url: Base URL for OpenAI API (default: "https://api.openai.com/v1")
        save_directory: Directory to save images (default: "./images")

    Returns:
        Dictionary with:
            - success: bool indicating if operation succeeded
            - format: output format used
            - data: the image data (URL, file path, or base64 string)
            - metadata: dict with model, size, quality
            - error: error message if success is False
    """
    # Validate image_input
    if not image_input:
        logger.error("Image input is required")
        return {"success": False, "error": "Image input is required"}

    logger.info(f"Editing image with prompt: {prompt[:50]}...")
    logger.debug(f"Parameters: image_input={image_input}, model={model}, size={size}, quality={quality}, output_format={output_format}")

    async def api_call(client):
        return await client.edit_image(
            image_url=image_input,
            prompt=prompt,
            model=model,
            size=size,
            quality=quality
        )

    return await process_image_request(
        api_key=api_key,
        base_url=base_url,
        save_directory=save_directory,
        output_format=output_format,
        output_path=output_path,
        model=model,
        size=size,
        quality=quality,
        api_call=api_call,
        operation_name="Editing"
    )
