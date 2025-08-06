"""
Trip MVP Storage Data Models

This package contains the data models and database configuration for the Trip Management System.

The system is designed around a flexible, schema-as-prompts approach with multi-level views,
storing trip data in DynamoDB with the ability to evolve schemas without migrations.

Key Components:
- db_config: DynamoDB setup and configuration
- trip_model: Flexible trip data model with versioning
- document_model: Document metadata and processing tracking  
- field_registry_model: Dynamic field discovery and registry

Usage:
    from trip_mvp.storage.data import DynamoDBConfig, Trip, DocumentMetadata, FieldRegistry
    
    # Setup database
    config = DynamoDBConfig(endpoint_url='http://localhost:4566')  # LocalStack
    config.setup_all_tables()
    
    # Create a trip
    trip = Trip()
    trip.traveler = Traveler(id="user-123", name="John Doe", email="john@example.com")
    trip.start_date = "2025-09-15"
    trip.end_date = "2025-09-18"
    
    # Add flight extension
    flight_data = {
        "confirmation_code": "ABC123",
        "segments": [{
            "segment_id": "seg-1",
            "flight_number": "SW1234",
            "departure": {"airport": "SFO", "time": "2025-09-15T09:30:00Z"},
            "arrival": {"airport": "JFK", "time": "2025-09-15T18:00:00Z"}
        }]
    }
    trip.add_extension("southwest_itinerary", flight_data)
"""

from .db_config import DynamoDBConfig, DynamoDBHelper
from .trip_model import (
    Trip, TripBuilder, Traveler, ChangeEntry, FlightSegment, 
    SourceDocument, VersionEntry, MergeCandidate,
    TripStatus, OriginType, ChangeType
)
from .document_model import (
    DocumentMetadata, DocumentBuilder, ExtractionResult, DocumentClassifier,
    DocumentSourceType, ProcessingStatus, DocumentType
)
from .field_registry_model import (
    FieldRegistryEntry, FieldRegistry, FieldAnalyzer, FieldExample, FieldStatistics,
    FieldDataType, FieldStability
)

__all__ = [
    # Database configuration
    'DynamoDBConfig',
    'DynamoDBHelper',
    
    # Trip models
    'Trip',
    'TripBuilder', 
    'Traveler',
    'ChangeEntry',
    'FlightSegment',
    'SourceDocument',
    'VersionEntry',
    'MergeCandidate',
    'TripStatus',
    'OriginType', 
    'ChangeType',
    
    # Document models
    'DocumentMetadata',
    'DocumentBuilder',
    'ExtractionResult', 
    'DocumentClassifier',
    'DocumentSourceType',
    'ProcessingStatus',
    'DocumentType',
    
    # Field registry models
    'FieldRegistryEntry',
    'FieldRegistry',
    'FieldAnalyzer',
    'FieldExample',
    'FieldStatistics',
    'FieldDataType',
    'FieldStability'
]

# Package metadata
__version__ = '0.1.0'
__author__ = 'Trip MVP Team'
__description__ = 'Flexible trip data models for DynamoDB storage'