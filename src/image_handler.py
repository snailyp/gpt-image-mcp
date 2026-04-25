import logging
import base64
import uuid
from pathlib import Path
from typing import Literal, Optional
from urllib.parse import urlparse
import httpx


logger = logging.getLogger(__name__)


class ImageHandler:
    """Handles image downloading, format conversion, and saving."""

    def __init__(
        self,
        save_directory: str = "./images",
        download_retry: int = 3,
        cloudflare_uploader: Optional['CloudflareUploader'] = None,
        auto_upload_to_cloudflare: bool = True
    ):
        """
        Initialize the image handler.

        Args:
            save_directory: Directory to save images
            download_retry: Number of retry attempts for downloads
            cloudflare_uploader: Optional CloudflareUploader instance
            auto_upload_to_cloudflare: Whether to auto-upload to Cloudflare when output_format is url
        """
        self.save_directory = Path(save_directory)
        self.download_retry = download_retry
        self.cloudflare_uploader = cloudflare_uploader
        self.auto_upload_to_cloudflare = auto_upload_to_cloudflare
        self.save_directory.mkdir(parents=True, exist_ok=True)

    async def download_image(
        self,
        url: str,
        output_format: Literal["url", "file", "base64"] = "url",
        output_path: Optional[str] = None
    ) -> dict:
        """
        Download an image and return it in the specified format.

        Args:
            url: URL of the image to download
            output_format: Output format (url, file, or base64)
            output_path: Optional custom path for file output

        Returns:
            Dictionary with format and data keys
        """
        if output_format == "url":
            return {"format": "url", "data": url}

        # Fetch the image
        image_data = await self._fetch_image(url)

        if output_format == "file":
            file_path = await self._save_image(image_data, url, output_path)
            return {"format": "file", "data": str(file_path)}

        elif output_format == "base64":
            encoded = base64.b64encode(image_data).decode("utf-8")
            return {"format": "base64", "data": encoded}

    async def process_base64_image(
        self,
        base64_data: str,
        output_format: Literal["url", "file", "base64"] = "url",
        output_path: Optional[str] = None,
        filename: Optional[str] = None
    ) -> dict:
        """
        Process base64 image data and return in specified format.

        Args:
            base64_data: base64-encoded image data
            output_format: Output format (url, file, or base64)
            output_path: Optional custom path for file output
            filename: Filename for Cloudflare upload

        Returns:
            Dictionary with format and data keys
        """
        if output_format == "url":
            if self.cloudflare_uploader and self.auto_upload_to_cloudflare:
                # Upload to Cloudflare
                try:
                    url = await self.cloudflare_uploader.upload_base64(
                        base64_data,
                        filename or f"{uuid.uuid4()}.png"
                    )
                    logger.info(f"Successfully uploaded to Cloudflare: {url}")
                    return {"format": "url", "data": url}
                except (httpx.HTTPError, ValueError) as e:
                    logger.error(f"Failed to upload to Cloudflare: {e}")
                    logger.warning("Falling back to base64 format")
                    return {"format": "base64", "data": base64_data}
            else:
                logger.warning("Cloudflare uploader not configured, returning base64")
                return {"format": "base64", "data": base64_data}

        elif output_format == "file":
            # Decode base64 and save to file
            image_bytes = base64.b64decode(base64_data)
            file_path = await self._save_image(image_bytes, "image.png", output_path)
            return {"format": "file", "data": str(file_path)}

        elif output_format == "base64":
            return {"format": "base64", "data": base64_data}

    async def _fetch_image(self, url: str) -> bytes:
        """
        Fetch image from URL with retry logic.

        Args:
            url: URL to fetch

        Returns:
            Image data as bytes
        """
        last_error = None

        for attempt in range(self.download_retry):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=30.0)
                    response.raise_for_status()
                    logger.info(f"Successfully downloaded image from {url}")
                    return response.content
            except Exception as e:
                last_error = e
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")

        raise Exception(f"Failed to download image after {self.download_retry} attempts: {last_error}")

    async def _save_image(self, image_data: bytes, url: str, output_path: Optional[str] = None) -> Path:
        """
        Save image data to disk.

        Args:
            image_data: Image bytes to save
            url: Original URL (used to determine extension)
            output_path: Optional custom path for the output file

        Returns:
            Path to saved file
        """
        # If custom output path is provided, use it
        if output_path:
            file_path = Path(output_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Create directory if it doesn't exist
            self.save_directory.mkdir(parents=True, exist_ok=True)

            # Determine file extension from URL using urlparse
            parsed_url = urlparse(url)
            extension = Path(parsed_url.path).suffix or ".png"

            # Generate unique filename
            filename = f"{uuid.uuid4()}{extension}"
            file_path = self.save_directory / filename

        # Write file
        file_path.write_bytes(image_data)
        logger.info(f"Saved image to {file_path}")

        return file_path
