import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import time
import json
from collections import deque
from threading import Lock
from loki_logger import get_logger, log_api_call


class HubSpotRateLimiter:
    """
    Rate limiter for HubSpot API: 150 requests per 10 seconds
    """
    def __init__(self, max_requests: int = 150, time_window: int = 10):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = Lock()
        
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        with self.lock:
            now = time.time()
            
            # Remove requests older than time_window
            while self.requests and now - self.requests[0] >= self.time_window:
                self.requests.popleft()
            
            # Check if we need to wait
            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (now - self.requests[0]) + 0.1  # Small buffer
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # Clean up old requests after waiting
                    now = time.time()
                    while self.requests and now - self.requests[0] >= self.time_window:
                        self.requests.popleft()
            
            # Record this request
            self.requests.append(now)


class HubSpotAPIService:
    """
    Service for interacting with HubSpot CRM APIs
    """
    
    def __init__(self, base_url: str = "https://api.hubapi.com", test_delay_seconds: float = 0):
        self.base_url = base_url.rstrip('/')
        self.test_delay_seconds = test_delay_seconds
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        self.rate_limiter = HubSpotRateLimiter()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'HubSpot-Deal-Extraction-Service/1.0'
        })
        
        self.logger.debug(
            "HubSpot API service initialized",
            extra={
                'operation': 'api_service_init', 
                'base_url': base_url,
                'test_delay_seconds': test_delay_seconds
            }
        )
    
    def set_access_token(self, token: str):
        """Set the HubSpot API access token"""
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
        self.logger.debug("HubSpot access token set", extra={'operation': 'token_set'})
    
    def _make_request(self, method: str, url: str, headers: Dict[str, str] = None, 
                     params: Dict[str, Any] = None, data: Dict[str, Any] = None,
                     max_retries: int = 3) -> requests.Response:
        """
        Make rate-limited request to HubSpot API with retry logic
        """
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Add test delay if configured
        if self.test_delay_seconds > 0:
            time.sleep(self.test_delay_seconds)
        
        # Merge headers
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        for attempt in range(max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    params=params,
                    json=data,
                    timeout=30
                )
                
                # Handle rate limiting (429) - HubSpot specific
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 1))
                    self.logger.warning(
                        "HubSpot rate limit hit, waiting",
                        extra={
                            'operation': 'make_request',
                            'retry_after': retry_after,
                            'attempt': attempt + 1,
                            'status_code': 429
                        }
                    )
                    if attempt < max_retries:
                        time.sleep(retry_after)
                        continue
                
                # Handle temporary server errors (5xx)
                if 500 <= response.status_code < 600 and attempt < max_retries:
                    backoff_time = (2 ** attempt) + 1  # Exponential backoff
                    self.logger.warning(
                        "Server error, retrying",
                        extra={
                            'operation': 'make_request',
                            'status_code': response.status_code,
                            'attempt': attempt + 1,
                            'backoff_seconds': backoff_time
                        }
                    )
                    time.sleep(backoff_time)
                    continue
                
                return response
                
            except requests.exceptions.Timeout as e:
                if attempt < max_retries:
                    backoff_time = (2 ** attempt) + 1
                    self.logger.warning(
                        "Request timeout, retrying",
                        extra={
                            'operation': 'make_request',
                            'attempt': attempt + 1,
                            'backoff_seconds': backoff_time,
                            'error': str(e)
                        }
                    )
                    time.sleep(backoff_time)
                    continue
                raise
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    backoff_time = (2 ** attempt) + 1
                    self.logger.warning(
                        "Request failed, retrying",
                        extra={
                            'operation': 'make_request',
                            'attempt': attempt + 1,
                            'backoff_seconds': backoff_time,
                            'error': str(e)
                        }
                    )
                    time.sleep(backoff_time)
                    continue
                raise
        
        return response

    def get_deals(self, 
                  limit: int = 100,
                  after: Optional[str] = None,
                  properties: Optional[List[str]] = None,
                  associations: Optional[List[str]] = None,
                  archived: bool = False,
                  **kwargs) -> Dict[str, Any]:
        """
        Get deals from HubSpot CRM API with pagination support
        
        Args:
            limit: Number of deals to return (max 100)
            after: Pagination cursor for next page
            properties: List of deal properties to retrieve
            associations: List of associated objects to include
            archived: Include archived deals
            **kwargs: Additional parameters
        
        Returns:
            Dict containing deals data and pagination info
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(
                "Starting deal retrieval from HubSpot",
                extra={
                    'operation': 'get_deals',
                    'limit': limit,
                    'has_cursor': after is not None,
                    'archived': archived,
                    'properties_count': len(properties) if properties else 0,
                    'associations_count': len(associations) if associations else 0
                }
            )
            
            # Build URL
            url = f"{self.base_url}/crm/v3/objects/deals"
            
            
            # Build parameters
            params = {
                'limit': min(limit, 100),  # HubSpot API limit
                'archived': str(archived).lower()
            }
            
            # Add pagination cursor
            if after:
                params['after'] = after
            
            # Add properties to retrieve
            if properties:
                params['properties'] = ','.join(properties)
            else:
                # Default properties for deals
                default_properties = [
                    'dealname', 'amount', 'dealstage', 'pipeline', 'closedate',
                    'createdate', 'hs_lastmodifieddate', 'hubspot_owner_id',
                    'dealtype', 'hs_deal_stage_probability'
                ]
                params['properties'] = ','.join(default_properties)
            
            # Add associations
            if associations:
                params['associations'] = ','.join(associations)
            
            # Add any additional parameters
            for key, value in kwargs.items():
                if not key.startswith('_test_') and key not in ['scan_id']:
                    params[key] = value
            
            # Make the request
            response = self._make_request('GET', url, params=params)
            response.raise_for_status()
            
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            result = response.json()
            
            # Process and normalize the response
            processed_result = self._process_deals_response(result)
            
            self.logger.info(
                "Deals retrieved successfully from HubSpot",
                extra={
                    'operation': 'get_deals',
                    'status_code': response.status_code,
                    'duration_ms': round(duration_ms, 2),
                    'deals_count': len(processed_result.get('results', [])),
                    'has_more': processed_result.get('paging', {}).get('next') is not None,
                    'next_cursor': processed_result.get('paging', {}).get('next', {}).get('after')
                }
            )
            
            log_api_call(
                self.logger,
                "hubspot_get_deals",
                method='GET',
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )
            
            return processed_result
            
        except requests.exceptions.RequestException as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            error_details = {
                'operation': 'get_deals',
                'error': str(e),
                'duration_ms': round(duration_ms, 2)
            }
            
            if hasattr(e, 'response') and e.response is not None:
                error_details['status_code'] = e.response.status_code
                try:
                    error_details['response_body'] = e.response.json()
                except:
                    error_details['response_text'] = e.response.text[:500]
            
            self.logger.error(
                "Error fetching deals from HubSpot",
                extra=error_details,
                exc_info=True
            )
            
            log_api_call(
                self.logger,
                "hubspot_get_deals",
                method='GET',
                status_code=getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500,
                duration_ms=round(duration_ms, 2)
            )
            
            raise

    def _process_deals_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize HubSpot deals API response"""
        processed = {
            'results': [],
            'paging': response_data.get('paging', {}),
            'total': response_data.get('total'),
        }
        
        for deal in response_data.get('results', []):
            processed_deal = {
                'id': deal.get('id'),
                'properties': deal.get('properties', {}),
                'associations': deal.get('associations', {}),
                'createdAt': deal.get('createdAt'),
                'updatedAt': deal.get('updatedAt'),
                'archived': deal.get('archived', False)
            }
            processed['results'].append(processed_deal)
        
        return processed

    def validate_token(self, access_token: str) -> bool:
        """
        Validate HubSpot API access token using account info endpoint
        """
        try:
            self.logger.debug(
                "Validating HubSpot access token",
                extra={'operation': 'validate_token'}
            )
            
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            # Use HubSpot account info endpoint for validation
            url = f"{self.base_url}/account-info/v3/api-usage/daily"
            
            response = self._make_request('GET', url, headers=headers, max_retries=1)
            is_valid = response.status_code == 200
            
            if is_valid:
                self.logger.info(
                    "HubSpot token validation successful",
                    extra={'operation': 'validate_token'}
                )
            else:
                self.logger.warning(
                    "HubSpot token validation failed",
                    extra={
                        'operation': 'validate_token',
                        'status_code': response.status_code
                    }
                )
            
            return is_valid
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "HubSpot token validation error",
                extra={'operation': 'validate_token', 'error': str(e)},
                exc_info=True
            )
            return False
    
    def get_api_usage(self, auth_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get API usage information from HubSpot
        """
        try:
            access_token = auth_config.get('hubspot_access_token') or auth_config.get('accessToken')
            if not access_token:
                return None
                
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            # HubSpot API usage endpoint
            url = f"{self.base_url}/account-info/v3/api-usage/daily"
            
            response = self._make_request('GET', url, headers=headers, max_retries=1)
            
            if response.status_code == 200:
                usage_data = response.json()
                
                # Process HubSpot usage response
                usage_info = {
                    'daily_limit': usage_data.get('currentUsage', {}).get('dailyLimit'),
                    'daily_remaining': usage_data.get('currentUsage', {}).get('dailyRemaining'),
                    'interval_limit': 150,  # HubSpot's 10-second limit
                    'interval_window_seconds': 10,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                # Add rate limit info from headers if available
                if 'X-HubSpot-RateLimit-Daily' in response.headers:
                    usage_info['daily_limit'] = int(response.headers['X-HubSpot-RateLimit-Daily'])
                if 'X-HubSpot-RateLimit-Daily-Remaining' in response.headers:
                    usage_info['daily_remaining'] = int(response.headers['X-HubSpot-RateLimit-Daily-Remaining'])
                
                filtered_usage = {k: v for k, v in usage_info.items() if v is not None}
                
                if filtered_usage:
                    self.logger.debug(
                        "HubSpot API usage info retrieved",
                        extra={
                            'operation': 'get_api_usage',
                            'daily_remaining': filtered_usage.get('daily_remaining'),
                            'daily_limit': filtered_usage.get('daily_limit')
                        }
                    )
                
                return filtered_usage if filtered_usage else None
            
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(
                "Could not retrieve HubSpot API usage",
                extra={'operation': 'get_api_usage', 'error': str(e)}
            )
            return None
    
    def get_account_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get HubSpot account information
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            # HubSpot account info endpoint
            url = f"{self.base_url}/account-info/v3/details"
            response = self._make_request('GET', url, headers=headers, max_retries=1)
            
            if response.status_code == 200:
                account_info = response.json()
                self.logger.debug(
                    "HubSpot account info retrieved",
                    extra={
                        'operation': 'get_account_info',
                        'portal_id': account_info.get('portalId'),
                        'account_type': account_info.get('accountType')
                    }
                )
                return account_info
            
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.debug(
                "HubSpot account info not available",
                extra={'operation': 'get_account_info', 'error': str(e)}
            )
            return None

    def test_connection(self, access_token: str) -> Dict[str, Any]:
        """
        Test connection to HubSpot API
        """
        self.logger.info(
            "Testing HubSpot API connection",
            extra={'operation': 'test_connection'}
        )
        
        results = {
            'token_valid': False,
            'api_reachable': False,
            'deals_accessible': False,
            'account_info': None,
            'usage_info': None,
            'error': None
        }
        
        try:
            # Test token validation
            results['token_valid'] = self.validate_token(access_token)
            results['api_reachable'] = results['token_valid']
            
            if results['token_valid']:
                # Get additional info
                results['account_info'] = self.get_account_info(access_token)
                results['usage_info'] = self.get_api_usage({'hubspot_access_token': access_token})
                
                # Test deals access
                try:
                    test_deals = self.get_deals(access_token, limit=1)
                    results['deals_accessible'] = True
                    
                    self.logger.info(
                        "HubSpot connection test successful",
                        extra={
                            'operation': 'test_connection',
                            'token_valid': results['token_valid'],
                            'deals_accessible': results['deals_accessible'],
                            'portal_id': results.get('account_info', {}).get('portalId')
                        }
                    )
                    
                except Exception as e:
                    results['error'] = f"Deals access failed: {str(e)}"
                    self.logger.warning(
                        "HubSpot deals access test failed",
                        extra={'operation': 'test_connection', 'error': str(e)}
                    )
            else:
                results['error'] = "Invalid access token"
                self.logger.warning(
                    "HubSpot connection test failed - invalid token",
                    extra={'operation': 'test_connection'}
                )
                
        except Exception as e:
            results['error'] = str(e)
            self.logger.error(
                "HubSpot connection test error",
                extra={'operation': 'test_connection', 'error': str(e)},
                exc_info=True
            )
        
        return results

    # Legacy method for backward compatibility
    def get_data(self, access_token: str, limit: int = 100, after: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Legacy wrapper for get_deals method"""
        return self.get_deals(access_token=access_token, limit=limit, after=after, **kwargs)