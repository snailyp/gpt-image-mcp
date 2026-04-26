# FastMCP Migration Design

**Date:** 2026-04-26  
**Status:** Draft  
**Author:** Claude

## Overview

Migrate the OpenAI Image MCP Server from the standard `mcp` library to `fastmcp` framework to simplify code, reduce boilerplate, and improve developer experience while maintaining all existing functionality.

## Goals

1. **Simplify code**: Reduce boilerplate through fastmcp's decorator-based API
2. **Improve DX**: Better type hints, automatic schema generation, and cleaner syntax
3. **Maintain functionality**: Keep all three tools (generate_image, edit_image, get_server_info) working identically
4. **Preserve configuration**: Keep existing config system (env vars, JSON, CLI args)
5. **Support dual transport**: Maintain stdio and remote access (SSE replaces HTTP)

## Non-Goals

- Rewriting business logic in tools/, openai_client.py, or image_handler.py
- Changing the configuration schema or file formats
- Modifying the tool APIs or response formats
- Adding new features (pure refactoring)

## Migration Strategy

**Approach:** Gradual migration (lowest risk)

1. Migrate tool definitions to fastmcp decorators
2. Replace server initialization with FastMCP
3. Use fastmcp's built-in transports (stdio and SSE)
4. Keep existing configuration and business logic unchanged
5. Remove custom transport implementations

## Architecture Changes

### Before (Standard MCP)

```
src/
├── server.py              # Manual tool registration, custom handlers
├── transports/
│   ├── stdio.py          # Custom stdio transport
│   └── http.py           # Custom HTTP/SSE transport
├── tools/
│   ├── generate.py       # Plain async functions
│   ├── edit.py           # Plain async functions
│   └── info.py           # Plain async functions
├── config.py             # Pydantic settings
└── [business logic...]   # OpenAI client, image handler, etc.
```

### After (FastMCP)

```
src/
├── server.py              # FastMCP initialization, minimal code
├── tools/
│   ├── generate.py       # @mcp.tool() decorated functions
│   ├── edit.py           # @mcp.tool() decorated functions
│   └── info.py           # @mcp.tool() decorated functions
├── config.py             # Unchanged
└── [business logic...]   # Unchanged
```

**Removed:**
- `transports/` directory (fastmcp handles this)
- Manual tool registration code (~150 lines)
- Custom transport implementations

## Detailed Design

### 1. Tool Definition Refactoring

**Current Pattern:**
```python
# tools/generate.py
async def generate_image_tool(
    prompt: str,
    model: str,
    size: str,
    quality: str,
    output_format: str,
    output_path: str | None,
    api_key: str,
    base_url: str,
    save_directory: str,
    cloudflare_auth_code: str | None,
    cloudflare_api_url: str | None,
    cloudflare_upload_folder: str | None,
    auto_upload_to_cloudflare: bool,
    timeout: int
) -> dict:
    # Business logic...
```

**New Pattern:**
```python
# tools/generate.py
from fastmcp import Context
from typing import Literal

@mcp.tool()
async def generate_image(
    prompt: str,
    ctx: Context,
    model: str | None = None,
    size: str | None = None,
    quality: Literal["standard", "hd"] | None = None,
    output_format: Literal["url", "file", "base64"] | None = None,
    output_path: str | None = None
) -> dict:
    """Generate an image using OpenAI API based on a text prompt.
    
    Args:
        prompt: Text description of the image to generate
        model: Model to use for generation (default: gpt-4o)
        size: Image size (default: 1024x1024)
        quality: Image quality: standard or hd (default: standard)
        output_format: Output format: url, file, or base64 (default: url)
        output_path: Optional custom path for file output
    """
    config = ctx["config"]
    
    # Apply defaults from config
    model = model or config.openai.default_model
    size = size or config.image.default_size
    quality = quality or config.image.default_quality
    output_format = output_format or config.image.default_output_format
    
    # Call existing business logic
    return await process_image_request(
        prompt=prompt,
        model=model,
        size=size,
        quality=quality,
        output_format=output_format,
        output_path=output_path,
        api_key=config.openai.api_key,
        base_url=config.openai.base_url,
        save_directory=config.image.save_directory,
        cloudflare_auth_code=config.cloudflare.auth_code,
        cloudflare_api_url=config.cloudflare.api_url,
        cloudflare_upload_folder=config.cloudflare.upload_folder,
        auto_upload_to_cloudflare=config.image.auto_upload_to_cloudflare,
        timeout=config.openai.timeout
    )
```

**Benefits:**
- Automatic JSON Schema generation from type hints
- Reduced parameter passing (config via Context)
- Self-documenting with docstrings
- Type safety with Literal types

### 2. Server Initialization

**Current Pattern:**
```python
# server.py (simplified)
from mcp.server import Server

server = Server(config.server.name)

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="generate_image", description="...", inputSchema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "..."},
                "model": {"type": "string", "default": "..."},
                # ... 50+ lines of schema definition
            }
        }),
        # ... more tools
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    if name == "generate_image":
        result = await generate_image_tool(...)
        return [TextContent(type="text", text=json.dumps(result))]
    elif name == "edit_image":
        # ...
    # ... more routing
```

**New Pattern:**
```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("gpt-image-mcp")

# Import tools (registers them automatically)
from src.tools.generate import generate_image
from src.tools.edit import edit_image
from src.tools.info import get_server_info

async def main():
    # Load configuration
    config = load_config(...)
    
    # Setup logging
    setup_logging(level=config.logging.level)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {config.server.name} v{config.server.version}")
    
    # Validate API key
    if not config.openai.api_key:
        raise ValueError("OpenAI API key is required")
    
    # Inject config into context
    mcp.context = {"config": config}
    
    # Run with configured transport
    if config.server.transport == "stdio":
        await mcp.run(transport="stdio")
    elif config.server.transport == "sse":
        await mcp.run(
            transport="sse",
            sse_host=config.http.host,
            sse_port=config.http.port
        )
    else:
        raise ValueError(f"Unsupported transport: {config.server.transport}")
```

**Code Reduction:**
- Before: ~250 lines in server.py
- After: ~50 lines in server.py
- Eliminated: Manual schema definitions, tool routing, response wrapping

### 3. Configuration and Context

**Configuration Loading:** Unchanged
- Keep existing `config.py` with pydantic-settings
- Support env vars, JSON files, CLI args
- Same priority order

**Context Injection:**
```python
# At startup
mcp.context = {
    "config": config  # Entire config object available to all tools
}

# In tool functions
@mcp.tool()
async def some_tool(ctx: Context, ...):
    config = ctx["config"]
    api_key = config.openai.api_key
    # ...
```

**Why Context?**
- Avoids passing 10+ config parameters to each tool
- Centralized configuration access
- Easy to extend with additional context (e.g., shared clients)

### 4. Transport Layer

**Stdio Transport:**
```python
await mcp.run(transport="stdio")
```
- Drop-in replacement for current stdio transport
- Fully compatible with Claude Desktop and other MCP clients
- No code changes needed

**SSE Transport (replaces HTTP):**
```python
await mcp.run(
    transport="sse",
    sse_host=config.http.host,
    sse_port=config.http.port
)
```

**Configuration Update:**
```bash
# .env - change from:
SERVER__TRANSPORT=http

# to:
SERVER__TRANSPORT=sse
```

**Why SSE over HTTP?**
- Better streaming support for long-running operations
- Built into fastmcp (no custom implementation needed)
- Standard MCP transport protocol
- Simpler client integration

**Removed Files:**
- `src/transports/stdio.py` (~30 lines)
- `src/transports/http.py` (~100 lines)

### 5. Error Handling

**Automatic Error Handling:**
- fastmcp automatically catches exceptions in tool functions
- Converts to standard MCP error responses
- No need for try-catch wrappers in server.py

**Tool-Level Error Handling:**
```python
@mcp.tool()
async def generate_image(...) -> dict:
    # Business logic can still raise exceptions
    if not prompt:
        raise ValueError("Prompt is required")
    
    # Or return error dict (existing pattern)
    return {"success": False, "error": "Something went wrong"}
```

**Logging:**
- Keep existing logging setup
- Continue using standard `logging` module in tools
- fastmcp logs transport-level events automatically

### 6. Response Format

**No Changes:**
- Tools continue returning dict objects
- fastmcp automatically serializes to JSON
- Existing response format preserved:

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

## Implementation Plan

### Phase 1: Setup
1. Add fastmcp to requirements.txt
2. Install dependencies
3. Create backup branch

### Phase 2: Tool Migration
1. Refactor `tools/generate.py` to use @mcp.tool()
2. Refactor `tools/edit.py` to use @mcp.tool()
3. Refactor `tools/info.py` to use @mcp.tool()
4. Extract common business logic if needed

### Phase 3: Server Migration
1. Replace Server with FastMCP in server.py
2. Remove manual tool registration
3. Add context injection
4. Update transport initialization

### Phase 4: Cleanup
1. Remove `transports/` directory
2. Update requirements.txt (remove mcp, starlette, uvicorn)
3. Update documentation

### Phase 5: Testing
1. Run existing unit tests
2. Update integration tests for fastmcp
3. Test stdio mode with Claude Desktop
4. Test SSE mode with HTTP client
5. Verify all three tools work correctly

### Phase 6: Documentation
1. Update README.md with fastmcp usage
2. Update configuration examples
3. Add migration notes

## Testing Strategy

### Unit Tests (Unchanged)
- `test_config.py` - Configuration loading
- `test_openai_client.py` - OpenAI API client
- `test_image_handler.py` - Image processing
- Business logic tests remain the same

### Integration Tests (Updated)
```python
# tests/test_fastmcp_integration.py
import pytest
from fastmcp.testing import MCPTestClient

@pytest.mark.asyncio
async def test_generate_image_tool():
    client = MCPTestClient(mcp)
    
    result = await client.call_tool(
        "generate_image",
        {"prompt": "a test image"}
    )
    
    assert result["success"] is True
    assert "data" in result
```

### Manual Testing
1. **Stdio mode**: Test with Claude Desktop
2. **SSE mode**: Test with curl/httpie
3. **All tools**: Verify generate_image, edit_image, get_server_info
4. **Configuration**: Test env vars, JSON config, CLI args
5. **Cloudflare**: Verify image upload still works

### Performance Validation
- Compare response times before/after
- Verify no regression in image generation speed
- Check memory usage

## Migration Risks and Mitigations

### Risk 1: Breaking Changes in fastmcp API
**Mitigation:** Pin fastmcp version in requirements.txt, test thoroughly

### Risk 2: Transport Compatibility Issues
**Mitigation:** Test with real MCP clients (Claude Desktop), keep stdio as primary

### Risk 3: Context Injection Bugs
**Mitigation:** Add validation that config is present in context, fail fast

### Risk 4: Type Hint Mismatches
**Mitigation:** Use mypy for type checking, test schema generation

### Risk 5: SSE Transport Differences from HTTP
**Mitigation:** Document SSE endpoint changes, provide migration guide for clients

## Rollback Plan

If migration fails:
1. Revert to backup branch
2. Keep fastmcp branch for future retry
3. Document issues encountered

Git workflow:
```bash
git checkout -b fastmcp-migration
# ... make changes ...
# If issues:
git checkout main
```

## Success Criteria

1. ✅ All three tools work identically to before
2. ✅ Stdio mode works with Claude Desktop
3. ✅ SSE mode accessible remotely
4. ✅ All existing tests pass
5. ✅ Configuration system unchanged
6. ✅ Code reduced by ~150+ lines
7. ✅ No performance regression

## Future Enhancements (Out of Scope)

After successful migration, consider:
- Using fastmcp's built-in configuration (replace pydantic-settings)
- Adding fastmcp resources for image history
- Leveraging fastmcp prompts for common use cases
- Using fastmcp's dependency injection for shared clients

## References

- [fastmcp Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- Current implementation: `src/server.py`, `src/tools/`
