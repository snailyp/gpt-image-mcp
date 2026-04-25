# OpenAI Image MCP Server 设计文档

**日期**: 2026-04-25  
**版本**: 1.0  
**状态**: 设计阶段

## 项目概述

创建一个基于 Python 的 MCP (Model Context Protocol) 服务器，通过 OpenAI Responses API 提供图像生成和编辑功能。该服务器作为独立的 MCP 服务供各种 MCP 客户端使用。

## 核心特性

- 使用 OpenAI Responses API（而非直接的 Images API）调用图像功能
- 支持文本生成图像（text-to-image）
- 支持图像编辑（image-to-image）
- 支持双传输模式：stdio 和 Streamable HTTP
- 灵活的图像输出格式：URL、本地文件、base64
- 多层级配置管理
- 完善的日志和错误处理

## 整体架构

### 核心组件

**1. MCP 服务器层**
- 使用 `mcp` Python SDK 实现标准 MCP 协议
- 支持双传输模式：
  - **stdio**: 用于本地开发和测试
  - **Streamable HTTP**: 用于远程部署和生产环境
- 暴露工具（tools）供客户端调用

**2. OpenAI Responses API 集成层**
- 使用 `openai` SDK 调用 Responses API
- 通过 Responses API 的内置 `image_generation` 工具实现图像生成和编辑
- 支持文本生成图像和图像编辑两种模式
- 处理 API 响应和图像数据

**3. 配置管理模块**
- 支持多层级配置优先级：启动参数 > 环境变量 > 配置文件
- 管理 API Key、默认模型、输出路径、传输模式等配置
- 使用 pydantic 进行配置验证

**4. 图像处理模块**
- 处理图像输出（URL/本地文件/base64）
- 管理本地图像存储
- 处理图像格式转换
- 支持图像下载重试机制

**5. 日志和错误处理**
- 使用 Python logging 模块
- 支持 DEBUG/INFO/WARNING/ERROR 级别
- 统一的错误处理和异常捕获

## MCP 工具定义

### 1. generate_image - 文本生成图像

**功能**: 根据文本描述生成图像

**输入参数**:
- `prompt` (string, 必需): 图像描述文本
- `model` (string, 可选): 使用的模型，默认 "gpt-4o"
- `size` (string, 可选): 图像尺寸，如 "1024x1024"
- `quality` (string, 可选): 图像质量，"standard" 或 "hd"
- `output_format` (string, 可选): 输出格式 "url" / "file" / "base64"，默认 "url"
- `output_path` (string, 可选): 保存路径（当 output_format="file" 时）

**返回值**:
```json
{
  "success": true,
  "format": "url|file|base64",
  "data": "图像 URL、本地路径或 base64 数据",
  "metadata": {
    "model": "gpt-4o",
    "size": "1024x1024",
    "quality": "standard"
  }
}
```

### 2. edit_image - 图像编辑

**功能**: 根据指令编辑现有图像

**输入参数**:
- `image_input` (string, 必需): 输入图像（URL 或 base64 或本地路径）
- `prompt` (string, 必需): 编辑指令文本
- `model` (string, 可选): 使用的模型，默认 "gpt-4o"
- `size` (string, 可选): 输出图像尺寸
- `quality` (string, 可选): 图像质量
- `output_format` (string, 可选): 输出格式 "url" / "file" / "base64"，默认 "url"
- `output_path` (string, 可选): 保存路径

**返回值**:
```json
{
  "success": true,
  "format": "url|file|base64",
  "data": "编辑后的图像 URL、本地路径或 base64 数据",
  "metadata": {
    "model": "gpt-4o",
    "size": "1024x1024",
    "quality": "standard"
  }
}
```

### 3. get_server_info - 获取服务器信息

**功能**: 获取服务器版本和配置信息

**输入参数**: 无

**返回值**:
```json
{
  "name": "gpt-image-mcp",
  "version": "1.0.0",
  "transport": "stdio|http",
  "supported_models": ["gpt-4o", "gpt-4-turbo"],
  "supported_formats": ["url", "file", "base64"],
  "config": {
    "default_model": "gpt-4o",
    "default_size": "1024x1024"
  }
}
```

## OpenAI Responses API 集成流程

### 核心实现方式

使用 OpenAI Responses API 的内置 `image_generation` 工具，而不是直接调用 Images API。这样可以在对话上下文中处理图像生成。

### 图像生成流程

1. MCP 客户端调用 `generate_image` 工具
2. MCP 服务器构造 Responses API 请求：
   - 使用 `client.responses.create()`
   - 在 `tools` 参数中启用 `image_generation` 工具
   - 将用户的 prompt 作为消息内容
3. OpenAI 模型决定调用 `image_generation` 工具
4. 获取工具调用结果（包含图像 URL）
5. 根据 `output_format` 参数处理图像：
   - `url`: 直接返回 URL
   - `file`: 下载并保存到本地，返回路径
   - `base64`: 下载并转换为 base64，返回数据
6. 返回结果给 MCP 客户端

### 图像编辑流程

1. MCP 客户端调用 `edit_image` 工具
2. 预处理输入图像（如果是本地路径，转换为 URL 或 base64）
3. 构造 Responses API 请求：
   - 在消息中包含输入图像和编辑指令
   - 启用 `image_generation` 工具
4. 模型分析图像并生成编辑后的新图像
5. 按照指定格式处理输出图像
6. 返回结果

### 错误处理策略

- **API 调用失败**: 捕获异常，返回友好错误信息，记录详细日志
- **图像下载失败**: 实现重试机制（最多 3 次），指数退避
- **格式转换失败**: 记录错误日志，返回原始 URL 作为降级方案
- **超时处理**: 设置合理的超时时间（默认 60 秒）
- **配额限制**: 捕获 OpenAI API 的配额错误，返回明确提示

## 项目结构

```
gpt-image-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # MCP 服务器主入口
│   ├── config.py              # 配置管理模块
│   ├── openai_client.py       # OpenAI Responses API 客户端
│   ├── image_handler.py       # 图像处理模块
│   ├── tools/                 # MCP 工具实现
│   │   ├── __init__.py
│   │   ├── generate.py        # generate_image 工具
│   │   ├── edit.py            # edit_image 工具
│   │   └── info.py            # get_server_info 工具
│   └── transports/            # 传输层实现
│       ├── __init__.py
│       ├── stdio.py           # stdio 传输
│       └── http.py            # Streamable HTTP 传输
├── tests/                     # 测试文件
│   ├── __init__.py
│   ├── test_tools.py
│   ├── test_image_handler.py
│   └── test_openai_client.py
├── config.example.json        # 配置文件示例
├── .env.example               # 环境变量示例
├── requirements.txt           # Python 依赖
├── pyproject.toml             # 项目配置
├── README.md                  # 项目文档
└── docs/                      # 文档目录
    └── superpowers/
        └── specs/
```

### 核心模块职责

- **server.py**: 初始化 MCP 服务器，注册工具，启动传输层
- **config.py**: 加载和管理配置（优先级：启动参数 > 环境变量 > 配置文件）
- **openai_client.py**: 封装 OpenAI Responses API 调用逻辑
- **image_handler.py**: 处理图像下载、保存、格式转换
- **tools/**: 各个 MCP 工具的具体实现
- **transports/**: stdio 和 HTTP 传输层的实现

## 配置管理

### 配置文件格式 (config.json)

```json
{
  "openai": {
    "api_key": "sk-...",
    "base_url": "https://api.openai.com/v1",
    "default_model": "gpt-4o",
    "timeout": 60
  },
  "image": {
    "default_size": "1024x1024",
    "default_quality": "standard",
    "default_output_format": "url",
    "save_directory": "./images",
    "download_retry": 3
  },
  "server": {
    "name": "gpt-image-mcp",
    "version": "1.0.0",
    "transport": "stdio"
  },
  "http": {
    "host": "0.0.0.0",
    "port": 8000,
    "endpoint": "/mcp"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

### 环境变量

```bash
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
MCP_TRANSPORT=stdio
MCP_HTTP_PORT=8000
LOG_LEVEL=INFO
```

### 配置优先级

1. 命令行启动参数（最高优先级）
2. 环境变量
3. 配置文件
4. 默认值（最低优先级）

## 启动和部署

### stdio 模式（本地开发）

```bash
# 使用默认配置
python -m src.server --transport stdio

# 使用配置文件
python -m src.server --config config.json

# 使用环境变量
export OPENAI_API_KEY=sk-...
python -m src.server --transport stdio
```

### Streamable HTTP 模式（远程部署）

```bash
# 启动 HTTP 服务器
python -m src.server --transport http --port 8000

# 使用配置文件
python -m src.server --config config.json --transport http

# 指定主机和端口
python -m src.server --transport http --host 0.0.0.0 --port 8000
```

### Docker 部署（可选）

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["python", "-m", "src.server", "--transport", "http", "--port", "8000"]
```

## 依赖包

### 核心依赖

- `mcp`: MCP Python SDK - 实现 MCP 协议
- `openai`: OpenAI Python SDK - 调用 Responses API
- `httpx`: HTTP 客户端 - 用于图像下载
- `python-dotenv`: 环境变量管理
- `pydantic`: 配置验证和数据模型

### 开发依赖

- `pytest`: 单元测试框架
- `pytest-asyncio`: 异步测试支持
- `pytest-mock`: Mock 支持
- `black`: 代码格式化
- `ruff`: 代码检查

## 测试策略

### 单元测试

- 测试各个模块的独立功能
- Mock OpenAI API 调用以避免实际费用
- 测试配置加载和优先级
- 测试图像处理逻辑

### 集成测试

- 测试 MCP 工具的端到端流程
- 测试 stdio 和 HTTP 传输模式
- 测试错误处理和重试机制

### 测试覆盖率目标

- 核心模块：>80%
- 工具实现：>90%
- 整体项目：>75%

## 日志和监控

### 日志级别

- **DEBUG**: 详细的调试信息（API 请求/响应、配置加载）
- **INFO**: 常规操作信息（工具调用、图像生成成功）
- **WARNING**: 警告信息（重试、降级）
- **ERROR**: 错误信息（API 失败、异常）

### 日志格式

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

示例：
```
2026-04-25 10:30:45 - gpt-image-mcp.tools.generate - INFO - Generating image with prompt: "a cat in space"
2026-04-25 10:30:47 - gpt-image-mcp.openai_client - DEBUG - API response received, image URL: https://...
2026-04-25 10:30:48 - gpt-image-mcp.image_handler - INFO - Image saved to: ./images/image_123.png
```

## 安全考虑

1. **API Key 保护**: 
   - 不在日志中输出完整 API Key
   - 支持通过环境变量传递敏感信息

2. **输入验证**:
   - 验证所有用户输入参数
   - 限制文件路径访问范围
   - 验证图像 URL 格式

3. **资源限制**:
   - 限制图像下载大小
   - 设置 API 调用超时
   - 限制并发请求数量

4. **错误信息**:
   - 不在错误信息中泄露敏感配置
   - 提供友好的用户错误提示

## 未来扩展

1. **缓存机制**: 缓存生成的图像，避免重复调用
2. **批量处理**: 支持批量生成多张图像
3. **图像变体**: 支持基于现有图像生成变体
4. **更多模型**: 支持更多 OpenAI 图像模型
5. **Webhook 通知**: 支持异步生成完成后的回调通知
6. **图像历史**: 记录生成历史，支持查询和管理

## 参考资料

- [OpenAI Image API Tutorial](https://www.aifreeapi.com/en/posts/openai-image-api-tutorial)
- [Generating images with gpt-image-1](https://github.com/john-carroll-sw/generating-images-with-gpt-image-1)
- [Cloudflare: Streamable HTTP MCP servers Python](https://blog.cloudflare.com/streamable-http-mcp-servers-python/)
- [MCP Streamable HTTP Transport](https://apigene.ai/blog/mcp-streamable-http)
- [MCP Developer Guide](https://particula.tech/blog/mcp-developer-guide)
