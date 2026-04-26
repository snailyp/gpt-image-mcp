import logging
from typing import Optional
import openai
import httpx


logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for OpenAI Responses API to generate and edit images."""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", timeout: int = 60):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            base_url: Base URL for OpenAI API
            timeout: Request timeout in seconds
        """
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )
        logger.info(f"Initialized OpenAI client with base_url={base_url}, timeout={timeout}s")

    async def generate_image(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> str:
        """Generate an image using OpenAI Images API.

        Args:
            prompt: Text description of the image to generate
            model: Model to use for generation (e.g., "dall-e-3", "dall-e-2")
            size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792")
            quality: Image quality ("standard" or "hd")

        Returns:
            Base64-encoded image data

        Raises:
            ValueError: If no image is generated
            openai.APIError: If the API request fails
            openai.APIConnectionError: If connection to API fails
        """
        import time
        start_time = time.time()

        logger.info(f"Generating image with prompt: {prompt[:50]}...")
        logger.debug(f"Parameters: model={model}, size={size}, quality={quality}")

        # Call Images API with error handling
        try:
            response = await self.client.images.generate(
                prompt=prompt,
                model=model,
                size=size,
                quality=quality,
                response_format="b64_json"
            )
        except openai.APIConnectionError as e:
            logger.error(f"Failed to connect to OpenAI API: {e}")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

        # Extract base64 image data from response
        if not response.data or len(response.data) == 0:
            logger.error("No image data in response")
            raise ValueError("No image generated")

        image_data = response.data[0].b64_json

        elapsed = time.time() - start_time
        logger.info(f"Successfully generated image (base64 data length: {len(image_data)}) in {elapsed:.2f}s")
        return image_data

    async def edit_image(
        self,
        image_data: str,
        prompt: str,
        model: str = "gpt-4o",
        size: str = "1024x1024",
        quality: str = "standard",
        previous_response_id: Optional[str] = None
    ) -> str:
        """Edit an image using OpenAI Responses API.

        NOTE: This method is temporarily disabled pending Task 5 migration to Images API.

        Args:
            image_data: Base64-encoded image data or image URL
            prompt: Text description of the edits to make
            model: Model to use for editing
            size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792")
            quality: Image quality ("standard" or "hd")
            previous_response_id: Optional ID of previous response for multi-turn editing

        Returns:
            Base64-encoded edited image data

        Raises:
            NotImplementedError: Method temporarily disabled pending Task 5 implementation
        """
        raise NotImplementedError(
            "edit_image() is temporarily disabled. "
            "This method will be reimplemented using Images API in Task 5."
        )

    def _get_image_generation_tool(self):
        """Temporary stub - will be removed in Task 5.

        Raises:
            NotImplementedError: Method deleted in Task 4, pending Task 5 reimplementation
        """
        raise NotImplementedError(
            "_get_image_generation_tool() was removed in Task 4. "
            "edit_image() will be reimplemented in Task 5."
        )

    def _extract_image_data_from_response(self, response):
        """Temporary stub - will be removed in Task 5.

        Raises:
            NotImplementedError: Method deleted in Task 4, pending Task 5 reimplementation
        """
        raise NotImplementedError(
            "_extract_image_data_from_response() was removed in Task 4. "
            "edit_image() will be reimplemented in Task 5."
        )

    async def _download_image(self, url: str) -> bytes:
        """Download image from URL.

        Args:
            url: Image URL to download

        Returns:
            Image data as bytes

        Raises:
            httpx.HTTPError: If download fails
        """
        logger.info(f"Downloading image from {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            logger.info(f"Successfully downloaded image ({len(response.content)} bytes)")
            return response.content

    def _ensure_png_format(self, image_bytes: bytes) -> bytes:
        """Ensure image is in PNG format, converting if necessary.

        Args:
            image_bytes: Image data as bytes

        Returns:
            PNG-formatted image data as bytes

        Raises:
            ValueError: If image cannot be processed
        """
        from PIL import Image
        from io import BytesIO

        try:
            # Open image from bytes
            img = Image.open(BytesIO(image_bytes))

            # If already PNG, return as-is
            if img.format == 'PNG':
                logger.debug("Image is already PNG format")
                return image_bytes

            # Convert to PNG
            logger.info(f"Converting image from {img.format} to PNG")
            png_buffer = BytesIO()

            # Convert RGBA to RGB if necessary (PNG supports both)
            if img.mode == 'RGBA':
                img.save(png_buffer, format='PNG')
            else:
                # Convert to RGB first for other modes
                rgb_img = img.convert('RGB')
                rgb_img.save(png_buffer, format='PNG')

            png_bytes = png_buffer.getvalue()
            logger.info(f"Successfully converted to PNG ({len(png_bytes)} bytes)")
            return png_bytes

        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            raise ValueError(f"Cannot process image: {e}")
