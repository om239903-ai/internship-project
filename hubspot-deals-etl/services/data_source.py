import dlt
import logging
from typing import Dict, List, Any, Iterator, Optional, Callable
from datetime import datetime, timezone
from .api_service import HubSpotAPIService
from loki_logger import get_logger, log_business_event, log_security_event


def create_data_source(
    job_config: Dict[str, Any],
    auth_config: Dict[str, Any],
    filters: Dict[str, Any],
    checkpoint_callback: Optional[Callable] = None,
    check_cancel_callback: Optional[Callable] = None,
    check_pause_callback: Optional[Callable] = None,
    resume_from: Optional[Dict[str, Any]] = None,
):
    """
    Create DLT source function for HubSpot deals data extraction with checkpoint support
    
    Args:
        job_config: Job configuration containing organizationId, scanId, etc.
        auth_config: Authentication config with hubspot_access_token
        filters: Extraction filters (properties, associations, etc.)
        checkpoint_callback: Function to save extraction progress
        check_cancel_callback: Function to check if extraction should be cancelled
        check_pause_callback: Function to check if extraction should be paused
        resume_from: Previous checkpoint data to resume from
    """
    logger = get_logger(__name__)
    
    # Extract authentication token FIRST - before initializing API service
    access_token = auth_config.get("accessToken")
    if not access_token:
        raise ValueError("No HubSpot access token found in auth configuration")

    organization_id = job_config.get("organizationId")
    if not organization_id:
        raise ValueError("No organization ID found in job configuration")

    scan_id = job_config.get("scanId") or filters.get("scan_id", "unknown")

    # Initialize API service and set the access token
    api_service = HubSpotAPIService(base_url="https://api.hubapi.com", test_delay_seconds=0.1)
    api_service.set_access_token(access_token)  # Set token in session headers

    logger.info(
        "Initializing HubSpot deals data extraction",
        extra={
            "organization_id": organization_id,
            "scan_id": scan_id,
            "has_properties_filter": bool(filters.get("properties")),
            "has_associations": bool(filters.get("associations")),
            "include_archived": filters.get("includeArchived", False),
        },
    )

    @dlt.resource(
        name="hubspot_deals",
        write_disposition="replace",
        primary_key="deal_id",
        columns={
            "deal_id": {"data_type": "text", "nullable": False},
            "deal_name": {"data_type": "text"},
            "amount": {"data_type": "decimal"},
            "currency": {"data_type": "text"},
            "deal_stage": {"data_type": "text"},
            "deal_stage_label": {"data_type": "text"},
            "pipeline_id": {"data_type": "text"},
            "pipeline_label": {"data_type": "text"},
            "close_date": {"data_type": "timestamp"},
            "created_at": {"data_type": "timestamp"},
            "updated_at": {"data_type": "timestamp"},
            "owner_id": {"data_type": "text"},
            "owner_email": {"data_type": "text"},
            "deal_type": {"data_type": "text"},
            "is_archived": {"data_type": "bool"},
            "deal_url": {"data_type": "text"},
            "_extracted_at": {"data_type": "timestamp"},
            "_scan_id": {"data_type": "text"},
            "_organization_id": {"data_type": "text"},
            "_page_number": {"data_type": "bigint"},
            "_source_service": {"data_type": "text"},
        }
    )
    def get_deals_data() -> Iterator[Dict[str, Any]]:
        """
        Extract deals data from HubSpot CRM API with checkpoint support and pagination
        """
        
        # Initialize state from checkpoint or start fresh
        if resume_from:
            after = resume_from.get("cursor")
            page_count = resume_from.get("page_number", 0)
            total_records = resume_from.get("records_processed", 0)
            logger.info(
                "Resuming HubSpot deals extraction",
                extra={
                    "operation": "deals_extraction",
                    "page_number": page_count + 1,
                    "total_processed": total_records,
                    "resume_cursor": after[:50] + "..." if after and len(after) > 50 else after,
                },
            )
        else:
            after = None
            page_count = 0
            total_records = 0
            logger.info(
                "Starting fresh HubSpot deals extraction",
                extra={"operation": "deals_extraction", "scan_id": scan_id},
            )

        # Configuration
        checkpoint_interval = filters.get("checkpoint_interval", 5)  # Save every 5 pages
        cancel_check_interval = 1  # Check for cancellation every page
        pause_check_interval = 1   # Check for pause every page
        batch_size = min(filters.get("batchSize", 100), 100)  # HubSpot API limit
        max_pages = filters.get("max_pages", 10000)  # Safety limit

        # Extract filter parameters
        properties = filters.get("properties", [])
        associations = filters.get("associationTypes", []) if filters.get("includeAssociations") else []
        include_archived = filters.get("includeArchived", False)

        while page_count < max_pages:
            try:
                # Check for cancellation
                if page_count % cancel_check_interval == 0:
                    if check_cancel_callback and check_cancel_callback(scan_id):
                        logger.info(
                            "HubSpot deals extraction cancelled by user",
                            extra={
                                "operation": "deals_extraction",
                                "scan_id": scan_id,
                                "page_number": page_count + 1,
                                "total_processed": total_records,
                            },
                        )

                        # Save cancellation checkpoint
                        if checkpoint_callback:
                            _save_checkpoint(
                                checkpoint_callback,
                                scan_id,
                                "deals_cancelled",
                                total_records,
                                after,
                                page_count,
                                batch_size,
                                {"cancellation_reason": "user_requested", "cancelled_at_page": page_count},
                                logger
                            )
                        return

                # Check for pause request
                if page_count % pause_check_interval == 0:
                    if check_pause_callback and check_pause_callback(scan_id):
                        logger.info(
                            "HubSpot deals extraction paused by user",
                            extra={
                                "operation": "deals_extraction",
                                "scan_id": scan_id,
                                "page_number": page_count + 1,
                                "total_processed": total_records,
                            },
                        )

                        # Save pause checkpoint
                        if checkpoint_callback:
                            _save_checkpoint(
                                checkpoint_callback,
                                scan_id,
                                "deals_paused",
                                total_records,
                                after,
                                page_count,
                                batch_size,
                                {
                                    "pause_reason": "user_requested",
                                    "paused_at_page": page_count,
                                    "paused_at": datetime.now(timezone.utc).isoformat(),
                                },
                                logger
                            )
                        return

                logger.debug(
                    "Fetching HubSpot deals page",
                    extra={
                        "operation": "deals_extraction",
                        "scan_id": scan_id,
                        "page_number": page_count + 1,
                        "batch_size": batch_size,
                    },
                )

                # Fetch deals data from HubSpot API
                # NOTE: No need to pass access_token - it's already set in session headers
                data = api_service.get_deals(
                    limit=batch_size,
                    after=after,
                    properties=properties,
                    associations=associations,
                    archived=include_archived,
                    scan_id=scan_id
                )

                page_records = 0
                deals = data.get("results", [])

                if not deals:
                    logger.info(
                        "No more deals to process",
                        extra={
                            "operation": "deals_extraction",
                            "scan_id": scan_id,
                            "page_number": page_count + 1,
                        },
                    )
                    break

                # Process each deal
                for deal in deals:
                    # Check for pause/cancel even within record processing
                    if check_pause_callback and check_pause_callback(scan_id):
                        logger.info(
                            "HubSpot deals extraction paused mid-page",
                            extra={
                                "operation": "deals_extraction",
                                "scan_id": scan_id,
                                "page_number": page_count + 1,
                                "records_in_page": page_records,
                                "total_processed": total_records + page_records,
                            },
                        )

                        if checkpoint_callback:
                            _save_checkpoint(
                                checkpoint_callback,
                                scan_id,
                                "deals_paused_mid_page",
                                total_records + page_records,
                                after,
                                page_count,
                                batch_size,
                                {
                                    "pause_reason": "user_requested_mid_page",
                                    "records_completed_in_page": page_records,
                                    "paused_at": datetime.now(timezone.utc).isoformat(),
                                },
                                logger
                            )
                        return

                    # Transform deal data to standardized format
                    transformed_deal = _transform_deal_record(deal, scan_id, organization_id, page_count + 1)
                    
                    yield transformed_deal
                    page_records += 1

                # Update counters
                total_records += page_records
                page_count += 1

                logger.info(
                    "Processed HubSpot deals page",
                    extra={
                        "operation": "deals_extraction",
                        "scan_id": scan_id,
                        "page_number": page_count,
                        "page_records": page_records,
                        "total_records": total_records,
                    },
                )

                # Save checkpoint periodically
                if checkpoint_callback and page_count % checkpoint_interval == 0:
                    next_cursor = _extract_next_cursor(data)
                    _save_checkpoint(
                        checkpoint_callback,
                        scan_id,
                        "deals_in_progress",
                        total_records,
                        next_cursor,
                        page_count,
                        batch_size,
                        {
                            "pages_processed": page_count,
                            "last_page_records": page_records,
                        },
                        logger
                    )

                # Check for more pages using HubSpot pagination
                next_cursor = _extract_next_cursor(data)
                if next_cursor:
                    after = next_cursor
                else:
                    # Final checkpoint on completion
                    if checkpoint_callback:
                        _save_checkpoint(
                            checkpoint_callback,
                            scan_id,
                            "deals_completed",
                            total_records,
                            None,
                            page_count,
                            batch_size,
                            {
                                "completion_status": "success",
                                "total_pages": page_count,
                                "final_total": total_records,
                            },
                            logger
                        )

                    logger.info(
                        "HubSpot deals extraction completed successfully",
                        extra={
                            "operation": "deals_extraction",
                            "scan_id": scan_id,
                            "total_records": total_records,
                            "total_pages": page_count,
                        },
                    )
                    break

            except Exception as e:
                logger.error(
                    "Error fetching HubSpot deals page",
                    extra={
                        "operation": "deals_extraction",
                        "scan_id": scan_id,
                        "page_number": page_count + 1,
                        "error": str(e),
                    },
                    exc_info=True,
                )

                # Save error checkpoint for recovery
                if checkpoint_callback:
                    _save_checkpoint(
                        checkpoint_callback,
                        scan_id,
                        "deals_error",
                        total_records,
                        after,
                        page_count,
                        batch_size,
                        {
                            "error": str(e),
                            "error_page": page_count + 1,
                            "recovery_cursor": after,
                        },
                        logger
                    )

                raise e

    @dlt.resource(
        name="hubspot_deal_associations",
        write_disposition="replace",
        primary_key=["deal_id", "association_id", "association_type"],
    )
    def get_deal_associations() -> Iterator[Dict[str, Any]]:
        """
        Extract deal associations (contacts, companies, line items) as separate resource
        """
        if not filters.get("includeAssociations"):
            return
            
        # This would be populated during the main deals extraction
        # For now, we'll extract it as part of the main deals data
        # In a more complex setup, this could be a separate API call
        return
        yield  # Make it a generator

    return [get_deals_data, get_deal_associations]


def _transform_deal_record(deal: Dict[str, Any], scan_id: str, organization_id: str, page_number: int) -> Dict[str, Any]:
    """Transform HubSpot deal record to standardized format"""
    
    properties = deal.get("properties", {})
    
    # Extract and transform deal data
    transformed = {
        # Primary identifiers
        "deal_id": deal.get("id"),
        
        # Basic deal information
        "deal_name": properties.get("dealname"),
        "amount": _safe_decimal(properties.get("amount")),
        "currency": properties.get("deal_currency_code", "USD"),
        
        # Deal stage and pipeline
        "deal_stage": properties.get("dealstage"),
        "deal_stage_label": properties.get("dealstage_label"),
        "pipeline_id": properties.get("pipeline"),
        "pipeline_label": properties.get("pipeline_label"),
        
        # Dates
        "close_date": _safe_datetime(properties.get("closedate")),
        "created_at": _safe_datetime(properties.get("createdate")),
        "updated_at": _safe_datetime(properties.get("hs_lastmodifieddate")),
        
        # Ownership
        "owner_id": properties.get("hubspot_owner_id"),
        "owner_email": properties.get("hubspot_owner_email"),
        
        # Deal metadata
        "deal_type": properties.get("dealtype"),
        "is_archived": deal.get("archived", False),
        "deal_url": f"https://app.hubspot.com/contacts/{properties.get('hs_object_id', '')}/deal/{deal.get('id', '')}" if deal.get('id') else None,
        
        # Custom properties (flatten all other properties)
        "properties": properties,
        
        # Associations
        "associations": deal.get("associations", {}),
        
        # Extraction metadata
        "_extracted_at": datetime.now(timezone.utc).isoformat(),
        "_scan_id": scan_id,
        "_organization_id": organization_id,
        "_page_number": page_number,
        "_source_service": "hubspot_deals",
    }
    
    return transformed


def _extract_next_cursor(data: Dict[str, Any]) -> Optional[str]:
    """Extract next page cursor from HubSpot API response"""
    paging = data.get("paging", {})
    if paging.get("next") and paging["next"].get("after"):
        return paging["next"]["after"]
    return None


def _safe_decimal(value: Any) -> Optional[float]:
    """Safely convert value to decimal/float"""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_datetime(value: Any) -> Optional[str]:
    """Safely convert HubSpot datetime to ISO format"""
    if not value:
        return None
    
    try:
        # HubSpot typically returns timestamps in milliseconds
        if isinstance(value, str) and value.isdigit():
            timestamp = int(value) / 1000  # Convert to seconds
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        elif isinstance(value, (int, float)):
            timestamp = value / 1000 if value > 1e10 else value  # Handle milliseconds
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        else:
            # Try to parse as ISO string
            return datetime.fromisoformat(value.replace('Z', '+00:00')).isoformat()
    except (ValueError, TypeError, OSError):
        return None


def _save_checkpoint(
    checkpoint_callback: Callable,
    scan_id: str,
    phase: str,
    records_processed: int,
    cursor: Optional[str],
    page_number: int,
    batch_size: int,
    additional_data: Dict[str, Any],
    logger: logging.Logger
) -> None:
    """Save checkpoint with error handling"""
    try:
        checkpoint_data = {
            "phase": phase,
            "records_processed": records_processed,
            "cursor": cursor,
            "page_number": page_number,
            "batch_size": batch_size,
            "checkpoint_data": {
                "service": "hubspot_deals",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **additional_data,
            },
        }
        
        checkpoint_callback(scan_id, checkpoint_data)
        
        logger.debug(
            "Checkpoint saved successfully",
            extra={
                "operation": "deals_extraction",
                "scan_id": scan_id,
                "phase": phase,
                "page_number": page_number,
                "records_processed": records_processed,
            },
        )
        
    except Exception as checkpoint_error:
        logger.warning(
            "Failed to save checkpoint",
            extra={
                "operation": "deals_extraction",
                "scan_id": scan_id,
                "phase": phase,
                "error": str(checkpoint_error),
            },
        )