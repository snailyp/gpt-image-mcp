import logging
from typing import Optional, Dict, Any, List
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

    def _get_image_generation_tool(self) -> List[Dict[str, Any]]:
        """Get the image generation tool definition.

        Returns:
            List containing the tool definition
        """
        return [{"type": "image_generation"}]

    def _extract_image_data_from_response(self, response: Any) -> str:
        """Extract base64 image data from OpenAI Responses API response.

        Args:
            response: OpenAI Responses API response object

        Returns:
            Base64-encoded image data

        Raises:
            ValueError: If no image data is found in the response
        """
        if not hasattr(response, 'output') or not response.output:
            logger.error("No output in response")
            raise ValueError("No image generated")

        # Filter for image_generation_call outputs
        image_outputs = [
            output for output in response.output
            if hasattr(output, 'type') and output.type == "image_generation_call"
        ]

        if not image_outputs:
            logger.error("No image_generation_call in response output")
            raise ValueError("No image generated")

        # Get the result from the first image output
        image_output = image_outputs[0]
        if not hasattr(image_output, 'result') or not image_output.result:
            logger.error("No result in image_generation_call output")
            raise ValueError("No image generated")

        return image_output.result

    async def generate_image(
        self,
        prompt: str,
        model: str = "gpt-4o",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> str:
        """Generate an image using OpenAI Responses API.

        Args:
            prompt: Text description of the image to generate
            model: Model to use for generation
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

        # Get tool definition
        tools = self._get_image_generation_tool()

        # Call Responses API with error handling
        try:
            response = await self.client.responses.create(
                model=model,
                input=prompt,
                tools=tools
            )
        except openai.APIConnectionError as e:
            logger.error(f"Failed to connect to OpenAI API: {e}")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

        # Extract base64 image data from response
        image_data = self._extract_image_data_from_response(response)

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
            ValueError: If no image is generated
            openai.APIError: If the API request fails
            openai.APIConnectionError: If connection to API fails
        """
        logger.info(f"Editing image with prompt: {prompt[:50]}...")
        logger.debug(f"Parameters: model={model}, size={size}, quality={quality}")

        # Get tool definition
        tools = self._get_image_generation_tool()

        # Prepare input with image reference
        input_content = f"[Image: {image_data[:50]}...]\n{prompt}" if len(image_data) > 50 else f"[Image: {image_data}]\n{prompt}"

        # Call Responses API with error handling
        try:
            request_params = {
                "model": model,
                "input": input_content,
                "tools": tools
            }

            # Add previous_response_id if provided for multi-turn editing
            if previous_response_id:
                request_params["previous_response_id"] = previous_response_id

            response = await self.client.responses.create(**request_params)
        except openai.APIConnectionError as e:
            logger.error(f"Failed to connect to OpenAI API: {e}")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

        # Extract base64 image data from response
        edited_image_data = self._extract_image_data_from_response(response)
        logger.info(f"Successfully edited image (base64 data length: {len(edited_image_data)})")
        return edited_image_data

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
