# OpenAI Image MCP Server

A Model Context Protocol (MCP) server that provides image generation and editing capabilities using OpenAI's Images API.

## Features

- **Text-to-Image Generation**: Create images from text prompts using gpt-image models (gpt-image-2, gpt-image-1.5)
- **Image Editing**: Modify existing images with natural language instructions using gpt-image 2
- **Multiple Output Formats**: Return images as URLs, save to files, or encode as base64
- **Cloudflare Integration**: Automatic upload to Cloudflare Images for persistent URLs
- **Dual Transport Modes**: Run locally via stdio or remotely via SSE
- **Flexible Configuration**: Environment variables, JSON config files, and CLI arguments
- **Automatic Format Conversion**: Converts images to PNG format for editing operations

## Installation

### Prerequisites

- Python 3.11 or higher
- OpenAI API key with access to gpt-image models (gpt-image-2 for generation, gpt-image-1.5 for editing)

### Install Dependencies

```bash
pip install -r requirements.txt
```

This project uses [fastmcp](https://github.com/jlowin/fastmcp) for the MCP server implementation.

## Configuration

The server supports three configuration methods with the following priority (highest to lowest):

1. Command-line arguments
2. Environment variables
3. Configuration file

### Environment Variables

Copy the example file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# OpenAI Configuration
OPENAI__API_KEY=sk-your-api-key-here
OPENAI__BASE_URL=https://api.openai.com/v1
OPENAI__DEFAULT_MODEL=gpt-image-2
OPENAI__TIMEOUT=60

# Image Configuration
IMAGE__DEFAULT_QUALITY=auto
IMAGE__DEFAULT_OUTPUT_FORMAT=url
IMAGE__SAVE_DIRECTORY=./images
IMAGE__DOWNLOAD_RETRY=3
IMAGE__AUTO_UPLOAD_TO_CLOUDFLARE=true

# Server Configuration
SERVER__NAME=gpt-image-mcp
SERVER__VERSION=1.0.0
SERVER__TRANSPORT=stdio  # Options: stdio (local/MCP clients), sse (remote access), http (alias for sse)

# SSE Configuration (for SSE transport)
HTTP__HOST=0.0.0.0
HTTP__PORT=8000
HTTP__ENDPOINT=/sse

# Logging Configuration
LOGGING__LEVEL=INFO
```

### Configuration File

Alternatively, use a JSON configuration file:

```bash
cp config.example.json config.json
```

Edit `config.json` with your settings. See `config.example.json` for the full structure.

## Usage

### stdio Mode (Local/MCP Client)

For use with MCP clients like Claude Desktop:

```bash
python -m src.server --transport stdio
```

Or with a custom config file:

```bash
python -m src.server --config config.json --transport stdio
```

### SSE Mode (Remote Access)

For remote access via Server-Sent Events:

```bash
python -m src.server --transport sse --port 8000
```

The server will be available at `http://0.0.0.0:8000`

### Command-Line Options

```bash
python -m src.server [OPTIONS]

Options:
  --config PATH       Path to JSON configuration file
  --transport TYPE    Transport mode: stdio, sse, or http (default: stdio)
  --port PORT         SSE server port (default: 8000)
  --host HOST         SSE server host (default: 0.0.0.0)
```

## MCP Tools

### generate_image

Generate an image from a text prompt using OpenAI's Images API.

**Parameters:**

- `prompt` (string, required): Text description of the image to generate
- `model` (string, optional): Model to use (default: `gpt-image-2`)
  - Supported: `gpt-image-2`, `gpt-image-1.5`
- `quality` (string, optional): Image quality (default: `auto`)
  - Options: `low`, `medium`, `high`, `auto`
- `output_format` (string, optional): Output format (default: `url`)
  - `url`: Return Cloudflare image URL (if configured) or base64 data
  - `file`: Download and save to disk
  - `base64`: Return base64-encoded image data
- `output_path` (string, optional): Custom file path when using `file` format

**Returns:**

```json
{
  "success": true,
  "format": "url",
  "data": "https://...",
  "metadata": {
    "model": "gpt-image-2",
    "quality": "auto"
  }
}
```

**Example:**

```json
{
  "prompt": "a serene mountain landscape at sunset",
  "model": "gpt-image-2",
  "quality": "high",
  "output_format": "file"
}
```

### edit_image

Edit an existing image using a text prompt with gpt-image 2.

**Parameters:**

- `image_input` (string, required): URL or file path of the image to edit (automatically converted to PNG)
- `prompt` (string, required): Text description of the desired changes
- `model` (string, optional): Model to use (default: `gpt-image-2`)
  - Note: Only `gpt-image-1.5` supports image editing
- `quality` (string, optional): Image quality (default: `auto`)
- `output_format` (string, optional): Output format (default: `url`)
- `output_path` (string, optional): Custom file path when using `file` format

**Returns:**

```json
{
  "success": true,
  "format": "url",
  "data": "https://...",
  "metadata": {
    "model": "gpt-image-2",
    "quality": "auto"
  }
}
```

**Example:**

```json
{
  "image_input": "https://example.com/original.png",
  "prompt": "add a rainbow in the sky",
  "output_format": "file",
  "output_path": "./images/edited_image.png"
}
```

### get_server_info

Get server information, configuration, and capabilities.

**Parameters:** None

**Returns:**

```json
{
  "name": "gpt-image-mcp",
  "version": "1.0.0",
  "transport": "stdio",
  "supported_models": ["gpt-image-2", "gpt-image-1.5"],
  "supported_formats": ["url", "file", "base64"],
  "config": {
    "default_model": "gpt-image-2"
  }
}
```

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

- `output_format="url"`会自动上传图片到Cloudflare并返回持久化URL
- `output_format="file"`会保存到本地文件
- `output_format="base64"`会返回base64编码数据

如果未配置Cloudflare或上传失败，系统会自动降级返回base64数据。

### 配置参数说明

- `CLOUDFLARE__AUTH_CODE`: Cloudflare API认证码
- `CLOUDFLARE__API_URL`: Cloudflare上传API地址
- `CLOUDFLARE__UPLOAD_FOLDER`: 上传文件夹名称（可选）
- `IMAGE__AUTO_UPLOAD_TO_CLOUDFLARE`: 是否启用自动上传（默认: true）

### 故障排查

#### 图片未上传到Cloudflare

1. 检查`CLOUDFLARE__AUTH_CODE`和`CLOUDFLARE__API_URL`是否正确配置
2. 检查`IMAGE__AUTO_UPLOAD_TO_CLOUDFLARE`是否设置为`true`
3. 查看日志中的错误信息

#### 上传失败

1. 验证Cloudflare API地址是否可访问
2. 确认认证码是否有效
3. 检查网络连接

## Integration with MCP Clients

### Claude Desktop

Add to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "openai-image": {
      "command": "python",
      "args": ["-m", "src.server", "--transport", "stdio"],
      "cwd": "/path/to/gpt-image-mcp",
      "env": {
        "OPENAI__API_KEY": "sk-your-api-key-here"
      }
    }
  }
}
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_tools.py -v
```

## Project Structure

```
gpt-image-mcp/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── openai_client.py       # OpenAI Responses API client
│   ├── image_handler.py       # Image download and format conversion
│   ├── server.py              # Main MCP server entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── generate.py        # generate_image tool
│   │   ├── edit.py            # edit_image tool
│   │   └── info.py            # get_server_info tool
│   └── transports/
│       ├── __init__.py
│       └── stdio.py           # stdio transport (SSE via fastmcp)
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_openai_client.py
│   ├── test_image_handler.py
│   ├── test_tools.py
│   └── test_integration.py
├── .env.example               # Example environment variables
├── config.example.json        # Example configuration file
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project metadata
└── README.md                 # This file
```

## Error Handling

All tools return a consistent error format:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

Common errors:

- **Invalid API Key**: Check your `OPENAI_API_KEY` configuration
- **Model Not Available**: Ensure you have access to the specified model
- **Image Download Failed**: Check network connectivity and URL validity

## Troubleshooting

### Server won't start

1. Verify Python version: `python --version` (must be 3.11+)
2. Check dependencies: `pip install -r requirements.txt`
3. Verify API key is set in environment or config file

### Image generation fails

1. Confirm API key has access to gpt-image models (gpt-image-2 or gpt-image-1.5)
2. Check OpenAI API status
3. Review logs for detailed error messages

### Image editing fails

1. Ensure the image is accessible (valid URL or file path)
2. Verify the image format (automatically converted to PNG)
3. Note: Only gpt-image-1.5 supports image editing
4. Check that the image meets OpenAI's content policy requirements

### SSE mode not accessible

1. Check firewall settings
2. Verify port is not in use: `netstat -an | grep 8000`
3. Try binding to localhost: `--host 127.0.0.1`

## Migration History

### OpenAI Images API Migration

This project has been migrated from OpenAI's Responses API to the Images API:

- **Image Generation**: Now uses `client.images.generate()` with gpt-image models
- **Image Editing**: Now uses `client.images.edit()` with gpt-image 2
- **Quality Parameters**: Mapped to Images API format (low/medium/high/auto)
- **Response Handling**: Supports both `b64_json` and `url` response formats
- **Format Conversion**: Automatic PNG conversion for image editing operations

Key commits:

- `1c4445d`: Migrated generate_image to Images API
- `d2c75e6`: Migrated edit_image to Images API
- `fc93422`: Removed unsupported response_format parameter
- `79c9600`: Mapped quality parameter values
- `e9ed57e`: Handle both b64_json and url response formats

### fastmcp Migration

This project uses `fastmcp` for improved developer experience:

- Simplified tool definitions using decorators
- Reduced server code by ~150 lines
- SSE (Server-Sent Events) transport for remote access
- Maintained all existing functionality and APIs

## License

MIT

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting pull requests.

## Support

For issues and questions:

- Check the troubleshooting section above
- Review test files for usage examples
- Consult OpenAI's Responses API documentation
