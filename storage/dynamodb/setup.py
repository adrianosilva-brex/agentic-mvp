#!/usr/bin/env python3
"""
DynamoDB Setup Script for Trip Management System

This script handles:
- Creating the trips table with GSIs
- Loading sample data
- Providing verification commands
- Table cleanup for testing

Usage:
    python setup.py create          # Create tables
    python setup.py load-examples   # Load sample data
    python setup.py verify          # Verify table setup
    python setup.py cleanup         # Delete tables (be careful!)
    python setup.py reset           # Cleanup and recreate
"""

import sys
import json
import os
from pathlib import Path
from db_config import DynamoDBConfig
from trips import TripsManager

def create_tables():
    """Create the trips table and GSIs."""
    print("🚀 Creating DynamoDB tables...")
    
    config = DynamoDBConfig()
    success = config.create_trips_table()
    
    if success:
        print("✅ Tables created successfully!")
        
        # Show table info
        table_info = config.get_table_info()
        if table_info:
            print(f"📊 Table Status: {table_info['TableStatus']}")
            print(f"📊 Item Count: {table_info['ItemCount']}")
            print(f"📊 GSIs: {len(table_info.get('GlobalSecondaryIndexes', []))}")
        return True
    else:
        print("❌ Failed to create tables")
        return False

def load_sample_data():
    """Load sample trip data from examples folder."""
    print("📝 Loading sample data...")
    
    # Get the examples directory
    examples_dir = Path(__file__).parent / "examples"
    
    if not examples_dir.exists():
        print("❌ Examples directory not found. Run with 'create-examples' first.")
        return False
    
    trips_manager = TripsManager()
    loaded_count = 0
    
    # Load all JSON files from examples directory
    for json_file in examples_dir.glob("*.json"):
        try:
            print(f"📄 Loading {json_file.name}...")
            
            with open(json_file, 'r') as f:
                trip_data = json.load(f)
            
            # Handle both single trip and array of trips
            if isinstance(trip_data, list):
                for trip in trip_data:
                    if trips_manager.create_trip(trip):
                        loaded_count += 1
            else:
                if trips_manager.create_trip(trip_data):
                    loaded_count += 1
                    
        except Exception as e:
            print(f"❌ Error loading {json_file.name}: {e}")
    
    print(f"✅ Loaded {loaded_count} sample trips")
    return loaded_count > 0

def verify_setup():
    """Verify that tables are set up correctly."""
    print("🔍 Verifying table setup...")
    
    config = DynamoDBConfig()
    trips_manager = TripsManager()
    
    # Check if table exists
    tables = config.list_tables()
    if 'trips' not in tables:
        print("❌ Trips table not found")
        return False
    
    print("✅ Trips table exists")
    
    # Get table info
    table_info = config.get_table_info()
    if table_info:
        print(f"📊 Table Status: {table_info['TableStatus']}")
        print(f"📊 Item Count: {table_info['ItemCount']}")
        
        # Check GSIs
        gsis = table_info.get('GlobalSecondaryIndexes', [])
        print(f"📊 Global Secondary Indexes: {len(gsis)}")
        for gsi in gsis:
            print(f"   - {gsi['IndexName']}: {gsi['IndexStatus']}")
    
    # Test basic operations
    print("\n🧪 Testing basic operations...")
    
    # List trips
    all_trips = trips_manager.list_all_trips()
    print(f"✅ Found {len(all_trips)} trips")
    
    if all_trips:
        # Test getting a specific trip
        sample_trip = all_trips[0]
        trip_id = sample_trip['trip_id']
        retrieved_trip = trips_manager.get_trip(trip_id)
        
        if retrieved_trip:
            print(f"✅ Successfully retrieved trip: {trip_id}")
        else:
            print(f"❌ Failed to retrieve trip: {trip_id}")
            return False
    
    print("✅ Basic operations working correctly")
    return True

def cleanup_tables():
    """Delete all tables (use with caution!)."""
    print("⚠️  CLEANUP: This will delete all trip data!")
    
    confirm = input("Are you sure? Type 'DELETE' to confirm: ")
    if confirm != 'DELETE':
        print("Cleanup cancelled")
        return False
    
    config = DynamoDBConfig()
    success = config.delete_table('trips')
    
    if success:
        print("🗑️  Tables deleted successfully")
        return True
    else:
        print("❌ Failed to delete tables")
        return False

def create_sample_examples():
    """Create the examples directory with sample JSON files."""
    print("📁 Creating examples directory with sample data...")
    
    examples_dir = Path(__file__).parent / "examples"
    examples_dir.mkdir(exist_ok=True)
    
    # Sample trip data based on SIMPLIFIED_DYNAMODB.md
    samples = {
        "basic_trip.json": {
            "trip_id": "trip-12345",
            "traveler_id": "user-789",
            "start_date": "2025-09-15",
            "end_date": "2025-09-18",
            "status": "confirmed",
            "origin_type": "explicit",
            "trip_confidence": 1.0,
            "purpose": "Client meeting in NYC",
            "destination": "New York, NY",
            "air": {
                "southwest": {
                    "confirmation_code": "ABC123",
                    "flight_number": "SW1234",
                    "departure": {
                        "airport": "SFO",
                        "time": "2025-09-15T09:30:00Z"
                    },
                    "arrival": {
                        "airport": "JFK",
                        "time": "2025-09-15T18:00:00Z"
                    },
                    "total_cost": 450.75
                }
            },
            "lodging": {
                "marriott": {
                    "confirmation_number": "H789012",
                    "hotel_name": "Marriott Times Square",
                    "check_in": "2025-09-15",
                    "check_out": "2025-09-18",
                    "nightly_rate": 199.00
                }
            },
            "source_documents": [
                {
                    "document_id": "doc-456",
                    "type": "email_itinerary",
                    "confidence": 0.95,
                    "contributed_fields": ["air.southwest"]
                }
            ]
        },
        
        "auto_generated_trip.json": {
            "trip_id": "trip-auto-67890",
            "traveler_id": "user-789",
            "start_date": "2025-10-05",
            "end_date": "2025-10-05",
            "status": "confirmed",
            "origin_type": "derived",
            "trip_confidence": 0.75,
            "purpose": "Auto-generated from booking",
            "destination": "Los Angeles, CA",
            "air": {
                "delta": {
                    "confirmation_code": "DEF456",
                    "flight_number": "DL2567",
                    "departure": {
                        "airport": "SFO",
                        "time": "2025-10-05T14:30:00Z"
                    },
                    "arrival": {
                        "airport": "LAX",
                        "time": "2025-10-05T16:45:00Z"
                    },
                    "total_cost": 285.50
                }
            },
            "merge_candidates": [
                {
                    "trip_id": "trip-12345",
                    "similarity_score": 0.85,
                    "reasons": ["same_traveler", "date_proximity", "similar_destination"]
                }
            ]
        },
        
        "complex_trip.json": {
            "trip_id": "trip-complex-001",
            "traveler_id": "user-456",
            "start_date": "2025-11-10",
            "end_date": "2025-11-15",
            "status": "confirmed",
            "origin_type": "explicit",
            "trip_confidence": 1.0,
            "purpose": "Multi-city business trip",
            "destination": "Multiple cities",
            "air": {
                "united": {
                    "confirmation_code": "UN789456",
                    "total_cost": 890.25,
                    "segments": [
                        {
                            "segment_id": 1,
                            "flight_number": "UA1234",
                            "departure": {"airport": "SFO", "time": "2025-11-10T08:00:00Z"},
                            "arrival": {"airport": "ORD", "time": "2025-11-10T14:30:00Z"}
                        },
                        {
                            "segment_id": 2,
                            "flight_number": "UA5678",
                            "departure": {"airport": "ORD", "time": "2025-11-12T16:15:00Z"},
                            "arrival": {"airport": "JFK", "time": "2025-11-12T19:45:00Z"}
                        }
                    ]
                }
            },
            "ground": {
                "avis": {
                    "confirmation_number": "R123456789",
                    "pickup_location": "ORD Airport",
                    "pickup_date": "2025-11-10T15:00:00Z",
                    "dropoff_location": "ORD Airport",
                    "dropoff_date": "2025-11-12T15:00:00Z",
                    "vehicle_class": "Economy",
                    "daily_rate": 45.99,
                    "total_cost": 91.98
                }
            }
        }
    }
    
    created_count = 0
    for filename, data in samples.items():
        file_path = examples_dir / filename
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Created {filename}")
        created_count += 1
    
    print(f"📁 Created {created_count} example files in {examples_dir}")
    return True

def main():
    """Main setup script entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "create":
        create_tables()
        
    elif command == "load-examples":
        load_sample_data()
        
    elif command == "verify":
        verify_setup()
        
    elif command == "cleanup":
        cleanup_tables()
        
    elif command == "reset":
        cleanup_tables()
        create_tables()
        
    elif command == "create-examples":
        create_sample_examples()
        
    elif command == "full-setup":
        print("🚀 Running full setup...")
        create_sample_examples()
        create_tables()
        load_sample_data()
        verify_setup()
        print("🎉 Full setup complete!")
        
    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()