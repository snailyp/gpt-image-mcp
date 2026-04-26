import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.openai_client import OpenAIClient


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
