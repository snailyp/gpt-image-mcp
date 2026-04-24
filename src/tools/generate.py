import logging
from typing import Optional, Literal, Dict, Any
from src.tools.common import process_image_request


logger = logging.getLogger(__name__)


async def generate_image_tool(
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
    Generate an image using OpenAI API and return it in the specified format.

    Args:
        prompt: Text description of the image to generate
        model: Model to use for generation (default: "gpt-4o")
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
    logger.info(f"Generating image with prompt: {prompt[:50]}...")

    async def api_call(client):
        return await client.generate_image(
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
        operation_name="Generating"
    )
