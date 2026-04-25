# Cloudflare图床上传功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 添加Cloudflare图床上传功能，使图片生成和编辑返回Cloudflare托管的URL而不是base64数据

**Architecture:** 创建CloudflareUploader类处理上传，扩展ImageHandler支持base64处理，通过配置控制是否启用Cloudflare上传，保持向后兼容

**Tech Stack:** Python 3.11+, httpx (异步HTTP), pydantic (配置管理), pytest (测试)

---

## 文件结构

**新建文件:**
- `src/cloudflare_uploader.py` - Cloudflare图床上传器
- `tests/test_cloudflare_uploader.py` - 上传器单元测试

**修改文件:**
- `src/config.py` - 添加CloudflareConfig配置类
- `src/image_handler.py` - 添加process_base64_image方法
- `src/tools/common.py` - 更新process_image_request支持Cloudflare
- `src/tools/generate.py` - 传递Cloudflare配置
- `src/tools/edit.py` - 传递Cloudflare配置
- `tests/test_image_handler.py` - 添加base64处理测试
- `tests/test_tools.py` - 更新工具测试
- `.env.example` - 添加Cloudflare配置示例
- `README.md` - 添加Cloudflare配置文档

---

### Task 1: 添加Cloudflare配置类

**Files:**
- Modify: `src/config.py:1-155`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py - 在文件末尾添加
def test_cloudflare_config_from_env(monkeypatch):
    """Test CloudflareConfig loads from environment variables."""
    monkeypatch.setenv("CLOUDFLARE__AUTH_CODE", "test_auth_code")
    monkeypatch.setenv("CLOUDFLARE__API_URL", "https://test.api.com")
    monkeypatch.setenv("CLOUDFLARE__UPLOAD_FOLDER", "test_folder")
    
    config = load_config()
    
    assert config.cloudflare.auth_code == "test_auth_code"
    assert config.cloudflare.api_url == "https://test.api.com"
    assert config.cloudflare.upload_folder == "test_folder"


def test_image_config_auto_upload_flag(monkeypatch):
    """Test ImageConfig auto_upload_to_cloudflare flag."""
    monkeypatch.setenv("IMAGE__AUTO_UPLOAD_TO_CLOUDFLARE", "false")
    
    config = load_config()
    
    assert config.image.auto_upload_to_cloudflare is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_cloudflare_config_from_env -v`
Expected: FAIL with "AttributeError: 'Config' object has no attribute 'cloudflare'"

- [ ] **Step 3: Add CloudflareConfig class**

```python
# src/config.py - 在ImageConfig类之后添加
class CloudflareConfig(BaseModel):
    """Cloudflare Images configuration."""
    auth_code: str = Field(default="")
    api_url: str = Field(default="")
    upload_folder: str = Field(default="")
```

- [ ] **Step 4: Update ImageConfig with auto_upload flag**

```python
# src/config.py - 修改ImageConfig类
class ImageConfig(BaseModel):
    """Image generation configuration."""
    default_size: str = Field(default="1024x1024")
    default_quality: str = Field(default="standard")
    default_output_format: str = Field(default="url")
    save_directory: str = Field(default="./images")
    download_retry: int = Field(default=3)
    auto_upload_to_cloudflare: bool = Field(default=True)
```

- [ ] **Step 5: Add cloudflare field to Config class**

```python
# src/config.py - 修改Config类
class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore'
    )

    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    image: ImageConfig = Field(default_factory=ImageConfig)
    cloudflare: CloudflareConfig = Field(default_factory=CloudflareConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    http: HTTPConfig = Field(default_factory=HTTPConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
```

// __CONTINUE_HERE__

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_config.py::test_cloudflare_config_from_env tests/test_config.py::test_image_config_auto_upload_flag -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/config.py tests/test_config.py
git commit -m "feat: add Cloudflare configuration support"
```

---

### Task 2: 实现CloudflareUploader类

**Files:**
- Create: `src/cloudflare_uploader.py`
- Create: `tests/test_cloudflare_uploader.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cloudflare_uploader.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cloudflare_uploader.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.cloudflare_uploader'"

- [ ] **Step 3: Implement CloudflareUploader class**

```python
# src/cloudflare_uploader.py
import logging
import base64
import httpx
from typing import Optional
from urllib.parse import urljoin, urlparse


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
            params = {
                "authCode": self.auth_code,
                "uploadNameType": "origin"
            }
            if self.upload_folder:
                params["uploadFolder"] = self.upload_folder
            
            # 准备文件数据
            files = {"file": (filename, image_bytes, "image/png")}
            
            # 发送POST请求
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    params=params,
                    files=files,
                    timeout=30.0
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cloudflare_uploader.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/cloudflare_uploader.py tests/test_cloudflare_uploader.py
git commit -m "feat: implement CloudflareUploader for image uploads"
```

---

### Task 3: 扩展ImageHandler支持base64处理

**Files:**
- Modify: `src/image_handler.py:1-117`
- Modify: `tests/test_image_handler.py:1-50`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_image_handler.py - 在文件末尾添加
@pytest.mark.asyncio
async def test_process_base64_image_to_url_with_cloudflare():
    """Test processing base64 to URL with Cloudflare uploader."""
    mock_uploader = Mock()
    mock_uploader.upload_base64 = AsyncMock(return_value="https://cdn.test.com/image.png")
    
    handler = ImageHandler(
        save_directory="./test_images",
        cloudflare_uploader=mock_uploader,
        auto_upload_to_cloudflare=True
    )
    
    result = await handler.process_base64_image(
        base64_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        output_format="url",
        filename="test.png"
    )
    
    assert result["format"] == "url"
    assert result["data"] == "https://cdn.test.com/image.png"
    mock_uploader.upload_base64.assert_called_once()


@pytest.mark.asyncio
async def test_process_base64_image_to_url_without_cloudflare():
    """Test processing base64 to URL without Cloudflare falls back to base64."""
    handler = ImageHandler(
        save_directory="./test_images",
        cloudflare_uploader=None,
        auto_upload_to_cloudflare=True
    )
    
    result = await handler.process_base64_image(
        base64_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        output_format="url"
    )
    
    assert result["format"] == "base64"
    assert result["data"] == "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


@pytest.mark.asyncio
async def test_process_base64_image_to_file():
    """Test processing base64 to file."""
    handler = ImageHandler(save_directory="./test_images")
    
    result = await handler.process_base64_image(
        base64_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        output_format="file"
    )
    
    assert result["format"] == "file"
    assert "test_images" in result["data"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_image_handler.py::test_process_base64_image_to_url_with_cloudflare -v`
Expected: FAIL with "AttributeError: 'ImageHandler' object has no attribute 'process_base64_image'"

- [ ] **Step 3: Update ImageHandler __init__ to accept cloudflare_uploader**

```python
# src/image_handler.py - 修改__init__方法
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
```

- [ ] **Step 4: Add process_base64_image method**

```python
# src/image_handler.py - 在download_image方法之后添加
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
            except Exception as e:
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_image_handler.py::test_process_base64_image_to_url_with_cloudflare tests/test_image_handler.py::test_process_base64_image_to_url_without_cloudflare tests/test_image_handler.py::test_process_base64_image_to_file -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/image_handler.py tests/test_image_handler.py
git commit -m "feat: add base64 image processing to ImageHandler"
```

---

### Task 4: 更新process_image_request支持Cloudflare

**Files:**
- Modify: `src/tools/common.py:1-92`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tools.py - 在文件末尾添加
@pytest.mark.asyncio
async def test_process_image_request_with_cloudflare():
    """Test process_image_request with Cloudflare configuration."""
    from src.tools.common import process_image_request
    from src.config import CloudflareConfig
    
    cloudflare_config = CloudflareConfig(
        auth_code="test_auth",
        api_url="https://api.test.com/upload",
        upload_folder="test_folder"
    )
    
    with patch('src.tools.common.OpenAIClient') as mock_client_class, \
         patch('src.tools.common.CloudflareUploader') as mock_uploader_class, \
         patch('src.tools.common.ImageHandler') as mock_handler_class:
        
        # Setup mocks
        mock_client = Mock()
        mock_client.generate_image = AsyncMock(return_value="base64_image_data")
        mock_client_class.return_value = mock_client
        
        mock_uploader = Mock()
        mock_uploader_class.return_value = mock_uploader
        
        mock_handler = Mock()
        mock_handler.process_base64_image = AsyncMock(return_value={
            "format": "url",
            "data": "https://cdn.test.com/image.png"
        })
        mock_handler_class.return_value = mock_handler
        
        # Call function
        async def api_call(client):
            return await client.generate_image(prompt="test")
        
        result = await process_image_request(
            api_key="test_key",
            base_url="https://api.openai.com/v1",
            save_directory="./images",
            output_format="url",
            output_path=None,
            model="gpt-4o",
            size="1024x1024",
            quality="standard",
            api_call=api_call,
            operation_name="Generating",
            cloudflare_config=cloudflare_config,
            auto_upload_to_cloudflare=True
        )
        
        # Assertions
        assert result["success"] is True
        assert result["data"] == "https://cdn.test.com/image.png"
        mock_uploader_class.assert_called_once_with(
            auth_code="test_auth",
            api_url="https://api.test.com/upload",
            upload_folder="test_folder"
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py::test_process_image_request_with_cloudflare -v`
Expected: FAIL with "TypeError: process_image_request() got an unexpected keyword argument 'cloudflare_config'"

- [ ] **Step 3: Update process_image_request function signature**

```python
# src/tools/common.py - 修改函数签名
async def process_image_request(
    api_key: str,
    base_url: str,
    save_directory: str,
    output_format: Literal["url", "file", "base64"],
    output_path: Optional[str],
    model: str,
    size: str,
    quality: str,
    api_call: Callable[[OpenAIClient], Awaitable[str]],
    operation_name: str,
    cloudflare_config: Optional[Any] = None,
    auto_upload_to_cloudflare: bool = True
) -> Dict[str, Any]:
```

- [ ] **Step 4: Update process_image_request implementation**

```python
# src/tools/common.py - 替换整个函数体
async def process_image_request(
    api_key: str,
    base_url: str,
    save_directory: str,
    output_format: Literal["url", "file", "base64"],
    output_path: Optional[str],
    model: str,
    size: str,
    quality: str,
    api_call: Callable[[OpenAIClient], Awaitable[str]],
    operation_name: str,
    cloudflare_config: Optional[Any] = None,
    auto_upload_to_cloudflare: bool = True
) -> Dict[str, Any]:
    """
    Common helper function for processing image generation and editing requests.

    Args:
        api_key: OpenAI API key
        base_url: Base URL for OpenAI API
        save_directory: Directory to save images
        output_format: Output format - "url", "file", or "base64"
        output_path: Optional custom path for file output
        model: Model to use
        size: Image size
        quality: Image quality
        api_call: Async callback function that takes OpenAIClient and returns base64 image data
        operation_name: Name of the operation for logging (e.g., "Generating", "Editing")
        cloudflare_config: Optional CloudflareConfig for image upload
        auto_upload_to_cloudflare: Whether to auto-upload to Cloudflare when output_format is url

    Returns:
        Dictionary with:
            - success: bool indicating if operation succeeded
            - format: output format used
            - data: the image data (URL, file path, or base64 string)
            - metadata: dict with model, size, quality
            - error: error message if success is False
    """
    # Validate API key
    if not api_key:
        logger.error("API key is required")
        return {"success": False, "error": "API key is required"}

    try:
        logger.info(f"{operation_name} image...")
        logger.debug(f"Parameters: model={model}, size={size}, quality={quality}, output_format={output_format}")

        # Create OpenAI client
        client = OpenAIClient(api_key=api_key, base_url=base_url)

        # Call the API (generate or edit) - returns base64 data
        base64_data = await api_call(client)

        logger.info(f"Image {operation_name.lower()} successfully, processing output format")

        # Create Cloudflare uploader if configured
        cloudflare_uploader = None
        if cloudflare_config and cloudflare_config.auth_code and cloudflare_config.api_url:
            from src.cloudflare_uploader import CloudflareUploader
            cloudflare_uploader = CloudflareUploader(
                auth_code=cloudflare_config.auth_code,
                api_url=cloudflare_config.api_url,
                upload_folder=cloudflare_config.upload_folder
            )
            logger.debug("Cloudflare uploader configured")

        # Create ImageHandler to process output format
        handler = ImageHandler(
            save_directory=save_directory,
            cloudflare_uploader=cloudflare_uploader,
            auto_upload_to_cloudflare=auto_upload_to_cloudflare
        )

        # Process base64 data to requested format
        import uuid
        result = await handler.process_base64_image(
            base64_data=base64_data,
            output_format=output_format,
            output_path=output_path,
            filename=f"{operation_name.lower()}_{uuid.uuid4()}.png"
        )

        logger.info(f"Image processed to {result['format']} format successfully")

        # Return success response with metadata
        return {
            "success": True,
            "format": result["format"],
            "data": result["data"],
            "metadata": {
                "model": model,
                "size": size,
                "quality": quality
            }
        }

    except (ValueError, Exception) as e:
        logger.error(f"Error {operation_name.lower()} image: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_tools.py::test_process_image_request_with_cloudflare -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/tools/common.py tests/test_tools.py
git commit -m "feat: add Cloudflare support to process_image_request"
```

---

### Task 5: 更新generate_image_tool传递Cloudflare配置

**Files:**
- Modify: `src/tools/generate.py:1-64`

- [ ] **Step 1: Update generate_image_tool to accept Cloudflare parameters**

```python
# src/tools/generate.py - 替换整个函数
async def generate_image_tool(
    prompt: str,
    model: str = "gpt-4o",
    size: str = "1024x1024",
    quality: str = "standard",
    output_format: Literal["url", "file", "base64"] = "url",
    output_path: Optional[str] = None,
    api_key: str = "",
    base_url: str = "https://api.openai.com/v1",
    save_directory: str = "./images",
    cloudflare_auth_code: str = "",
    cloudflare_api_url: str = "",
    cloudflare_upload_folder: str = "",
    auto_upload_to_cloudflare: bool = True
) -> Dict[str, Any]:
    """
    Generate an image using OpenAI API and return it in the specified format.

    Args:
        prompt: Text description of the image to generate
        model: Model to use for generation (default: "gpt-4o")
        size: Image size (default: "1024x1024")
        quality: Image quality "standard" or "hd" (default: "standard")
        output_format: Output format - "url", "file", or "base64" (default: "url")
        output_path: Optional custom path for file output
        api_key: OpenAI API key
        base_url: Base URL for OpenAI API (default: "https://api.openai.com/v1")
        save_directory: Directory to save images (default: "./images")
        cloudflare_auth_code: Cloudflare authentication code
        cloudflare_api_url: Cloudflare API URL
        cloudflare_upload_folder: Cloudflare upload folder
        auto_upload_to_cloudflare: Whether to auto-upload to Cloudflare when output_format is url

    Returns:
        Dictionary with:
            - success: bool indicating if operation succeeded
            - format: output format used
            - data: the image data (URL, file path, or base64 string)
            - metadata: dict with model, size, quality
            - error: error message if success is False
    """
    logger.info(f"Generating image with prompt: {prompt[:50]}...")

    # Construct CloudflareConfig if credentials provided
    cloudflare_config = None
    if cloudflare_auth_code and cloudflare_api_url:
        from src.config import CloudflareConfig
        cloudflare_config = CloudflareConfig(
            auth_code=cloudflare_auth_code,
            api_url=cloudflare_api_url,
            upload_folder=cloudflare_upload_folder
        )

    async def api_call(client):
        return await client.generate_image(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality
        )

    return await process_image_request(
        api_key=api_key,
        base_url=base_url,
        save_directory=save_directory,
        output_format=output_format,
        output_path=output_path,
        model=model,
        size=size,
        quality=quality,
        api_call=api_call,
        operation_name="Generating",
        cloudflare_config=cloudflare_config,
        auto_upload_to_cloudflare=auto_upload_to_cloudflare
    )
```

- [ ] **Step 2: Run existing tests to verify backward compatibility**

Run: `pytest tests/test_tools.py::test_generate_image_tool_url_format -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/tools/generate.py
git commit -m "feat: add Cloudflare parameters to generate_image_tool"
```

---

### Task 6: 更新edit_image_tool传递Cloudflare配置

**Files:**
- Modify: `src/tools/edit.py:1-73`

- [ ] **Step 1: Update edit_image_tool to accept Cloudflare parameters**

```python
# src/tools/edit.py - 替换整个函数
async def edit_image_tool(
    image_input: str,
    prompt: str,
    model: str = "gpt-4o",
    size: str = "1024x1024",
    quality: str = "standard",
    output_format: Literal["url", "file", "base64"] = "url",
    output_path: Optional[str] = None,
    api_key: str = "",
    base_url: str = "https://api.openai.com/v1",
    save_directory: str = "./images",
    cloudflare_auth_code: str = "",
    cloudflare_api_url: str = "",
    cloudflare_upload_folder: str = "",
    auto_upload_to_cloudflare: bool = True
) -> Dict[str, Any]:
    """
    Edit an image using OpenAI API and return it in the specified format.

    Args:
        image_input: URL or path to the image to edit
        prompt: Text description of the edits to make
        model: Model to use for editing (default: "gpt-4o")
        size: Image size (default: "1024x1024")
        quality: Image quality "standard" or "hd" (default: "standard")
        output_format: Output format - "url", "file", or "base64" (default: "url")
        output_path: Optional custom path for file output
        api_key: OpenAI API key
        base_url: Base URL for OpenAI API (default: "https://api.openai.com/v1")
        save_directory: Directory to save images (default: "./images")
        cloudflare_auth_code: Cloudflare authentication code
        cloudflare_api_url: Cloudflare API URL
        cloudflare_upload_folder: Cloudflare upload folder
        auto_upload_to_cloudflare: Whether to auto-upload to Cloudflare when output_format is url

    Returns:
        Dictionary with:
            - success: bool indicating if operation succeeded
            - format: output format used
            - data: the image data (URL, file path, or base64 string)
            - metadata: dict with model, size, quality
            - error: error message if success is False
    """
    # Validate image_input
    if not image_input:
        logger.error("Image input is required")
        return {"success": False, "error": "Image input is required"}

    logger.info(f"Editing image with prompt: {prompt[:50]}...")
    logger.debug(f"Parameters: image_input={image_input}, model={model}, size={size}, quality={quality}, output_format={output_format}")

    # Construct CloudflareConfig if credentials provided
    cloudflare_config = None
    if cloudflare_auth_code and cloudflare_api_url:
        from src.config import CloudflareConfig
        cloudflare_config = CloudflareConfig(
            auth_code=cloudflare_auth_code,
            api_url=cloudflare_api_url,
            upload_folder=cloudflare_upload_folder
        )

    async def api_call(client):
        return await client.edit_image(
            image_url=image_input,
            prompt=prompt,
            model=model,
            size=size,
            quality=quality
        )

    return await process_image_request(
        api_key=api_key,
        base_url=base_url,
        save_directory=save_directory,
        output_format=output_format,
        output_path=output_path,
        model=model,
        size=size,
        quality=quality,
        api_call=api_call,
        operation_name="Editing",
        cloudflare_config=cloudflare_config,
        auto_upload_to_cloudflare=auto_upload_to_cloudflare
    )
```

- [ ] **Step 2: Run existing tests to verify backward compatibility**

Run: `pytest tests/test_tools.py -v -k edit`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/tools/edit.py
git commit -m "feat: add Cloudflare parameters to edit_image_tool"
```

---

### Task 7: 更新文档

**Files:**
- Modify: `.env.example`
- Modify: `README.md`

- [ ] **Step 1: Update .env.example with Cloudflare configuration**

```bash
# .env.example - 在文件末尾添加
# Cloudflare Configuration
CLOUDFLARE__AUTH_CODE=your-auth-code-here
CLOUDFLARE__API_URL=https://your-cloudflare-api.com/upload
CLOUDFLARE__UPLOAD_FOLDER=mcp-images

# Image Configuration - Auto Upload
IMAGE__AUTO_UPLOAD_TO_CLOUDFLARE=true
```

- [ ] **Step 2: Update README.md with Cloudflare documentation**

```markdown
# README.md - 在"Image Configuration"部分之后添加新章节

## Cloudflare图床配置

本服务支持将生成的图片自动上传到Cloudflare图床，获得持久化的URL。

### 配置方法

#### 环境变量配置

在`.env`文件中添加：

```bash
# Cloudflare图床配置
CLOUDFLARE__AUTH_CODE=your-auth-code-here
CLOUDFLARE__API_URL=https://your-cloudflare-api.com/upload
CLOUDFLARE__UPLOAD_FOLDER=mcp-images

# 启用自动上传
IMAGE__AUTO_UPLOAD_TO_CLOUDFLARE=true
```

#### 配置文件

在`config.json`中添加：

```json
{
  "cloudflare": {
    "auth_code": "your-auth-code-here",
    "api_url": "https://your-cloudflare-api.com/upload",
    "upload_folder": "mcp-images"
  },
  "image": {
    "auto_upload_to_cloudflare": true
  }
}
```

### 工作原理

当`IMAGE__AUTO_UPLOAD_TO_CLOUDFLARE=true`且配置了Cloudflare凭证时：
- `output_format="url"`会自动上传图片到Cloudflare并返回URL
- `output_format="file"`会保存到本地文件
- `output_format="base64"`会返回base64数据

如果未配置Cloudflare或上传失败，系统会自动降级返回base64数据。

### 故障排查

**图片未上传到Cloudflare**
1. 检查`CLOUDFLARE__AUTH_CODE`和`CLOUDFLARE__API_URL`是否正确配置
2. 检查`IMAGE__AUTO_UPLOAD_TO_CLOUDFLARE`是否设置为`true`
3. 查看日志中的错误信息

**上传失败**
1. 验证Cloudflare API地址是否可访问
2. 确认认证码是否有效
3. 检查网络连接
```

- [ ] **Step 3: Commit documentation**

```bash
git add .env.example README.md
git commit -m "docs: add Cloudflare configuration documentation"
```

---

### Task 8: 集成测试

**Files:**
- Modify: `tests/test_integration.py`

- [ ] **Step 1: Add integration test for Cloudflare upload**

```python
# tests/test_integration.py - 在文件末尾添加
@pytest.mark.asyncio
async def test_generate_image_with_cloudflare_integration():
    """Integration test for image generation with Cloudflare upload."""
    from src.tools.generate import generate_image_tool
    
    with patch('src.tools.common.OpenAIClient') as mock_client_class, \
         patch('src.cloudflare_uploader.httpx.AsyncClient.post') as mock_post:
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_client.generate_image = AsyncMock(return_value="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
        mock_client_class.return_value = mock_client
        
        # Mock Cloudflare response
        mock_response = Mock()
        mock_response.json.return_value = [{"src": "https://cdn.test.com/image.png"}]
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Call tool with Cloudflare config
        result = await generate_image_tool(
            prompt="A test image",
            api_key="test_key",
            output_format="url",
            cloudflare_auth_code="test_auth",
            cloudflare_api_url="https://api.test.com/upload",
            cloudflare_upload_folder="test",
            auto_upload_to_cloudflare=True
        )
        
        # Verify result
        assert result["success"] is True
        assert result["format"] == "url"
        assert result["data"] == "https://cdn.test.com/image.png"
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_integration.py::test_generate_image_with_cloudflare_integration -v`
Expected: PASS

- [ ] **Step 3: Run all tests to verify nothing broke**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration test for Cloudflare upload"
```

---

## 规范自查

### 规范覆盖检查

- [x] 配置管理 - Task 1
- [x] CloudflareUploader实现 - Task 2
- [x] ImageHandler扩展 - Task 3
- [x] process_image_request更新 - Task 4
- [x] generate_image_tool更新 - Task 5
- [x] edit_image_tool更新 - Task 6
- [x] 文档更新 - Task 7
- [x] 集成测试 - Task 8

### 占位符检查

- [x] 所有代码块都包含完整实现
- [x] 所有测试都有具体的断言
- [x] 所有命令都有预期输出
- [x] 没有TBD、TODO或"类似Task N"的引用

### 类型一致性检查

- [x] CloudflareConfig在所有任务中使用一致的字段名
- [x] process_base64_image方法签名在Task 3和Task 4中一致
- [x] 函数参数名称在所有任务中保持一致

---

## 执行说明

计划已完成并保存到 `docs/superpowers/plans/2026-04-26-cloudflare-image-upload.md`。

两种执行选项：

**1. Subagent-Driven (推荐)** - 每个任务派发新的子代理，任务间审查，快速迭代

**2. Inline Execution** - 在当前会话中使用executing-plans执行任务，批量执行带检查点

选择哪种方式？

