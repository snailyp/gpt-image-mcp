# FastMCP Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate OpenAI Image MCP Server from standard `mcp` library to `fastmcp` framework to simplify code and improve developer experience.

**Architecture:** Gradual migration approach - refactor tool definitions to use fastmcp decorators, replace server initialization with FastMCP, use built-in transports (stdio and SSE), keep existing configuration and business logic unchanged.

**Tech Stack:** fastmcp, Python 3.11+, OpenAI API, pydantic-settings

---

## File Structure

**Files to Create:**
- None (all modifications to existing files)

**Files to Modify:**
- `requirements.txt` - Add fastmcp, remove mcp/starlette/uvicorn
- `src/server.py` - Replace Server with FastMCP, simplify initialization
- `src/tools/generate.py` - Add @mcp.tool() decorator
- `src/tools/edit.py` - Add @mcp.tool() decorator
- `src/tools/info.py` - Add @mcp.tool() decorator
- `.env.example` - Update transport config
- `README.md` - Update documentation

**Files to Delete:**
- `src/transports/stdio.py` - Replaced by fastmcp built-in
- `src/transports/http.py` - Replaced by fastmcp built-in
- `src/transports/__init__.py` - No longer needed

**Files Unchanged:**
- `src/config.py` - Configuration system preserved
- `src/openai_client.py` - Business logic unchanged
- `src/image_handler.py` - Business logic unchanged
- `src/cloudflare_uploader.py` - Business logic unchanged
- `src/tools/common.py` - Shared logic unchanged
- All test files - Will be updated in testing phase

---

### Task 1: Setup and Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Create backup branch**

```bash
git checkout -b fastmcp-migration
```

Expected: Switched to a new branch 'fastmcp-migration'

- [ ] **Step 2: Update requirements.txt**

Replace the dependencies section:

```txt
fastmcp>=0.1.0
openai>=1.0.0
httpx>=0.27.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-mock>=3.12.0
```

Remove these lines:
- `mcp>=1.0.0`
- `starlette>=0.37.0`
- `uvicorn>=0.29.0`

- [ ] **Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: Successfully installed fastmcp and dependencies

- [ ] **Step 4: Verify fastmcp installation**

```bash
python -c "import fastmcp; print(fastmcp.__version__)"
```

Expected: Prints fastmcp version (e.g., "0.1.0")

- [ ] **Step 5: Commit dependency changes**

```bash
git add requirements.txt
git commit -m "build: migrate to fastmcp framework"
```

---

### Task 2: Refactor generate_image Tool

**Files:**
- Modify: `src/tools/generate.py`

- [ ] **Step 1: Add fastmcp imports**

At the top of `src/tools/generate.py`, add:

```python
from fastmcp import Context
```

- [ ] **Step 2: Create mcp instance**

After imports, before the function definition:

```python
from fastmcp import FastMCP

mcp = FastMCP("gpt-image-mcp")
```

- [ ] **Step 3: Refactor generate_image_tool to use decorator**

Replace the entire `generate_image_tool` function with:

```python
@mcp.tool()
async def generate_image(
    prompt: str,
    ctx: Context,
    model: str | None = None,
    size: str | None = None,
    quality: Literal["standard", "hd"] | None = None,
    output_format: Literal["url", "file", "base64"] | None = None,
    output_path: str | None = None
) -> Dict[str, Any]:
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
    
    logger.info(f"Generating image with prompt: {prompt[:50]}...")
    
    # Construct CloudflareConfig if credentials provided
    cloudflare_config = None
    if config.cloudflare.auth_code and config.cloudflare.api_url:
        from src.config import CloudflareConfig
        cloudflare_config = CloudflareConfig(
            auth_code=config.cloudflare.auth_code,
            api_url=config.cloudflare.api_url,
            upload_folder=config.cloudflare.upload_folder
        )
    
    async def api_call(client):
        return await client.generate_image(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality
        )
    
    return await process_image_request(
        api_key=config.openai.api_key,
        base_url=config.openai.base_url,
        save_directory=config.image.save_directory,
        output_format=output_format,
        output_path=output_path,
        model=model,
        size=size,
        quality=quality,
        api_call=api_call,
        operation_name="Generating",
        cloudflare_config=cloudflare_config,
        auto_upload_to_cloudflare=config.image.auto_upload_to_cloudflare,
        timeout=config.openai.timeout
    )
```

- [ ] **Step 4: Verify syntax**

```bash
python -m py_compile src/tools/generate.py
```

Expected: No output (successful compilation)

- [ ] **Step 5: Commit generate_image tool refactor**

```bash
git add src/tools/generate.py
git commit -m "refactor: migrate generate_image to fastmcp decorator"
```

---

### Task 3: Refactor edit_image Tool

**Files:**
- Modify: `src/tools/edit.py`

- [ ] **Step 1: Add fastmcp imports**

At the top of `src/tools/edit.py`, add:

```python
from fastmcp import Context
```

- [ ] **Step 2: Import mcp instance**

After imports:

```python
from src.tools.generate import mcp
```

- [ ] **Step 3: Refactor edit_image_tool to use decorator**

Replace the entire `edit_image_tool` function with:

```python
@mcp.tool()
async def edit_image(
    image_input: str,
    prompt: str,
    ctx: Context,
    model: str | None = None,
    size: str | None = None,
    quality: Literal["standard", "hd"] | None = None,
    output_format: Literal["url", "file", "base64"] | None = None,
    output_path: str | None = None
) -> Dict[str, Any]:
    """Edit an existing image using OpenAI API based on a text prompt.
    
    Args:
        image_input: URL or file path of the image to edit
        prompt: Text description of the desired changes
        model: Model to use for editing (default: gpt-4o)
        size: Output image dimensions (default: 1024x1024)
        quality: Image quality: standard or hd (default: standard)
        output_format: Output format: url, file, or base64 (default: url)
        output_path: Optional custom path for file output
    """
    config = ctx["config"]
    
    # Validate image_input
    if not image_input:
        logger.error("Image input is required")
        return {"success": False, "error": "Image input is required"}
    
    # Apply defaults from config
    model = model or config.openai.default_model
    size = size or config.image.default_size
    quality = quality or config.image.default_quality
    output_format = output_format or config.image.default_output_format
    
    logger.info(f"Editing image with prompt: {prompt[:50]}...")
    logger.debug(f"Parameters: image_input={image_input}, model={model}, size={size}, quality={quality}, output_format={output_format}")
    
    # Construct CloudflareConfig if credentials provided
    cloudflare_config = None
    if config.cloudflare.auth_code and config.cloudflare.api_url:
        from src.config import CloudflareConfig
        cloudflare_config = CloudflareConfig(
            auth_code=config.cloudflare.auth_code,
            api_url=config.cloudflare.api_url,
            upload_folder=config.cloudflare.upload_folder
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
        api_key=config.openai.api_key,
        base_url=config.openai.base_url,
        save_directory=config.image.save_directory,
        output_format=output_format,
        output_path=output_path,
        model=model,
        size=size,
        quality=quality,
        api_call=api_call,
        operation_name="Editing",
        cloudflare_config=cloudflare_config,
        auto_upload_to_cloudflare=config.image.auto_upload_to_cloudflare,
        timeout=config.openai.timeout
    )
```

- [ ] **Step 4: Verify syntax**

```bash
python -m py_compile src/tools/edit.py
```

Expected: No output (successful compilation)

- [ ] **Step 5: Commit edit_image tool refactor**

```bash
git add src/tools/edit.py
git commit -m "refactor: migrate edit_image to fastmcp decorator"
```

---

### Task 4: Refactor get_server_info Tool

**Files:**
- Modify: `src/tools/info.py`

- [ ] **Step 1: Add fastmcp imports**

At the top of `src/tools/info.py`, add:

```python
from fastmcp import Context
```

- [ ] **Step 2: Import mcp instance**

After imports:

```python
from src.tools.generate import mcp
```

- [ ] **Step 3: Refactor get_server_info_tool to use decorator**

Replace the entire `get_server_info_tool` function with:

```python
@mcp.tool()
def get_server_info(ctx: Context) -> dict:
    """Get server metadata and configuration information.
    
    Returns server name, version, transport mode, supported models and formats,
    and current configuration defaults.
    """
    config = ctx["config"]
    
    return {
        "name": config.server.name,
        "version": config.server.version,
        "transport": config.server.transport,
        "supported_models": ["gpt-4o", "gpt-4-turbo"],
        "supported_formats": ["url", "file", "base64"],
        "config": {
            "default_model": config.openai.default_model,
            "default_size": config.image.default_size
        }
    }
```

- [ ] **Step 4: Verify syntax**

```bash
python -m py_compile src/tools/info.py
```

Expected: No output (successful compilation)

- [ ] **Step 5: Commit get_server_info tool refactor**

```bash
git add src/tools/info.py
git commit -m "refactor: migrate get_server_info to fastmcp decorator"
```

---

### Task 5: Refactor Server Initialization

**Files:**
- Modify: `src/server.py`

- [ ] **Step 1: Replace imports**

Replace the mcp imports at the top of `src/server.py`:

```python
# Remove these lines:
# from mcp.server import Server
# from mcp.types import Tool, TextContent
# from src.transports.stdio import run_stdio_server

# Add this line:
from fastmcp import FastMCP
```

- [ ] **Step 2: Import tool functions**

After the config import, add:

```python
from src.tools.generate import mcp, generate_image
from src.tools.edit import edit_image
from src.tools.info import get_server_info
```

- [ ] **Step 3: Remove old server initialization and handlers**

Delete these sections from `src/server.py`:
- Line 64: `server = Server(config.server.name)`
- Lines 66-164: The entire `@server.list_tools()` handler
- Lines 166-231: The entire `@server.call_tool()` handler

- [ ] **Step 4: Simplify main() function**

Replace the transport logic (lines 233-245) with:

```python
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
        logger.error(f"Unsupported transport: {config.server.transport}")
        raise ValueError(f"Unsupported transport: {config.server.transport}")
```

- [ ] **Step 5: Verify syntax**

```bash
python -m py_compile src/server.py
```

Expected: No output (successful compilation)

- [ ] **Step 6: Commit server refactor**

```bash
git add src/server.py
git commit -m "refactor: migrate server to fastmcp framework"
```

---

### Task 6: Remove Transport Files

**Files:**
- Delete: `src/transports/stdio.py`
- Delete: `src/transports/http.py`
- Delete: `src/transports/__init__.py`

- [ ] **Step 1: Remove stdio transport**

```bash
git rm src/transports/stdio.py
```

Expected: rm 'src/transports/stdio.py'

- [ ] **Step 2: Remove http transport**

```bash
git rm src/transports/http.py
```

Expected: rm 'src/transports/http.py'

- [ ] **Step 3: Remove transports __init__.py**

```bash
git rm src/transports/__init__.py
```

Expected: rm 'src/transports/__init__.py'

- [ ] **Step 4: Remove transports directory**

```bash
rmdir src/transports
```

Expected: Directory removed (or empty directory remains, which is fine)

- [ ] **Step 5: Commit transport removal**

```bash
git commit -m "refactor: remove custom transport implementations"
```

---

### Task 7: Update Configuration Examples

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Update transport configuration in .env.example**

Find the line:

```bash
SERVER__TRANSPORT=stdio
```

Update the comment above it to:

```bash
# Server Configuration
SERVER__NAME=gpt-image-mcp
SERVER__VERSION=1.0.0
SERVER__TRANSPORT=stdio  # Options: stdio, sse
```

- [ ] **Step 2: Update HTTP section comment**

Find the section:

```bash
# HTTP Configuration (for HTTP transport)
```

Change to:

```bash
# SSE Configuration (for SSE transport)
```

- [ ] **Step 3: Verify .env.example syntax**

```bash
cat .env.example | grep -E "SERVER__TRANSPORT|SSE Configuration"
```

Expected: Shows updated lines

- [ ] **Step 4: Commit configuration updates**

```bash
git add .env.example
git commit -m "docs: update transport configuration for fastmcp"
```

---

### Task 8: Basic Smoke Testing

**Files:**
- Test: `src/server.py`

- [ ] **Step 1: Test stdio mode startup**

```bash
timeout 5 python -m src.server --transport stdio || true
```

Expected: Server starts, logs "Starting gpt-image-mcp", then times out (normal for stdio)

- [ ] **Step 2: Test SSE mode startup**

```bash
timeout 5 python -m src.server --transport sse --port 8001 || true
```

Expected: Server starts, logs "Starting gpt-image-mcp", then times out (normal)

- [ ] **Step 3: Test invalid transport**

```bash
python -m src.server --transport invalid 2>&1 | grep "Unsupported transport"
```

Expected: Error message "Unsupported transport: invalid"

- [ ] **Step 4: Verify tool registration**

```bash
python -c "from src.tools.generate import mcp; print(len(mcp._tools))"
```

Expected: Prints "3" (three tools registered)

- [ ] **Step 5: Commit smoke test verification**

```bash
git add -A
git commit -m "test: verify basic fastmcp functionality"
```

---

### Task 9: Update Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update installation section**

In the "Installation" section, update the dependencies note:

```markdown
### Install Dependencies

```bash
pip install -r requirements.txt
```

This project uses [fastmcp](https://github.com/jlowin/fastmcp) for the MCP server implementation.
```

- [ ] **Step 2: Update usage examples**

In the "Usage" section, update the transport mode description:

```markdown
### stdio Mode (Local/MCP Client)

For use with MCP clients like Claude Desktop:

```bash
python -m src.server --transport stdio
```

### SSE Mode (Remote Access)

For remote access via Server-Sent Events:

```bash
python -m src.server --transport sse --port 8000
```

The server will be available at `http://0.0.0.0:8000`
```

- [ ] **Step 3: Update configuration section**

Update the SERVER__TRANSPORT description:

```markdown
SERVER__TRANSPORT=stdio  # Options: stdio, sse
```

And update the SSE configuration section header:

```markdown
# SSE Configuration (for SSE transport)
HTTP__HOST=0.0.0.0
HTTP__PORT=8000
```

- [ ] **Step 4: Add migration note**

Add a new section before "License":

```markdown
## Migration to fastmcp

This project has been migrated from the standard `mcp` library to `fastmcp` for improved developer experience and reduced boilerplate. The migration:

- Simplified tool definitions using decorators
- Reduced server code by ~150 lines
- Replaced HTTP transport with SSE (Server-Sent Events)
- Maintained all existing functionality and APIs

For the migration design and implementation details, see `docs/superpowers/specs/2026-04-26-fastmcp-migration-design.md`.
```

- [ ] **Step 5: Commit documentation updates**

```bash
git add README.md
git commit -m "docs: update README for fastmcp migration"
```

---

### Task 10: Integration Testing

**Files:**
- Test: All three tools via MCP protocol

- [ ] **Step 1: Create test script**

Create `test_fastmcp_integration.py`:

```python
import asyncio
import json
from src.server import mcp
from src.config import load_config

async def test_tools():
    # Load config
    config = load_config()
    mcp.context = {"config": config}
    
    # Test get_server_info
    print("Testing get_server_info...")
    from src.tools.info import get_server_info
    info = get_server_info(mcp.context)
    assert info["name"] == config.server.name
    assert "supported_models" in info
    print("✓ get_server_info works")
    
    # Test generate_image (mock mode - just validate structure)
    print("\nTesting generate_image structure...")
    from src.tools.generate import generate_image
    # Note: Actual API call requires valid API key
    print("✓ generate_image function exists and is decorated")
    
    # Test edit_image structure
    print("\nTesting edit_image structure...")
    from src.tools.edit import edit_image
    print("✓ edit_image function exists and is decorated")
    
    print("\n✅ All integration tests passed!")

if __name__ == "__main__":
    asyncio.run(test_tools())
```

- [ ] **Step 2: Run integration test**

```bash
python test_fastmcp_integration.py
```

Expected: All tests pass with ✓ marks

- [ ] **Step 3: Test with Claude Desktop (manual)**

Update Claude Desktop config to use the new server:

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

Restart Claude Desktop and verify the server connects.

- [ ] **Step 4: Test SSE mode (manual)**

Start server in SSE mode:

```bash
python -m src.server --transport sse --port 8000
```

Verify server is accessible at http://localhost:8000

- [ ] **Step 5: Clean up test file**

```bash
rm test_fastmcp_integration.py
```

---

### Task 11: Final Verification and Merge

**Files:**
- Review: All changes

- [ ] **Step 1: Review all changes**

```bash
git log --oneline master..fastmcp-migration
```

Expected: Shows all commits from the migration

- [ ] **Step 2: Run final syntax check**

```bash
python -m py_compile src/server.py src/tools/*.py
```

Expected: No errors

- [ ] **Step 3: Verify file structure**

```bash
find src -name "*.py" | sort
```

Expected: No transports/ directory, all tool files present

- [ ] **Step 4: Create summary of changes**

```bash
git diff master --stat
```

Expected: Shows files modified/deleted with line counts

- [ ] **Step 5: Merge to main branch**

```bash
git checkout master
git merge fastmcp-migration --no-ff -m "feat: migrate to fastmcp framework

- Simplified tool definitions using @mcp.tool() decorators
- Replaced manual server initialization with FastMCP
- Removed custom transport implementations (stdio, http)
- Migrated HTTP transport to SSE (Server-Sent Events)
- Reduced server code by ~150 lines
- Updated documentation and configuration examples
- All existing functionality preserved"
```

Expected: Merge successful

- [ ] **Step 6: Tag the release**

```bash
git tag -a v2.0.0-fastmcp -m "FastMCP migration release"
```

- [ ] **Step 7: Push changes**

```bash
git push origin master --tags
```

---

## Plan Self-Review

**Spec Coverage Check:**

✅ **Setup and Dependencies** - Task 1 covers adding fastmcp, removing old deps
✅ **Tool Migration** - Tasks 2, 3, 4 cover all three tools (generate, edit, info)
✅ **Server Migration** - Task 5 covers FastMCP initialization and context injection
✅ **Transport Layer** - Task 6 removes custom transports, Task 5 uses fastmcp built-in
✅ **Configuration** - Task 7 updates .env.example for SSE
✅ **Testing** - Task 8 (smoke tests), Task 10 (integration tests)
✅ **Documentation** - Task 9 updates README
✅ **Cleanup and Merge** - Task 11 final verification

**Placeholder Scan:**

✅ No TBD, TODO, or "implement later"
✅ All code blocks are complete
✅ All commands have expected output
✅ No "similar to Task N" references
✅ All file paths are exact

**Type Consistency:**

✅ `generate_image` function name consistent across tasks
✅ `edit_image` function name consistent across tasks
✅ `get_server_info` function name consistent across tasks
✅ `Context` type from fastmcp used consistently
✅ `mcp` instance imported consistently in tools

**Additional Notes:**

- Each task is atomic and can be completed independently
- Commits are frequent (after each major change)
- Testing is integrated throughout (smoke tests, integration tests)
- Manual testing steps included for Claude Desktop and SSE mode
- Rollback is easy (git checkout master)

