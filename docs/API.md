# ReDSL API Documentation

## Overview

ReDSL API provides REST endpoints for code analysis, refactoring, and quality checks. The API is versioned to ensure backward compatibility.

## Base URL

- **Development**: `http://localhost:8002`
- **API v1**: `http://localhost:8002/v1`
- **Legacy**: `http://localhost:8002` (without versioning for backward compatibility)

## Authentication

Currently, the API does not require authentication. JWT authentication will be added in future versions.

## API Versioning

### v1 (Current)

All endpoints are available under `/v1/` prefix:

```bash
# Health check (v1)
GET http://localhost:8002/v1/health

# Scan remote repository (v1)
POST http://localhost:8002/v1/cqrs/scan/remote

# Query scan status (v1)
GET http://localhost:8002/v1/cqrs/query/scan/status?repo_url=...
```

### Legacy (Deprecated)

Legacy endpoints are available without versioning for backward compatibility:

```bash
# Health check (legacy)
GET http://localhost:8002/health

# Scan remote repository (legacy)
POST http://localhost:8002/cqrs/scan/remote
```

**Note**: Legacy endpoints will be removed in future versions. Use `/v1/` endpoints.

## Documentation

- **Swagger UI**: `http://localhost:8002/v1/docs`
- **ReDoc**: `http://localhost:8002/v1/redoc`
- **OpenAPI Spec**: `http://localhost:8002/v1/openapi.json`

## Endpoints

### Health

#### GET /v1/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Scan

#### POST /v1/cqrs/scan/remote

Scan a remote Git repository.

**Request Body:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "branch": "main",
  "depth": 1,
  "async_mode": false
}
```

**Parameters:**
- `repo_url` (required): Git repository URL
- `branch` (optional): Branch to checkout (default: auto-detected from GitHub API)
- `depth` (optional): Clone depth (default: 1)
- `async_mode` (optional): Async mode - returns ID, check status via query API (default: false)

**Response (sync mode):**
```json
{
  "status": "success",
  "data": {
    "total_files": 604,
    "total_lines": 100481,
    "avg_cc": 7.7,
    "critical_count": 133,
    "alerts": [...],
    "top_issues": [...],
    "summary": "604 plików, 100 481 linii kodu, średnia CC=7.7, 133 krytycznych problemów"
  }
}
```

**Response (async mode):**
```json
{
  "status": "accepted",
  "aggregate_id": "scan:https://github.com/owner/repo",
  "correlation_id": "...",
  "message": "Scan rozpoczety w tle (CQRS Command)",
  "check_status_url": "/cqrs/query/scan/status?repo_url=...",
  "websocket": "ws://localhost:8002/ws/cqrs/events"
}
```

#### GET /v1/cqrs/query/scan/status

Query scan status for a repository.

**Query Parameters:**
- `repo_url` (required): Git repository URL

**Response:**
```json
{
  "status": "in_progress",
  "phase": "analyze",
  "progress_percent": 50,
  "message": "Analyzing code...",
  "data": {
    "total_files": 0,
    "total_lines": 0,
    "avg_cc": 0,
    "critical_count": 0
  }
}
```

**Status values:**
- `in_progress`: Scan is running
- `completed`: Scan finished successfully
- `failed`: Scan failed
- `not_found`: No scan found for this repository

### CQRS Queries

#### GET /v1/cqrs/query/project/health

Query project health metrics.

**Query Parameters:**
- `repo_url` (required): Git repository URL

#### GET /v1/cqrs/query/events/recent

Query recent events from event store.

#### GET /v1/cqrs/query/aggregate/history

Query event history for an aggregate.

**Query Parameters:**
- `aggregate_id` (required): Aggregate ID

#### GET /v1/cqrs/query/projections/list

List all available projections.

### Refactor

#### POST /v1/refactor

Run refactoring on a project.

**Request Body:**
```json
{
  "project_dir": ".",
  "max_actions": 3
}
```

### PyQual

#### POST /v1/pyqual/analyze

Analyze Python code quality without LLM.

**Request Body:**
```json
{
  "project_dir": "."
}
```

#### POST /v1/pyqual/fix

Apply automatic quality fixes.

**Request Body:**
```json
{
  "project_dir": "."
}
```

### Examples

#### GET /v1/examples

List packaged example scenarios.

#### GET /v1/examples/{name}/yaml

Get raw YAML data for an example.

#### POST /v1/examples/run

Run a packaged example scenario.

### Debug

#### GET /v1/debug/config

Get configuration info.

#### GET /v1/debug/decisions

Get DSL decisions for a project.

### Webhook

#### POST /v1/webhook/push

GitHub push webhook endpoint.

## WebSocket

### WS /v1/ws/cqrs/events

WebSocket endpoint for real-time CQRS events.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8002/v1/ws/cqrs/events');

// Subscribe to scan aggregate
ws.send(JSON.stringify({
  type: 'subscribe',
  aggregate_id: 'scan:https://github.com/owner/repo'
}));

// Handle events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'event') {
    console.log('Event:', data.data.event_type);
    console.log('Payload:', data.data.payload);
  }
};
```

**Event Types:**
- `ScanStarted`: Scan initiated
- `ScanProgress`: Scan progress update
- `ScanCompleted`: Scan finished
- `ScanFailed`: Scan failed
- `RefactorStarted`: Refactoring initiated
- `RefactorProgress`: Refactoring progress
- `RefactorCompleted`: Refactoring finished
- `RefactorFailed`: Refactoring failed

## Testing

Run API tests:

```bash
# Run all API tests
pytest tests/api/test_api_v1.py -v

# Run specific test class
pytest tests/api/test_api_v1.py::TestAPIVersioning -v

# Run specific test
pytest tests/api/test_api_v1.py::TestScanEndpoints::test_v1_scan_remote_sync_mode -v
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `202`: Accepted (async operations)
- `400`: Bad Request
- `404`: Not Found
- `422`: Unprocessable Entity
- `500`: Internal Server Error

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Currently, there is no rate limiting. This will be added in future versions.

## CORS

The API allows CORS from all origins for development purposes. This will be restricted in production deployments.

## Examples

### Scan Repository (Sync Mode)

```bash
curl -X POST http://localhost:8002/v1/cqrs/scan/remote \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/oqlos/testql",
    "branch": "main",
    "depth": 1,
    "async_mode": false
  }'
```

### Scan Repository (Async Mode)

```bash
curl -X POST http://localhost:8002/v1/cqrs/scan/remote \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/oqlos/testql",
    "async_mode": true
  }'
```

### Query Scan Status

```bash
curl "http://localhost:8002/v1/cqrs/query/scan/status?repo_url=https://github.com/oqlos/testql"
```

### Health Check

```bash
curl http://localhost:8002/v1/health
```

## Migration Guide

### Migrating from Legacy to v1

1. Update base URL to include `/v1/` prefix
2. Update documentation references
3. Test with v1 endpoints before deploying
4. Monitor for deprecation warnings

Example:
```python
# Legacy
response = requests.post('http://localhost:8002/cqrs/scan/remote', json=payload)

# v1
response = requests.post('http://localhost:8002/v1/cqrs/scan/remote', json=payload)
```

## Changelog

### v1.0.0 (Current)
- Initial API versioning
- Added `/v1/` prefix to all endpoints
- Legacy endpoints maintained for backward compatibility
- Comprehensive OpenAPI documentation
- API tests added
