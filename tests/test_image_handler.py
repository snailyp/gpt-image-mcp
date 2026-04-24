import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from src.image_handler import ImageHandler


@pytest.mark.asyncio
async def test_download_image_to_file():
    handler = ImageHandler(save_directory="./test_images", download_retry=3)

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = await handler.download_image("https://example.com/image.png", output_format="file")

        assert result["format"] == "file"
        assert "test_images" in result["data"]


@pytest.mark.asyncio
async def test_download_image_to_base64():
    handler = ImageHandler(save_directory="./test_images", download_retry=3)

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = await handler.download_image("https://example.com/image.png", output_format="base64")

        assert result["format"] == "base64"
        assert result["data"] == "ZmFrZV9pbWFnZV9kYXRh"  # base64 of "fake_image_data"


@pytest.mark.asyncio
async def test_download_retry_mechanism():
    handler = ImageHandler(save_directory="./test_images", download_retry=3)

    with patch('httpx.AsyncClient.get') as mock_get:
        # First two attempts fail, third succeeds
        mock_get.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            Mock(content=b"fake_image_data", status_code=200)
        ]

        result = await handler.download_image("https://example.com/image.png", output_format="base64")

        assert result["format"] == "base64"
        assert result["data"] == "ZmFrZV9pbWFnZV9kYXRh"
        assert mock_get.call_count == 3


@pytest.mark.asyncio
async def test_download_retry_exhausted():
    handler = ImageHandler(save_directory="./test_images", download_retry=3)

    with patch('httpx.AsyncClient.get') as mock_get:
        # All attempts fail
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Failed to download image after 3 attempts"):
            await handler.download_image("https://example.com/image.png", output_format="base64")


@pytest.mark.asyncio
async def test_url_format_passthrough():
    handler = ImageHandler(save_directory="./test_images", download_retry=3)

    result = await handler.download_image("https://example.com/image.png", output_format="url")

    assert result["format"] == "url"
    assert result["data"] == "https://example.com/image.png"


@pytest.mark.asyncio
async def test_directory_creation():
    handler = ImageHandler(save_directory="./test_images/nested/path", download_retry=3)

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = await handler.download_image("https://example.com/image.png", output_format="file")

        assert result["format"] == "file"
        # Use Path to normalize path separators for cross-platform compatibility
        assert "test_images" in result["data"] and "nested" in result["data"] and "path" in result["data"]
        # Verify directory was created
        assert Path("./test_images/nested/path").exists()


@pytest.mark.asyncio
async def test_url_with_query_parameters():
    handler = ImageHandler(save_directory="./test_images", download_retry=3)

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = await handler.download_image(
            "https://example.com/image.jpg?size=large&format=jpeg",
            output_format="file"
        )

        assert result["format"] == "file"
        # Verify the file has .jpg extension despite query parameters
        assert result["data"].endswith(".jpg")


@pytest.mark.asyncio
async def test_custom_output_path():
    handler = ImageHandler(save_directory="./test_images", download_retry=3)

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        custom_path = "./test_images/custom_image.png"
        result = await handler.download_image(
            "https://example.com/image.png",
            output_format="file",
            output_path=custom_path
        )

        assert result["format"] == "file"
        # Normalize paths for cross-platform comparison
        assert Path(result["data"]) == Path(custom_path)
        assert Path(custom_path).exists()

