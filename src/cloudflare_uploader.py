import base64
import logging
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)


class CloudflareUploader:
    """Cloudflare图床上传器"""

    def __init__(self, auth_code: str, api_url: str, upload_folder: str = ""):
        """
        初始化Cloudflare上传器

        Args:
            auth_code: 认证码
            api_url: API地址
            upload_folder: 上传文件夹路径（可选）
        """
        self.auth_code = auth_code
        self.api_url = api_url
        self.upload_folder = upload_folder

    async def upload_base64(self, base64_data: str, filename: str) -> str:
        """
        上传base64图片到Cloudflare

        Args:
            base64_data: base64编码的图片数据
            filename: 文件名

        Returns:
            图片URL

        Raises:
            Exception: 上传失败时抛出异常
        """
        try:
            # 解码base64为bytes
            image_bytes = base64.b64decode(base64_data)

            # 构造请求URL和参数
            params = {"authCode": self.auth_code, "uploadNameType": "origin"}
            if self.upload_folder:
                params["uploadFolder"] = self.upload_folder

            # 准备文件数据
            files = {"file": (filename, image_bytes, "image/png")}

            # 发送POST请求
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url, params=params, files=files, timeout=30.0
                )
                response.raise_for_status()

            # 解析响应
            result = response.json()
            if not isinstance(result, list) or len(result) == 0:
                raise ValueError("Invalid response format from Cloudflare")

            src = result[0].get("src")
            if not src:
                raise ValueError("No 'src' field in response")

            # 如果是相对路径，拼接完整URL
            if not src.startswith("http"):
                parsed_api_url = urlparse(self.api_url)
                base_url = f"{parsed_api_url.scheme}://{parsed_api_url.netloc}"
                full_url = urljoin(base_url, src)
                logger.info(f"Successfully uploaded image to Cloudflare: {full_url}")
                return full_url

            logger.info(f"Successfully uploaded image to Cloudflare: {src}")
            return src

        except httpx.HTTPError as e:
            logger.error(f"HTTP error uploading to Cloudflare: {e}")
            raise Exception(f"Failed to upload to Cloudflare: {e}") from e
        except Exception as e:
            logger.error(f"Error uploading to Cloudflare: {e}")
            raise Exception(f"Failed to upload to Cloudflare: {e}") from e
