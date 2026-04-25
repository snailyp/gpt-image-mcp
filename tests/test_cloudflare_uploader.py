import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.cloudflare_uploader import CloudflareUploader


@pytest.mark.asyncio
async def test_upload_base64_success():
    """Test successful upload to Cloudflare."""
    uploader = CloudflareUploader(
        auth_code="test_auth",
        api_url="https://api.test.com/upload",
        upload_folder="test_folder"
    )

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = [{"src": "/images/test.png"}]
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = await uploader.upload_base64("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==", "test.png")

        assert result == "https://api.test.com/images/test.png"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_upload_base64_with_full_url():
    """Test upload when API returns full URL."""
    uploader = CloudflareUploader(
        auth_code="test_auth",
        api_url="https://api.test.com/upload"
    )

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = [{"src": "https://cdn.test.com/images/test.png"}]
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = await uploader.upload_base64("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==", "test.png")

        assert result == "https://cdn.test.com/images/test.png"
