import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.openai_client import OpenAIClient
from io import BytesIO
from PIL import Image
import openai


@pytest.mark.asyncio
async def test_download_image_success():
    """Test successful image download from URL."""
    client = OpenAIClient(api_key="test-key")

    mock_response = MagicMock()
    mock_response.content = b"fake_image_data"
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await client._download_image("https://example.com/image.png")

        assert result == b"fake_image_data"
        mock_client.get.assert_called_once_with("https://example.com/image.png", timeout=30.0)


def test_ensure_png_format_already_png():
    """Test PNG conversion when image is already PNG."""
    client = OpenAIClient(api_key="test-key")

    # Create a PNG image in memory
    img = Image.new('RGB', (100, 100), color='red')
    png_buffer = BytesIO()
    img.save(png_buffer, format='PNG')
    png_bytes = png_buffer.getvalue()

    result = client._ensure_png_format(png_bytes)

    # Verify it's still valid PNG
    result_img = Image.open(BytesIO(result))
    assert result_img.format == 'PNG'
    assert result_img.size == (100, 100)


def test_ensure_png_format_convert_jpeg():
    """Test PNG conversion from JPEG."""
    client = OpenAIClient(api_key="test-key")

    # Create a JPEG image in memory
    img = Image.new('RGB', (100, 100), color='blue')
    jpeg_buffer = BytesIO()
    img.save(jpeg_buffer, format='JPEG')
    jpeg_bytes = jpeg_buffer.getvalue()

    result = client._ensure_png_format(jpeg_bytes)

    # Verify it's converted to PNG
    result_img = Image.open(BytesIO(result))
    assert result_img.format == 'PNG'
    assert result_img.size == (100, 100)


@pytest.mark.asyncio
async def test_generate_image_with_images_api():
    """Test image generation using Images API."""
    client = OpenAIClient(api_key="test-key")

    # Mock the Images API response
    mock_response = MagicMock()
    mock_data = MagicMock()
    mock_data.b64_json = "fake_base64_image_data"
    mock_response.data = [mock_data]

    client.client.images.generate = AsyncMock(return_value=mock_response)

    result = await client.generate_image(
        prompt="a sunset",
        model="dall-e-3",
        size="1024x1024",
        quality="standard"
    )

    assert result == "fake_base64_image_data"
    client.client.images.generate.assert_called_once_with(
        prompt="a sunset",
        model="dall-e-3",
        size="1024x1024",
        quality="standard",
        response_format="b64_json"
    )


@pytest.mark.asyncio
async def test_generate_image_api_error():
    """Test error handling when API fails."""
    client = OpenAIClient(api_key="test-key")

    # Create a proper APIError with required request parameter
    mock_request = MagicMock()
    api_error = openai.APIError("API error", request=mock_request, body=None)

    client.client.images.generate = AsyncMock(
        side_effect=api_error
    )

    with pytest.raises(openai.APIError):
        await client.generate_image(prompt="test")
