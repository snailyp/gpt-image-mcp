# OpenAI Images API Migration Design

**Date**: 2026-04-26  
**Status**: Approved  
**Author**: Claude

## Overview

Migrate image generation and editing functionality from OpenAI Responses API's `image_generation` tool to OpenAI Images API (`client.images.generate()` and `client.images.edit()`). This migration follows a minimal-change approach, replacing only the API call logic while preserving all existing features and interfaces.

## Goals

- Replace Responses API with Images API for image generation and editing
- Maintain 100% backward compatibility with existing tool interfaces
- Preserve all current features: Cloudflare upload, multiple output formats, configuration system
- Minimize code changes to reduce risk and testing overhead

## Non-Goals

- Adding new Images API features (style parameter, n parameter for multiple images)
- Refactoring existing code structure
- Changing tool interfaces or parameter names
- Performance optimization beyond API replacement

## Background

The current implementation uses OpenAI's Responses API with the `image_generation` tool, which returns base64-encoded image data. The migration to Images API will use the same base64 response format (`response_format="b64_json"`) to maintain consistency with existing downstream processing logic.

## Design

### Architecture Changes

**Modified Files**:
- `src/openai_client.py` - Only file requiring changes

**Unchanged Components**:
- `src/tools/generate.py` - Tool interface remains identical
- `src/tools/edit.py` - Tool interface remains identical
- `src/tools/common.py` - Image processing logic unchanged
- `src/image_handler.py` - Format conversion logic unchanged
- `src/cloudflare_uploader.py` - Upload logic unchanged
- `src/config.py` - Configuration structure unchanged

### API Migration Details

#### 1. `generate_image()` Method

**Current Implementation**:
```python
tools = [{"type": "image_generation"}]
response = await self.client.responses.create(
    model=model,
    input=prompt,
    tools=tools
)
image_data = self._extract_image_data_from_response(response)
```

**New Implementation**:
```python
response = await self.client.images.generate(
    prompt=prompt,
    model=model,
    size=size,
    quality=quality,
    response_format="b64_json"
)
image_data = response.data[0].b64_json
```

**Changes**:
- Remove `_get_image_generation_tool()` helper method
- Remove `_extract_image_data_from_response()` helper method
- Direct API call with simpler response extraction
- Use `response_format="b64_json"` to get base64 data

#### 2. `edit_image()` Method

**Current Implementation**:
```python
# Accepts image_data parameter (base64 or URL)
input_content = f"[Image: {image_data[:50]}...]\n{prompt}"
response = await self.client.responses.create(
    model=model,
    input=input_content,
    tools=tools
)
```

**New Implementation**:
```python
# Accept image_url parameter (URL or file path)
# Step 1: Download/read image
if image_url.startswith(('http://', 'https://')):
    image_bytes = await self._download_image(image_url)
else:
    with open(image_url, 'rb') as f:
        image_bytes = f.read()

# Step 2: Convert to PNG if needed
png_bytes = self._ensure_png_format(image_bytes)

# Step 3: Call Images API
response = await self.client.images.edit(
    image=png_bytes,
    prompt=prompt,
    model=model,
    size=size,
    response_format="b64_json"
)
edited_data = response.data[0].b64_json
```

**Changes**:
- Parameter name change: `image_data` → `image_url` (internal only, tool interface unchanged)
- Add image preprocessing: download URL or read local file
- Add PNG format conversion (Images API requires PNG)
- Direct API call with file upload

**New Helper Methods**:
- `_download_image(url: str) -> bytes` - Download image from URL
- `_ensure_png_format(image_bytes: bytes) -> bytes` - Convert to PNG if needed

#### 3. Model Handling

**Approach**: No model name mapping or translation

- Accept any model name passed by the user
- Directly pass model parameter to Images API
- Users configure appropriate model via `OPENAI__DEFAULT_MODEL` environment variable
- Recommended default: `dall-e-3`

**Why**: Keeps implementation simple and allows flexibility for future model additions without code changes.

### Error Handling

**Existing Error Types** (preserved):
- `openai.APIConnectionError` - Network/connection failures
- `openai.APIError` - API-level errors (auth, rate limits, etc.)
- `ValueError` - Data extraction/validation failures

**New Error Scenarios**:
- Image download failure (HTTP errors, timeouts)
- File read failure (file not found, permission denied)
- Image format conversion failure (corrupted image, unsupported format)

**Error Handling Strategy**:
- All errors logged via `logger.error()`
- Exceptions propagated to `process_image_request()` for unified error response formatting
- Maintain existing error response structure: `{"success": false, "error": "message"}`

### Data Flow

**Generate Image Flow** (unchanged externally):
```
User Request → generate_image tool
  → OpenAIClient.generate_image() [MODIFIED: Images API call]
  → process_image_request()
  → ImageHandler (format conversion)
  → CloudflareUploader (optional)
  → Response to user
```

**Edit Image Flow** (unchanged externally):
```
User Request → edit_image tool
  → OpenAIClient.edit_image() [MODIFIED: Images API call + preprocessing]
  → process_image_request()
  → ImageHandler (format conversion)
  → CloudflareUploader (optional)
  → Response to user
```

### Configuration Changes

**Required User Action**:
Users must update `OPENAI__DEFAULT_MODEL` in `.env` or `config.json`:

```bash
# Before (Responses API models)
OPENAI__DEFAULT_MODEL=gpt-4o

# After (Images API models)
OPENAI__DEFAULT_MODEL=dall-e-3
```

**Supported Models**:
- `dall-e-3` (recommended)
- `dall-e-2`
- Any future OpenAI image models

**No Code Changes Required For**:
- Size configurations
- Quality settings
- Output format preferences
- Cloudflare settings
- Timeout values

## Implementation Plan

### Phase 1: Core API Migration
1. Create new branch: `feature/openai-images-api`
2. Modify `OpenAIClient.generate_image()` method
3. Modify `OpenAIClient.edit_image()` method
4. Add helper methods for image preprocessing

### Phase 2: Testing
1. Update unit tests in `tests/test_openai_client.py`
2. Update integration tests in `tests/test_integration.py`
3. Manual testing with real API calls

### Phase 3: Documentation
1. Update README.md with new model requirements
2. Update `.env.example` with `dall-e-3` default
3. Add migration notes for existing users

### Phase 4: Deployment
1. Merge to main branch
2. Tag release version
3. Notify users of configuration changes

## Testing Strategy

### Unit Tests
**File**: `tests/test_openai_client.py`

Test cases to update:
1. `test_generate_image_success` - Mock `client.images.generate()`
2. `test_generate_image_api_error` - Verify error handling
3. `test_edit_image_with_url` - Mock URL download + API call
4. `test_edit_image_with_file` - Mock file read + API call
5. `test_edit_image_png_conversion` - Verify format conversion
6. `test_edit_image_download_failure` - Error handling for bad URLs

### Integration Tests
**File**: `tests/test_integration.py`

Test scenarios:
1. End-to-end image generation with file output
2. End-to-end image editing with URL input
3. End-to-end with Cloudflare upload enabled
4. Error scenarios with invalid inputs

### Manual Testing Checklist
- [ ] Generate image with default settings
- [ ] Generate image with custom size/quality
- [ ] Edit image from URL
- [ ] Edit image from local file
- [ ] Test with Cloudflare upload enabled
- [ ] Test all output formats (url, file, base64)
- [ ] Verify error messages are user-friendly

## Risks and Mitigations

### Risk 1: Images API Behavior Differences
**Impact**: Medium  
**Likelihood**: Low  
**Mitigation**: Thorough testing with real API calls before deployment. Use `response_format="b64_json"` to match current data flow.

### Risk 2: PNG Conversion Issues
**Impact**: Medium  
**Likelihood**: Medium  
**Mitigation**: Use well-tested image library (Pillow). Add comprehensive error handling and logging.

### Risk 3: Breaking Changes for Existing Users
**Impact**: High  
**Likelihood**: Low  
**Mitigation**: Maintain all tool interfaces unchanged. Only require configuration update (model name).

### Risk 4: Image Download Failures
**Impact**: Low  
**Likelihood**: Medium  
**Mitigation**: Reuse existing retry logic from `image_handler.py`. Add timeout configuration.

## Success Criteria

1. All existing tool interfaces work without modification
2. All unit tests pass with updated mocks
3. Integration tests pass with real API calls
4. Cloudflare upload continues to work
5. All output formats (url, file, base64) function correctly
6. Error handling maintains existing behavior
7. Performance is comparable or better than current implementation

## Rollback Plan

If critical issues are discovered:
1. Revert the branch merge
2. Restore previous Responses API implementation
3. Investigate issues in separate branch
4. Re-test before second deployment attempt

The minimal-change approach makes rollback straightforward since only `openai_client.py` is modified.

## Future Enhancements (Out of Scope)

These features are explicitly excluded from this migration but could be added later:
- Support for `style` parameter (vivid/natural)
- Support for `n` parameter (generate multiple images)
- Support for mask images in `edit_image()`
- Automatic model selection based on prompt complexity
- Caching of downloaded images for repeated edits

## Dependencies

**Python Packages** (no changes):
- `openai` - Already installed, Images API available in current version
- `Pillow` - Already installed, used for PNG conversion
- `aiohttp` - Already installed, used for async HTTP requests

**External Services** (no changes):
- OpenAI API - Requires API key with Images API access
- Cloudflare (optional) - Existing integration unchanged

## Appendix: API Comparison

### Responses API (Current)
```python
response = await client.responses.create(
    model="gpt-4o",
    input="a sunset over mountains",
    tools=[{"type": "image_generation"}]
)
# Extract from response.output[0].result
```

### Images API (New)
```python
response = await client.images.generate(
    prompt="a sunset over mountains",
    model="dall-e-3",
    size="1024x1024",
    quality="standard",
    response_format="b64_json"
)
# Extract from response.data[0].b64_json
```

**Key Differences**:
- Simpler, more direct API
- Explicit parameters instead of tool definition
- Cleaner response structure
- Native support for image editing with file upload
