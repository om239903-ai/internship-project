# 📋 Data Extraction Service - Integration with HubSpot API

This document explains the HubSpot REST API endpoints required by the Data Extraction Service to extract deal data from HubSpot instances.

---

## 📋 Overview

The Data Extraction Service integrates with HubSpot REST API endpoints to extract deal information. Below are the required and optional endpoints:

### ✅ **Required Endpoint (Essential)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/crm/v3/objects/deals`            | Search and list deals               | v3          | crm.objects.deals.read   | **Required** |

### 🔧 **Optional Endpoints (Advanced Features)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/crm/v3/objects/deals/{dealId}`   | Get detailed deal information       | v3          | crm.objects.deals.read   | Optional     |
| `/crm/v3/properties/deals`         | Get deal properties schema          | v3          | crm.schemas.deals.read   | Optional     |
| `/crm/v3/objects/deals/batch/read` | Get multiple deals in batch         | v3          | crm.objects.deals.read   | Optional     |
| `/crm/v3/pipelines/deals`          | Get deal pipelines configuration    | v3          | crm.objects.deals.read   | Optional     |

---

## 🌐 HubSpot API Endpoints

### 🎯 **PRIMARY ENDPOINT (Required for Basic Deal Extraction)**

### 1. **Search Deals** - `/crm/v3/objects/deals` ✅ **REQUIRED**

**Purpose**: Get paginated list of all deals - **THIS IS ALL YOU NEED FOR BASIC DEAL EXTRACTION**

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals`

**Query Parameters**:
```
?properties=dealname,amount,dealstage,pipeline&limit=100&after={paging_token}
```

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/objects/deals?properties=dealname,amount,dealstage,pipeline,closedate&limit=100
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure** (Contains ALL essential deal data):
```json
{
  "results": [
    {
      "id": "12345678901",
      "properties": {
        "amount": "50000",
        "closedate": "2025-10-15T00:00:00.000Z",
        "createdate": "2025-09-01T14:30:00.000Z",
        "dealname": "New Enterprise Deal",
        "dealstage": "presentationscheduled",
        "hs_lastmodifieddate": "2025-09-28T10:15:00.000Z",
        "hs_object_id": "12345678901",
        "pipeline": "default"
      },
      "createdAt": "2025-09-01T14:30:00.000Z",
      "updatedAt": "2025-09-28T10:15:00.000Z",
      "archived": false
    },
    {
      "id": "12345678902",
      "properties": {
        "amount": "25000",
        "closedate": "2025-11-30T00:00:00.000Z",
        "createdate": "2025-09-15T09:00:00.000Z",
        "dealname": "SMB Subscription Renewal",
        "dealstage": "qualifiedtobuy",
        "hs_lastmodifieddate": "2025-09-29T08:30:00.000Z",
        "hs_object_id": "12345678902",
        "pipeline": "default"
      },
      "createdAt": "2025-09-15T09:00:00.000Z",
      "updatedAt": "2025-09-29T08:30:00.000Z",
      "archived": false
    }
  ],
  "paging": {
    "next": {
      "after": "NTI1Cg%3D%3D",
      "link": "?after=NTI1Cg%3D%3D"
    }
  }
}
```

**✅ This endpoint provides ALL the default deal fields:**
- Deal ID, Deal Name, Amount, Close Date
- Deal Stage and Pipeline information
- Creation and modification timestamps
- Object metadata (archived status, unique identifiers)
- Any custom properties you specify in the query
- Association data when requested

**Rate Limit**: 100 requests per 10 seconds (per access token)

---

## 🔧 **OPTIONAL ENDPOINTS (Advanced Features Only)**

> **⚠️ Note**: These endpoints are NOT required for basic deal extraction. Only implement if you need advanced deal analytics like detailed deal information, property schemas, batch operations, or pipeline configurations.

### 2. **Get Individual Deal** - `/crm/v3/objects/deals/{dealId}`

**Purpose**: Retrieve detailed information for a specific deal by ID

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals/{dealId}`

**Query Parameters**:
```
?properties=dealname,amount,dealstage&associations=contacts,companies
```

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/objects/deals/12345678901?properties=dealname,amount,dealstage,closedate,pipeline&associations=contacts,companies
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure**:
```json
{
  "id": "12345678901",
  "properties": {
    "amount": "50000",
    "closedate": "2025-10-15T00:00:00.000Z",
    "createdate": "2025-09-01T14:30:00.000Z",
    "dealname": "New Enterprise Deal",
    "dealstage": "presentationscheduled",
    "hs_lastmodifieddate": "2025-09-28T10:15:00.000Z",
    "hs_object_id": "12345678901",
    "pipeline": "default",
    "hubspot_owner_id": "12345"
  },
  "createdAt": "2025-09-01T14:30:00.000Z",
  "updatedAt": "2025-09-28T10:15:00.000Z",
  "archived": false,
  "associations": {
    "contacts": {
      "results": [
        {
          "id": "987654321",
          "type": "deal_to_contact"
        },
        {
          "id": "987654322",
          "type": "deal_to_contact"
        }
      ]
    },
    "companies": {
      "results": [
        {
          "id": "567890123",
          "type": "deal_to_company"
        }
      ]
    }
  }
}
```

**Use Case**: When you need full details of a single deal including its associations

---

### 3. **Get Deal Properties Schema** - `/crm/v3/properties/deals`

**Purpose**: Retrieve the complete schema of all available deal properties including custom fields

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/properties/deals`

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/properties/deals
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure**:
```json
{
  "results": [
    {
      "updatedAt": "2025-01-15T10:30:00.000Z",
      "createdAt": "2020-05-12T08:00:00.000Z",
      "name": "dealname",
      "label": "Deal Name",
      "type": "string",
      "fieldType": "text",
      "description": "The name given to this deal",
      "groupName": "dealinformation",
      "options": [],
      "createdUserId": "12345",
      "updatedUserId": "12345",
      "displayOrder": 1,
      "calculated": false,
      "externalOptions": false,
      "hasUniqueValue": false,
      "hidden": false,
      "hubspotDefined": true,
      "modificationMetadata": {
        "archivable": true,
        "readOnlyDefinition": true,
        "readOnlyValue": false
      }
    },
    {
      "updatedAt": "2025-01-15T10:30:00.000Z",
      "createdAt": "2020-05-12T08:00:00.000Z",
      "name": "amount",
      "label": "Amount",
      "type": "number",
      "fieldType": "number",
      "description": "The total value of the deal in the deal's currency",
      "groupName": "dealinformation",
      "options": [],
      "createdUserId": "12345",
      "updatedUserId": "12345",
      "displayOrder": 2,
      "calculated": false,
      "externalOptions": false,
      "hasUniqueValue": false,
      "hidden": false,
      "hubspotDefined": true,
      "modificationMetadata": {
        "archivable": true,
        "readOnlyDefinition": true,
        "readOnlyValue": false
      }
    },
    {
      "updatedAt": "2025-01-15T10:30:00.000Z",
      "createdAt": "2020-05-12T08:00:00.000Z",
      "name": "dealstage",
      "label": "Deal Stage",
      "type": "enumeration",
      "fieldType": "select",
      "description": "The stage of the deal within the deal pipeline",
      "groupName": "dealinformation",
      "options": [
        {
          "label": "Appointment Scheduled",
          "value": "appointmentscheduled",
          "displayOrder": 1,
          "hidden": false
        },
        {
          "label": "Qualified to Buy",
          "value": "qualifiedtobuy",
          "displayOrder": 2,
          "hidden": false
        },
        {
          "label": "Presentation Scheduled",
          "value": "presentationscheduled",
          "displayOrder": 3,
          "hidden": false
        },
        {
          "label": "Decision Maker Bought-In",
          "value": "decisionmakerboughtin",
          "displayOrder": 4,
          "hidden": false
        },
        {
          "label": "Contract Sent",
          "value": "contractsent",
          "displayOrder": 5,
          "hidden": false
        },
        {
          "label": "Closed Won",
          "value": "closedwon",
          "displayOrder": 6,
          "hidden": false
        },
        {
          "label": "Closed Lost",
          "value": "closedlost",
          "displayOrder": 7,
          "hidden": false
        }
      ],
      "createdUserId": "12345",
      "updatedUserId": "12345",
      "displayOrder": 3,
      "calculated": false,
      "externalOptions": false,
      "hasUniqueValue": false,
      "hidden": false,
      "hubspotDefined": true,
      "modificationMetadata": {
        "archivable": true,
        "readOnlyDefinition": true,
        "readOnlyValue": false
      }
    },
    {
      "updatedAt": "2025-09-20T14:22:00.000Z",
      "createdAt": "2025-09-20T14:22:00.000Z",
      "name": "custom_deal_source",
      "label": "Deal Source",
      "type": "enumeration",
      "fieldType": "select",
      "description": "Custom property to track where the deal originated from",
      "groupName": "dealinformation",
      "options": [
        {
          "label": "Inbound Marketing",
          "value": "inbound",
          "displayOrder": 1,
          "hidden": false
        },
        {
          "label": "Outbound Sales",
          "value": "outbound",
          "displayOrder": 2,
          "hidden": false
        },
        {
          "label": "Referral",
          "value": "referral",
          "displayOrder": 3,
          "hidden": false
        }
      ],
      "createdUserId": "67890",
      "updatedUserId": "67890",
      "displayOrder": 100,
      "calculated": false,
      "externalOptions": false,
      "hasUniqueValue": false,
      "hidden": false,
      "hubspotDefined": false,
      "modificationMetadata": {
        "archivable": true,
        "readOnlyDefinition": false,
        "readOnlyValue": false
      }
    }
  ]
}
```

**Use Case**: Discovery of available properties and custom field definitions

---

### 4. **Batch Read Deals** - `/crm/v3/objects/deals/batch/read`

**Purpose**: Retrieve multiple specific deals in a single request for improved performance

**Method**: `POST`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals/batch/read`

**Request Example**:
```http
POST https://api.hubapi.com/crm/v3/objects/deals/batch/read
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body**:
```json
{
  "properties": ["dealname", "dealstage", "amount", "closedate", "pipeline"],
  "propertiesWithHistory": ["dealstage"],
  "inputs": [
    {"id": "12345678901"},
    {"id": "12345678902"},
    {"id": "12345678903"}
  ]
}
```

**Response Structure**:
```json
{
  "status": "COMPLETE",
  "results": [
    {
      "id": "12345678901",
      "properties": {
        "amount": "50000",
        "closedate": "2025-10-15T00:00:00.000Z",
        "dealname": "New Enterprise Deal",
        "dealstage": "presentationscheduled",
        "pipeline": "default",
        "hs_object_id": "12345678901"
      },
      "propertiesWithHistory": {
        "dealstage": [
          {
            "value": "presentationscheduled",
            "timestamp": "2025-09-28T10:15:00.000Z",
            "sourceType": "CRM_UI",
            "sourceId": "userId:12345",
            "updatedByUserId": 12345
          },
          {
            "value": "qualifiedtobuy",
            "timestamp": "2025-09-15T14:30:00.000Z",
            "sourceType": "CRM_UI",
            "sourceId": "userId:12345",
            "updatedByUserId": 12345
          },
          {
            "value": "appointmentscheduled",
            "timestamp": "2025-09-01T14:30:00.000Z",
            "sourceType": "CRM_UI",
            "sourceId": "userId:12345",
            "updatedByUserId": 12345
          }
        ]
      },
      "createdAt": "2025-09-01T14:30:00.000Z",
      "updatedAt": "2025-09-28T10:15:00.000Z",
      "archived": false
    },
    {
      "id": "12345678902",
      "properties": {
        "amount": "25000",
        "closedate": "2025-11-30T00:00:00.000Z",
        "dealname": "SMB Subscription Renewal",
        "dealstage": "qualifiedtobuy",
        "pipeline": "default",
        "hs_object_id": "12345678902"
      },
      "propertiesWithHistory": {
        "dealstage": [
          {
            "value": "qualifiedtobuy",
            "timestamp": "2025-09-20T09:00:00.000Z",
            "sourceType": "CRM_UI",
            "sourceId": "userId:67890",
            "updatedByUserId": 67890
          },
          {
            "value": "appointmentscheduled",
            "timestamp": "2025-09-15T09:00:00.000Z",
            "sourceType": "INTEGRATIONS_PLATFORM",
            "sourceId": "integration:salesforce",
            "updatedByUserId": null
          }
        ]
      },
      "createdAt": "2025-09-15T09:00:00.000Z",
      "updatedAt": "2025-09-29T08:30:00.000Z",
      "archived": false
    },
    {
      "id": "12345678903",
      "properties": {
        "amount": "75000",
        "closedate": "2025-12-31T00:00:00.000Z",
        "dealname": "Annual Contract - ACME Corp",
        "dealstage": "contractsent",
        "pipeline": "default",
        "hs_object_id": "12345678903"
      },
      "propertiesWithHistory": {
        "dealstage": [
          {
            "value": "contractsent",
            "timestamp": "2025-09-29T16:45:00.000Z",
            "sourceType": "API",
            "sourceId": "integration:docusign",
            "updatedByUserId": null
          },
          {
            "value": "decisionmakerboughtin",
            "timestamp": "2025-09-25T11:20:00.000Z",
            "sourceType": "CRM_UI",
            "sourceId": "userId:12345",
            "updatedByUserId": 12345
          }
        ]
      },
      "createdAt": "2025-08-01T10:00:00.000Z",
      "updatedAt": "2025-09-29T16:45:00.000Z",
      "archived": false
    }
  ]
}
```

**Use Case**: Efficiently fetching multiple deals by ID with property history

---

### 5. **Get Deal Pipelines** - `/crm/v3/pipelines/deals`

**Purpose**: Retrieve pipeline configurations including stages, probabilities, and settings

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/pipelines/deals`

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/pipelines/deals
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure**:
```json
{
  "results": [
    {
      "id": "default",
      "label": "Sales Pipeline",
      "displayOrder": 1,
      "createdAt": "2020-05-12T08:00:00.000Z",
      "updatedAt": "2025-01-15T10:30:00.000Z",
      "archived": false,
      "stages": [
        {
          "id": "appointmentscheduled",
          "label": "Appointment Scheduled",
          "displayOrder": 0,
          "metadata": {
            "probability": "0.2",
            "isClosed": "false"
          },
          "createdAt": "2020-05-12T08:00:00.000Z",
          "updatedAt": "2020-05-12T08:00:00.000Z",
          "archived": false
        },
        {
          "id": "qualifiedtobuy",
          "label": "Qualified to Buy",
          "displayOrder": 1,
          "metadata": {
            "probability": "0.4",
            "isClosed": "false"
          },
          "createdAt": "2020-05-12T08:00:00.000Z",
          "updatedAt": "2020-05-12T08:00:00.000Z",
          "archived": false
        },
        {
          "id": "presentationscheduled",
          "label": "Presentation Scheduled",
          "displayOrder": 2,
          "metadata": {
            "probability": "0.6",
            "isClosed": "false"
          },
          "createdAt": "2020-05-12T08:00:00.000Z",
          "updatedAt": "2020-05-12T08:00:00.000Z",
          "archived": false
        },
        {
          "id": "decisionmakerboughtin",
          "label": "Decision Maker Bought-In",
          "displayOrder": 3,
          "metadata": {
            "probability": "0.8",
            "isClosed": "false"
          },
          "createdAt": "2020-05-12T08:00:00.000Z",
          "updatedAt": "2020-05-12T08:00:00.000Z",
          "archived": false
        },
        {
          "id": "contractsent",
          "label": "Contract Sent",
          "displayOrder": 4,
          "metadata": {
            "probability": "0.9",
            "isClosed": "false"
          },
          "createdAt": "2020-05-12T08:00:00.000Z",
          "updatedAt": "2020-05-12T08:00:00.000Z",
          "archived": false
        },
        {
          "id": "closedwon",
          "label": "Closed Won",
          "displayOrder": 5,
          "metadata": {
            "probability": "1.0",
            "isClosed": "true"
          },
          "createdAt": "2020-05-12T08:00:00.000Z",
          "updatedAt": "2020-05-12T08:00:00.000Z",
          "archived": false
        },
        {
          "id": "closedlost",
          "label": "Closed Lost",
          "displayOrder": 6,
          "metadata": {
            "probability": "0.0",
            "isClosed": "true"
          },
          "createdAt": "2020-05-12T08:00:00.000Z",
          "updatedAt": "2020-05-12T08:00:00.000Z",
          "archived": false
        }
      ]
    },
    {
      "id": "8675309",
      "label": "Partnership Pipeline",
      "displayOrder": 2,
      "createdAt": "2024-03-10T12:00:00.000Z",
      "updatedAt": "2025-02-20T15:45:00.000Z",
      "archived": false,
      "stages": [
        {
          "id": "partner_identified",
          "label": "Partner Identified",
          "displayOrder": 0,
          "metadata": {
            "probability": "0.1",
            "isClosed": "false"
          },
          "createdAt": "2024-03-10T12:00:00.000Z",
          "updatedAt": "2024-03-10T12:00:00.000Z",
          "archived": false
        },
        {
          "id": "partner_qualified",
          "label": "Partner Qualified",
          "displayOrder": 1,
          "metadata": {
            "probability": "0.3",
            "isClosed": "false"
          },
          "createdAt": "2024-03-10T12:00:00.000Z",
          "updatedAt": "2024-03-10T12:00:00.000Z",
          "archived": false
        },
        {
          "id": "agreement_negotiation",
          "label": "Agreement Negotiation",
          "displayOrder": 2,
          "metadata": {
            "probability": "0.7",
            "isClosed": "false"
          },
          "createdAt": "2024-03-10T12:00:00.000Z",
          "updatedAt": "2024-03-10T12:00:00.000Z",
          "archived": false
        },
        {
          "id": "partnership_active",
          "label": "Partnership Active",
          "displayOrder": 3,
          "metadata": {
            "probability": "1.0",
            "isClosed": "true"
          },
          "createdAt": "2024-03-10T12:00:00.000Z",
          "updatedAt": "2024-03-10T12:00:00.000Z",
          "archived": false
        },
        {
          "id": "partnership_declined",
          "label": "Partnership Declined",
          "displayOrder": 4,
          "metadata": {
            "probability": "0.0",
            "isClosed": "true"
          },
          "createdAt": "2024-03-10T12:00:00.000Z",
          "updatedAt": "2024-03-10T12:00:00.000Z",
          "archived": false
        }
      ]
    }
  ]
}
```

**Use Case**: Understanding available pipelines and stage configurations for proper deal categorization

---

## 📊 Data Extraction Flow

### 🎯 **SIMPLE FLOW (Recommended - Using Only Required Endpoint)**

### **Single Endpoint Approach - `/crm/v3/objects/deals` Only**
```python
def extract_all_deals_simple():
    """Extract all deals using only the /crm/v3/objects/deals endpoint"""
    after = None
    batch_size = 100
    all_deals = []
    
    while True:
        params = {
            "limit": batch_size,
            "properties": "dealname,amount,dealstage,closedate,pipeline,createdate"
        }
        
        if after:
            params["after"] = after
        
        response = requests.get(
            "https://api.hubapi.com/crm/v3/objects/deals",
            params=params,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        data = response.json()
        deals = data.get("results", [])
        
        if not deals:  # No more deals
            break
            
        all_deals.extend(deals)
        
        # Check if there's a next page
        paging = data.get("paging", {})
        if "next" not in paging:
            break
            
        after = paging["next"]["after"]
    
    return all_deals

# This gives you ALL essential deal data:
# - id, dealname, amount, dealstage
# - pipeline, closedate, createdate
# - createdAt, updatedAt, archived status
# - Any custom properties you specify
```

---

### 🔧 **ADVANCED FLOW (Optional - Multiple Endpoints)**

> **⚠️ Only use this if you need associations, property schemas, or batch operations with history**

### **Step 1: Batch Deal Retrieval**
```python
# Get deals in batches of 100
after = None
while True:
    response = requests.get(
        "https://api.hubapi.com/crm/v3/objects/deals",
        params={
            "after": after,
            "limit": 100,
            "properties": "dealname,amount,dealstage,pipeline"
        },
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )
    deals_data = response.json()
    deals = deals_data.get("results", [])
    
    # Process deals...
    
    paging = deals_data.get("paging", {})
    if "next" not in paging:
        break
    after = paging["next"]["after"]
```

### **Step 2: Enhanced Deal Details (Optional)**
```python
# Get detailed information with associations for each deal
for deal in deals:
    response = requests.get(
        f"https://api.hubapi.com/crm/v3/objects/deals/{deal['id']}",
        params={
            "properties": "dealname,amount,dealstage,closedate",
            "associations": "contacts,companies,line_items"
        },
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )
    detailed_deal = response.json()
```

### **Step 3: Deal Property History (Optional)**
```python
# Get property change history for specific deals
deal_ids = [deal["id"] for deal in deals]

# Batch read with history (max 100 per request)
for i in range(0, len(deal_ids), 100):
    batch = deal_ids[i:i+100]
    response = requests.post(
        "https://api.hubapi.com/crm/v3/objects/deals/batch/read",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "properties": ["dealname", "amount", "dealstage"],
            "propertiesWithHistory": ["dealstage", "amount"],
            "inputs": [{"id": deal_id} for deal_id in batch]
        }
    )
    deals_with_history = response.json()
```

### **Step 4: Pipeline Configuration (Optional)**
```python
# Get all pipeline configurations once
response = requests.get(
    "https://api.hubapi.com/crm/v3/pipelines/deals",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
)
pipelines = response.json()

# Map pipeline IDs to names and stages
pipeline_map = {}
for pipeline in pipelines.get("results", []):
    pipeline_map[pipeline["id"]] = {
        "name": pipeline["label"],
        "stages": {stage["id"]: stage["label"] for stage in pipeline["stages"]}
    }
```

---

## ⚡ Performance Considerations

### **Rate Limiting**
- **Default Limit**: 100 requests per 10 seconds per access token
- **Burst Limit**: Secondary limits may apply for high-volume usage
- **Best Practice**: Implement exponential backoff on 429 responses

### **Batch Processing**
- **Recommended Batch Size**: 100 deals per request (API maximum)
- **Concurrent Requests**: Max 3-5 parallel requests (deals can have complex associations)
- **Request Interval**: 100ms between requests to stay under rate limits

### **Error Handling**
```http
# Rate limit exceeded
HTTP/429 Too Many Requests
Retry-After: 1

# Authentication failed  
HTTP/401 Unauthorized

# Insufficient permissions
HTTP/403 Forbidden

# Deal not found
HTTP/404 Not Found
```

---

## 🔒 Security Requirements

### **API Token Permissions**

#### ✅ **Required (Minimum Permissions)**
```
Required Scopes:
- crm.objects.deals.read (for basic deal information)
```

#### 🔧 **Optional (Advanced Features)**
```
Additional Scopes (only if using optional endpoints):
- crm.schemas.deals.read (for property schema information)
- crm.objects.contacts.read (for contact associations)
- crm.objects.companies.read (for company associations)
- crm.objects.line_items.read (for line item associations)
```

### **User Permissions**

#### ✅ **Required (Minimum)**
The API token user must have:
- **View deals** permission in HubSpot
- Access to the deals object

#### 🔧 **Optional (Advanced Features)**
Additional permissions (only if using optional endpoints):
- **View contacts** permission (for contact association details)
- **View companies** permission (for company association details)
- **View products** permission (for line item access)

---

## 📈 Monitoring & Debugging

### **Request Headers for Debugging**
```http
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
User-Agent: DealExtractor/1.0
X-Request-ID: deal-scan-001-batch-1
```

### **Response Validation**
```python
def validate_deal_response(deal_data):
    required_fields = ["id", "properties", "createdAt", "updatedAt"]
    for field in required_fields:
        if field not in deal_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate deal has essential properties
    props = deal_data.get("properties", {})
    if "dealname" not in props or "dealstage" not in props:
        raise ValueError(f"Missing essential deal properties")
    
    # Validate archived status
    if "archived" not in deal_data:
        raise ValueError("Missing archived status")
```

### **API Usage Metrics**
- Track requests per 10-second window
- Monitor response times (should be < 2 seconds)
- Log rate limit headers (X-HubSpot-RateLimit-*)
- Track authentication failures and 403 errors

---

## 🧪 Testing API Integration

### **Test Authentication**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### **Test Deal Search**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=5&properties=dealname,amount,dealstage" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### **Test Deal Details**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals/12345678901?properties=dealname,amount&associations=contacts,companies" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### **Test Batch Read**
```bash
curl -X POST \
  "https://api.hubapi.com/crm/v3/objects/deals/batch/read" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "properties": ["dealname", "amount", "dealstage"],
    "inputs": [
      {"id": "12345678901"},
      {"id": "12345678902"}
    ]
  }'
```

### **Test Pipeline Retrieval**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/pipelines/deals" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

---

All endpoints require OAuth 2.0 authentication with appropriate scopes:
- `crm.objects.deals.read` - Read access to deals
- `crm.schemas.deals.read` - Read access to deal schemas

---

## 📚 Additional Resources

- [HubSpot Deal API Documentation](https://developers.hubspot.com/docs/api-reference/crm-deals-v3/guide)
- [HubSpot OAuth Guide](https://developers.hubspot.com/docs/api/working-with-oauth)