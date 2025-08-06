#!/usr/bin/env python3
"""
Example usage of the Trip MVP storage data models.

This script demonstrates how to:
1. Set up DynamoDB tables (LocalStack or AWS)
2. Create trip data with flexible extensions
3. Track document metadata and processing
4. Build a field registry from extracted data
5. Query and analyze the data

Usage:
    python example_usage.py --localstack  # Use LocalStack
    python example_usage.py --aws         # Use AWS DynamoDB
"""

import json
import argparse
from datetime import datetime, timedelta
from decimal import Decimal

# Import our data models
try:
    # Try relative import first (when imported as module)
    from . import (
        DynamoDBConfig, Trip, TripBuilder, DocumentMetadata, 
        DocumentBuilder, FieldRegistry, Traveler, TripStatus,
        DocumentSourceType, DocumentType, FieldDataType
    )
except ImportError:
    # Fall back to direct imports (when run as script)
    from db_config import DynamoDBConfig
    from trip_model import Trip, TripBuilder, Traveler, TripStatus
    from document_model import DocumentMetadata, DocumentBuilder, DocumentSourceType, DocumentType
    from field_registry_model import FieldRegistry, FieldDataType

def setup_database(use_localstack: bool = True):
    """Set up DynamoDB tables."""
    print("🔧 Setting up DynamoDB tables...")
    
    if use_localstack:
        config = DynamoDBConfig(
            region_name='us-east-1',
            endpoint_url='http://localhost:4566'
        )
        print("   Using LocalStack endpoint")
    else:
        config = DynamoDBConfig(region_name='us-east-1')
        print("   Using AWS DynamoDB")
    
    # Create all tables
    success = config.setup_all_tables()
    if success:
        print("✅ All tables created successfully")
    else:
        print("❌ Some tables failed to create")
        return None
    
    return config

def create_sample_trip():
    """Create a sample trip with various extensions."""
    print("\n📝 Creating sample trip...")
    
    # Use the builder pattern for clean trip creation
    trip = (TripBuilder()
           .with_traveler("user-12345", "Jane Smith", "jane.smith@company.com", "+1-555-0123")
           .with_dates("2025-09-15", "2025-09-18")
           .with_purpose("Client meeting in New York")
           .with_status(TripStatus.CONFIRMED)
           .build())
    
    # Add Southwest Airlines flight extension
    southwest_data = {
        "confirmation_code": "ABC123",
        "reservation_date": "2025-07-30",
        "total_cost": 450.75,
        "segments": [
            {
                "segment_id": "seg-12345",
                "version": 1,
                "status": "confirmed", 
                "flight_number": "SW1234",
                "departure": {
                    "airport": "SFO",
                    "time": "2025-09-15T09:30:00Z",
                    "terminal": "1"
                },
                "arrival": {
                    "airport": "JFK",
                    "time": "2025-09-15T18:00:00Z",
                    "terminal": "4"
                },
                "change_history": []
            }
        ]
    }
    trip.add_extension("southwest_itinerary", southwest_data)
    
    # Add hotel booking extension
    hotel_data = {
        "provider": "Marriott",
        "confirmation_number": "H789012",
        "check_in": "2025-09-15",
        "check_out": "2025-09-18", 
        "nightly_rate": 199.00,
        "address": "123 Broadway, New York, NY 10001",
        "room_type": "King Executive Room"
    }
    trip.add_extension("hotel_booking", hotel_data)
    
    # Add source document references
    trip.add_source_document({
        "document_id": "doc-123456",
        "type": "itinerary",
        "confidence_score": 0.92,
        "extracted_at": "2025-08-02T15:35:00Z",
        "contributed_fields": ["southwest_itinerary.confirmation_code", "traveler"]
    })
    
    # Add version history
    trip.add_version_entry(
        document_id="doc-123456",
        change_type="creation", 
        changed_fields=["traveler", "southwest_itinerary", "hotel_booking"]
    )
    
    print(f"✅ Created trip: {trip.trip_id}")
    print(f"   Traveler: {trip.traveler.name}")
    print(f"   Dates: {trip.start_date} to {trip.end_date}")
    print(f"   Extensions: {list(trip.extensions.keys())}")
    
    return trip

def create_sample_documents():
    """Create sample document metadata entries."""
    print("\n📄 Creating sample documents...")
    
    documents = []
    
    # Southwest itinerary PDF
    doc1 = (DocumentBuilder("southwest-itinerary.pdf")
           .with_content(b"Mock PDF content for Southwest itinerary...")
           .with_source(DocumentSourceType.EMAIL_ATTACHMENT, {
               "email_sender": "confirmations@southwest.com",
               "email_subject": "Flight Confirmation - ABC123"
           })
           .with_s3_location("trip-documents", "2025/08/02/southwest-itinerary.pdf")
           .with_document_type(DocumentType.ITINERARY, 0.95)
           .with_extracted_text("Southwest Airlines Flight Confirmation\nConfirmation Code: ABC123\nFlight: SW1234\nSFO to JFK...")
           .with_tags(["flight", "southwest", "itinerary"])
           .build())
    
    # Mark as successfully processed
    doc1.update_processing_status("completed")
    doc1.associate_with_trip("trip-789012")
    
    # Add extraction result
    doc1.add_extraction_result({
        "extracted_at": "2025-08-02T15:35:00Z",
        "confidence_score": 0.92,
        "extracted_data": {
            "airline": "Southwest",
            "confirmation_code": "ABC123",
            "flight_number": "SW1234",
            "departure": {"airport": "SFO", "time": "2025-09-15T09:30:00Z"},
            "arrival": {"airport": "JFK", "time": "2025-09-15T18:00:00Z"}
        },
        "processing_time_ms": 1250
    })
    
    documents.append(doc1)
    
    # Hotel confirmation email
    doc2 = (DocumentBuilder("marriott-confirmation.html")
           .with_content(b"Mock HTML email content for Marriott booking...")
           .with_source(DocumentSourceType.EMAIL_BODY, {
               "email_sender": "reservations@marriott.com",
               "email_subject": "Your Reservation Confirmation"
           })
           .with_s3_location("trip-documents", "2025/08/02/marriott-confirmation.html") 
           .with_document_type(DocumentType.HOTEL_CONFIRMATION, 0.88)
           .with_extracted_text("Dear Jane Smith, Your reservation is confirmed. Confirmation: H789012...")
           .with_tags(["hotel", "marriott", "confirmation"])
           .build())
    
    doc2.update_processing_status("completed")
    doc2.associate_with_trip("trip-789012")
    
    documents.append(doc2)
    
    # Flight change notification
    doc3 = (DocumentBuilder("sw-flight-change.txt")
           .with_content(b"Flight time change notification...")
           .with_source(DocumentSourceType.EMAIL_BODY, {
               "email_sender": "alerts@southwest.com", 
               "email_subject": "Flight Schedule Change - ABC123"
           })
           .with_s3_location("trip-documents", "2025/08/05/sw-flight-change.txt")
           .with_document_type(DocumentType.FLIGHT_UPDATE, 0.91)
           .with_extracted_text("Your flight SW1234 has been rescheduled. New departure: 09:30...")
           .with_tags(["flight", "southwest", "change", "schedule"])
           .build())
    
    doc3.update_processing_status("completed")
    doc3.associate_with_trip("trip-789012")
    
    documents.append(doc3)
    
    print(f"✅ Created {len(documents)} sample documents")
    for doc in documents:
        print(f"   {doc.filename} ({doc.document_type})")
    
    return documents

def build_field_registry(trip, documents):
    """Build a field registry from trip and document data."""
    print("\n🏗️  Building field registry...")
    
    registry = FieldRegistry()
    
    # Register fields from trip data
    trip_data = trip.to_dict()
    registry.register_document_fields(trip_data, f"trip-{trip.trip_id}")
    
    # Register fields from document extraction results
    for doc in documents:
        for result in doc.extraction_results:
            registry.register_document_fields(result.extracted_data, doc.document_id)
    
    print(f"✅ Field registry built:")
    print(f"   Total fields: {len(registry.fields)}")
    print(f"   Namespaces: {list(registry.namespaces)}")
    
    # Show some example fields
    print("\n   Example fields discovered:")
    for field_path, field in list(registry.fields.items())[:5]:
        print(f"   - {field_path} ({field.data_type}) - {field.occurrence_count} occurrences")
    
    return registry

def analyze_data(registry):
    """Analyze the field registry and provide insights."""
    print("\n🔍 Analyzing field registry...")
    
    # Get schema summary
    summary = registry.get_schema_summary()
    
    print(f"   📊 Schema Analysis:")
    print(f"      Total fields: {summary['total_fields']}")
    print(f"      Documents processed: {summary['total_documents_processed']}")
    print(f"      Namespaces: {len(summary['namespaces'])}")
    
    print(f"\n   🎯 Fields by stability:")
    for stability, count in summary['fields_by_stability'].items():
        print(f"      {stability.capitalize()}: {count}")
    
    print(f"\n   📝 Fields by type:")
    for data_type, count in summary['fields_by_type'].items():
        if count > 0:
            print(f"      {data_type}: {count}")
    
    # Show stable fields
    stable_fields = registry.get_stable_fields()
    if stable_fields:
        print(f"\n   🏆 Stable fields (appear in >80% of documents):")
        for field in stable_fields[:5]:
            print(f"      {field.path} ({field.occurrence_percentage:.1f}%)")
    
    # Show suggested indexes
    suggestions = summary['suggested_indexes']
    if suggestions:
        print(f"\n   💡 Suggested indexes:")
        for suggestion in suggestions[:5]:
            print(f"      {suggestion}")
    
    return summary

def demonstrate_queries(trip, registry):
    """Demonstrate various query patterns."""
    print("\n🔍 Demonstrating query patterns...")
    
    # Query trip by traveler
    print(f"\n   Trip for traveler {trip.traveler.id}:")
    print(f"      {trip.trip_id}: {trip.start_date} to {trip.end_date}")
    
    # Get flight information
    flight_segments = trip.get_flight_segments()
    if flight_segments:
        print(f"\n   Flight segments:")
        for segment in flight_segments:
            print(f"      {segment.flight_number}: {segment.departure['airport']} → {segment.arrival['airport']}")
    
    # Get hotel bookings
    hotel_bookings = trip.get_hotel_bookings()
    if hotel_bookings:
        print(f"\n   Hotel bookings:")
        for booking in hotel_bookings:
            print(f"      {booking.get('provider', 'Unknown')}: {booking.get('check_in')} - {booking.get('check_out')}")
    
    # Query fields by type
    email_fields = registry.get_fields_by_type(FieldDataType.EMAIL)
    if email_fields:
        print(f"\n   Email fields found:")
        for field in email_fields:
            print(f"      {field.path} (confidence: {field.type_confidence:.2f})")
    
    # Get airport codes
    airport_fields = registry.get_fields_by_type(FieldDataType.AIRPORT_CODE)
    if airport_fields:
        print(f"\n   Airport code fields:")
        for field in airport_fields:
            print(f"      {field.path}")

def save_sample_data(trip, documents, registry):
    """Save sample data to JSON files for inspection."""
    print("\n💾 Saving sample data...")
    
    # Save trip data
    trip_data = trip.to_dict()
    with open('/tmp/sample_trip.json', 'w') as f:
        json.dumps(trip_data, f, indent=2, default=str)
    
    # Save documents data
    docs_data = [doc.to_dict() for doc in documents]
    with open('/tmp/sample_documents.json', 'w') as f:
        json.dumps(docs_data, f, indent=2, default=str)
    
    # Save field registry
    registry_data = registry.export_schema()
    with open('/tmp/field_registry.json', 'w') as f:
        json.dumps(registry_data, f, indent=2, default=str)
    
    print("   ✅ Sample data saved to /tmp/")
    print("      - sample_trip.json")
    print("      - sample_documents.json") 
    print("      - field_registry.json")

def main():
    """Main example execution."""
    parser = argparse.ArgumentParser(description="Trip MVP Storage Example")
    parser.add_argument("--localstack", action="store_true", 
                       help="Use LocalStack instead of AWS")
    parser.add_argument("--aws", action="store_true",
                       help="Use AWS DynamoDB")
    parser.add_argument("--skip-db", action="store_true",
                       help="Skip database setup (data models only)")
    
    args = parser.parse_args()
    
    print("🚀 Trip MVP Storage Data Models Example")
    print("=" * 50)
    
    # Setup database if requested
    if not args.skip_db:
        config = setup_database(use_localstack=args.localstack or not args.aws)
        if not config:
            return
    
    # Create sample data
    trip = create_sample_trip()
    documents = create_sample_documents()
    registry = build_field_registry(trip, documents)
    
    # Analyze data
    summary = analyze_data(registry)
    
    # Demonstrate queries
    demonstrate_queries(trip, registry)
    
    # Save sample data
    save_sample_data(trip, documents, registry)
    
    print("\n🎉 Example completed successfully!")
    print("\nNext steps:")
    print("- Examine the saved JSON files to understand the data structure")
    print("- Try modifying the trip data and see how the field registry adapts")
    print("- Implement actual DynamoDB storage operations using the models")

if __name__ == "__main__":
    main()