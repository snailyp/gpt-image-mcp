import logging
from typing import Optional, Literal, Dict, Any, Callable, Awaitable
from src.openai_client import OpenAIClient
from src.image_handler import ImageHandler


logger = logging.getLogger(__name__)


async def process_image_request(
    api_key: str,
    base_url: str,
    save_directory: str,
    output_format: Literal["url", "file", "base64"],
    output_path: Optional[str],
    model: str,
    size: str,
    quality: str,
    api_call: Callable[[OpenAIClient], Awaitable[str]],
    operation_name: str
) -> Dict[str, Any]:
    """
    Common helper function for processing image generation and editing requests.

    Args:
        api_key: OpenAI API key
        base_url: Base URL for OpenAI API
        save_directory: Directory to save images
        output_format: Output format - "url", "file", or "base64"
        output_path: Optional custom path for file output
        model: Model to use
        size: Image size
        quality: Image quality
        api_call: Async callback function that takes OpenAIClient and returns image URL
        operation_name: Name of the operation for logging (e.g., "Generating", "Editing")

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
        logger.info(f"{operation_name} image...")
        logger.debug(f"Parameters: model={model}, size={size}, quality={quality}, output_format={output_format}")

        # Create OpenAI client
        client = OpenAIClient(api_key=api_key, base_url=base_url)

        # Call the API (generate or edit)
        image_url = await api_call(client)

        logger.info(f"Image {operation_name.lower()} successfully: {image_url}")

        # Create ImageHandler to process output format
        handler = ImageHandler(save_directory=save_directory)

        # Download/convert image to requested format
        result = await handler.download_image(
            url=image_url,
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
        logger.error(f"Error {operation_name.lower()} image: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
