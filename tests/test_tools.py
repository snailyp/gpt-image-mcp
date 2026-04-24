import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.tools.generate import generate_image_tool


@pytest.mark.asyncio
async def test_generate_image_tool_url_format():
    """Test generate_image_tool with URL output format."""
    with patch('src.tools.generate.OpenAIClient') as mock_client_class, \
         patch('src.tools.generate.ImageHandler') as mock_handler_class:

        # Setup mocks
        mock_client = Mock()
        mock_client.generate_image = AsyncMock(return_value="https://example.com/generated.png")
        mock_client_class.return_value = mock_client

        mock_handler = Mock()
        mock_handler.download_image = AsyncMock(return_value={
            "format": "url",
            "data": "https://example.com/generated.png"
        })
        mock_handler_class.return_value = mock_handler

        # Call the tool
        result = await generate_image_tool(
            prompt="A beautiful sunset",
            model="gpt-4o",
            output_format="url",
            api_key="test_api_key"
        )

        # Assertions
        assert result["success"] is True
        assert result["format"] == "url"
        assert result["data"] == "https://example.com/generated.png"
        assert result["metadata"]["model"] == "gpt-4o"
        assert result["metadata"]["size"] == "1024x1024"
        assert result["metadata"]["quality"] == "standard"

        # Verify client was called correctly
        mock_client_class.assert_called_once_with(
            api_key="test_api_key",
            base_url="https://api.openai.com/v1"
        )
        mock_client.generate_image.assert_called_once_with(
            prompt="A beautiful sunset",
            model="gpt-4o",
            size="1024x1024",
            quality="standard"
        )

        # Verify handler was called correctly
        mock_handler_class.assert_called_once_with(save_directory="./images")
        mock_handler.download_image.assert_called_once_with(
            url="https://example.com/generated.png",
            output_format="url",
            output_path=None
        )


@pytest.mark.asyncio
async def test_generate_image_tool_file_format():
    """Test generate_image_tool with file output format."""
    with patch('src.tools.generate.OpenAIClient') as mock_client_class, \
         patch('src.tools.generate.ImageHandler') as mock_handler_class:

        # Setup mocks
        mock_client = Mock()
        mock_client.generate_image = AsyncMock(return_value="https://example.com/generated.png")
        mock_client_class.return_value = mock_client

        mock_handler = Mock()
        mock_handler.download_image = AsyncMock(return_value={
            "format": "file",
            "data": "./images/12345-abcde.png"
        })
        mock_handler_class.return_value = mock_handler

        # Call the tool
        result = await generate_image_tool(
            prompt="A mountain landscape",
            model="gpt-4o",
            size="1792x1024",
            quality="hd",
            output_format="file",
            api_key="test_api_key",
            save_directory="./custom_images"
        )

        # Assertions
        assert result["success"] is True
        assert result["format"] == "file"
        assert "12345-abcde.png" in result["data"]
        assert result["metadata"]["model"] == "gpt-4o"
        assert result["metadata"]["size"] == "1792x1024"
        assert result["metadata"]["quality"] == "hd"

        # Verify client was called correctly
        mock_client_class.assert_called_once_with(
            api_key="test_api_key",
            base_url="https://api.openai.com/v1"
        )
        mock_client.generate_image.assert_called_once_with(
            prompt="A mountain landscape",
            model="gpt-4o",
            size="1792x1024",
            quality="hd"
        )

        # Verify handler was called correctly
        mock_handler_class.assert_called_once_with(save_directory="./custom_images")
        mock_handler.download_image.assert_called_once_with(
            url="https://example.com/generated.png",
            output_format="file",
            output_path=None
        )


@pytest.mark.asyncio
async def test_generate_image_tool_base64_format():
    """Test generate_image_tool with base64 output format."""
    with patch('src.tools.generate.OpenAIClient') as mock_client_class, \
         patch('src.tools.generate.ImageHandler') as mock_handler_class:

        # Setup mocks
        mock_client = Mock()
        mock_client.generate_image = AsyncMock(return_value="https://example.com/generated.png")
        mock_client_class.return_value = mock_client

        mock_handler = Mock()
        mock_handler.download_image = AsyncMock(return_value={
            "format": "base64",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        })
        mock_handler_class.return_value = mock_handler

        # Call the tool
        result = await generate_image_tool(
            prompt="A simple test image",
            output_format="base64",
            api_key="test_api_key"
        )

        # Assertions
        assert result["success"] is True
        assert result["format"] == "base64"
        assert result["data"].startswith("iVBORw0KGgo")
        assert result["metadata"]["model"] == "gpt-4o"


@pytest.mark.asyncio
async def test_generate_image_tool_with_custom_output_path():
    """Test generate_image_tool with custom output path."""
    with patch('src.tools.generate.OpenAIClient') as mock_client_class, \
         patch('src.tools.generate.ImageHandler') as mock_handler_class:

        # Setup mocks
        mock_client = Mock()
        mock_client.generate_image = AsyncMock(return_value="https://example.com/generated.png")
        mock_client_class.return_value = mock_client

        mock_handler = Mock()
        mock_handler.download_image = AsyncMock(return_value={
            "format": "file",
            "data": "./custom/path/my_image.png"
        })
        mock_handler_class.return_value = mock_handler

        # Call the tool
        result = await generate_image_tool(
            prompt="A custom image",
            output_format="file",
            output_path="./custom/path/my_image.png",
            api_key="test_api_key"
        )

        # Assertions
        assert result["success"] is True
        assert result["format"] == "file"
        assert result["data"] == "./custom/path/my_image.png"

        # Verify handler was called with custom output path
        mock_handler.download_image.assert_called_once_with(
            url="https://example.com/generated.png",
            output_format="file",
            output_path="./custom/path/my_image.png"
        )


@pytest.mark.asyncio
async def test_generate_image_tool_error_handling():
    """Test generate_image_tool error handling."""
    with patch('src.tools.generate.OpenAIClient') as mock_client_class:

        # Setup mock to raise an exception
        mock_client = Mock()
        mock_client.generate_image = AsyncMock(side_effect=Exception("API connection failed"))
        mock_client_class.return_value = mock_client

        # Call the tool
        result = await generate_image_tool(
            prompt="This will fail",
            api_key="test_api_key"
        )

        # Assertions
        assert result["success"] is False
        assert "error" in result
        assert "API connection failed" in result["error"]


@pytest.mark.asyncio
async def test_generate_image_tool_with_custom_base_url():
    """Test generate_image_tool with custom base URL."""
    with patch('src.tools.generate.OpenAIClient') as mock_client_class, \
         patch('src.tools.generate.ImageHandler') as mock_handler_class:

        # Setup mocks
        mock_client = Mock()
        mock_client.generate_image = AsyncMock(return_value="https://example.com/generated.png")
        mock_client_class.return_value = mock_client

        mock_handler = Mock()
        mock_handler.download_image = AsyncMock(return_value={
            "format": "url",
            "data": "https://example.com/generated.png"
        })
        mock_handler_class.return_value = mock_handler

        # Call the tool with custom base URL
        result = await generate_image_tool(
            prompt="Test with custom base URL",
            api_key="test_api_key",
            base_url="https://custom.api.com/v1"
        )

        # Assertions
        assert result["success"] is True

        # Verify client was initialized with custom base URL
        mock_client_class.assert_called_once_with(
            api_key="test_api_key",
            base_url="https://custom.api.com/v1"
        )


@pytest.mark.asyncio
async def test_generate_image_tool_empty_api_key():
    """Test generate_image_tool with empty API key."""
    # Call the tool with empty API key
    result = await generate_image_tool(
        prompt="This should fail",
        api_key=""
    )

    # Assertions
    assert result["success"] is False
    assert "error" in result
    assert "API key is required" in result["error"]


@pytest.mark.asyncio
async def test_edit_image_tool():
    """Test edit_image_tool with URL output format."""
    from src.tools.edit import edit_image_tool

    with patch('src.tools.edit.OpenAIClient') as mock_client_class, \
         patch('src.tools.edit.ImageHandler') as mock_handler_class:

        # Setup mocks
        mock_client = Mock()
        mock_client.edit_image = AsyncMock(return_value="https://example.com/edited.png")
        mock_client_class.return_value = mock_client

        mock_handler = Mock()
        mock_handler.download_image = AsyncMock(return_value={
            "format": "url",
            "data": "https://example.com/edited.png"
        })
        mock_handler_class.return_value = mock_handler

        # Call the tool
        result = await edit_image_tool(
            image_input="https://example.com/original.png",
            prompt="Make the sky blue",
            output_format="url",
            api_key="test_api_key"
        )

        # Assertions
        assert result["success"] is True
        assert result["format"] == "url"
        assert result["data"] == "https://example.com/edited.png"
        assert result["metadata"]["model"] == "gpt-4o"
        assert result["metadata"]["size"] == "1024x1024"
        assert result["metadata"]["quality"] == "standard"

        # Verify client was called correctly
        mock_client_class.assert_called_once_with(
            api_key="test_api_key",
            base_url="https://api.openai.com/v1"
        )
        mock_client.edit_image.assert_called_once_with(
            image_url="https://example.com/original.png",
            prompt="Make the sky blue",
            model="gpt-4o",
            size="1024x1024",
            quality="standard"
        )

        # Verify handler was called correctly
        mock_handler_class.assert_called_once_with(save_directory="./images")
        mock_handler.download_image.assert_called_once_with(
            url="https://example.com/edited.png",
            output_format="url",
            output_path=None
        )
