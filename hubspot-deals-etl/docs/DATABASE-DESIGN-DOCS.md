# 🗄️ HubSpot Deal Scan Job Database Schema

This document provides a database schema for implementing HubSpot deal scan job functionality with two core tables: ScanJob and DealResults.

---

## 📋 Overview

The Scan Job database schema consists of two main tables:

1. **ScanJob** - Core scan job management and tracking
2. **DealResults** - Storage for extracted HubSpot deal data

---

## 🏗️ Table Schemas

### 1. ScanJob Table

**Purpose**: Core scan job management and status tracking

| **Column Name**         | **Type**    | **Constraints**           | **Description**                          |
|-------------------------|-------------|---------------------------|------------------------------------------|
| `id`                    | String      | PRIMARY KEY               | Unique internal identifier               |
| `scan_id`               | String      | UNIQUE, NOT NULL, INDEX   | External scan identifier                 |
| `status`                | String      | NOT NULL, INDEX           | pending, running, completed, failed, cancelled |
| `scan_type`             | String      | NOT NULL                  | hubspot_deals                            |
| `config`                | JSON        | NOT NULL                  | Scan configuration and parameters        |
| `organization_id`       | String      | NULLABLE                  | Organization/tenant identifier           |
| `error_message`         | Text        | NULLABLE                  | Error details if scan failed            |
| `started_at`            | DateTime    | NULLABLE                  | When scan execution started             |
| `completed_at`          | DateTime    | NULLABLE                  | When scan finished                      |
| `total_items`           | Integer     | DEFAULT 0                 | Total deals to process                  |
| `processed_items`       | Integer     | DEFAULT 0                 | Deals successfully processed            |
| `failed_items`          | Integer     | DEFAULT 0                 | Deals that failed processing            |
| `success_rate`          | String      | NULLABLE                  | Calculated success percentage           |
| `batch_size`            | Integer     | DEFAULT 100               | Processing batch size (HubSpot max)     |
| `created_at`            | DateTime    | NOT NULL                  | Record creation timestamp               |
| `updated_at`            | DateTime    | NOT NULL                  | Record last update timestamp            |

**Indexes:**
```sql
-- Performance indexes
CREATE INDEX idx_scan_status_created ON scan_jobs(status, created_at);
CREATE INDEX idx_scan_id_status ON scan_jobs(scan_id, status);
CREATE INDEX idx_scan_type_status ON scan_jobs(scan_type, status);
CREATE INDEX idx_scan_org_status ON scan_jobs(organization_id, status);
```

**Config JSON Structure Example:**
```json
{
  "hubspot_api_key": "encrypted_token",
  "properties": ["dealname", "amount", "dealstage", "closedate", "pipeline"],
  "include_associations": true,
  "association_types": ["contacts", "companies"],
  "include_archived": false,
  "filter_pipeline": null,
  "filter_dealstage": null
}
```

---

### 2. DealResults Table

**Purpose**: Store extracted HubSpot deal data

| **Column Name**         | **Type**    | **Constraints**           | **Description**                          |
|-------------------------|-------------|---------------------------|------------------------------------------|
| `id`                    | String      | PRIMARY KEY               | Unique result identifier                 |
| `scan_job_id`           | String      | FOREIGN KEY, NOT NULL     | Reference to scan_jobs.id               |
| `deal_id`               | String      | NOT NULL, INDEX           | HubSpot deal ID (hs_object_id)          |
| `deal_name`             | String      | NULLABLE                  | Name of the deal                        |
| `amount`                | Decimal     | NULLABLE                  | Deal amount/value                       |
| `currency`              | String      | NULLABLE                  | Deal currency code (USD, EUR, etc.)     |
| `deal_stage`            | String      | NULLABLE, INDEX           | Current deal stage ID                   |
| `deal_stage_label`      | String      | NULLABLE                  | Human-readable stage name               |
| `pipeline_id`           | String      | NULLABLE, INDEX           | Pipeline ID                             |
| `pipeline_label`        | String      | NULLABLE                  | Human-readable pipeline name            |
| `close_date`            | DateTime    | NULLABLE, INDEX           | Expected or actual close date           |
| `deal_created_at`       | DateTime    | NULLABLE, INDEX           | When deal was created in HubSpot        |
| `deal_updated_at`       | DateTime    | NULLABLE                  | When deal was last modified in HubSpot  |
| `owner_id`              | String      | NULLABLE, INDEX           | HubSpot owner/user ID                   |
| `owner_email`           | String      | NULLABLE                  | Deal owner email                        |
| `deal_type`             | String      | NULLABLE                  | Type of deal (newbusiness, renewal, etc.)|
| `is_archived`           | Boolean     | DEFAULT FALSE, INDEX      | Whether deal is archived                |
| `properties`            | JSON        | NULLABLE                  | All deal properties as JSON             |
| `associations`          | JSON        | NULLABLE                  | Associated contacts, companies, etc.    |
| `custom_properties`     | JSON        | NULLABLE                  | Custom HubSpot properties               |
| `deal_url`              | String      | NULLABLE                  | Direct link to deal in HubSpot          |
| `created_at`            | DateTime    | NOT NULL                  | Record creation timestamp               |
| `updated_at`            | DateTime    | NOT NULL                  | Record last update timestamp            |

**Indexes:**
```sql
-- Performance indexes for common queries
CREATE INDEX idx_deal_scan_job ON deal_results(scan_job_id);
CREATE INDEX idx_deal_id_scan ON deal_results(deal_id, scan_job_id);
CREATE INDEX idx_deal_stage ON deal_results(deal_stage, pipeline_id);
CREATE INDEX idx_deal_owner ON deal_results(owner_id);
CREATE INDEX idx_deal_close_date ON deal_results(close_date);
CREATE INDEX idx_deal_created ON deal_results(deal_created_at);
CREATE INDEX idx_deal_archived ON deal_results(is_archived);
CREATE INDEX idx_deal_pipeline_stage ON deal_results(pipeline_id, deal_stage);

-- Composite index for common filtering
CREATE INDEX idx_deal_pipeline_stage_close ON deal_results(pipeline_id, deal_stage, close_date);
```

**Unique Constraint:**
```sql
-- Prevent duplicate deals within same scan
CREATE UNIQUE INDEX idx_unique_deal_per_scan ON deal_results(scan_job_id, deal_id);
```

---

## 📊 Common Data Patterns

### Properties JSON Structure
```json
{
  "dealname": "Enterprise Deal - ACME Corp",
  "amount": "50000",
  "dealstage": "presentationscheduled",
  "closedate": "2025-10-15T00:00:00.000Z",
  "pipeline": "default",
  "createdate": "2025-09-01T14:30:00.000Z",
  "hs_lastmodifieddate": "2025-09-28T10:15:00.000Z",
  "hubspot_owner_id": "12345",
  "dealtype": "newbusiness",
  "hs_priority": "high",
  "custom_deal_source": "inbound"
}
```

### Associations JSON Structure
```json
{
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
```

---

## 🔍 Common Queries

### Get All Deals from Latest Completed Scan
```sql
SELECT 
    dr.*
FROM deal_results dr
JOIN scan_jobs sj ON dr.scan_job_id = sj.id
WHERE sj.status = 'completed'
ORDER BY sj.completed_at DESC, dr.deal_created_at DESC
LIMIT 1000;
```

### Get Deals by Pipeline and Stage
```sql
SELECT 
    deal_id,
    deal_name,
    amount,
    deal_stage_label,
    close_date,
    owner_email
FROM deal_results
WHERE scan_job_id = 'latest_scan_id'
    AND pipeline_id = 'default'
    AND deal_stage IN ('presentationscheduled', 'contractsent')
    AND is_archived = FALSE
ORDER BY close_date ASC;
```

### Get Scan Job Statistics
```sql
SELECT 
    scan_id,
    status,
    total_items,
    processed_items,
    failed_items,
    success_rate,
    TIMESTAMPDIFF(MINUTE, started_at, completed_at) as duration_minutes
FROM scan_jobs
WHERE scan_type = 'hubspot_deals'
ORDER BY created_at DESC;
```

### Get Deal Count by Stage
```sql
SELECT 
    pipeline_label,
    deal_stage_label,
    COUNT(*) as deal_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount
FROM deal_results
WHERE scan_job_id = 'latest_scan_id'
    AND is_archived = FALSE
GROUP BY pipeline_label, deal_stage_label
ORDER BY pipeline_label, deal_count DESC;
```

### Get Deals Closing This Quarter
```sql
SELECT 
    deal_id,
    deal_name,
    amount,
    deal_stage_label,
    close_date,
    owner_email
FROM deal_results
WHERE scan_job_id = 'latest_scan_id'
    AND close_date >= DATE_TRUNC('quarter', CURRENT_DATE)
    AND close_date < DATE_TRUNC('quarter', CURRENT_DATE) + INTERVAL '3 months'
    AND is_archived = FALSE
ORDER BY close_date ASC, amount DESC;
```

---

## 🔄 Data Refresh Strategy

### Incremental Updates
```sql
-- Track last scan for incremental updates
ALTER TABLE scan_jobs ADD COLUMN last_sync_timestamp DateTime NULLABLE;

-- Store only changed deals
CREATE INDEX idx_deal_updated ON deal_results(deal_updated_at);
```

### Handling Duplicates
```sql
-- Upsert pattern for deal updates
INSERT INTO deal_results (
    id, scan_job_id, deal_id, deal_name, amount, ...
) VALUES (
    ?, ?, ?, ?, ?, ...
)
ON DUPLICATE KEY UPDATE
    deal_name = VALUES(deal_name),
    amount = VALUES(amount),
    deal_stage = VALUES(deal_stage),
    updated_at = CURRENT_TIMESTAMP;
```

---

## 📈 Storage Considerations

### Estimated Storage per Deal
- **Minimal (core fields only)**: ~0.5 KB per deal
- **Standard (with properties JSON)**: ~2-3 KB per deal
- **Full (with associations and history)**: ~5-10 KB per deal

### Example Calculations
- **1,000 deals**: ~2-10 MB
- **10,000 deals**: ~20-100 MB
- **100,000 deals**: ~200 MB - 1 GB
- **1,000,000 deals**: ~2-10 GB

### Retention Policy Recommendations
- Keep last 30 days of scan jobs: For historical comparison
- Archive completed scans older than 90 days: To external storage
- Keep only latest scan results: For active reporting
- Store delta/changes: For audit trail

---

## 🛠️ Maintenance Tasks

### Cleanup Old Scans
```sql
-- Delete scans older than 90 days
DELETE FROM scan_jobs 
WHERE status IN ('completed', 'failed') 
    AND completed_at < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- Cascade will remove associated deal_results
```

### Archive Historical Data
```sql
-- Move old results to archive table
INSERT INTO deal_results_archive 
SELECT * FROM deal_results
WHERE scan_job_id IN (
    SELECT id FROM scan_jobs 
    WHERE completed_at < DATE_SUB(NOW(), INTERVAL 90 DAY)
);
```

### Update Success Rates
```sql
-- Recalculate success rates
UPDATE scan_jobs 
SET success_rate = CONCAT(
    ROUND((processed_items * 100.0) / NULLIF(total_items, 0), 2), 
    '%'
)
WHERE status = 'completed';
```