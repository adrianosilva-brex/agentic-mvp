"""
Anon TMC Provider Implementation

This module implements the Anon-specific TMC provider logic using existing API functions.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from base_tmc_provider import (
    BaseTMCProvider, TMCProviderType, HealthStatus,
    TMCProviderError, TMCProviderConnectionError, TMCProviderAuthError
)

# Add the anon directory to path for local api import
anon_dir = os.path.dirname(__file__)
if anon_dir not in sys.path:
    sys.path.append(anon_dir)

from api import get_anon_embedded_url, health_check as anon_health_check

load_dotenv()


class AnonProvider(BaseTMCProvider):
    """Anon TMC Provider implementation using existing API functions."""
    
    def __init__(self):
        config = {
            "api_url": os.getenv("ANON_API_URL"),
            "api_key": os.getenv("ANON_API_KEY")
        }
        super().__init__(TMCProviderType.ANON, config)
    
    @property
    def provider_name(self) -> str:
        return "Anon Travel Management"
    
    def health_check(self) -> Dict[str, Any]:
        """Check Anon API health status using existing function."""
        try:
            result = anon_health_check()
            
            if result["status"] == "success":
                return {
                    "status": HealthStatus.HEALTHY,
                    "code": result["code"],
                    "message": "Anon API is healthy",
                    "data": result.get("data")
                }
            else:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "code": result["code"],
                    "message": f"Anon API error: {result.get('error', 'Unknown error')}",
                    "data": None
                }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "code": 500,
                "message": f"Health check failed: {str(e)}",
                "data": None
            }
    
    def get_embedded_url(self, user_id: str, **kwargs) -> str:
        """Get Anon embedded migration modal URL using existing function."""
        source_provider = kwargs.get('source_provider', 'navan')
        
        try:
            return get_anon_embedded_url(user_id, source_provider)
        except Exception as e:
            if "authentication" in str(e).lower():
                raise TMCProviderAuthError(f"Anon authentication failed: {str(e)}", "anon", 401)
            elif "timeout" in str(e).lower():
                raise TMCProviderConnectionError(f"Anon connection timeout: {str(e)}", "anon", 408)
            else:
                raise TMCProviderError(f"Failed to get Anon embedded URL: {str(e)}", "anon")
    
    def sync_trip_data(self, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync trip data with Anon."""
        # Mock implementation - would use actual Anon sync API when available
        try:
            return {
                "status": "success",
                "provider": "anon",
                "trip_id": trip_data.get("trip_id"),
                "synced_at": "2025-01-27T10:00:00Z",
                "anon_reference": f"anon-{trip_data.get('trip_id', 'unknown')}",
                "message": "Trip data synced with Anon successfully",
                "migration_data": {
                    "source_provider": trip_data.get("source_provider", "unknown"),
                    "migration_status": "pending"
                }
            }
        except Exception as e:
            raise TMCProviderError(f"Failed to sync trip data with Anon: {str(e)}", "anon")
    
    def get_trip_data(self, trip_id: str) -> Dict[str, Any]:
        """Retrieve trip data from Anon."""
        # Mock implementation - would use actual Anon retrieval API when available
        try:
            return {
                "trip_id": trip_id,
                "provider": "anon",
                "status": "confirmed",
                "traveler": "John Doe",
                "destination": "New York",
                "dates": {
                    "start": "2025-02-15",
                    "end": "2025-02-18"
                },
                "anon_data": {
                    "migration_status": "completed",
                    "original_provider": "navan",
                    "migration_date": "2025-01-15T10:00:00Z"
                }
            }
        except Exception as e:
            raise TMCProviderError(f"Failed to get trip data from Anon: {str(e)}", "anon")
    
    def validate_config(self) -> bool:
        """Validate Anon provider configuration."""
        required_keys = ["api_url", "api_key"]
        return all(self.config.get(key) for key in required_keys)