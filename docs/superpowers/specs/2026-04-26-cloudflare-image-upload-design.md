# Cloudflare图床上传功能设计文档

## 概述

为MCP图片生成服务添加Cloudflare图床上传功能，使图片生成和编辑操作返回Cloudflare托管的URL而不是base64数据。

## 背景

当前实现中，OpenAI Responses API返回base64编码的图片数据。虽然项目支持多种输出格式（url/file/base64），但`output_format="url"`实际上无法返回真正的URL，因为OpenAI API不提供持久化的图片URL。

用户需要将生成的图片上传到Cloudflare图床，以获得可持久访问的URL。

## 设计目标

1. 支持将base64图片数据自动上传到Cloudflare图床
2. 通过配置控制是否启用Cloudflare上传
3. 支持环境变量和配置文件两种配置方式
4. 保持向后兼容，未配置时降级到原有行为
5. 提供清晰的错误处理和日志记录

## 技术方案

### 方案选择：智能模式（配置驱动）

在配置中添加`IMAGE__AUTO_UPLOAD_TO_CLOUDFLARE`开关：
- 启用时：`output_format="url"`自动上传到Cloudflare并返回URL
- 禁用时：保持原有行为（返回base64或报错）

**优点：**
- 语义清晰，`output_format="url"`真正返回URL
- 配置灵活，可全局控制
- 不需要修改API接口
- 向后兼容

## 详细设计

### 1. 配置管理

#### 1.1 添加CloudflareConfig

在`src/config.py`中添加：

```python
class CloudflareConfig(BaseModel):
    """Cloudflare Images configuration."""
    auth_code: str = Field(default="")
    api_url: str = Field(default="")
    upload_folder: str = Field(default="")
```

#### 1.2 扩展ImageConfig

```python
class ImageConfig(BaseModel):
    """Image generation configuration."""
    default_size: str = Field(default="1024x1024")
    default_quality: str = Field(default="standard")
    default_output_format: str = Field(default="url")
    save_directory: str = Field(default="./images")
    download_retry: int = Field(default=3)
    auto_upload_to_cloudflare: bool = Field(default=True)
```

#### 1.3 更新Config类

```python
class Config(BaseSettings):
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    image: ImageConfig = Field(default_factory=ImageConfig)
    cloudflare: CloudflareConfig = Field(default_factory=CloudflareConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    http: HTTPConfig = Field(default_factory=HTTPConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
```

#### 1.4 环境变量支持

- `CLOUDFLARE__AUTH_CODE` - Cloudflare认证码
- `CLOUDFLARE__API_URL` - Cloudflare API地址
- `CLOUDFLARE__UPLOAD_FOLDER` - 上传文件夹（可选）
- `IMAGE__AUTO_UPLOAD_TO_CLOUDFLARE` - 是否自动上传（默认true）

### 2. Cloudflare上传器实现

创建新文件`src/cloudflare_uploader.py`：

```python
import logging
import base64
import httpx
from typing import Optional

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
        # 解码base64为bytes
        # 构造请求URL（包含query参数）
        # 发送POST请求上传文件
        # 解析响应JSON，提取图片URL
        # 返回完整的图片URL
```

**实现细节：**
- 构造URL时添加query参数：`authCode`, `uploadFolder`, `uploadNameType=origin`
- 使用multipart/form-data格式上传文件
- 解析响应JSON数组，提取第一个元素的`src`字段
- 如果返回的是相对路径，拼接完整URL
- 捕获网络错误、解析错误等异常

### 3. 修改ImageHandler

在`src/image_handler.py`中添加Cloudflare支持：

#### 3.1 更新构造函数

```python
def __init__(
    self, 
    save_directory: str = "./images", 
    download_retry: int = 3,
    cloudflare_uploader: Optional[CloudflareUploader] = None,
    auto_upload_to_cloudflare: bool = True
):
    self.save_directory = Path(save_directory)
    self.download_retry = download_retry
    self.cloudflare_uploader = cloudflare_uploader
    self.auto_upload_to_cloudflare = auto_upload_to_cloudflare
    self.save_directory.mkdir(parents=True, exist_ok=True)
```

#### 3.2 添加process_base64_image方法

```python
async def process_base64_image(
    self,
    base64_data: str,
    output_format: Literal["url", "file", "base64"] = "url",
    output_path: Optional[str] = None,
    filename: Optional[str] = None
) -> dict:
    """
    处理base64图片数据
    
    Args:
        base64_data: base64编码的图片数据
        output_format: 输出格式
        output_path: 自定义输出路径（用于file格式）
        filename: 文件名（用于Cloudflare上传）
        
    Returns:
        包含format和data的字典
    """
    if output_format == "url":
        if self.cloudflare_uploader and self.auto_upload_to_cloudflare:
            # 上传到Cloudflare
            try:
                url = await self.cloudflare_uploader.upload_base64(
                    base64_data, 
                    filename or f"{uuid.uuid4()}.png"
                )
                return {"format": "url", "data": url}
            except Exception as e:
                logger.error(f"Failed to upload to Cloudflare: {e}")
                logger.warning("Falling back to base64 format")
                return {"format": "base64", "data": base64_data}
        else:
            logger.warning("Cloudflare uploader not configured, returning base64")
            return {"format": "base64", "data": base64_data}
    
    elif output_format == "file":
        # 解码base64并保存到文件
        image_bytes = base64.b64decode(base64_data)
        file_path = await self._save_image(image_bytes, "image.png", output_path)
        return {"format": "file", "data": str(file_path)}
    
    elif output_format == "base64":
        return {"format": "base64", "data": base64_data}
```

#### 3.3 保留原有download_image方法

保持`download_image`方法不变，用于处理从URL下载的场景。

### 4. 修改工具函数

在`src/tools/common.py`中更新`process_image_request`：

#### 4.1 添加参数

```python
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
    cloudflare_config: Optional[CloudflareConfig] = None,
    auto_upload_to_cloudflare: bool = True
) -> Dict[str, Any]:
```

#### 4.2 更新实现逻辑

```python
# 创建OpenAI客户端
client = OpenAIClient(api_key=api_key, base_url=base_url)

# 调用API获取base64数据
base64_data = await api_call(client)

# 创建Cloudflare上传器（如果配置存在）
cloudflare_uploader = None
if cloudflare_config and cloudflare_config.auth_code and cloudflare_config.api_url:
    from src.cloudflare_uploader import CloudflareUploader
    cloudflare_uploader = CloudflareUploader(
        auth_code=cloudflare_config.auth_code,
        api_url=cloudflare_config.api_url,
        upload_folder=cloudflare_config.upload_folder
    )

# 创建ImageHandler
handler = ImageHandler(
    save_directory=save_directory,
    cloudflare_uploader=cloudflare_uploader,
    auto_upload_to_cloudflare=auto_upload_to_cloudflare
)

# 处理base64数据
result = await handler.process_base64_image(
    base64_data=base64_data,
    output_format=output_format,
    output_path=output_path,
    filename=f"{operation_name.lower()}_{uuid.uuid4()}.png"
)
```

### 5. 更新工具入口

#### 5.1 修改generate.py

```python
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
    # 构造CloudflareConfig
    cloudflare_config = None
    if cloudflare_auth_code and cloudflare_api_url:
        cloudflare_config = CloudflareConfig(
            auth_code=cloudflare_auth_code,
            api_url=cloudflare_api_url,
            upload_folder=cloudflare_upload_folder
        )
    
    # 调用process_image_request
    return await process_image_request(
        # ... 其他参数
        cloudflare_config=cloudflare_config,
        auto_upload_to_cloudflare=auto_upload_to_cloudflare
    )
```

#### 5.2 修改edit.py

类似地更新`edit_image_tool`函数。

### 6. 错误处理策略

#### 6.1 配置验证

- 如果`auto_upload_to_cloudflare=True`但Cloudflare配置不完整：
  - 记录WARNING日志
  - 降级返回base64格式

#### 6.2 上传失败处理

- 如果Cloudflare上传失败：
  - 记录ERROR日志（包含详细错误信息）
  - 降级返回base64格式
  - 不中断用户操作

#### 6.3 日志级别

- INFO: 成功上传到Cloudflare
- WARNING: 配置不完整，降级到base64
- ERROR: 上传失败，降级到base64

### 7. 文档更新

#### 7.1 更新.env.example

添加Cloudflare配置示例：

```bash
# Cloudflare Configuration
CLOUDFLARE__AUTH_CODE=your-auth-code-here
CLOUDFLARE__API_URL=https://your-cloudflare-api.com/upload
CLOUDFLARE__UPLOAD_FOLDER=mcp-images

# Image Configuration
IMAGE__AUTO_UPLOAD_TO_CLOUDFLARE=true
```

#### 7.2 更新README.md

添加Cloudflare配置说明章节：
- 配置方法
- 环境变量说明
- 使用示例
- 故障排查

#### 7.3 更新config.example.json

添加cloudflare配置段。

## 实现顺序

1. 添加配置类（config.py）
2. 实现CloudflareUploader（cloudflare_uploader.py）
3. 修改ImageHandler（image_handler.py）
4. 修改工具函数（tools/common.py）
5. 更新工具入口（tools/generate.py, tools/edit.py）
6. 更新文档（README.md, .env.example）
7. 测试验证

## 测试计划

1. 单元测试：CloudflareUploader上传功能
2. 集成测试：完整的生成和编辑流程
3. 配置测试：各种配置组合的行为验证
4. 错误处理测试：网络失败、配置缺失等场景

## 向后兼容性

- 未配置Cloudflare时，保持原有行为
- 所有现有API参数保持不变
- 配置文件格式向后兼容
- 环境变量命名遵循现有规范

## 安全考虑

- Cloudflare认证码通过环境变量配置，不硬编码
- 上传失败时不暴露敏感信息
- 日志中不记录完整的认证码

## 性能影响

- 上传到Cloudflare会增加响应时间（网络IO）
- 失败时降级到base64，不影响功能可用性
- 异步实现，不阻塞其他操作
