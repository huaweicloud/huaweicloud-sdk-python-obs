# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the HuaweiCloud OBS (Object Storage Service) Python SDK (`esdk-obs-python`), version 3.25.8. It provides a comprehensive Python interface for interacting with HuaweiCloud's object storage service.

### Key Architecture

The SDK follows a **layered client-server architecture**:

1. **Main Entry Point**: `ObsClient` (src/obs/client.py) - Primary interface for all OBS operations
2. **HTTP Layer** (src/obs/http.py): Abstracted HTTP communication with connection pooling
3. **Authentication** (src/obs/auth.py): Multiple auth methods (AK/SK, security tokens, ECS agency)
4. **Data Models** (src/obs/model.py): Type-safe request/response objects for all OBS APIs
5. **Converters** (src/obs/convertor.py): XML serialization/deserialization for API payloads
6. **Transfer System** (src/obs/transfer.py, src/obs/posix_transfer.py): Resumable uploads/downloads with progress tracking
7. **Crypto Client** (src/obs/crypto_client.py): Client-side encryption support

### Modular Components

- **BucketClient** (src/obs/bucket.py): Bucket-specific operations (bucket-scoped client)
- **WorkflowClient** (src/obs/workflow.py): Service orchestration APIs
- **Cache System** (src/obs/cache.py): Local caching for performance optimization
- **Security Providers**: Pluggable authentication framework
- **Progress Tracking** (src/obs/progress.py): Callback system for upload/download progress

## Development Commands

### Installation

```bash
# Install from source
cd src
python setup.py install

# Install dependencies
pip install -r requirements.txt  # if available, or use setup.py dependencies
```

### Running Tests

**Unit Tests** (no OBS credentials required):
```bash
cd src/tests
python3 -m pytest ut/ -v
```

**Integration Tests** (requires OBS credentials in `test_config.json`):
```bash
cd src/tests
python3 -m pytest test_obs_client.py -v
python3 -m pytest . -v  # Run all integration tests
```

**Run specific test file**:
```bash
cd src/tests
python3 -m pytest ut/test_tag_model.py -v
python3 -m pytest test_object_tagging.py -v
```

**Test with coverage**:
```bash
cd src/tests
python3 -m pytest --cov=obs ut/
```

### Test Configuration

Integration tests require `src/tests/test_config.json` with:
> **Note**: The `test_config.json` file must exist in the `src/tests/` directory before running integration tests.
- `ak`: Access Key ID
- `sk`: Secret Access Key
- `endpoint`: OBS service endpoint
- `bucketName`: Default test bucket
- `test_files`: File size configurations for tests (1k, 99k, 1M, 100M)

## Code Organization Patterns

### Adding New Features

When adding new OBS API features:

1. **Add models** in `src/obs/model.py`:
   - Request models (extend `BaseModel`)
   - Response models (extend `BaseModel`)
   - Header models for API-specific headers

2. **Add converter methods** in `src/obs/convertor.py`:
   - `trans_<operation>()`: Convert request parameters to HTTP request format
   - `parse<Operation>()`: Parse HTTP response into model objects

3. **Add client methods** in `src/obs/client.py`:
   - Use `@funcCache` decorator for caching
   - Return response model objects
   - Support both positional and keyword arguments

4. **Add constants** in `src/obs/const.py`:
   - API endpoint paths
   - Parameter names
   - Header names

5. **Update exports** in `src/obs/__init__.py`

### XML Conversion Pattern

XML handling follows this pattern:
```python
# In convertor.py
def trans_new_feature(self, **kwargs):
    # Convert input to HTTP request format
    return {'pathArgs': {...}, 'headers': {...}, 'entity': xml_string}

def parseNewFeature(self, xml_body):
    # Parse XML response into model objects
    return ResponseModel(...)
```

### Authentication System

The SDK supports flexible authentication via **security providers**:
- Direct AK/SK credentials
- Environment variables
- ECS agency (with IMDSv2 support)
- Custom security providers

See `src/obs/auth.py` and `src/obs/loadtoken.py` for implementation.

## Important Design Patterns

### Thread Safety
- Uses thread-local storage for signature negotiation
- Lock-based caching system (`src/obs/locks.py`)
- Thread-safe HTTP connection pooling

### Error Handling
- All API responses wrapped in response model objects
- HTTP errors logged at ERROR level
- Signature negotiation failures handled gracefully

### Retry Logic
- Built into HTTP layer
- Supports configurable retry counts
- Resumable uploads/downloads use checkpoint files

### Progress Callbacks
- Supported on upload/download operations
- Progress amount calculated automatically
- Callback functions receive progress updates

## Recent Feature Additions

Based on version history, recent features include:
- Object tagging ( getObjectTagging, setObjectTagging, deleteObjectTagging )
- Custom domain management
- Bucket Public Access Block (BPA)
- CRC64 data integrity verification
- Access label management
- Client-side encryption (CryptoObsClient)

## Testing Philosophy

- **Unit tests**: Isolated component testing in `tests/ut/`
- **Integration tests**: Full API testing with real OBS service
- **Test data generation**: Utilities in `tests/conftest.py`
- **Data integrity**: SHA256 verification for file operations

## Version Management

Version format: `Main.Version.Year.Month` (e.g., 3.25.8)
- Update version in `src/setup.py`
- Maintain changelog in `README.md`
