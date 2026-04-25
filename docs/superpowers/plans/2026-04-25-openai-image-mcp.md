# OpenAI Image MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python MCP server that provides image generation and editing via OpenAI Responses API

**Architecture:** MCP server with stdio/HTTP transports, OpenAI Responses API integration, flexible image output handling (URL/file/base64), multi-layer config management

**Tech Stack:** Python 3.11+, mcp SDK, openai SDK, httpx, pydantic, pytest

---

## File Structure Overview

**Core modules:**
- `src/config.py` - Configuration management with priority loading
- `src/openai_client.py` - OpenAI Responses API wrapper
- `src/image_handler.py` - Image download, save, format conversion
- `src/tools/generate.py` - generate_image tool implementation
- `src/tools/edit.py` - edit_image tool implementation
- `src/tools/info.py` - get_server_info tool implementation
- `src/transports/stdio.py` - stdio transport
- `src/transports/http.py` - Streamable HTTP transport
- `src/server.py` - Main entry point

**Tests:**
- `tests/test_config.py` - Config loading tests
- `tests/test_openai_client.py` - OpenAI client tests
- `tests/test_image_handler.py` - Image handler tests
- `tests/test_tools.py` - Tool integration tests

---

## Task 1: Project Setup and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `config.example.json`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```txt
mcp>=1.0.0
openai>=1.0.0
httpx>=0.27.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-mock>=3.12.0
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[project]
name = "gpt-image-mcp"
version = "1.0.0"
description = "MCP server for OpenAI image generation via Responses API"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
    "openai>=1.0.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
]
```


- [ ] **Step 3: Create .env.example**

```bash
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
MCP_TRANSPORT=stdio
MCP_HTTP_PORT=8000
LOG_LEVEL=INFO
```

- [ ] **Step 4: Create config.example.json**

```json
{
  "openai": {
    "api_key": "",
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


- [ ] **Step 5: Create src/__init__.py**

```python
"""OpenAI Image MCP Server"""
__version__ = "1.0.0"
```

- [ ] **Step 6: Create tests/__init__.py**

```python
"""Tests for OpenAI Image MCP Server"""
```

- [ ] **Step 7: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: All packages installed successfully

- [ ] **Step 8: Commit project setup**

```bash
git add requirements.txt pyproject.toml .env.example config.example.json src/__init__.py tests/__init__.py
git commit -m "chore: initial project setup with dependencies"
```

---

## Task 2: Configuration Management Module

**Files:**
- Create: `src/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing test for config loading**

```python
# tests/test_config.py
import os
import json
import tempfile
from pathlib import Path
import pytest
from src.config import Config, load_config


def test_load_config_from_env():
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    config = load_config()
    
    assert config.openai.api_key == "test-key"
    assert config.logging.level == "DEBUG"
```


- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_load_config_from_env -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.config'"

- [ ] **Step 3: Write minimal config implementation**

```python
# src/config.py
import os
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class OpenAIConfig(BaseModel):
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.openai.com/v1")
    default_model: str = Field(default="gpt-4o")
    timeout: int = Field(default=60)


class ImageConfig(BaseModel):
    default_size: str = Field(default="1024x1024")
    default_quality: str = Field(default="standard")
    default_output_format: str = Field(default="url")
    save_directory: str = Field(default="./images")
    download_retry: int = Field(default=3)


class ServerConfig(BaseModel):
    name: str = Field(default="gpt-image-mcp")
    version: str = Field(default="1.0.0")
    transport: str = Field(default="stdio")


class HTTPConfig(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    endpoint: str = Field(default="/mcp")


class LoggingConfig(BaseModel):
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class Config(BaseSettings):
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    image: ImageConfig = Field(default_factory=ImageConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    http: HTTPConfig = Field(default_factory=HTTPConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        env_nested_delimiter = "__"
        env_prefix = ""


def load_config(config_file: Optional[str] = None, **cli_args) -> Config:
    config_data = 
    
    if config_file and Path(config_file).exists():
        with open(config_file) as f:
            config_data = json.load(f)
    
    if "OPENAI_API_KEY" in os.environ:
        if "openai" not in config_data:
            config_data["openai"] = {}
        config_data["openai"]["api_key"] = os.environ["OPENAI_API_KEY"]
    
    if "LOG_LEVEL" in os.environ:
        if "logging" not in config_data:
            config_data["logging"] = {}
        config_data["logging"]["level"] = os.environ["LOG_LEVEL"]
    
    config_data.update(cli_args)
    
    return Config(**config_data)
```


- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py::test_load_config_from_env -v`
Expected: PASS

- [ ] **Step 5: Write test for config file loading**

```python
# tests/test_config.py (add to existing file)
def test_load_config_from_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "openai": {"api_key": "file-key", "default_model": "gpt-4-turbo"},
            "image": {"default_size": "512x512"}
        }, f)
        config_file = f.name
    
    try:
        config = load_config(config_file=config_file)
        assert config.openai.api_key == "file-key"
        assert config.openai.default_model == "gpt-4-turbo"
        assert config.image.default_size == "512x512"
    finally:
        os.unlink(config_file)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_config.py::test_load_config_from_file -v`
Expected: PASS

- [ ] **Step 7: Write test for config priority**

```python
# tests/test_config.py (add to existing file)
def test_config_priority_env_over_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"openai": {"api_key": "file-key"}}, f)
        config_file = f.name
    
    os.environ["OPENAI_API_KEY"] = "env-key"
    
    try:
        config = load_config(config_file=config_file)
        assert config.openai.api_key == "env-key"
    finally:
        os.unlink(config_file)
        del os.environ["OPENAI_API_KEY"]
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/test_config.py::test_config_priority_env_over_file -v`
Expected: PASS

- [ ] **Step 9: Run all config tests**

Run: `pytest tests/test_config.py -v`
Expected: All tests PASS

- [ ] **Step 10: Commit config module**

```bash
git add src/config.py tests/test_config.py
git commit -m "feat: add configuration management with priority loading"
```

---

## Task 3: Image Handler Module

**Files:**
- Create: `src/image_handler.py`
- Create: `tests/test_image_handler.py`

- [ ] **Step 1: Write failing test for image download**

```python
# tests/test_image_handler.py
import pytest
from unittest.mock import Mock, patch
from src.image_handler import ImageHandler


@pytest.mark.asyncio
async def test_download_image_to_file():
    handler = ImageHandler(save_directory="./test_images", download_retry=3)
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = await handler.download_image("https://example.com/image.png", output_format="file")
        
        assert result["format"] == "file"
        assert "test_images" in result["data"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_image_handler.py::test_download_image_to_file -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.image_handler'"

- [ ] **Step 3: Write minimal image handler implementation**

```python
# src/image_handler.py
import os
import base64
import logging
from pathlib import Path
from typing import Dict, Literal
import httpx


logger = logging.getLogger(__name__)


class ImageHandler:
    def __init__(self, save_directory: str = "./images", download_retry: int = 3):
        self.save_directory = Path(save_directory)
        self.download_retry = download_retry
        self.save_directory.mkdir(parents=True, exist_ok=True)
    
    async def download_image(
        self, 
        url: str, 
        output_format: Literal["url", "file", "base64"] = "url",
        output_path: str = None
    ) -> Dict[str, str]:
        if output_format == "url":
            return {"format": "url", "data": url}
        
        image_data = await self._fetch_image(url)
        
        if output_format == "base64":
            b64_data = base64.b64encode(image_data).decode('utf-8')
            return {"format": "base64", "data": b64_data}
        
        if output_format == "file":
            file_path = await self._save_image(image_data, output_path)
            return {"format": "file", "data": str(file_path)}
    
    async def _fetch_image(self, url: str) -> bytes:
        for attempt in range(self.download_retry):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=30.0)
                    response.raise_for_status()
                    return response.content
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if attempt == self.download_retry - 1:
                    raise
        
    async def _save_image(self, image_data: bytes, output_path: str = None) -> Path:
        if output_path:
            file_path = Path(output_path)
        else:
            import uuid
            filename = f"image_{uuid.uuid4().hex[:8]}.png"
            file_path = self.save_directory / filename
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"Image saved to: {file_path}")
        return file_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_image_handler.py::test_download_image_to_file -v`
Expected: PASS

- [ ] **Step 5: Write test for base64 conversion**

```python
# tests/test_image_handler.py (add to existing file)
@pytest.mark.asyncio
async def test_download_image_to_base64():
    handler = ImageHandler(save_directory="./test_images")
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = await handler.download_image("https://example.com/image.png", output_format="base64")
        
        assert result["format"] == "base64"
        assert isinstance(result["data"], str)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_image_handler.py::test_download_image_to_base64 -v`
Expected: PASS

- [ ] **Step 7: Write test for retry mechanism**

```python
# tests/test_image_handler.py (add to existing file)
@pytest.mark.asyncio
async def test_download_retry_on_failure():
    handler = ImageHandler(save_directory="./test_images", download_retry=3)
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            Mock(content=b"success", status_code=200)
        ]
        
        result = await handler.download_image("https://example.com/image.png", output_format="base64")
        
        assert result["format"] == "base64"
        assert mock_get.call_count == 3
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/test_image_handler.py::test_download_retry_on_failure -v`
Expected: PASS

- [ ] **Step 9: Run all image handler tests**

Run: `pytest tests/test_image_handler.py -v`
Expected: All tests PASS

- [ ] **Step 10: Commit image handler module**

```bash
git add src/image_handler.py tests/test_image_handler.py
git commit -m "feat: add image handler with download and format conversion"
```

---

## Task 4: OpenAI Responses API Client

**Files:**
- Create: `src/openai_client.py`
- Create: `tests/test_openai_client.py`

- [ ] **Step 1: Write failing test for image generation**

```python
# tests/test_openai_client.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.openai_client import OpenAIClient


@pytest.mark.asyncio
async def test_generate_image():
    client = OpenAIClient(api_key="test-key", base_url="https://api.openai.com/v1")
    
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(tool_calls=[
            Mock(
                id="call_123",
                function=Mock(name="image_generation", arguments='{"image_url": "https://example.com/image.png"}')
            )
        ]))]
        mock_openai.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await client.generate_image(
            prompt="a cat in space",
            model="gpt-4o",
            size="1024x1024",
            quality="standard"
        )
        
        assert result == "https://example.com/image.png"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_openai_client.py::test_generate_image -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.openai_client'"

- [ ] **Step 3: Write minimal OpenAI client implementation**

```python
# src/openai_client.py
import json
import logging
from typing import Optional
from openai import AsyncOpenAI


logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", timeout: int = 60):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
    
    async def generate_image(
        self,
        prompt: str,
        model: str = "gpt-4o",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> str:
        logger.info(f"Generating image with prompt: {prompt}")
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            tools=[
                {
                    "type": "image_generation",
                    "image_generation": {
                        "size": size,
                        "quality": quality
                    }
                }
            ]
        )
        
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            if tool_call.function.name == "image_generation":
                result = json.loads(tool_call.function.arguments)
                image_url = result.get("image_url")
                logger.debug(f"Image generated: {image_url}")
                return image_url
        
        raise ValueError("No image generated by the model")
    
    async def edit_image(
        self,
        image_url: str,
        prompt: str,
        model: str = "gpt-4o",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> str:
        logger.info(f"Editing image with prompt: {prompt}")
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            tools=[
                {
                    "type": "image_generation",
                    "image_generation": {
                        "size": size,
                        "quality": quality
                    }
                }
            ]
        )
        
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            if tool_call.function.name == "image_generation":
                result = json.loads(tool_call.function.arguments)
                image_url = result.get("image_url")
                logger.debug(f"Image edited: {image_url}")
                return image_url
        
        raise ValueError("No image generated by the model")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_openai_client.py::test_generate_image -v`
Expected: PASS

- [ ] **Step 5: Write test for image editing**

```python
# tests/test_openai_client.py (add to existing file)
@pytest.mark.asyncio
async def test_edit_image():
    client = OpenAIClient(api_key="test-key")
    
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(tool_calls=[
            Mock(
                id="call_456",
                function=Mock(name="image_generation", arguments='{"image_url": "https://example.com/edited.png"}')
            )
        ]))]
        mock_openai.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await client.edit_image(
            image_url="https://example.com/original.png",
            prompt="make it blue",
            model="gpt-4o"
        )
        
        assert result == "https://example.com/edited.png"
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_openai_client.py::test_edit_image -v`
Expected: PASS

- [ ] **Step 7: Run all OpenAI client tests**

Run: `pytest tests/test_openai_client.py -v`
Expected: All tests PASS

- [ ] **Step 8: Commit OpenAI client module**

```bash
git add src/openai_client.py tests/test_openai_client.py
git commit -m "feat: add OpenAI Responses API client for image generation"
```

---

## Task 5: MCP Tools - Generate Image

**Files:**
- Create: `src/tools/__init__.py`
- Create: `src/tools/generate.py`
- Create: `tests/test_tools.py`

- [ ] **Step 1: Create tools package init**

```python
# src/tools/__init__.py
"""MCP tools for image generation and editing"""
```

- [ ] **Step 2: Write failing test for generate_image tool**

```python
# tests/test_tools.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.tools.generate import generate_image_tool


@pytest.mark.asyncio
async def test_generate_image_tool_url_format():
    with patch('src.tools.generate.OpenAIClient') as mock_client_class, \
         patch('src.tools.generate.ImageHandler') as mock_handler_class:
        
        mock_client = Mock()
        mock_client.generate_image = AsyncMock(return_value="https://example.com/image.png")
        mock_client_class.return_value = mock_client
        
        result = await generate_image_tool(
            prompt="a cat in space",
            model="gpt-4o",
            output_format="url",
            api_key="test-key"
        )
        
        assert result["success"] is True
        assert result["format"] == "url"
        assert result["data"] == "https://example.com/image.png"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_tools.py::test_generate_image_tool_url_format -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.tools.generate'"

- [ ] **Step 4: Write minimal generate_image tool implementation**

```python
# src/tools/generate.py
import logging
from typing import Optional, Literal, Dict
from src.openai_client import OpenAIClient
from src.image_handler import ImageHandler


logger = logging.getLogger(__name__)


async def generate_image_tool(
    prompt: str,
    model: str = "gpt-4o",
    size: str = "1024x1024",
    quality: str = "standard",
    output_format: Literal["url", "file", "base64"] = "url",
    output_path: Optional[str] = None,
    api_key: str = "",
    base_url: str = "https://api.openai.com/v1",
    save_directory: str = "./images"
) -> Dict:
    try:
        client = OpenAIClient(api_key=api_key, base_url=base_url)
        
        image_url = await client.generate_image(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality
        )
        
        handler = ImageHandler(save_directory=save_directory)
        result = await handler.download_image(
            url=image_url,
            output_format=output_format,
            output_path=output_path
        )
        
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
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_tools.py::test_generate_image_tool_url_format -v`
Expected: PASS

- [ ] **Step 6: Write test for file output format**

```python
# tests/test_tools.py (add to existing file)
@pytest.mark.asyncio
async def test_generate_image_tool_file_format():
    with patch('src.tools.generate.OpenAIClient') as mock_client_class, \
         patch('src.tools.generate.ImageHandler') as mock_handler_class:
        
        mock_client = Mock()
        mock_client.generate_image = AsyncMock(return_value="https://example.com/image.png")
        mock_client_class.return_value = mock_client
        
        mock_handler = Mock()
        mock_handler.download_image = AsyncMock(return_value={"format": "file", "data": "./images/image_abc.png"})
        mock_handler_class.return_value = mock_handler
        
        result = await generate_image_tool(
            prompt="a cat in space",
            output_format="file",
            api_key="test-key"
        )
        
        assert result["success"] is True
        assert result["format"] == "file"
        assert "image_abc.png" in result["data"]
```

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/test_tools.py::test_generate_image_tool_file_format -v`
Expected: PASS

- [ ] **Step 8: Commit generate tool**

```bash
git add src/tools/__init__.py src/tools/generate.py tests/test_tools.py
git commit -m "feat: add generate_image MCP tool"
```

---

## Task 6: MCP Tools - Edit Image

**Files:**
- Create: `src/tools/edit.py`

- [ ] **Step 1: Write failing test for edit_image tool**

```python
# tests/test_tools.py (add to existing file)
from src.tools.edit import edit_image_tool


@pytest.mark.asyncio
async def test_edit_image_tool():
    with patch('src.tools.edit.OpenAIClient') as mock_client_class, \
         patch('src.tools.edit.ImageHandler') as mock_handler_class:
        
        mock_client = Mock()
        mock_client.edit_image = AsyncMock(return_value="https://example.com/edited.png")
        mock_client_class.return_value = mock_client
        
        result = await edit_image_tool(
            image_input="https://example.com/original.png",
            prompt="make it blue",
            output_format="url",
            api_key="test-key"
        )
        
        assert result["success"] is True
        assert result["format"] == "url"
        assert result["data"] == "https://example.com/edited.png"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py::test_edit_image_tool -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.tools.edit'"

- [ ] **Step 3: Write minimal edit_image tool implementation**

```python
# src/tools/edit.py
import logging
from typing import Optional, Literal, Dict
from src.openai_client import OpenAIClient
from src.image_handler import ImageHandler


logger = logging.getLogger(__name__)


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
    save_directory: str = "./images"
) -> Dict:
    try:
        client = OpenAIClient(api_key=api_key, base_url=base_url)
        
        image_url = await client.edit_image(
            image_url=image_input,
            prompt=prompt,
            model=model,
            size=size,
            quality=quality
        )
        
        handler = ImageHandler(save_directory=save_directory)
        result = await handler.download_image(
            url=image_url,
            output_format=output_format,
            output_path=output_path
        )
        
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
    except Exception as e:
        logger.error(f"Error editing image: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools.py::test_edit_image_tool -v`
Expected: PASS

- [ ] **Step 5: Commit edit tool**

```bash
git add src/tools/edit.py
git commit -m "feat: add edit_image MCP tool"
```

---

## Task 7: MCP Tools - Server Info

**Files:**
- Create: `src/tools/info.py`

- [ ] **Step 1: Write failing test for get_server_info tool**

```python
# tests/test_tools.py (add to existing file)
from src.tools.info import get_server_info_tool


def test_get_server_info_tool():
    result = get_server_info_tool(
        server_name="gpt-image-mcp",
        server_version="1.0.0",
        transport="stdio",
        default_model="gpt-4o",
        default_size="1024x1024"
    )
    
    assert result["name"] == "gpt-image-mcp"
    assert result["version"] == "1.0.0"
    assert result["transport"] == "stdio"
    assert "gpt-4o" in result["supported_models"]
    assert "url" in result["supported_formats"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py::test_get_server_info_tool -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.tools.info'"

- [ ] **Step 3: Write minimal get_server_info tool implementation**

```python
# src/tools/info.py
from typing import Dict, List


def get_server_info_tool(
    server_name: str = "gpt-image-mcp",
    server_version: str = "1.0.0",
    transport: str = "stdio",
    default_model: str = "gpt-4o",
    default_size: str = "1024x1024"
) -> Dict:
    return {
        "name": server_name,
        "version": server_version,
        "transport": transport,
        "supported_models": ["gpt-4o", "gpt-4-turbo"],
        "supported_formats": ["url", "file", "base64"],
        "config": {
            "default_model": default_model,
            "default_size": default_size
        }
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools.py::test_get_server_info_tool -v`
Expected: PASS

- [ ] **Step 5: Run all tool tests**

Run: `pytest tests/test_tools.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit info tool**

```bash
git add src/tools/info.py
git commit -m "feat: add get_server_info MCP tool"
```

---

## Task 8: MCP Server with stdio Transport

**Files:**
- Create: `src/transports/__init__.py`
- Create: `src/transports/stdio.py`
- Create: `src/server.py`

- [ ] **Step 1: Create transports package init**

```python
# src/transports/__init__.py
"""Transport implementations for MCP server"""
```

- [ ] **Step 2: Write stdio transport implementation**

```python
# src/transports/stdio.py
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server


logger = logging.getLogger(__name__)


async def run_stdio_server(server: Server):
    logger.info("Starting MCP server with stdio transport")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )
```

- [ ] **Step 3: Write main server entry point**

```python
# src/server.py
import asyncio
import logging
import argparse
from mcp.server import Server
from src.config import load_config
from src.tools.generate import generate_image_tool
from src.tools.edit import edit_image_tool
from src.tools.info import get_server_info_tool
from src.transports.stdio import run_stdio_server


def setup_logging(level: str, format_str: str):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_str
    )


async def main():
    parser = argparse.ArgumentParser(description="OpenAI Image MCP Server")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--transport", type=str, default="stdio", choices=["stdio", "http"])
    parser.add_argument("--port", type=int, help="HTTP port (for http transport)")
    parser.add_argument("--host", type=str, help="HTTP host (for http transport)")
    args = parser.parse_args()
    
    config = load_config(
        config_file=args.config,
        transport=args.transport,
        port=args.port,
        host=args.host
    )
    
    setup_logging(config.logging.level, config.logging.format)
    logger = logging.getLogger(__name__)
    
    server = Server(config.server.name)
    
    @server.list_tools()
    async def list_tools():
        return [
            {
                "name": "generate_image",
                "description": "Generate an image from a text prompt",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Image description"},
                        "model": {"type": "string", "default": config.openai.default_model},
                        "size": {"type": "string", "default": config.image.default_size},
                        "quality": {"type": "string", "default": config.image.default_quality},
                        "output_format": {"type": "string", "enum": ["url", "file", "base64"], "default": config.image.default_output_format},
                        "output_path": {"type": "string"}
                    },
                    "required": ["prompt"]
                }
            },
            {
                "name": "edit_image",
                "description": "Edit an existing image with a text prompt",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_input": {"type": "string", "description": "Image URL or path"},
                        "prompt": {"type": "string", "description": "Edit instruction"},
                        "model": {"type": "string", "default": config.openai.default_model},
                        "size": {"type": "string", "default": config.image.default_size},
                        "quality": {"type": "string", "default": config.image.default_quality},
                        "output_format": {"type": "string", "enum": ["url", "file", "base64"], "default": config.image.default_output_format},
                        "output_path": {"type": "string"}
                    },
                    "required": ["image_input", "prompt"]
                }
            },
            {
                "name": "get_server_info",
                "description": "Get server information and configuration",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "generate_image":
            return await generate_image_tool(
                api_key=config.openai.api_key,
                base_url=config.openai.base_url,
                save_directory=config.image.save_directory,
                **arguments
            )
        elif name == "edit_image":
            return await edit_image_tool(
                api_key=config.openai.api_key,
                base_url=config.openai.base_url,
                save_directory=config.image.save_directory,
                **arguments
            )
        elif name == "get_server_info":
            return get_server_info_tool(
                server_name=config.server.name,
                server_version=config.server.version,
                transport=config.server.transport,
                default_model=config.openai.default_model,
                default_size=config.image.default_size
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    if config.server.transport == "stdio":
        await run_stdio_server(server)
    else:
        logger.error(f"Transport {config.server.transport} not yet implemented")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Test server manually with stdio**

Run: `python -m src.server --transport stdio`
Expected: Server starts without errors, waits for input

- [ ] **Step 5: Commit server with stdio transport**

```bash
git add src/transports/__init__.py src/transports/stdio.py src/server.py
git commit -m "feat: add MCP server with stdio transport"
```

---

## Task 9: HTTP Transport (Streamable HTTP)

**Files:**
- Create: `src/transports/http.py`
- Modify: `src/server.py`

- [ ] **Step 1: Write HTTP transport implementation**

```python
# src/transports/http.py
import logging
from mcp.server import Server
from mcp.server.sse import sse_server


logger = logging.getLogger(__name__)


async def run_http_server(server: Server, host: str = "0.0.0.0", port: int = 8000):
    logger.info(f"Starting MCP server with HTTP transport on {host}:{port}")
    
    from starlette.applications import Starlette
    from starlette.routing import Route
    import uvicorn
    
    async def handle_sse(request):
        async with sse_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    
    app = Starlette(
        routes=[
            Route("/mcp", endpoint=handle_sse)
        ]
    )
    
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()
```

- [ ] **Step 2: Update requirements for HTTP support**

```txt
# Add to requirements.txt
starlette>=0.37.0
uvicorn>=0.29.0
```

- [ ] **Step 3: Update server.py to support HTTP transport**

```python
# src/server.py (modify the main function's transport handling)
# Replace the transport handling section with:

    if config.server.transport == "stdio":
        await run_stdio_server(server)
    elif config.server.transport == "http":
        from src.transports.http import run_http_server
        await run_http_server(
            server,
            host=config.http.host,
            port=config.http.port
        )
    else:
        logger.error(f"Unknown transport: {config.server.transport}")
```

- [ ] **Step 4: Install new dependencies**

Run: `pip install starlette uvicorn`
Expected: Packages installed successfully

- [ ] **Step 5: Test HTTP server manually**

Run: `python -m src.server --transport http --port 8000`
Expected: Server starts on http://0.0.0.0:8000

- [ ] **Step 6: Commit HTTP transport**

```bash
git add src/transports/http.py src/server.py requirements.txt
git commit -m "feat: add Streamable HTTP transport support"
```

---

## Task 10: Documentation and Examples

**Files:**
- Create: `README.md`
- Modify: `.env.example`
- Modify: `config.example.json`

- [ ] **Step 1: Write comprehensive README**

```markdown
# OpenAI Image MCP Server

MCP server for image generation and editing using OpenAI Responses API.

## Features

- Text-to-image generation
- Image editing with prompts
- Multiple output formats (URL, file, base64)
- Dual transport modes (stdio, HTTP)
- Flexible configuration management

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Config File

```bash
cp config.example.json config.json
# Edit config.json as needed
```

## Usage

### stdio Mode (Local)

```bash
python -m src.server --transport stdio
```

### HTTP Mode (Remote)

```bash
python -m src.server --transport http --port 8000
```

## MCP Tools

### generate_image

Generate an image from a text prompt.

**Parameters:**
- `prompt` (required): Image description
- `model`: Model to use (default: gpt-4o)
- `size`: Image size (default: 1024x1024)
- `quality`: Image quality (standard/hd)
- `output_format`: Output format (url/file/base64)
- `output_path`: Save path for file output

### edit_image

Edit an existing image with a prompt.

**Parameters:**
- `image_input` (required): Image URL or path
- `prompt` (required): Edit instruction
- `model`: Model to use
- `size`: Output image size
- `quality`: Image quality
- `output_format`: Output format
- `output_path`: Save path

### get_server_info

Get server information and configuration.

## Testing

```bash
pytest tests/ -v
```

## License

MIT
```

- [ ] **Step 2: Commit documentation**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## Task 11: Integration Testing

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test for full workflow**

```python
# tests/test_integration.py
import pytest
import os
from unittest.mock import patch, Mock, AsyncMock
from src.config import load_config
from src.tools.generate import generate_image_tool
from src.tools.edit import edit_image_tool
from src.tools.info import get_server_info_tool


@pytest.mark.asyncio
async def test_full_generate_workflow():
    os.environ["OPENAI_API_KEY"] = "test-key"
    config = load_config()
    
    with patch('src.tools.generate.OpenAIClient') as mock_client_class, \
         patch('src.tools.generate.ImageHandler') as mock_handler_class:
        
        mock_client = Mock()
        mock_client.generate_image = AsyncMock(return_value="https://example.com/image.png")
        mock_client_class.return_value = mock_client
        
        mock_handler = Mock()
        mock_handler.download_image = AsyncMock(return_value={"format": "url", "data": "https://example.com/image.png"})
        mock_handler_class.return_value = mock_handler
        
        result = await generate_image_tool(
            prompt="a cat in space",
            api_key=config.openai.api_key,
            output_format="url"
        )
        
        assert result["success"] is True
        assert result["format"] == "url"
        assert "metadata" in result


@pytest.mark.asyncio
async def test_full_edit_workflow():
    os.environ["OPENAI_API_KEY"] = "test-key"
    config = load_config()
    
    with patch('src.tools.edit.OpenAIClient') as mock_client_class, \
         patch('src.tools.edit.ImageHandler') as mock_handler_class:
        
        mock_client = Mock()
        mock_client.edit_image = AsyncMock(return_value="https://example.com/edited.png")
        mock_client_class.return_value = mock_client
        
        mock_handler = Mock()
        mock_handler.download_image = AsyncMock(return_value={"format": "url", "data": "https://example.com/edited.png"})
        mock_handler_class.return_value = mock_handler
        
        result = await edit_image_tool(
            image_input="https://example.com/original.png",
            prompt="make it blue",
            api_key=config.openai.api_key,
            output_format="url"
        )
        
        assert result["success"] is True
        assert result["format"] == "url"


def test_server_info_workflow():
    result = get_server_info_tool()
    
    assert "name" in result
    assert "version" in result
    assert "supported_models" in result
    assert "supported_formats" in result
```

- [ ] **Step 2: Run integration tests**

Run: `pytest tests/test_integration.py -v`
Expected: All tests PASS

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit integration tests**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for full workflows"
```

---

## Task 12: Final Verification and Cleanup

**Files:**
- All project files

- [ ] **Step 1: Run all tests with coverage**

Run: `pytest tests/ -v --cov=src --cov-report=term-missing`
Expected: All tests PASS, coverage >75%

- [ ] **Step 2: Verify project structure**

Run: `tree -L 3 -I '__pycache__|*.pyc'`
Expected: Structure matches design spec

- [ ] **Step 3: Test stdio mode end-to-end**

Run: `python -m src.server --transport stdio`
Expected: Server starts successfully

- [ ] **Step 4: Test HTTP mode end-to-end**

Run: `python -m src.server --transport http --port 8000`
Expected: Server starts on port 8000

- [ ] **Step 5: Verify configuration loading**

Run: `python -m src.server --config config.example.json --transport stdio`
Expected: Server loads config and starts

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "chore: final verification and cleanup"
```

---

## Spec Coverage Review

**Configuration Management** ✓
- Task 2: Multi-layer config with priority loading
- Environment variables, config files, CLI args

**OpenAI Responses API Integration** ✓
- Task 4: OpenAI client with Responses API
- Image generation and editing via image_generation tool

**Image Handling** ✓
- Task 3: Image download, save, format conversion
- URL, file, base64 output formats
- Retry mechanism

**MCP Tools** ✓
- Task 5: generate_image tool
- Task 6: edit_image tool
- Task 7: get_server_info tool

**Transport Modes** ✓
- Task 8: stdio transport
- Task 9: Streamable HTTP transport

**Testing** ✓
- Unit tests for all modules
- Integration tests for workflows
- Mock OpenAI API calls

**Documentation** ✓
- Task 10: Comprehensive README
- Configuration examples
- Usage instructions

**Error Handling** ✓
- Implemented in all tool functions
- Logging at appropriate levels
- Graceful degradation

All spec requirements covered.

