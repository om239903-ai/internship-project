# HubSpot Deal Extraction Service - API Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URLs](#base-urls)
4. [Common Response Formats](#common-response-formats)
5. [API Endpoints](#api-endpoints)
6. [Health & Stats Endpoints](#health--stats-endpoints)
7. [Error Handling](#error-handling)
8. [Examples](#examples)
9. [Rate Limiting](#rate-limiting)
10. [Changelog](#changelog)

## 🔍 Overview

The HubSpot Deal Extraction Service provides a REST API for extracting deal data from HubSpot CRM instances. It supports batch processing, progress tracking, and flexible configuration for deal properties and associations.

### API Version
- **Version**: 1.0.0
- **Base Path**: `/api/v1`
- **Content Type**: `application/json`
- **Documentation**: Available at `/docs` (Swagger UI)

### Key Features
- **Batch Deal Extraction**: Extract all deals from HubSpot with pagination support
- **Progress Tracking**: Real-time monitoring of extraction progress and statistics
- **Flexible Configuration**: Choose which properties and associations to extract
- **Error Resilience**: Automatic retry logic and detailed error reporting
- **Rate Limit Management**: Intelligent handling of HubSpot API rate limits
- **Multi-tenant Support**: Organization-level isolation for enterprise deployments

## 🔐 Authentication

The service uses HubSpot OAuth 2.0 access tokens for authenticating with the HubSpot API. Each scan request must include a valid HubSpot access token.

### Required Credentials
- **HubSpot Access Token**: OAuth 2.0 Bearer token with appropriate scopes
- **Organization ID**: (Optional) For multi-tenant deployments
- **Scan ID**: Unique identifier for tracking extraction jobs

### Required HubSpot Permissions
- `crm.objects.deals.read` - Read access to deals
- `crm.schemas.deals.read` - (Optional) Access to deal property schemas
- `crm.objects.contacts.read` - (Optional) For contact associations
- `crm.objects.companies.read` - (Optional) For company associations

### Authentication Headers
```
Content-Type: application/json
```

**Note**: HubSpot authentication is passed in the request body `config.auth` object, not in headers.

## 🌐 Base URLs

### Development
```
http://localhost:8000
```

### Staging
```
https://staging-api.hubspot-extractor.com
```

### Production
```
https://api.hubspot-extractor.com
```

### Swagger Documentation
```
http://localhost:8000/docs
```

## 📊 Common Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2025-09-29T10:30:00Z"
}
```

### Error Response (Validation)
```json
{
  "status": "error",
  "message": "Input validation failed",
  "errors": {
    "config.auth.hubspot_access_token": "Field is required",
    "config.scanId": "Must be alphanumeric with hyphens/underscores only"
  },
  "timestamp": "2025-09-29T10:30:00Z"
}
```

### Error Response (Application Logic)
```json
{
  "status": "error",
  "error_code": "HUBSPOT_AUTH_FAILED",
  "message": "Failed to authenticate with HubSpot API",
  "details": {
    "hubspot_error": "Invalid access token",
    "status_code": 401
  },
  "timestamp": "2025-09-29T10:30:00Z"
}
```

### Pagination Response
```json
{
  "pagination": {
    "current_page": 1,
    "page_size": 100,
    "total_items": 2543,
    "total_pages": 26,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null,
    "next_cursor": "NTI1Cg%3D%3D"
  }
}
```

## 🔍 Scan Endpoints

### 1. Start Deal Extraction

**POST** `/scan/start`

Initiates a new HubSpot deal extraction process for the specified configuration.

#### Request Body
```json
{
  "config": {
    "scanId": "hubspot-deals-2025-q3",
    "type": ["hubspot_deals"],
    "auth": {
      "hubspot_access_token": "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    },
    "organizationId": "org_123456",
    "properties": [
      "dealname",
      "amount",
      "dealstage",
      "pipeline",
      "closedate",
      "createdate",
      "hs_lastmodifieddate",
      "hubspot_owner_id",
      "dealtype"
    ],
    "includeAssociations": true,
    "associationTypes": [
      "contacts",
      "companies",
      "line_items"
    ],
    "filters": {
      "includeArchived": false,
      "pipelineId": null,
      "dealstage": null,
      "dateFilter": {
        "property": "createdate",
        "startDate": "2024-01-01",
        "endDate": "2025-12-31"
      }
    },
    "batchSize": 100
  }
}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config.scanId` | string | Yes | Unique identifier for the scan (alphanumeric, hyphens, underscores only, max 255 chars) |
| `config.type` | array | Yes | Service types to scan (must include "hubspot_deals") |
| `config.auth.hubspot_access_token` | string | Yes | HubSpot OAuth 2.0 access token |
| `config.organizationId` | string | No | Organization identifier for multi-tenant setups |
| `config.properties` | array | No | List of deal properties to extract (defaults to standard properties) |
| `config.includeAssociations` | boolean | No | Whether to include associated records (default: false) |
| `config.associationTypes` | array | No | Types of associations to include (contacts, companies, line_items) |
| `config.filters.includeArchived` | boolean | No | Include archived deals (default: false) |
| `config.filters.pipelineId` | string | No | Filter by specific pipeline ID |
| `config.filters.dealstage` | string | No | Filter by specific deal stage |
| `config.filters.dateFilter` | object | No | Filter deals by date property |
| `config.batchSize` | integer | No | Batch size for processing (default: 100, max: 100) |

#### Response
```json
{
  "message": "HubSpot deal extraction started",
  "scanId": "hubspot-deals-2025-q3",
  "status": "started",
  "jobId": "job_abc123xyz",
  "estimatedDuration": "5-10 minutes"
}
```

#### Status Codes
- **202**: Extraction started successfully
- **400**: Invalid request data (validation errors)
- **409**: Extraction already in progress for this scanId
- **500**: Internal server error

#### Example Errors
```json
{
  "status": "error",
  "message": "Extraction already in progress",
  "error_code": "SCAN_IN_PROGRESS",
  "details": {
    "scanId": "hubspot-deals-2025-q3",
    "currentStatus": "running",
    "startedAt": "2025-09-29T10:15:00Z"
  },
  "timestamp": "2025-09-29T10:30:00Z"
}
```

---

### 2. Get Extraction Status

**GET** `/scan/status/{scan_id}`

Retrieves the current status and progress of a deal extraction process.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response (Running Extraction)
```json
{
  "id": "job_abc123xyz",
  "scanId": "hubspot-deals-2025-q3",
  "status": "running",
  "scanType": "hubspot_deals",
  "organizationId": "org_123456",
  "started_at": "2025-09-29T10:30:00Z",
  "completed_at": null,
  "error_message": null,
  "created_at": "2025-09-29T10:30:00Z",
  "updated_at": "2025-09-29T10:35:00Z",
  "progress": {
    "total_items": 2543,
    "processed_items": 1200,
    "failed_items": 3,
    "success_rate": "99.75%",
    "current_batch": 12,
    "total_batches": 26,
    "estimated_time_remaining": "3 minutes"
  },
  "config": {
    "properties": ["dealname", "amount", "dealstage"],
    "includeAssociations": true,
    "batchSize": 100
  }
}
```

#### Response (Completed Extraction)
```json
{
  "id": "job_abc123xyz",
  "scanId": "hubspot-deals-2025-q3",
  "status": "completed",
  "scanType": "hubspot_deals",
  "organizationId": "org_123456",
  "started_at": "2025-09-29T10:30:00Z",
  "completed_at": "2025-09-29T10:42:15Z",
  "error_message": null,
  "created_at": "2025-09-29T10:30:00Z",
  "updated_at": "2025-09-29T10:42:15Z",
  "progress": {
    "total_items": 2543,
    "processed_items": 2540,
    "failed_items": 3,
    "success_rate": "99.88%",
    "duration_seconds": 735
  },
  "results": {
    "deals_extracted": 2540,
    "with_associations": 2540,
    "archived_deals": 0,
    "data_size_mb": 15.4
  }
}
```

#### Response (Failed Extraction)
```json
{
  "id": "job_abc123xyz",
  "scanId": "hubspot-deals-2025-q3",
  "status": "failed",
  "scanType": "hubspot_deals",
  "started_at": "2025-09-29T10:30:00Z",
  "completed_at": "2025-09-29T10:32:00Z",
  "error_message": "HubSpot API authentication failed: Invalid access token",
  "created_at": "2025-09-29T10:30:00Z",
  "updated_at": "2025-09-29T10:32:00Z",
  "progress": {
    "total_items": 0,
    "processed_items": 0,
    "failed_items": 0,
    "success_rate": "0%"
  }
}
```

#### Response (Non-existent Extraction)
```json
{
  "id": null,
  "scanId": null,
  "status": "not_found",
  "started_at": null,
  "completed_at": null,
  "error_message": null,
  "created_at": null,
  "updated_at": null
}
```

#### Status Values
- **pending**: Extraction queued but not started
- **running**: Extraction in progress
- **completed**: Extraction finished successfully
- **failed**: Extraction failed with error
- **cancelled**: Extraction cancelled by user
- **not_found**: Extraction does not exist

#### Status Codes
- **200**: Always returns 200 (check `status` field for actual state)
- **400**: Invalid scan ID format

--

#### Status Codes
- **200**: List retrieved successfully
- **400**: Invalid query parameters

---
### 3. Cancel Extraction

**POST** `/scan/cancel/{scan_id}`

Cancels a running deal extraction process.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response
```json
{
  "message": "Extraction cancelled successfully",
  "scanId": "hubspot-deals-2025-q3",
  "status": "cancelled",
  "itemsProcessed": 1200,
  "cancelledAt": "2025-09-29T10:35:00Z"
}
```

#### Status Codes
- **200**: Cancellation successful
- **400**: Invalid scan ID or scan cannot be cancelled
- **404**: Scan not found
- **500**: Internal server error

#### Example Errors
```json
{
  "status": "error",
  "message": "Cannot cancel completed extraction",
  "error_code": "INVALID_CANCELLATION",
  "details": {
    "scanId": "hubspot-deals-2025-q3",
    "currentStatus": "completed"
  },
  "timestamp": "2025-09-29T10:35:00Z"
}
```

---

### 4. Get Extraction Results

**GET** `/scan/results/{scan_id}`

Retrieves the extracted deal data for a completed scan.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 50, max: 500) |
| `pipeline` | string | No | Filter by pipeline ID |
| `dealstage` | string | No | Filter by deal stage |
| `owner_id` | string | No | Filter by owner ID |

#### Response
```json
{
  "scanId": "hubspot-deals-2025-q3",
  "status": "completed",
  "pagination": {
    "current_page": 1,
    "page_size": 50,
    "total_items": 2540,
    "total_pages": 51,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null,
    "next_cursor": "NTI1Cg%3D%3D"
  },
  "deals": [
    {
      "id": "result_001",
      "deal_id": "12345678901",
      "deal_name": "Enterprise Deal - ACME Corp",
      "amount": 50000.00,
      "currency": "USD",
      "deal_stage": "presentationscheduled",
      "deal_stage_label": "Presentation Scheduled",
      "pipeline_id": "default",
      "pipeline_label": "Sales Pipeline",
      "close_date": "2025-10-15T00:00:00Z",
      "deal_created_at": "2025-09-01T14:30:00Z",
      "deal_updated_at": "2025-09-28T10:15:00Z",
      "owner_id": "12345",
      "owner_email": "sales@company.com",
      "deal_type": "newbusiness",
      "is_archived": false,
      "deal_url": "https://app.hubspot.com/contacts/123456/deal/12345678901",
      "properties": {
        "dealname": "Enterprise Deal - ACME Corp",
        "amount": "50000",
        "hs_priority": "high",
        "num_contacted_notes": "5",
        "hs_analytics_source": "ORGANIC_SEARCH"
      },
      "associations": {
        "contacts": [
          {"id": "987654321", "type": "deal_to_contact"},
          {"id": "987654322", "type": "deal_to_contact"}
        ],
        "companies": [
          {"id": "567890123", "type": "deal_to_company"}
        ],
        "line_items": [
          {"id": "111222333", "type": "deal_to_line_item"}
        ]
      }
    }
  ]
}
```

#### Status Codes
- **200**: Results retrieved successfully
- **404**: Scan not found or not completed
- **400**: Invalid query parameters

#### Example Errors
```json
{
  "status": "error",
  "message": "Scan not completed yet",
  "error_code": "SCAN_NOT_READY",
  "details": {
    "scanId": "hubspot-deals-2025-q3",
    "currentStatus": "running",
    "progress": "45%"
  },
  "timestamp": "2025-09-29T10:35:00Z"
}
```

---

### 5. List All Scans

**GET** `/scan/list`

Retrieves a list of all scan jobs with optional filtering.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status (pending, running, completed, failed) |
| `organization_id` | string | No | Filter by organization |
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20, max: 100) |
| `sort_by` | string | No | Sort field (created_at, completed_at, default: created_at) |
| `sort_order` | string | No | Sort order (asc, desc, default: desc) |

#### Response
```json
{
  "pagination": {
    "current_page": 1,
    "page_size": 20,
    "total_items": 45,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
  },
  "scans": [
    {
      "id": "job_abc123xyz",
      "scanId": "hubspot-deals-2025-q3",
      "status": "completed",
      "scanType": "hubspot_deals",
      "organizationId": "org_123456",
      "started_at": "2025-09-29T10:30:00Z",
      "completed_at": "2025-09-29T10:42:15Z",
      "total_items": 2543,
      "processed_items": 2540,
      "success_rate": "99.88%",
      "duration_seconds": 735,
      "data_size_mb": 15.4
    },
    {
      "id": "job_def456uvw",
      "scanId": "hubspot-deals-2025-q2",
      "status": "failed",
      "scanType": "hubspot_deals",
      "organizationId": "org_123456",
      "started_at": "2025-08-15T14:20:00Z",
      "completed_at": "2025-08-15T14:22:30Z",
      "total_items": 0,
      "processed_items": 0,
      "success_rate": "0%",
      "error_message": "Invalid HubSpot access token"
    },
    {
      "id": "job_ghi789rst",
      "scanId": "hubspot-deals-2025-q1",
      "status": "running",
      "scanType": "hubspot_deals",
      "organizationId": "org_123456",
      "started_at": "2025-09-29T11:00:00Z",
      "completed_at": null,
      "total_items": 1800,
      "processed_items": 900,
      "success_rate": "100%",
      "estimated_time_remaining": "2 minutes"
    }
  ]
}
```

#### Status Codes
- **200**: List retrieved successfully
- **400**: Invalid query parameters

---

## 🏥 Health & Stats Endpoints

### 6. Service Health Check

**GET** `/health`

Returns the current health status of the service and its dependencies.

#### Response
```json
{
  "status": "healthy",
  "timestamp": "2025-09-29T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "dependencies": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12
    },
    "hubspot_api": {
      "status": "healthy",
      "response_time_ms": 245,
      "rate_limit_remaining": 85
    },
    "redis_cache": {
      "status": "healthy",
      "response_time_ms": 3
    }
  },
  "metrics": {
    "active_scans": 3,
    "completed_scans_today": 47,
    "total_deals_extracted_today": 125430
  }
}
```

#### Status Codes
- **200**: Service is healthy
- **503**: Service is unhealthy (one or more dependencies failed)

---

### 7. Service Statistics

**GET** `/stats`

Provides aggregate statistics about service usage and performance.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period` | string | No | Time period (24h, 7d, 30d, default: 24h) |
| `organization_id` | string | No | Filter by organization |

#### Response
```json
{
  "period": "24h",
  "timestamp": "2025-09-29T10:30:00Z",
  "summary": {
    "total_scans": 47,
    "successful_scans": 44,
    "failed_scans": 3,
    "success_rate": "93.6%",
    "total_deals_extracted": 125430,
    "average_scan_duration_seconds": 342,
    "total_data_extracted_mb": 1247.5
  },
  "status_breakdown": {
    "completed": 44,
    "failed": 3,
    "running": 2,
    "pending": 0,
    "cancelled": 1
  },
  "performance_metrics": {
    "fastest_scan_seconds": 45,
    "slowest_scan_seconds": 1240,
    "average_deals_per_second": 15.2,
    "peak_concurrent_scans": 8
  },
  "error_analysis": {
    "authentication_failures": 2,
    "rate_limit_errors": 0,
    "network_timeouts": 1,
    "other_errors": 0
  }
}
```

#### Status Codes
- **200**: Statistics retrieved successfully
- **400**: Invalid query parameters

---

## 🚨 Error Handling

### Common Error Codes

| Error Code | HTTP Status | Description | Resolution |
|------------|-------------|-------------|------------|
| `VALIDATION_ERROR` | 400 | Request validation failed | Check request format and required fields |
| `HUBSPOT_AUTH_FAILED` | 401 | HubSpot authentication failed | Verify access token and permissions |
| `SCAN_NOT_FOUND` | 404 | Scan ID does not exist | Check scan ID spelling and existence |
| `SCAN_IN_PROGRESS` | 409 | Scan already running | Wait for completion or cancel existing scan |
| `RATE_LIMIT_EXCEEDED` | 429 | API rate limit exceeded | Wait and retry with backoff |
| `HUBSPOT_API_ERROR` | 502 | HubSpot API returned error | Check HubSpot service status |
| `INTERNAL_ERROR` | 500 | Unexpected server error | Contact support with error details |

### Error Response Structure
All error responses follow this consistent format:
```json
{
  "status": "error",
  "error_code": "ERROR_CODE_HERE",
  "message": "Human-readable error description",
  "details": {
    "additional": "context-specific information"
  },
  "timestamp": "2025-09-29T10:30:00Z",
  "request_id": "req_uuid_12345"
}
```

---

## 📋 Examples

### Complete Workflow Example

#### 1. Start Extraction
```bash
curl -X POST "http://localhost:8000/api/v1/scan/start" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "scanId": "my-deals-extraction",
      "type": ["hubspot_deals"],
      "auth": {
        "hubspot_access_token": "pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
      },
      "properties": ["dealname", "amount", "dealstage", "closedate"],
      "includeAssociations": true,
      "batchSize": 100
    }
  }'
```

#### 2. Monitor Progress
```bash
curl "http://localhost:8000/api/v1/scan/status/my-deals-extraction"
```

#### 3. Get Results
```bash
curl "http://localhost:8000/api/v1/scan/results/my-deals-extraction?page=1&page_size=50"
```

---

## ⏱️ Rate Limiting

### HubSpot API Limits
- **Daily Limit**: 250,000 requests per day
- **Burst Limit**: 150 requests per 10 seconds
- **Automatic Retry**: Built-in exponential backoff

### Service Rate Limits
- **Concurrent Scans**: Maximum 10 per organization
- **API Requests**: 1000 requests per minute per API key
- **Results Download**: 100 MB per minute per organization

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1664461200
```

---

## 📋 Changelog

### Version 1.0.0 (2025-09-29)
- Initial release
- Basic deal extraction functionality
- Progress tracking and status monitoring
- Association support for contacts, companies, and line items
- Multi-tenant organization support
- Comprehensive error handling and retry logic
