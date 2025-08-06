# Trip MVP Storage Data Models

This package provides flexible data models for the Trip Management System, designed to work with Amazon DynamoDB and support the schema-as-prompts approach described in the MVP documentation.

## Overview

The system uses a flexible, document-based approach to store trip data, allowing for:

- **Schema Evolution**: Add new fields without database migrations
- **Version Tracking**: Complete history of all trip changes 
- **Flexible Extensions**: Namespaced extensions for different data sources
- **Field Discovery**: Automatic cataloging of observed fields
- **Change Management**: Track how trip components evolve over time

## Architecture

### Core Components

1. **Trip Model** (`trip_model.py`)
   - Flexible trip data with namespaced extensions
   - Version tracking and change history
   - Support for merge candidate detection
   - Builder pattern for clean object creation

2. **Document Model** (`document_model.py`)
   - Document metadata and processing status tracking
   - S3 storage integration
   - Extraction result management
   - Automatic document type classification

3. **Field Registry** (`field_registry_model.py`)
   - Dynamic field discovery and cataloging
   - Statistical analysis of field usage patterns
   - Data type inference and validation
   - Schema evolution tracking

4. **Database Configuration** (`db_config.py`)
   - DynamoDB table setup and management
   - LocalStack support for development
   - Optimized indexes for query patterns
   - Connection management utilities

## Database Schema

### Tables Created

1. **trips** - Main trip data with flexible schema
   - Partition Key: `trip_id`
   - GSI1: `traveler_id-start_date-index` (user queries)
   - GSI2: `status-updated_at-index` (status-based queries)
   - GSI3: `origin_type-trip_confidence-index` (merge candidates)

2. **documents_metadata** - Document tracking and processing
   - Partition Key: `document_id`  
   - GSI1: `source_type-upload_timestamp-index`
   - GSI2: `processing_status-upload_timestamp-index`

3. **field_registry** - Field discovery and analysis
   - Partition Key: `field_id`
   - GSI1: `source_namespace-occurrence_count-index`
   - GSI2: `data_type-first_seen-index`

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Setup Database (LocalStack)

```python
from trip_mvp.storage.data import DynamoDBConfig

# Setup for local development with LocalStack
config = DynamoDBConfig(
    region_name='us-east-1',
    endpoint_url='http://localhost:4566'
)

# Create all tables
config.setup_all_tables()
```

### Create a Trip

```python
from trip_mvp.storage.data import Trip, TripBuilder, TripStatus

# Using the builder pattern
trip = (TripBuilder()
       .with_traveler("user-123", "John Doe", "john@example.com")
       .with_dates("2025-09-15", "2025-09-18") 
       .with_purpose("Business meeting")
       .with_status(TripStatus.CONFIRMED)
       .build())

# Add airline-specific data
southwest_data = {
    "confirmation_code": "ABC123",
    "segments": [{
        "segment_id": "seg-1",
        "flight_number": "SW1234",
        "departure": {"airport": "SFO", "time": "2025-09-15T09:30:00Z"},
        "arrival": {"airport": "JFK", "time": "2025-09-15T18:00:00Z"}
    }]
}
trip.add_extension("southwest_itinerary", southwest_data)

# Convert to DynamoDB format
item = trip.to_dynamodb_item()
```

### Track Documents

```python
from trip_mvp.storage.data import DocumentBuilder, DocumentSourceType, DocumentType

# Create document metadata
doc = (DocumentBuilder("flight-confirmation.pdf")
       .with_content(pdf_bytes)
       .with_source(DocumentSourceType.EMAIL_ATTACHMENT)
       .with_s3_location("documents", "2025/08/flight-confirmation.pdf")
       .with_document_type(DocumentType.ITINERARY, confidence=0.95)
       .build())

# Track processing
doc.update_processing_status("completed")
doc.associate_with_trip("trip-123")

# Add extraction results
doc.add_extraction_result({
    "extracted_at": "2025-08-02T15:35:00Z",
    "confidence_score": 0.92,
    "extracted_data": {"airline": "Southwest", "confirmation": "ABC123"}
})
```

### Build Field Registry

```python
from trip_mvp.storage.data import FieldRegistry

registry = FieldRegistry()

# Register fields from trip data
trip_data = trip.to_dict()
registry.register_document_fields(trip_data, trip.trip_id)

# Analyze discovered fields
summary = registry.get_schema_summary()
stable_fields = registry.get_stable_fields()
suggested_indexes = registry.suggest_indexes()
```

## Data Model Details

### Trip Structure

Trips use a flexible schema with core fields and namespaced extensions:

```json
{
  "trip_id": "trip-789012",
  "version": 3,
  "created_at": "2025-08-02T15:35:00Z",
  "updated_at": "2025-08-02T15:40:00Z",
  
  // Core fields (always present)
  "traveler": {
    "id": "user-456789", 
    "name": "John Doe",
    "email": "john@example.com"
  },
  "status": "confirmed",
  "start_date": "2025-09-15",
  "end_date": "2025-09-18",
  "purpose": "Client meeting",
  
  // Trip metadata
  "origin_type": "explicit",
  "trip_confidence": 0.95,
  
  // Flexible extensions (airline-specific)
  "southwest_itinerary": {
    "confirmation_code": "ABC123",
    "segments": [...]
  },
  
  "hotel_booking": {
    "provider": "Marriott", 
    "confirmation_number": "H789012"
  },
  
  // Document references
  "source_documents": [...],
  
  // Version tracking
  "version_history": [...],
  
  // Merge candidates
  "merge_candidates": [...]
}
```

### Change Tracking

The system tracks changes at multiple levels:

1. **Trip-level version history** - Overall trip changes
2. **Component-level change history** - Individual booking changes
3. **Source document tracking** - Which documents contributed what data
4. **Confidence scoring** - Reliability of extracted information

### Field Registry

The field registry automatically discovers and tracks fields:

```python
# Example field entry
{
  "field_id": "southwest_itinerary.confirmation_code",
  "path": "southwest_itinerary.confirmation_code",
  "data_type": "confirmation_code",
  "source_namespace": "southwest_itinerary", 
  "occurrence_count": 27,
  "occurrence_percentage": 85.2,
  "stability": "stable",
  "examples": [{"value": "ABC123", "source_document_id": "doc-123"}]
}
```

## Advanced Usage

### Handling Standalone Bookings

The system automatically creates trips for standalone bookings:

```python
# Standalone booking becomes a derived trip
trip = Trip(origin_type=OriginType.DERIVED, trip_confidence=0.8)

# System can suggest merging with related trips
trip.add_merge_candidate({
    "trip_id": "trip-456",
    "similarity_score": 0.85,
    "match_reasons": ["same_traveler", "date_proximity"]
})
```

### Query Patterns

```python
# Get flight information
segments = trip.get_flight_segments()
airports = trip.get_all_airports()
hotels = trip.get_hotel_bookings()

# Field registry queries
email_fields = registry.get_fields_by_type(FieldDataType.EMAIL)
stable_fields = registry.get_stable_fields()
namespace_fields = registry.get_fields_by_namespace("southwest_itinerary")
```

### Schema Evolution

Fields can be added dynamically without migrations:

```python
# Add new extension
trip.add_extension("uber_rides", {
    "ride_id": "ride-789",
    "pickup_location": "SFO Terminal 1", 
    "dropoff_location": "123 Main St"
})

# Field registry automatically discovers new fields
registry.register_document_fields({"uber_rides": {...}}, "doc-456")
```

## Development

### Run Example

```bash
# With LocalStack
python example_usage.py --localstack

# With AWS DynamoDB
python example_usage.py --aws

# Data models only (no database)
python example_usage.py --skip-db
```

### Testing

```bash
pip install pytest pytest-mock moto
pytest
```

### LocalStack Setup

```bash
# Start LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Verify DynamoDB is available
aws --endpoint-url=http://localhost:4566 dynamodb list-tables
```

## Integration Points

This data layer integrates with:

- **Document Processing Pipeline** - Stores extraction results
- **LLM Services** - Provides flexible schema for extracted data  
- **CLI Interface** - Queryable trip data
- **Table View** - Field registry enables dynamic columns
- **Change Detection** - Version tracking enables change analysis

## Performance Considerations

- **Indexes**: Optimized GSIs for common query patterns
- **Pagination**: Support for large result sets
- **Caching**: Field registry can be cached for performance
- **Batch Operations**: Models support batch reads/writes
- **Selective Loading**: Load only needed extensions

## Security

- **IAM Integration**: Works with AWS IAM policies
- **Encryption**: Supports DynamoDB encryption at rest
- **Access Patterns**: Designed for least-privilege access
- **PII Handling**: Separate handling for sensitive traveler data

## Monitoring

- **CloudWatch Integration**: Table and index metrics
- **Stream Processing**: DynamoDB streams for change events  
- **Logging**: Structured logging for operations
- **Alerting**: Configurable alerts for errors and performance