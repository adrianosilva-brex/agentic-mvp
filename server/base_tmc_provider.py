"""
Base TMC Provider Interface

This module defines the common interface that all TMC (Travel Management Company) 
providers must implement. Each provider (deck, anon, supergood) will inherit from
this base class and implement the required methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum


class TMCProviderType(str, Enum):
    """TMC Provider types enumeration."""
    DECK = "deck"
    ANON = "anon" 
    SUPERGOOD = "supergood.ai"


class HealthStatus(str, Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class BaseTMCProvider(ABC):
    """
    Base abstract class for all TMC providers.
    
    Each TMC provider must implement these core methods to ensure
    consistent behavior across different integrations.
    """
    
    def __init__(self, provider_type: TMCProviderType, config: Dict[str, Any] = None):
        self.provider_type = provider_type
        self.config = config or {}
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the human-readable name of the provider."""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health/status of the TMC provider.
        
        Returns:
            Dict containing:
            - status: HealthStatus enum value
            - code: HTTP status code or custom code
            - message: Human readable status message
            - data: Optional additional data
        """
        pass
    
    @abstractmethod
    def get_embedded_url(self, user_id: str, **kwargs) -> str:
        """
        Get the embedded URL for the TMC provider interface.
        
        Args:
            user_id: User identifier
            **kwargs: Additional provider-specific parameters
            
        Returns:
            URL string for embedding the TMC interface
        """
        pass
    
    @abstractmethod
    def sync_trip_data(self, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync trip data with the TMC provider.
        
        Args:
            trip_data: Trip information to sync
            
        Returns:
            Dict containing sync results and status
        """
        pass
    
    @abstractmethod
    def get_trip_data(self, trip_id: str) -> Dict[str, Any]:
        """
        Retrieve trip data from the TMC provider.
        
        Args:
            trip_id: Trip identifier
            
        Returns:
            Dict containing trip data
        """
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get basic information about this TMC provider.
        
        Returns:
            Dict containing provider metadata
        """
        return {
            "type": self.provider_type,
            "name": self.provider_name,
            "config_keys": list(self.config.keys()),
            "supported_operations": [
                "health_check",
                "get_embedded_url", 
                "sync_trip_data",
                "get_trip_data"
            ]
        }
    
    def validate_config(self) -> bool:
        """
        Validate the provider configuration.
        Override in subclasses for specific validation logic.
        
        Returns:
            True if configuration is valid
        """
        return True


class TMCProviderError(Exception):
    """Base exception for TMC provider errors."""
    
    def __init__(self, message: str, provider_type: str = None, status_code: int = None):
        super().__init__(message)
        self.provider_type = provider_type
        self.status_code = status_code


class TMCProviderConnectionError(TMCProviderError):
    """Exception for TMC provider connection issues."""
    pass


class TMCProviderAuthError(TMCProviderError):
    """Exception for TMC provider authentication issues."""
    pass


class TMCProviderDataError(TMCProviderError):
    """Exception for TMC provider data validation issues."""
    pass