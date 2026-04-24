import logging
from typing import Optional, Literal, Dict, Any
from src.openai_client import OpenAIClient
from src.image_handler import ImageHandler


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
    try:
        logger.info(f"Generating image with prompt: {prompt[:50]}...")
        logger.debug(f"Parameters: model={model}, size={size}, quality={quality}, output_format={output_format}")

        # Create OpenAI client
        client = OpenAIClient(api_key=api_key, base_url=base_url)

        # Generate image and get URL
        image_url = await client.generate_image(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality
        )

        logger.info(f"Image generated successfully: {image_url}")

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

    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return {
            "success": False,
            "error": str(e)
        }
