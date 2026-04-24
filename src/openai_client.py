import json
import logging
from typing import Optional
import openai


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
        logger.info(f"Initialized OpenAI client with base_url={base_url}")

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
            URL of the generated image

        Raises:
            ValueError: If no image is generated
        """
        logger.info(f"Generating image with prompt: {prompt[:50]}...")
        logger.debug(f"Parameters: model={model}, size={size}, quality={quality}")

        # Define the image_generation tool
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "image_generation",
                    "description": "Generate an image based on a text prompt",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string"},
                            "size": {"type": "string"},
                            "quality": {"type": "string"}
                        },
                        "required": ["prompt"]
                    }
                }
            }
        ]

        # Call Responses API
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            tools=tools
        )

        # Extract image URL from tool call
        if not response.choices or not response.choices[0].message.tool_calls:
            logger.error("No tool calls in response")
            raise ValueError("No image generated")

        tool_call = response.choices[0].message.tool_calls[0]
        if tool_call.function.name != "image_generation":
            logger.error(f"Unexpected tool call: {tool_call.function.name}")
            raise ValueError("No image generated")

        # Parse tool call arguments
        try:
            arguments = json.loads(tool_call.function.arguments)
            image_url = arguments.get("image_url")
            if not image_url:
                logger.error("No image_url in tool call arguments")
                raise ValueError("No image generated")

            logger.info(f"Successfully generated image: {image_url}")
            return image_url
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool call arguments: {e}")
            raise ValueError("No image generated")

    async def edit_image(
        self,
        image_url: str,
        prompt: str,
        model: str = "gpt-4o",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> str:
        """Edit an image using OpenAI Responses API.

        Args:
            image_url: URL of the image to edit
            prompt: Text description of the edits to make
            model: Model to use for editing
            size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792")
            quality: Image quality ("standard" or "hd")

        Returns:
            URL of the edited image

        Raises:
            ValueError: If no image is generated
        """
        logger.info(f"Editing image with prompt: {prompt[:50]}...")
        logger.debug(f"Parameters: image_url={image_url}, model={model}, size={size}, quality={quality}")

        # Define the image_generation tool
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "image_generation",
                    "description": "Generate or edit an image based on a text prompt",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string"},
                            "size": {"type": "string"},
                            "quality": {"type": "string"}
                        },
                        "required": ["prompt"]
                    }
                }
            }
        ]

        # Call Responses API with image in messages
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            tools=tools
        )

        # Extract image URL from tool call
        if not response.choices or not response.choices[0].message.tool_calls:
            logger.error("No tool calls in response")
            raise ValueError("No image generated")

        tool_call = response.choices[0].message.tool_calls[0]
        if tool_call.function.name != "image_generation":
            logger.error(f"Unexpected tool call: {tool_call.function.name}")
            raise ValueError("No image generated")

        # Parse tool call arguments
        try:
            arguments = json.loads(tool_call.function.arguments)
            edited_image_url = arguments.get("image_url")
            if not edited_image_url:
                logger.error("No image_url in tool call arguments")
                raise ValueError("No image generated")

            logger.info(f"Successfully edited image: {edited_image_url}")
            return edited_image_url
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool call arguments: {e}")
            raise ValueError("No image generated")
