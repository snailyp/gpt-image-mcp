# OpenAI Image MCP Server

A Model Context Protocol (MCP) server that provides image generation and editing capabilities using OpenAI's Responses API with the `image_generation` tool.

## Features

- **Text-to-Image Generation**: Create images from text prompts using GPT-4o or GPT-4-turbo
- **Image Editing**: Modify existing images with natural language instructions
- **Multiple Output Formats**: Return images as URLs, save to files, or encode as base64
- **Dual Transport Modes**: Run locally via stdio or remotely via HTTP
- **Flexible Configuration**: Environment variables, JSON config files, and CLI arguments
- **Retry Mechanism**: Automatic retry for image downloads with configurable attempts

## Installation

### Prerequisites

- Python 3.11 or higher
- OpenAI API key with access to GPT-4o or GPT-4-turbo

### Install Dependencies

```bash
pip install -r requirements.txt
```

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
OPENAI__DEFAULT_MODEL=gpt-4o
OPENAI__TIMEOUT=60

# Image Configuration
IMAGE__DEFAULT_SIZE=1024x1024
IMAGE__DEFAULT_QUALITY=standard
IMAGE__DEFAULT_OUTPUT_FORMAT=url
IMAGE__SAVE_DIRECTORY=./images
IMAGE__DOWNLOAD_RETRY=3

# Server Configuration
SERVER__NAME=gpt-image-mcp
SERVER__VERSION=1.0.0
SERVER__TRANSPORT=stdio

# HTTP Configuration (for HTTP transport)
HTTP__HOST=0.0.0.0
HTTP__PORT=8000
HTTP__ENDPOINT=/mcp

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

### HTTP Mode (Remote Access)

For remote access via HTTP:

```bash
python -m src.server --transport http --port 8000
```

The server will be available at `http://0.0.0.0:8000/mcp`

### Command-Line Options

```bash
python -m src.server [OPTIONS]

Options:
  --config PATH       Path to JSON configuration file
  --transport TYPE    Transport mode: stdio or http (default: stdio)
  --port PORT         HTTP server port (default: 8000)
  --host HOST         HTTP server host (default: 0.0.0.0)
```

## MCP Tools

### generate_image

Generate an image from a text prompt using OpenAI's Responses API.

**Parameters:**

- `prompt` (string, required): Text description of the image to generate
- `model` (string, optional): Model to use (default: `gpt-4o`)
  - Supported: `gpt-4o`, `gpt-4-turbo`
- `size` (string, optional): Image dimensions (default: `1024x1024`)
  - Supported: `1024x1024`, `1792x1024`, `1024x1792`
- `quality` (string, optional): Image quality (default: `standard`)
  - Options: `standard`, `hd`
- `output_format` (string, optional): Output format (default: `url`)
  - `url`: Return the image URL
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
    "model": "gpt-4o",
    "size": "1024x1024",
    "quality": "standard"
  }
}
```

**Example:**

```json
{
  "prompt": "a serene mountain landscape at sunset",
  "model": "gpt-4o",
  "size": "1024x1024",
  "quality": "hd",
  "output_format": "file"
}
```

### edit_image

Edit an existing image using a text prompt.

**Parameters:**

- `image_input` (string, required): URL or file path of the image to edit
- `prompt` (string, required): Text description of the desired changes
- `model` (string, optional): Model to use (default: `gpt-4o`)
- `size` (string, optional): Output image dimensions (default: `1024x1024`)
- `quality` (string, optional): Image quality (default: `standard`)
- `output_format` (string, optional): Output format (default: `url`)
- `output_path` (string, optional): Custom file path when using `file` format

**Returns:**

```json
{
  "success": true,
  "format": "url",
  "data": "https://...",
  "metadata": {
    "model": "gpt-4o",
    "size": "1024x1024",
    "quality": "standard"
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
  "supported_models": ["gpt-4o", "gpt-4-turbo"],
  "supported_formats": ["url", "file", "base64"],
  "config": {
    "default_model": "gpt-4o",
    "default_size": "1024x1024"
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

- `output_format="url"`会自动上传图片到Cloudflare并返回URL
- `output_format="file"`会保存到本地文件
- `output_format="base64"`会返回base64数据

如果未配置Cloudflare或上传失败，系统会自动降级返回base64数据。

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
│       ├── stdio.py           # stdio transport
│       └── http.py            # HTTP transport
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
- **Invalid Size**: Use supported dimensions (1024x1024, 1792x1024, 1024x1792)

## Troubleshooting

### Server won't start

1. Verify Python version: `python --version` (must be 3.11+)
2. Check dependencies: `pip install -r requirements.txt`
3. Verify API key is set in environment or config file

### Image generation fails

1. Confirm API key has access to GPT-4o or GPT-4-turbo
2. Check OpenAI API status
3. Review logs for detailed error messages

### HTTP mode not accessible

1. Check firewall settings
2. Verify port is not in use: `netstat -an | grep 8000`
3. Try binding to localhost: `--host 127.0.0.1`

## License

MIT

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting pull requests.

## Support

For issues and questions:

- Check the troubleshooting section above
- Review test files for usage examples
- Consult OpenAI's Responses API documentation
