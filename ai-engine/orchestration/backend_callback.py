"""
Backend callback utility for IncidentOS orchestration.

This module provides a lightweight, reusable utility for sending
data to backend callback endpoints without coupling agents directly
to backend infrastructure.

Features:
- Async HTTP requests using httpx
- Environment variable configuration
- Graceful error handling
- Structured logging
- No direct backend coupling in agents
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import httpx  # type: ignore
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None  # type: ignore
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

class BackendConfig:
    """Backend callback configuration from environment variables."""
    
    @staticmethod
    def get_backend_url() -> Optional[str]:
        """Get backend URL from environment."""
        return os.getenv("BACKEND_URL")
    
    @staticmethod
    def get_callback_api_key() -> Optional[str]:
        """Get callback API key from environment."""
        return os.getenv("CALLBACK_API_KEY")
    
    @staticmethod
    def is_configured() -> bool:
        """Check if backend callback is properly configured."""
        return bool(
            BackendConfig.get_backend_url() and 
            BackendConfig.get_callback_api_key()
        )


# ============================================================================
# CALLBACK UTILITY
# ============================================================================

class BackendCallback:
    """
    Lightweight utility for sending callbacks to backend.
    
    This class handles:
    - Async HTTP POST requests
    - Authentication headers
    - Error handling and logging
    - Graceful degradation on failures
    """
    
    def __init__(
        self,
        backend_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 10.0
    ):
        """
        Initialize backend callback utility.
        
        Args:
            backend_url: Backend base URL (defaults to env var)
            api_key: API key for authentication (defaults to env var)
            timeout: Request timeout in seconds
        """
        self.backend_url = backend_url or BackendConfig.get_backend_url()
        self.api_key = api_key or BackendConfig.get_callback_api_key()
        self.timeout = timeout
        
        if not HTTPX_AVAILABLE:
            logger.warning("httpx not available - callbacks will be skipped")
    
    def is_enabled(self) -> bool:
        """Check if callbacks are enabled and configured."""
        return HTTPX_AVAILABLE and bool(self.backend_url and self.api_key)
    
    async def send_async(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        repo_id: Optional[str] = None,
        node_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send async callback to backend endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., "/callback/dependencies-extracted")
            payload: JSON payload to send
            repo_id: Optional repository ID for logging
            node_name: Optional node name for logging
            
        Returns:
            Dict with success status and response data
        """
        if not self.is_enabled():
            logger.warning(
                f"[{node_name or 'CALLBACK'}] Backend callback disabled - "
                f"httpx_available={HTTPX_AVAILABLE}, "
                f"configured={bool(self.backend_url and self.api_key)}"
            )
            return {
                "success": False,
                "error": "Backend callback not configured or httpx not available",
                "skipped": True
            }
        
        url = f"{self.backend_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key or "",
        }
        
        log_prefix = f"[{node_name or 'CALLBACK'}]"
        if repo_id:
            log_prefix += f" [repo_id={repo_id}]"
        
        try:
            logger.info(f"{log_prefix} Sending callback to {endpoint}")
            
            if httpx is None:
                raise ImportError("httpx not available")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:  # type: ignore
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers
                )
                
                response.raise_for_status()
                
                logger.info(
                    f"{log_prefix} Callback successful - "
                    f"status={response.status_code}"
                )
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": response.json() if response.text else None
                }
                
        except Exception as e:
            # Handle httpx-specific exceptions
            if httpx and isinstance(e, httpx.HTTPStatusError):  # type: ignore
                logger.error(
                    f"{log_prefix} Callback failed - "
                    f"status={e.response.status_code}, error={str(e)}"
                )
                return {
                    "success": False,
                    "error": f"HTTP {e.response.status_code}: {str(e)}",
                    "status_code": e.response.status_code
                }
            elif httpx and isinstance(e, httpx.TimeoutException):  # type: ignore
                logger.error(f"{log_prefix} Callback timeout after {self.timeout}s")
                return {
                    "success": False,
                    "error": f"Request timeout after {self.timeout}s"
                }
            else:
                logger.error(
                    f"{log_prefix} Callback failed - {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                return {
                    "success": False,
                    "error": f"{type(e).__name__}: {str(e)}"
                }
    
    def send_sync(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        repo_id: Optional[str] = None,
        node_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send synchronous callback to backend endpoint.
        
        This is a blocking version for non-async contexts.
        
        Args:
            endpoint: API endpoint path
            payload: JSON payload to send
            repo_id: Optional repository ID for logging
            node_name: Optional node name for logging
            
        Returns:
            Dict with success status and response data
        """
        if not self.is_enabled():
            logger.warning(
                f"[{node_name or 'CALLBACK'}] Backend callback disabled"
            )
            return {
                "success": False,
                "error": "Backend callback not configured or httpx not available",
                "skipped": True
            }
        
        url = f"{self.backend_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key or "",
        }
        
        log_prefix = f"[{node_name or 'CALLBACK'}]"
        if repo_id:
            log_prefix += f" [repo_id={repo_id}]"
        
        try:
            logger.info(f"{log_prefix} Sending callback to {endpoint}")
            
            if httpx is None:
                raise ImportError("httpx not available")
            
            with httpx.Client(timeout=self.timeout) as client:  # type: ignore
                response = client.post(
                    url,
                    json=payload,
                    headers=headers
                )
                
                response.raise_for_status()
                
                logger.info(
                    f"{log_prefix} Callback successful - "
                    f"status={response.status_code}"
                )
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": response.json() if response.text else None
                }
                
        except Exception as e:
            # Handle httpx-specific exceptions
            if httpx and isinstance(e, httpx.HTTPStatusError):  # type: ignore
                logger.error(
                    f"{log_prefix} Callback failed - "
                    f"status={e.response.status_code}, error={str(e)}"
                )
                return {
                    "success": False,
                    "error": f"HTTP {e.response.status_code}: {str(e)}",
                    "status_code": e.response.status_code
                }
            elif httpx and isinstance(e, httpx.TimeoutException):  # type: ignore
                logger.error(f"{log_prefix} Callback timeout after {self.timeout}s")
                return {
                    "success": False,
                    "error": f"Request timeout after {self.timeout}s"
                }
            else:
                logger.error(
                    f"{log_prefix} Callback failed - {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                return {
                    "success": False,
                    "error": f"{type(e).__name__}: {str(e)}"
                }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def send_callback_async(
    endpoint: str,
    payload: Dict[str, Any],
    repo_id: Optional[str] = None,
    node_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for sending async callbacks.
    
    Args:
        endpoint: API endpoint path
        payload: JSON payload to send
        repo_id: Optional repository ID for logging
        node_name: Optional node name for logging
        
    Returns:
        Dict with success status and response data
    """
    callback = BackendCallback()
    return await callback.send_async(endpoint, payload, repo_id, node_name)


def send_callback_sync(
    endpoint: str,
    payload: Dict[str, Any],
    repo_id: Optional[str] = None,
    node_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for sending synchronous callbacks.
    
    Args:
        endpoint: API endpoint path
        payload: JSON payload to send
        repo_id: Optional repository ID for logging
        node_name: Optional node name for logging
        
    Returns:
        Dict with success status and response data
    """
    callback = BackendCallback()
    return callback.send_sync(endpoint, payload, repo_id, node_name)

# Made with Bob
