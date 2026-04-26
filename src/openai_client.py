import logging
from typing import Optional

import httpx
import openai

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for OpenAI Responses API to generate and edit images."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 60,
    ):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            base_url: Base URL for OpenAI API
            timeout: Request timeout in seconds
        """
        self.client = openai.AsyncOpenAI(
            api_key=api_key, base_url=base_url, timeout=timeout
        )
        logger.info(
            f"Initialized OpenAI client with base_url={base_url}, timeout={timeout}s"
        )

    async def generate_image(
        self, prompt: str, model: str = "dall-e-3", quality: str = "auto"
    ) -> str:
        """Generate an image using OpenAI Images API.

        Args:
            prompt: Text description of the image to generate
            model: Model to use for generation (e.g., "dall-e-3", "dall-e-2")
            quality: Image quality ("low", "medium", "high", or "auto")

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
        logger.debug(f"Parameters: model={model}, quality={quality}")

        # Call Images API with error handling
        try:
            response = await self.client.images.generate(
                prompt=prompt, model=model, quality=quality
            )
        except openai.APIConnectionError as e:
            logger.error(f"Failed to connect to OpenAI API: {e}")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

        # Extract image data from response
        if not response.data or len(response.data) == 0:
            logger.error("No image data in response")
            raise ValueError("No image generated")

        # Check if response has b64_json or url
        image_obj = response.data[0]

        if hasattr(image_obj, "b64_json") and image_obj.b64_json:
            # Response already contains base64 data
            logger.info("Received base64 image data directly from API")
            image_data = image_obj.b64_json
        elif hasattr(image_obj, "url") and image_obj.url:
            # Response contains URL, download and convert to base64
            image_url = image_obj.url
            logger.info(f"Downloading generated image from: {image_url}")
            image_bytes = await self._download_image(image_url)

            # Convert to base64
            import base64

            image_data = base64.b64encode(image_bytes).decode("utf-8")
        else:
            logger.error("Response contains neither b64_json nor url")
            raise ValueError("Invalid response format from API")

        elapsed = time.time() - start_time
        logger.info(
            f"Successfully generated image (base64 data length: {len(image_data)}) in {elapsed:.2f}s"
        )
        return image_data

    async def edit_image(
        self,
        image_url: str,
        prompt: str,
        model: str = "dall-e-2",
        quality: str = "auto",
        previous_response_id: Optional[str] = None,
    ) -> str:
        """Edit an image using OpenAI Images API.

        Args:
            image_url: Image URL or local file path
            prompt: Text description of the edits to make
            model: Model to use for editing (dall-e-2)
            quality: Image quality ("low", "medium", "high", or "auto")
            previous_response_id: Ignored (kept for compatibility)

        Returns:
            Base64-encoded edited image data

        Raises:
            ValueError: If image cannot be loaded or processed
            openai.APIError: If API call fails
        """
        import os
        from io import BytesIO

        logger.info(f"Editing image with prompt: {prompt}")

        # Determine if input is URL or file path
        if image_url.startswith(("http://", "https://")):
            # Download from URL
            image_bytes = await self._download_image(image_url)
        else:
            # Read from local file
            if not os.path.exists(image_url):
                raise ValueError(f"Image file not found: {image_url}")

            logger.info(f"Reading image from file: {image_url}")
            with open(image_url, "rb") as f:
                image_bytes = f.read()

        # Ensure PNG format (Images API requirement)
        png_bytes = self._ensure_png_format(image_bytes)

        # Create file-like object for upload
        image_file = BytesIO(png_bytes)
        image_file.name = "image.png"

        # Call Images API
        logger.info(f"Calling Images API edit with model={model}, quality={quality}")
        response = await self.client.images.edit(
            image=image_file, prompt=prompt, model=model, quality=quality, n=1
        )

        # Extract image data from response
        if not response.data or len(response.data) == 0:
            logger.error("No image data in response")
            raise ValueError("No image generated")

        # Check if response has b64_json or url
        image_obj = response.data[0]

        if hasattr(image_obj, "b64_json") and image_obj.b64_json:
            # Response already contains base64 data
            logger.info("Received base64 image data directly from API")
            edited_image = image_obj.b64_json
        elif hasattr(image_obj, "url") and image_obj.url:
            # Response contains URL, download and convert to base64
            edited_image_url = image_obj.url
            logger.info(f"Downloading edited image from: {edited_image_url}")
            edited_image_bytes = await self._download_image(edited_image_url)

            # Convert to base64
            import base64

            edited_image = base64.b64encode(edited_image_bytes).decode("utf-8")
        else:
            logger.error("Response contains neither b64_json nor url")
            raise ValueError("Invalid response format from API")

        logger.info("Successfully edited image")
        return edited_image

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
            logger.info(
                f"Successfully downloaded image ({len(response.content)} bytes)"
            )
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
        from io import BytesIO

        from PIL import Image

        try:
            # Open image from bytes
            img = Image.open(BytesIO(image_bytes))

            # If already PNG, return as-is
            if img.format == "PNG":
                logger.debug("Image is already PNG format")
                return image_bytes

            # Convert to PNG
            logger.info(f"Converting image from {img.format} to PNG")
            png_buffer = BytesIO()

            # Convert RGBA to RGB if necessary (PNG supports both)
            if img.mode == "RGBA":
                img.save(png_buffer, format="PNG")
            else:
                # Convert to RGB first for other modes
                rgb_img = img.convert("RGB")
                rgb_img.save(png_buffer, format="PNG")

            png_bytes = png_buffer.getvalue()
            logger.info(f"Successfully converted to PNG ({len(png_bytes)} bytes)")
            return png_bytes

        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            raise ValueError(f"Cannot process image: {e}")
