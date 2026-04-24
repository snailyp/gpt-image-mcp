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
