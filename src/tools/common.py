import logging
import uuid
from typing import Optional, Literal, Dict, Any, Callable, Awaitable, TYPE_CHECKING
from src.openai_client import OpenAIClient
from src.image_handler import ImageHandler

if TYPE_CHECKING:
    from src.cloudflare_uploader import CloudflareUploader
    from src.config import CloudflareConfig


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
    operation_name: str,
    cloudflare_config: Optional['CloudflareConfig'] = None,
    auto_upload_to_cloudflare: bool = True,
    timeout: int = 60
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
        api_call: Async callback function that takes OpenAIClient and returns base64 or URL
        operation_name: Name of the operation for logging (e.g., "Generating", "Editing")
        cloudflare_config: Optional CloudflareConfig for uploading images
        auto_upload_to_cloudflare: Whether to auto-upload to Cloudflare when output_format is url
        timeout: Request timeout in seconds

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
        logger.info(f"Using timeout: {timeout}s")

        # Create OpenAI client
        client = OpenAIClient(api_key=api_key, base_url=base_url, timeout=timeout)

        # Call the API (generate or edit) - returns base64 data or URL
        image_data = await api_call(client)

        logger.info(f"Image {operation_name.lower()} successfully")

        # Create CloudflareUploader if config is provided
        uploader = None
        if cloudflare_config and cloudflare_config.auth_code and cloudflare_config.api_url:
            from src.cloudflare_uploader import CloudflareUploader
            uploader = CloudflareUploader(
                auth_code=cloudflare_config.auth_code,
                api_url=cloudflare_config.api_url,
                upload_folder=cloudflare_config.upload_folder
            )
            logger.debug("CloudflareUploader initialized")

        # Create ImageHandler with optional Cloudflare uploader
        handler = ImageHandler(
            save_directory=save_directory,
            cloudflare_uploader=uploader,
            auto_upload_to_cloudflare=auto_upload_to_cloudflare
        )

        # Check if image_data is a URL or base64
        if image_data.startswith("http://") or image_data.startswith("https://"):
            # It's a URL, use download_image
            result = await handler.download_image(
                url=image_data,
                output_format=output_format,
                output_path=output_path
            )
        else:
            # It's base64 data, use process_base64_image
            result = await handler.process_base64_image(
                base64_data=image_data,
                output_format=output_format,
                output_path=output_path,
                filename=f"{operation_name.lower()}_{uuid.uuid4()}.png"
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
