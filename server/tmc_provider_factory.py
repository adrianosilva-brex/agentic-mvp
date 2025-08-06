"""
TMC Provider Factory

This module provides a factory for creating TMC provider instances
and routing operations based on the selected provider type.
"""

import os
from typing import Dict, Any, Optional
from base_tmc_provider import BaseTMCProvider, TMCProviderType, TMCProviderError


class TMCProviderFactory:
    """Factory for creating and managing TMC provider instances."""
    
    _providers: Dict[TMCProviderType, BaseTMCProvider] = {}
    _current_provider: Optional[TMCProviderType] = None
    
    @classmethod
    def register_provider(cls, provider_type: TMCProviderType, provider_instance: BaseTMCProvider):
        """Register a TMC provider instance."""
        cls._providers[provider_type] = provider_instance
    
    @classmethod
    def get_provider(cls, provider_type: TMCProviderType) -> BaseTMCProvider:
        """Get a specific TMC provider instance."""
        if provider_type not in cls._providers:
            # Lazy load provider if not registered
            cls._load_provider(provider_type)
        
        if provider_type not in cls._providers:
            raise TMCProviderError(f"Provider {provider_type} not found")
        
        return cls._providers[provider_type]
    
    @classmethod
    def get_current_provider(cls) -> BaseTMCProvider:
        """Get the currently selected TMC provider."""
        if cls._current_provider is None:
            # Default to first available provider
            if cls._providers:
                cls._current_provider = next(iter(cls._providers.keys()))
            else:
                # Load default provider
                cls._load_provider(TMCProviderType.DECK)
                cls._current_provider = TMCProviderType.DECK
        
        return cls.get_provider(cls._current_provider)
    
    @classmethod
    def set_current_provider(cls, provider_type: TMCProviderType):
        """Set the current active TMC provider."""
        # Ensure provider is loaded
        cls.get_provider(provider_type)
        cls._current_provider = provider_type
    
    @classmethod
    def list_providers(cls) -> Dict[TMCProviderType, Dict[str, Any]]:
        """List all available TMC providers with their info."""
        providers_info = {}
        
        # Load all known providers
        for provider_type in TMCProviderType:
            try:
                provider = cls.get_provider(provider_type)
                providers_info[provider_type] = provider.get_provider_info()
            except Exception as e:
                providers_info[provider_type] = {
                    "error": str(e),
                    "status": "unavailable"
                }
        
        return providers_info
    
    @classmethod
    def _load_provider(cls, provider_type: TMCProviderType):
        """Lazy load a specific provider."""
        try:
            if provider_type == TMCProviderType.DECK:
                from deck.deck_provider import DeckProvider
                cls._providers[provider_type] = DeckProvider()
            elif provider_type == TMCProviderType.ANON:
                from anon.anon_provider import AnonProvider
                cls._providers[provider_type] = AnonProvider()
            elif provider_type == TMCProviderType.SUPERGOOD:
                from supergood.supergood_provider import SupergoodProvider
                cls._providers[provider_type] = SupergoodProvider()
            else:
                raise TMCProviderError(f"Unknown provider type: {provider_type}")
        except ImportError as e:
            raise TMCProviderError(f"Failed to load provider {provider_type}: {e}")


class TMCRouter:
    """Router for TMC operations that delegates to the current provider."""
    
    def __init__(self):
        self.factory = TMCProviderFactory()
    
    def health_check(self, provider_type: TMCProviderType = None) -> Dict[str, Any]:
        """Health check for specified or current provider."""
        if provider_type:
            provider = self.factory.get_provider(provider_type)
        else:
            provider = self.factory.get_current_provider()
        
        return provider.health_check()
    
    def get_embedded_url(self, user_id: str, provider_type: TMCProviderType = None, **kwargs) -> str:
        """Get embedded URL for specified or current provider."""
        if provider_type:
            provider = self.factory.get_provider(provider_type)
        else:
            provider = self.factory.get_current_provider()
        
        return provider.get_embedded_url(user_id, **kwargs)
    
    def sync_trip_data(self, trip_data: Dict[str, Any], provider_type: TMCProviderType = None) -> Dict[str, Any]:
        """Sync trip data with specified or current provider."""
        if provider_type:
            provider = self.factory.get_provider(provider_type)
        else:
            provider = self.factory.get_current_provider()
        
        return provider.sync_trip_data(trip_data)
    
    def get_trip_data(self, trip_id: str, provider_type: TMCProviderType = None) -> Dict[str, Any]:
        """Get trip data from specified or current provider."""
        if provider_type:
            provider = self.factory.get_provider(provider_type)
        else:
            provider = self.factory.get_current_provider()
        
        return provider.get_trip_data(trip_id)
    
    def switch_provider(self, provider_type: TMCProviderType):
        """Switch to a different TMC provider."""
        self.factory.set_current_provider(provider_type)
        return {
            "status": "success",
            "current_provider": provider_type,
            "message": f"Switched to {provider_type} provider"
        }
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        current = self.factory._current_provider
        providers = self.factory.list_providers()
        
        return {
            "current_provider": current,
            "available_providers": providers,
            "total_providers": len(providers)
        }