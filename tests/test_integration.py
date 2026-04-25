"""Integration tests for full end-to-end workflows."""

import pytest
import os
from unittest.mock import patch, Mock, AsyncMock
from src.config import load_config
from src.tools.generate import generate_image_tool
from src.tools.edit import edit_image_tool
from src.tools.info import get_server_info_tool


@pytest.mark.asyncio
async def test_full_generate_workflow():
    """
    Test complete image generation workflow:
    1. Load config from environment
    2. Execute generate_image_tool
    3. Verify complete data flow through all layers
    4. Check result includes all expected fields
    """
    # Setup: Load config from environment
    os.environ["OPENAI__API_KEY"] = "test-integration-key"
    os.environ["IMAGE__DEFAULT_SIZE"] = "1024x1024"
    os.environ["IMAGE__DEFAULT_OUTPUT_FORMAT"] = "url"

    try:
        config = load_config()

        # Verify config loaded correctly
        assert config.openai.api_key == "test-integration-key"
        assert config.image.default_size == "1024x1024"
        assert config.image.default_output_format == "url"

        # Mock external dependencies
        with patch('src.tools.common.OpenAIClient') as mock_client_class, \
             patch('src.tools.common.ImageHandler') as mock_handler_class:

            # Setup OpenAI client mock
            mock_client = Mock()
            mock_client.generate_image = AsyncMock(return_value="https://example.com/generated-image.png")
            mock_client_class.return_value = mock_client

            # Setup ImageHandler mock
            mock_handler = Mock()
            mock_handler.download_image = AsyncMock(return_value={
                "format": "url",
                "data": "https://example.com/generated-image.png"
            })
            mock_handler_class.return_value = mock_handler

            # Execute: Call generate_image_tool with config values
            result = await generate_image_tool(
                prompt="a beautiful sunset over mountains",
                model=config.openai.default_model,
                size=config.image.default_size,
                quality=config.image.default_quality,
                output_format=config.image.default_output_format,
                api_key=config.openai.api_key,
                base_url=config.openai.base_url,
                save_directory=config.image.save_directory
            )

            # Verify: Check complete result structure
            assert result["success"] is True
            assert result["format"] == "url"
            assert result["data"] == "https://example.com/generated-image.png"
            assert "metadata" in result
            assert result["metadata"]["model"] == config.openai.default_model
            assert result["metadata"]["size"] == config.image.default_size
            assert result["metadata"]["quality"] == config.image.default_quality

            # Verify: Check that all layers were called correctly
            mock_client_class.assert_called_once_with(
                api_key=config.openai.api_key,
                base_url=config.openai.base_url
            )
            mock_client.generate_image.assert_called_once_with(
                prompt="a beautiful sunset over mountains",
                model=config.openai.default_model,
                size=config.image.default_size,
                quality=config.image.default_quality
            )
            mock_handler_class.assert_called_once_with(save_directory=config.image.save_directory)
            mock_handler.download_image.assert_called_once_with(
                url="https://example.com/generated-image.png",
                output_format=config.image.default_output_format,
                output_path=None
            )
    finally:
        # Cleanup environment
        del os.environ["OPENAI__API_KEY"]
        del os.environ["IMAGE__DEFAULT_SIZE"]
        del os.environ["IMAGE__DEFAULT_OUTPUT_FORMAT"]


@pytest.mark.asyncio
async def test_full_edit_workflow():
    """
    Test complete image editing workflow:
    1. Load config from environment
    2. Execute edit_image_tool
    3. Verify complete data flow through all layers
    4. Check result includes all expected fields
    """
    # Setup: Load config from environment
    os.environ["OPENAI__API_KEY"] = "test-edit-key"
    os.environ["IMAGE__DEFAULT_QUALITY"] = "hd"
    os.environ["IMAGE__SAVE_DIRECTORY"] = "./test_images"

    try:
        config = load_config()

        # Verify config loaded correctly
        assert config.openai.api_key == "test-edit-key"
        assert config.image.default_quality == "hd"
        assert config.image.save_directory == "./test_images"

        # Mock external dependencies
        with patch('src.tools.common.OpenAIClient') as mock_client_class, \
             patch('src.tools.common.ImageHandler') as mock_handler_class:

            # Setup OpenAI client mock
            mock_client = Mock()
            mock_client.edit_image = AsyncMock(return_value="https://example.com/edited-image.png")
            mock_client_class.return_value = mock_client

            # Setup ImageHandler mock
            mock_handler = Mock()
            mock_handler.download_image = AsyncMock(return_value={
                "format": "file",
                "data": "./test_images/edited-12345.png"
            })
            mock_handler_class.return_value = mock_handler

            # Execute: Call edit_image_tool with config values
            result = await edit_image_tool(
                image_input="https://example.com/original.png",
                prompt="make the sky more dramatic",
                model=config.openai.default_model,
                size=config.image.default_size,
                quality=config.image.default_quality,
                output_format="file",
                api_key=config.openai.api_key,
                base_url=config.openai.base_url,
                save_directory=config.image.save_directory
            )

            # Verify: Check complete result structure
            assert result["success"] is True
            assert result["format"] == "file"
            assert "edited-12345.png" in result["data"]
            assert "metadata" in result
            assert result["metadata"]["model"] == config.openai.default_model
            assert result["metadata"]["size"] == config.image.default_size
            assert result["metadata"]["quality"] == "hd"

            # Verify: Check that all layers were called correctly
            mock_client_class.assert_called_once_with(
                api_key=config.openai.api_key,
                base_url=config.openai.base_url
            )
            mock_client.edit_image.assert_called_once_with(
                image_url="https://example.com/original.png",
                prompt="make the sky more dramatic",
                model=config.openai.default_model,
                size=config.image.default_size,
                quality="hd"
            )
            mock_handler_class.assert_called_once_with(save_directory="./test_images")
            mock_handler.download_image.assert_called_once_with(
                url="https://example.com/edited-image.png",
                output_format="file",
                output_path=None
            )
    finally:
        # Cleanup environment
        del os.environ["OPENAI__API_KEY"]
        del os.environ["IMAGE__DEFAULT_QUALITY"]
        del os.environ["IMAGE__SAVE_DIRECTORY"]


def test_server_info_workflow():
    """
    Test server info retrieval workflow:
    1. Load config from environment
    2. Execute get_server_info_tool
    3. Verify all server metadata is returned correctly
    """
    # Setup: Load config from environment
    os.environ["SERVER__NAME"] = "test-mcp-server"
    os.environ["SERVER__VERSION"] = "2.0.0"
    os.environ["SERVER__TRANSPORT"] = "http"
    os.environ["OPENAI__DEFAULT_MODEL"] = "gpt-4-turbo"
    os.environ["IMAGE__DEFAULT_SIZE"] = "512x512"

    try:
        config = load_config()

        # Verify config loaded correctly
        assert config.server.name == "test-mcp-server"
        assert config.server.version == "2.0.0"
        assert config.server.transport == "http"
        assert config.openai.default_model == "gpt-4-turbo"
        assert config.image.default_size == "512x512"

        # Execute: Call get_server_info_tool with config values
        result = get_server_info_tool(
            server_name=config.server.name,
            server_version=config.server.version,
            transport=config.server.transport,
            default_model=config.openai.default_model,
            default_size=config.image.default_size
        )

        # Verify: Check all expected fields are present
        assert "name" in result
        assert "version" in result
        assert "transport" in result
        assert "supported_models" in result
        assert "supported_formats" in result
        assert "config" in result

        # Verify: Check values match config
        assert result["name"] == "test-mcp-server"
        assert result["version"] == "2.0.0"
        assert result["transport"] == "http"
        assert result["config"]["default_model"] == "gpt-4-turbo"
        assert result["config"]["default_size"] == "512x512"

        # Verify: Check supported capabilities
        assert "gpt-4o" in result["supported_models"]
        assert "gpt-4-turbo" in result["supported_models"]
        assert "url" in result["supported_formats"]
        assert "file" in result["supported_formats"]
        assert "base64" in result["supported_formats"]
    finally:
        # Cleanup environment
        del os.environ["SERVER__NAME"]
        del os.environ["SERVER__VERSION"]
        del os.environ["SERVER__TRANSPORT"]
        del os.environ["OPENAI__DEFAULT_MODEL"]
        del os.environ["IMAGE__DEFAULT_SIZE"]


@pytest.mark.asyncio
async def test_full_workflow_with_base64_output():
    """
    Test complete workflow with base64 output format:
    1. Load config
    2. Generate image
    3. Convert to base64
    4. Verify base64 data is returned
    """
    os.environ["OPENAI__API_KEY"] = "test-base64-key"

    try:
        config = load_config()

        with patch('src.tools.common.OpenAIClient') as mock_client_class, \
             patch('src.tools.common.ImageHandler') as mock_handler_class:

            mock_client = Mock()
            mock_client.generate_image = AsyncMock(return_value="https://example.com/image.png")
            mock_client_class.return_value = mock_client

            mock_handler = Mock()
            mock_handler.download_image = AsyncMock(return_value={
                "format": "base64",
                "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            })
            mock_handler_class.return_value = mock_handler

            result = await generate_image_tool(
                prompt="test image",
                output_format="base64",
                api_key=config.openai.api_key
            )

            assert result["success"] is True
            assert result["format"] == "base64"
            assert result["data"].startswith("iVBORw0KGgo")
            assert len(result["data"]) > 0
    finally:
        del os.environ["OPENAI__API_KEY"]


@pytest.mark.asyncio
async def test_full_workflow_error_handling():
    """
    Test error handling across the full workflow:
    1. Load config
    2. Simulate API failure
    3. Verify error is properly propagated and formatted
    """
    os.environ["OPENAI__API_KEY"] = "test-error-key"

    try:
        config = load_config()

        with patch('src.tools.common.OpenAIClient') as mock_client_class:

            mock_client = Mock()
            mock_client.generate_image = AsyncMock(side_effect=Exception("OpenAI API rate limit exceeded"))
            mock_client_class.return_value = mock_client

            result = await generate_image_tool(
                prompt="this will fail",
                api_key=config.openai.api_key
            )

            # Verify error is properly handled
            assert result["success"] is False
            assert "error" in result
            assert "OpenAI API rate limit exceeded" in result["error"]
            assert "format" not in result
            assert "data" not in result
    finally:
        del os.environ["OPENAI__API_KEY"]


@pytest.mark.asyncio
async def test_full_workflow_with_custom_output_path():
    """
    Test complete workflow with custom output path:
    1. Load config
    2. Generate image with custom output path
    3. Verify file is saved to specified location
    """
    os.environ["OPENAI__API_KEY"] = "test-custom-path-key"

    try:
        config = load_config()
        custom_path = "./custom/output/my_image.png"

        with patch('src.tools.common.OpenAIClient') as mock_client_class, \
             patch('src.tools.common.ImageHandler') as mock_handler_class:

            mock_client = Mock()
            mock_client.generate_image = AsyncMock(return_value="https://example.com/image.png")
            mock_client_class.return_value = mock_client

            mock_handler = Mock()
            mock_handler.download_image = AsyncMock(return_value={
                "format": "file",
                "data": custom_path
            })
            mock_handler_class.return_value = mock_handler

            result = await generate_image_tool(
                prompt="custom path test",
                output_format="file",
                output_path=custom_path,
                api_key=config.openai.api_key
            )

            assert result["success"] is True
            assert result["format"] == "file"
            assert result["data"] == custom_path

            # Verify handler was called with custom path
            mock_handler.download_image.assert_called_once_with(
                url="https://example.com/image.png",
                output_format="file",
                output_path=custom_path
            )
    finally:
        del os.environ["OPENAI__API_KEY"]
