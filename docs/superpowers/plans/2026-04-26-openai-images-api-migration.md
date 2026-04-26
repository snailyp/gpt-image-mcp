# OpenAI Images API Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate from OpenAI Responses API to Images API for image generation and editing with minimal code changes.

**Architecture:** Replace API calls in `OpenAIClient` class only. Add helper methods for image preprocessing (download, PNG conversion) to support `edit_image()`. Maintain all existing interfaces and features.

**Tech Stack:** OpenAI Python SDK, Pillow (image processing), httpx (async HTTP), pytest (testing)

---

## File Structure

**Modified Files:**
- `src/openai_client.py` - Replace Responses API calls with Images API calls, add image preprocessing helpers
- `tests/test_openai_client.py` - Create new test file for OpenAIClient unit tests
- `README.md` - Update model configuration documentation
- `.env.example` - Update default model to dall-e-3

**Unchanged Files:**
- `src/tools/generate.py` - Tool interface unchanged
- `src/tools/edit.py` - Tool interface unchanged
- `src/tools/common.py` - Processing logic unchanged
- `src/image_handler.py` - Format conversion unchanged
- `src/cloudflare_uploader.py` - Upload logic unchanged

---

## Task 1: Create New Branch

**Files:**
- None (git operation)

- [ ] **Step 1: Create feature branch**

```bash
git checkout -b feature/openai-images-api
```

Expected: Switched to a new branch 'feature/openai-images-api'

- [ ] **Step 2: Verify branch**

```bash
git branch --show-current
```

Expected: feature/openai-images-api

---

## Task 2: Add Image Preprocessing Helper - Download Image

**Files:**
- Modify: `src/openai_client.py:182` (after existing `edit_image` method)
- Test: `tests/test_openai_client.py` (new file)

- [ ] **Step 1: Write failing test for image download**

Create `tests/test_openai_client.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.openai_client import OpenAIClient


@pytest.mark.asyncio
async def test_download_image_success():
    """Test successful image download from URL."""
    client = OpenAIClient(api_key="test-key")
    
    mock_response = MagicMock()
    mock_response.content = b"fake_image_data"
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        result = await client._download_image("https://example.com/image.png")
        
        assert result == b"fake_image_data"
        mock_client.get.assert_called_once_with("https://example.com/image.png", timeout=30.0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_openai_client.py::test_download_image_success -v
```

Expected: FAIL with "AttributeError: 'OpenAIClient' object has no attribute '_download_image'"

- [ ] **Step 3: Implement _download_image method**

Add to `src/openai_client.py` after line 181:

```python
    async def _download_image(self, url: str) -> bytes:
        """Download image from URL.
        
        Args:
            url: Image URL to download
            
        Returns:
            Image data as bytes
            
        Raises:
            httpx.HTTPError: If download fails
        """
        import httpx
        
        logger.info(f"Downloading image from {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            logger.info(f"Successfully downloaded image ({len(response.content)} bytes)")
            return response.content
```

- [ ] **Step 4: Add httpx import at top of file**

Modify `src/openai_client.py:3`:

```python
import logging
from typing import Optional, Dict, Any, List
import openai
import httpx
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_openai_client.py::test_download_image_success -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/openai_client.py tests/test_openai_client.py
git commit -m "feat: add image download helper method"
```

---

## Task 3: Add Image Preprocessing Helper - PNG Conversion

**Files:**
- Modify: `src/openai_client.py:202` (after `_download_image` method)
- Test: `tests/test_openai_client.py`

- [ ] **Step 1: Write failing test for PNG conversion**

Add to `tests/test_openai_client.py`:

```python
from io import BytesIO
from PIL import Image


def test_ensure_png_format_already_png():
    """Test PNG conversion when image is already PNG."""
    client = OpenAIClient(api_key="test-key")
    
    # Create a PNG image in memory
    img = Image.new('RGB', (100, 100), color='red')
    png_buffer = BytesIO()
    img.save(png_buffer, format='PNG')
    png_bytes = png_buffer.getvalue()
    
    result = client._ensure_png_format(png_bytes)
    
    # Verify it's still valid PNG
    result_img = Image.open(BytesIO(result))
    assert result_img.format == 'PNG'
    assert result_img.size == (100, 100)


def test_ensure_png_format_convert_jpeg():
    """Test PNG conversion from JPEG."""
    client = OpenAIClient(api_key="test-key")
    
    # Create a JPEG image in memory
    img = Image.new('RGB', (100, 100), color='blue')
    jpeg_buffer = BytesIO()
    img.save(jpeg_buffer, format='JPEG')
    jpeg_bytes = jpeg_buffer.getvalue()
    
    result = client._ensure_png_format(jpeg_bytes)
    
    # Verify it's converted to PNG
    result_img = Image.open(BytesIO(result))
    assert result_img.format == 'PNG'
    assert result_img.size == (100, 100)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_openai_client.py::test_ensure_png_format_already_png -v
pytest tests/test_openai_client.py::test_ensure_png_format_convert_jpeg -v
```

Expected: FAIL with "AttributeError: 'OpenAIClient' object has no attribute '_ensure_png_format'"

- [ ] **Step 3: Implement _ensure_png_format method**

Add to `src/openai_client.py` after `_download_image` method:

```python
    def _ensure_png_format(self, image_bytes: bytes) -> bytes:
        """Ensure image is in PNG format, converting if necessary.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            PNG-formatted image data as bytes
            
        Raises:
            ValueError: If image cannot be processed
        """
        from PIL import Image
        from io import BytesIO
        
        try:
            # Open image from bytes
            img = Image.open(BytesIO(image_bytes))
            
            # If already PNG, return as-is
            if img.format == 'PNG':
                logger.debug("Image is already PNG format")
                return image_bytes
            
            # Convert to PNG
            logger.info(f"Converting image from {img.format} to PNG")
            png_buffer = BytesIO()
            
            # Convert RGBA to RGB if necessary (PNG supports both)
            if img.mode == 'RGBA':
                img.save(png_buffer, format='PNG')
            else:
                # Convert to RGB first for other modes
                rgb_img = img.convert('RGB')
                rgb_img.save(png_buffer, format='PNG')
            
            png_bytes = png_buffer.getvalue()
            logger.info(f"Successfully converted to PNG ({len(png_bytes)} bytes)")
            return png_bytes
            
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            raise ValueError(f"Cannot process image: {e}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_openai_client.py::test_ensure_png_format_already_png -v
pytest tests/test_openai_client.py::test_ensure_png_format_convert_jpeg -v
```

Expected: PASS (both tests)

- [ ] **Step 5: Commit**

```bash
git add src/openai_client.py tests/test_openai_client.py
git commit -m "feat: add PNG format conversion helper"
```

---

## Task 4: Migrate generate_image() to Images API

**Files:**
- Modify: `src/openai_client.py:69-120` (replace `generate_image` method)
- Test: `tests/test_openai_client.py`

- [ ] **Step 1: Write failing test for new generate_image**

Add to `tests/test_openai_client.py`:

```python
@pytest.mark.asyncio
async def test_generate_image_with_images_api():
    """Test image generation using Images API."""
    client = OpenAIClient(api_key="test-key")
    
    # Mock the Images API response
    mock_response = MagicMock()
    mock_data = MagicMock()
    mock_data.b64_json = "fake_base64_image_data"
    mock_response.data = [mock_data]
    
    client.client.images.generate = AsyncMock(return_value=mock_response)
    
    result = await client.generate_image(
        prompt="a sunset",
        model="dall-e-3",
        size="1024x1024",
        quality="standard"
    )
    
    assert result == "fake_base64_image_data"
    client.client.images.generate.assert_called_once_with(
        prompt="a sunset",
        model="dall-e-3",
        size="1024x1024",
        quality="standard",
        response_format="b64_json"
    )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_openai_client.py::test_generate_image_with_images_api -v
```

Expected: FAIL (current implementation uses Responses API)

- [ ] **Step 3: Replace generate_image method**

Replace the entire `generate_image` method in `src/openai_client.py` (lines 69-120):

```python
    async def generate_image(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> str:
        """Generate an image using OpenAI Images API.

        Args:
            prompt: Text description of the image to generate
            model: Model to use for generation (e.g., "dall-e-3", "dall-e-2")
            size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792")
            quality: Image quality ("standard" or "hd")

        Returns:
            Base64-encoded image data

        Raises:
            ValueError: If no image is generated
            openai.APIError: If the API request fails
            openai.APIConnectionError: If connection to API fails
        """
        import time
        start_time = time.time()

        logger.info(f"Generating image with prompt: {prompt[:50]}...")
        logger.debug(f"Parameters: model={model}, size={size}, quality={quality}")

        # Call Images API with error handling
        try:
            response = await self.client.images.generate(
                prompt=prompt,
                model=model,
                size=size,
                quality=quality,
                response_format="b64_json"
            )
        except openai.APIConnectionError as e:
            logger.error(f"Failed to connect to OpenAI API: {e}")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

        # Extract base64 image data from response
        if not response.data or len(response.data) == 0:
            logger.error("No image data in response")
            raise ValueError("No image generated")

        image_data = response.data[0].b64_json

        elapsed = time.time() - start_time
        logger.info(f"Successfully generated image (base64 data length: {len(image_data)}) in {elapsed:.2f}s")
        return image_data
```

- [ ] **Step 4: Remove obsolete helper methods**

Delete these methods from `src/openai_client.py`:
- `_get_image_generation_tool()` (lines 27-33)
- `_extract_image_data_from_response()` (lines 35-67)

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_openai_client.py::test_generate_image_with_images_api -v
```

Expected: PASS

- [ ] **Step 6: Add error handling test**

Add to `tests/test_openai_client.py`:

```python
@pytest.mark.asyncio
async def test_generate_image_api_error():
    """Test error handling when API fails."""
    client = OpenAIClient(api_key="test-key")
    
    client.client.images.generate = AsyncMock(
        side_effect=openai.APIError("API error")
    )
    
    with pytest.raises(openai.APIError):
        await client.generate_image(prompt="test")
```

- [ ] **Step 7: Run error test**

```bash
pytest tests/test_openai_client.py::test_generate_image_api_error -v
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/openai_client.py tests/test_openai_client.py
git commit -m "feat: migrate generate_image to Images API"
```

---

## Task 5: Migrate edit_image() to Images API

**Files:**
- Modify: `src/openai_client.py:122-181` (replace `edit_image` method)
- Test: `tests/test_openai_client.py`

- [ ] **Step 1: Write failing test for edit_image with URL**

Add to `tests/test_openai_client.py`:

```python
@pytest.mark.asyncio
async def test_edit_image_with_url():
    """Test image editing with URL input using Images API."""
    client = OpenAIClient(api_key="test-key")
    
    # Mock download
    client._download_image = AsyncMock(return_value=b"fake_image_bytes")
    
    # Mock PNG conversion
    client._ensure_png_format = MagicMock(return_value=b"fake_png_bytes")
    
    # Mock Images API response
    mock_response = MagicMock()
    mock_data = MagicMock()
    mock_data.b64_json = "edited_base64_data"
    mock_response.data = [mock_data]
    
    client.client.images.edit = AsyncMock(return_value=mock_response)
    
    result = await client.edit_image(
        image_url="https://example.com/image.jpg",
        prompt="add a rainbow",
        model="dall-e-2",
        size="1024x1024",
        quality="standard"
    )
    
    assert result == "edited_base64_data"
    client._download_image.assert_called_once_with("https://example.com/image.jpg")
    client._ensure_png_format.assert_called_once_with(b"fake_image_bytes")
```

- [ ] **Step 2: Write failing test for edit_image with file path**

Add to `tests/test_openai_client.py`:

```python
@pytest.mark.asyncio
async def test_edit_image_with_file_path():
    """Test image editing with local file path."""
    client = OpenAIClient(api_key="test-key")
    
    # Mock file read
    mock_file_data = b"fake_file_bytes"
    
    # Mock PNG conversion
    client._ensure_png_format = MagicMock(return_value=b"fake_png_bytes")
    
    # Mock Images API response
    mock_response = MagicMock()
    mock_data = MagicMock()
    mock_data.b64_json = "edited_base64_data"
    mock_response.data = [mock_data]
    
    client.client.images.edit = AsyncMock(return_value=mock_response)
    
    with patch("builtins.open", create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = mock_file_data
        
        result = await client.edit_image(
            image_url="/path/to/image.png",
            prompt="change colors",
            model="dall-e-2"
        )
    
    assert result == "edited_base64_data"
    client._ensure_png_format.assert_called_once_with(mock_file_data)
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_openai_client.py::test_edit_image_with_url -v
pytest tests/test_openai_client.py::test_edit_image_with_file_path -v
```

Expected: FAIL (current implementation uses Responses API)

- [ ] **Step 4: Replace edit_image method**

Replace the entire `edit_image` method in `src/openai_client.py` (lines 122-181):

```python
    async def edit_image(
        self,
        image_url: str,
        prompt: str,
        model: str = "dall-e-2",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> str:
        """Edit an image using OpenAI Images API.

        Args:
            image_url: URL or local file path of the image to edit
            prompt: Text description of the edits to make
            model: Model to use for editing (e.g., "dall-e-2")
            size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792")
            quality: Image quality ("standard" or "hd")

        Returns:
            Base64-encoded edited image data

        Raises:
            ValueError: If no image is generated or file cannot be read
            openai.APIError: If the API request fails
            openai.APIConnectionError: If connection to API fails
        """
        logger.info(f"Editing image with prompt: {prompt[:50]}...")
        logger.debug(f"Parameters: image_url={image_url}, model={model}, size={size}, quality={quality}")

        # Step 1: Get image bytes (download from URL or read from file)
        try:
            if image_url.startswith(('http://', 'https://')):
                logger.info(f"Downloading image from URL: {image_url}")
                image_bytes = await self._download_image(image_url)
            else:
                logger.info(f"Reading image from file: {image_url}")
                with open(image_url, 'rb') as f:
                    image_bytes = f.read()
        except FileNotFoundError as e:
            logger.error(f"Image file not found: {image_url}")
            raise ValueError(f"Image file not found: {image_url}")
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            raise ValueError(f"Failed to load image: {e}")

        # Step 2: Ensure PNG format
        try:
            png_bytes = self._ensure_png_format(image_bytes)
        except ValueError as e:
            logger.error(f"Failed to convert image to PNG: {e}")
            raise

        # Step 3: Call Images API with error handling
        try:
            from io import BytesIO
            
            response = await self.client.images.edit(
                image=BytesIO(png_bytes),
                prompt=prompt,
                model=model,
                size=size,
                response_format="b64_json"
            )
        except openai.APIConnectionError as e:
            logger.error(f"Failed to connect to OpenAI API: {e}")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

        # Extract base64 image data from response
        if not response.data or len(response.data) == 0:
            logger.error("No image data in response")
            raise ValueError("No image generated")

        edited_image_data = response.data[0].b64_json
        logger.info(f"Successfully edited image (base64 data length: {len(edited_image_data)})")
        return edited_image_data
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_openai_client.py::test_edit_image_with_url -v
pytest tests/test_openai_client.py::test_edit_image_with_file_path -v
```

Expected: PASS (both tests)

- [ ] **Step 6: Add error handling test**

Add to `tests/test_openai_client.py`:

```python
@pytest.mark.asyncio
async def test_edit_image_file_not_found():
    """Test error handling when file doesn't exist."""
    client = OpenAIClient(api_key="test-key")
    
    with pytest.raises(ValueError, match="Image file not found"):
        await client.edit_image(
            image_url="/nonexistent/file.png",
            prompt="test"
        )
```

- [ ] **Step 7: Run error test**

```bash
pytest tests/test_openai_client.py::test_edit_image_file_not_found -v
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/openai_client.py tests/test_openai_client.py
git commit -m "feat: migrate edit_image to Images API"
```

---

## Task 6: Run All Tests

**Files:**
- Test: `tests/test_openai_client.py`

- [ ] **Step 1: Run all unit tests**

```bash
pytest tests/test_openai_client.py -v
```

Expected: All tests PASS

- [ ] **Step 2: Run tests with coverage**

```bash
pytest tests/test_openai_client.py -v --cov=src.openai_client --cov-report=term-missing
```

Expected: Coverage > 80% for openai_client.py

- [ ] **Step 3: Fix any failing tests**

If any tests fail, debug and fix them before proceeding.

---

## Task 7: Update Configuration Documentation

**Files:**
- Modify: `README.md:26-27, 49-51, 133-136, 223-224`
- Modify: `.env.example:3`

- [ ] **Step 1: Update README model references**

Modify `README.md` line 26-27:

```markdown
- **Text-to-Image Generation**: Create images from text prompts using DALL-E 3 or DALL-E 2
- **Image Editing**: Modify existing images with natural language instructions
```

- [ ] **Step 2: Update README configuration section**

Modify `README.md` lines 49-51:

```bash
# OpenAI Configuration
OPENAI__API_KEY=sk-your-api-key-here
OPENAI__BASE_URL=https://api.openai.com/v1
OPENAI__DEFAULT_MODEL=dall-e-3
OPENAI__TIMEOUT=60
```

- [ ] **Step 3: Update README tool documentation**

Modify `README.md` lines 133-136:

```markdown
- `model` (string, optional): Model to use (default: `dall-e-3`)
  - Supported: `dall-e-3`, `dall-e-2`
- `size` (string, optional): Image dimensions (default: `1024x1024`)
  - Supported: `1024x1024`, `1792x1024`, `1024x1792`
```

- [ ] **Step 4: Update README supported models**

Modify `README.md` lines 223-224:

```json
  "supported_models": ["dall-e-3", "dall-e-2"],
  "supported_formats": ["url", "file", "base64"],
```

- [ ] **Step 5: Update .env.example**

Modify `.env.example` line 3:

```bash
OPENAI__DEFAULT_MODEL=dall-e-3
```

- [ ] **Step 6: Commit documentation updates**

```bash
git add README.md .env.example
git commit -m "docs: update model configuration for Images API"
```

---

## Task 8: Add Migration Notes to README

**Files:**
- Modify: `README.md:404` (after "Migration to fastmcp" section)

- [ ] **Step 1: Add migration section**

Add to `README.md` after line 413:

```markdown
## Migration to OpenAI Images API

This project has migrated from OpenAI's Responses API with `image_generation` tool to the dedicated Images API (`client.images.generate()` and `client.images.edit()`). The migration:

- Simplified API calls and response handling
- Improved error messages and debugging
- Maintained 100% backward compatibility with tool interfaces
- Requires model configuration update (see below)

### Configuration Update Required

**Action Required:** Update your `OPENAI__DEFAULT_MODEL` configuration:

**Before:**
```bash
OPENAI__DEFAULT_MODEL=gpt-4o
```

**After:**
```bash
OPENAI__DEFAULT_MODEL=dall-e-3
```

**Supported Models:**
- `dall-e-3` (recommended) - Latest model with best quality
- `dall-e-2` - Previous generation model

All other configuration remains unchanged. For migration design details, see `docs/superpowers/specs/2026-04-26-openai-images-api-migration-design.md`.
```

- [ ] **Step 2: Commit migration notes**

```bash
git add README.md
git commit -m "docs: add Images API migration notes"
```

---

## Task 9: Manual Testing

**Files:**
- None (manual testing)

- [ ] **Step 1: Update local .env file**

Edit `.env` and change:

```bash
OPENAI__DEFAULT_MODEL=dall-e-3
```

- [ ] **Step 2: Test generate_image with real API**

Run the server and test image generation:

```bash
python -m src.server --transport stdio
```

Send a test request through your MCP client or test script to generate an image.

Expected: Image generated successfully with base64 data

- [ ] **Step 3: Test edit_image with URL**

Test image editing with a URL input.

Expected: Image edited successfully

- [ ] **Step 4: Test edit_image with local file**

Test image editing with a local file path.

Expected: Image edited successfully

- [ ] **Step 5: Test Cloudflare upload**

If Cloudflare is configured, test with `output_format="url"`.

Expected: Image uploaded to Cloudflare and URL returned

- [ ] **Step 6: Test error scenarios**

Test with invalid inputs (bad URL, missing file, invalid model).

Expected: Appropriate error messages returned

- [ ] **Step 7: Document test results**

Create a simple test log noting what was tested and results.

---

## Task 10: Final Review and Merge

**Files:**
- None (git operations)

- [ ] **Step 1: Review all changes**

```bash
git diff master...feature/openai-images-api
```

Expected: Only `src/openai_client.py`, `tests/test_openai_client.py`, `README.md`, `.env.example` modified

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 3: Check git status**

```bash
git status
```

Expected: Working tree clean, all changes committed

- [ ] **Step 4: Push branch**

```bash
git push -u origin feature/openai-images-api
```

Expected: Branch pushed successfully

- [ ] **Step 5: Merge to master**

```bash
git checkout master
git merge feature/openai-images-api
```

Expected: Fast-forward merge successful

- [ ] **Step 6: Push master**

```bash
git push origin master
```

Expected: Master updated successfully

- [ ] **Step 7: Tag release**

```bash
git tag -a v2.0.0 -m "feat: migrate to OpenAI Images API"
git push origin v2.0.0
```

Expected: Tag created and pushed

---

## Self-Review Checklist

**Spec Coverage:**
- ✅ Task 2-3: Image preprocessing helpers (download, PNG conversion)
- ✅ Task 4: Migrate generate_image() to Images API
- ✅ Task 5: Migrate edit_image() to Images API
- ✅ Task 6: Unit tests for all new functionality
- ✅ Task 7-8: Documentation updates (README, .env.example, migration notes)
- ✅ Task 9: Manual testing with real API
- ✅ Task 10: Merge and release

**Placeholder Scan:**
- ✅ No TBD, TODO, or "implement later" placeholders
- ✅ All code blocks contain complete implementations
- ✅ All test cases have actual assertions
- ✅ All commands have expected outputs

**Type Consistency:**
- ✅ `_download_image(url: str) -> bytes` - consistent across all tasks
- ✅ `_ensure_png_format(image_bytes: bytes) -> bytes` - consistent across all tasks
- ✅ `generate_image()` returns `str` (base64) - consistent with design
- ✅ `edit_image()` parameter `image_url: str` - consistent across all tasks
- ✅ All API responses use `response.data[0].b64_json` - consistent pattern

**Test Coverage:**
- ✅ Unit tests for helper methods (_download_image, _ensure_png_format)
- ✅ Unit tests for generate_image (success and error cases)
- ✅ Unit tests for edit_image (URL, file path, error cases)
- ✅ Manual testing checklist for integration scenarios

All requirements from the spec are covered. No gaps identified.
