import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.openai_client import OpenAIClient


@pytest.mark.asyncio
async def test_generate_image():
    with patch('openai.AsyncOpenAI') as mock_openai:
        # Create mock function object
        mock_function = Mock()
        mock_function.name = "image_generation"
        mock_function.arguments = '{"image_url": "https://example.com/image.png"}'

        # Create mock tool call
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = mock_function

        # Create mock response
        mock_message = Mock()
        mock_message.tool_calls = [mock_tool_call]

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_response = Mock()
        mock_response.choices = [mock_choice]

        mock_openai.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

        client = OpenAIClient(api_key="test-key", base_url="https://api.openai.com/v1")

        result = await client.generate_image(
            prompt="a cat in space",
            model="gpt-4o",
            size="1024x1024",
            quality="standard"
        )

        assert result == "https://example.com/image.png"


@pytest.mark.asyncio
async def test_edit_image():
    with patch('openai.AsyncOpenAI') as mock_openai:
        # Create mock function object
        mock_function = Mock()
        mock_function.name = "image_generation"
        mock_function.arguments = '{"image_url": "https://example.com/edited-image.png"}'

        # Create mock tool call
        mock_tool_call = Mock()
        mock_tool_call.id = "call_456"
        mock_tool_call.function = mock_function

        # Create mock response
        mock_message = Mock()
        mock_message.tool_calls = [mock_tool_call]

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_response = Mock()
        mock_response.choices = [mock_choice]

        mock_openai.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

        client = OpenAIClient(api_key="test-key", base_url="https://api.openai.com/v1")

        result = await client.edit_image(
            image_url="https://example.com/original.png",
            prompt="add a hat to the cat",
            model="gpt-4o",
            size="1024x1024",
            quality="standard"
        )

        assert result == "https://example.com/edited-image.png"
