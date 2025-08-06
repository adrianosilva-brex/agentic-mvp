"""
Deck TMC Provider Implementation

This module implements the Deck-specific TMC provider logic.
"""

import os
from typing import Dict, Any

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from base_tmc_provider import (
    BaseTMCProvider, TMCProviderType, HealthStatus,
    TMCProviderError
)

# Try to load dotenv if available, but don't fail if it's not
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class DeckProvider(BaseTMCProvider):
    """Deck TMC Provider implementation."""
    
    def __init__(self):
        config = {
            "api_url": os.getenv("DECK_API_URL", "http://deck.co.mock.url"),
            "api_key": os.getenv("DECK_API_KEY")
        }
        super().__init__(TMCProviderType.DECK, config)
    
    @property
    def provider_name(self) -> str:
        return "Deck Travel Management"
    
    def health_check(self) -> Dict[str, Any]:
        """Check Deck API health status."""
        # Basic implementation - would normally call Deck API
        return {
            "status": HealthStatus.HEALTHY,
            "code": 200,
            "message": "Deck API is healthy",
            "data": {"version": "1.0", "uptime": "99.9%"}
        }
    
    def get_embedded_url(self, user_id: str, **kwargs) -> str:
        """Get Deck embedded URL."""
        # Basic implementation - would normally generate real Deck URL
        base_url = self.config.get("api_url", "http://deck.co.mock.url")
        return f"{base_url}/embed?user_id={user_id}"
    
    def sync_trip_data(self, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync trip data with Deck."""
        # Mock implementation - would normally sync with Deck API
        return {
            "status": "success",
            "provider": "deck",
            "trip_id": trip_data.get("trip_id"),
            "synced_at": "2025-01-27T10:00:00Z",
            "deck_reference": f"deck-{trip_data.get('trip_id', 'unknown')}",
            "message": "Trip data synced with Deck successfully"
        }
    
    def get_trip_data(self, trip_id: str) -> Dict[str, Any]:
        """Retrieve trip data from Deck."""
        # Mock implementation - would normally fetch from Deck API
        return {
            "trip_id": trip_id,
            "provider": "deck",
            "status": "confirmed",
            "traveler": "Jane Smith",
            "destination": "San Francisco",
            "dates": {
                "start": "2025-02-20",
                "end": "2025-02-23"
            },
            "deck_data": {
                "booking_reference": f"DECK{trip_id}",
                "travel_policy": "standard"
            }
        }
    
    def validate_config(self) -> bool:
        """Validate Deck provider configuration."""
        # Basic validation - api_url is required
        return bool(self.config.get("api_url"))