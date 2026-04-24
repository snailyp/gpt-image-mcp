import logging
from typing import Optional, Literal, Dict, Any
from src.openai_client import OpenAIClient
from src.image_handler import ImageHandler


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
    # Validate API key
    if not api_key:
        logger.error("API key is required")
        return {"success": False, "error": "API key is required"}

    try:
        logger.info(f"Editing image with prompt: {prompt[:50]}...")
        logger.debug(f"Parameters: image_input={image_input}, model={model}, size={size}, quality={quality}, output_format={output_format}")

        # Create OpenAI client
        client = OpenAIClient(api_key=api_key, base_url=base_url)

        # Edit image and get URL
        edited_image_url = await client.edit_image(
            image_url=image_input,
            prompt=prompt,
            model=model,
            size=size,
            quality=quality
        )

        logger.info(f"Image edited successfully: {edited_image_url}")

        # Create ImageHandler to process output format
        handler = ImageHandler(save_directory=save_directory)

        # Download/convert image to requested format
        result = await handler.download_image(
            url=edited_image_url,
            output_format=output_format,
            output_path=output_path
        )

        logger.info(f"Image processed to {output_format} format successfully")

        # Return success response with metadata
        return {
            "success": True,
            "format": result["format"],
            "data": result["data"],
            "metadata": {
                "model": model,
                "size": size,
                "quality": quality
            }
        }

    except (ValueError, Exception) as e:
        logger.error(f"Error editing image: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
