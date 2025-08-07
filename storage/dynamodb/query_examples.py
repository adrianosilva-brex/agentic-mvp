#!/usr/bin/env python3
"""
Interactive query examples for the trips table.

This script demonstrates various query patterns and data operations.

Usage:
    python query_examples.py
"""

from trips import TripsService
from db_config import DynamoDBConfig
import json
from datetime import datetime, timezone

def main():
    print("🔍 Trip Management System - Query Examples")
    print("=" * 50)
    
    # Initialize
    config = DynamoDBConfig()
    trips_service = TripsService()
    
    # Check if table exists
    tables = config.list_tables()
    if 'trips' not in tables:
        print("❌ Trips table not found. Run 'python setup.py create' first.")
        return
    
    print("✅ Connected to trips table")
    
    # Example 1: List all trips
    print("\n📋 Example 1: List all trips")
    all_trips = trips_service.list_all_trips()
    print(f"Total trips in database: {len(all_trips)}")
    
    if not all_trips:
        print("No trips found. Run 'python setup.py load-examples' to load sample data.")
        return
    
    for trip in all_trips[:3]:  # Show first 3
        print(f"  • {trip['trip_id']}: {trip.get('purpose', 'No purpose')} ({trip['start_date']})")
    
    if len(all_trips) > 3:
        print(f"  ... and {len(all_trips) - 3} more")
    
    # Example 2: Query by user
    print("\n👤 Example 2: Get trips for specific user")
    user_id = "user-789"
    user_trips = trips_service.get_user_trips(user_id)
    print(f"Trips for {user_id}: {len(user_trips)}")
    
    for trip in user_trips:
        print(f"  • {trip['trip_id']}: {trip['destination']} ({trip['start_date']} to {trip['end_date']})")
    
    # Example 3: Query upcoming trips
    print("\n🔮 Example 3: Get upcoming trips")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    upcoming_trips = trips_service.get_user_trips(user_id, today)
    print(f"Upcoming trips for {user_id}: {len(upcoming_trips)}")
    
    for trip in upcoming_trips:
        print(f"  • {trip['trip_id']}: {trip['destination']} (starts {trip['start_date']})")
    
    # Example 4: Query by status
    print("\n✅ Example 4: Get trips by status")
    confirmed_trips = trips_service.get_trips_by_status("confirmed")
    print(f"Confirmed trips: {len(confirmed_trips)}")
    
    # Example 5: Find merge candidates
    print("\n🔄 Example 5: Find auto-generated trips (merge candidates)")
    merge_candidates = trips_service.find_merge_candidates(user_id)
    print(f"Auto-generated trips for {user_id}: {len(merge_candidates)}")
    
    for trip in merge_candidates:
        print(f"  • {trip['trip_id']}: confidence={trip['trip_confidence']}, origin={trip['origin_type']}")
    
    # Example 6: Detailed trip view
    if all_trips:
        print("\n🔍 Example 6: Detailed trip view")
        sample_trip = all_trips[0]
        trip_id = sample_trip['trip_id']
        detailed_trip = trips_service.get_trip(trip_id)
        
        print(f"Trip ID: {trip_id}")
        print(f"Traveler: {detailed_trip['traveler_id']}")
        print(f"Dates: {detailed_trip['start_date']} to {detailed_trip['end_date']}")
        print(f"Status: {detailed_trip['status']}")
        print(f"Version: {detailed_trip.get('version', 1)}")
        
        # Show bookings
        print("Bookings:")
        for key, value in detailed_trip.items():
            if key.endswith('_booking') or key.endswith('_rental') or key.endswith('_data'):
                print(f"  • {key}: {type(value).__name__}")
                if isinstance(value, dict) and 'confirmation_code' in value:
                    print(f"    Confirmation: {value['confirmation_code']}")
                elif isinstance(value, dict) and 'confirmation_number' in value:
                    print(f"    Confirmation: {value['confirmation_number']}")
    
    # Example 7: Version history
    print("\n📚 Example 7: Check version history")
    versioned_trips = [trip for trip in all_trips if trip.get('version', 1) > 1]
    
    if versioned_trips:
        trip = versioned_trips[0]
        print(f"Trip {trip['trip_id']} has {len(trip.get('version_history', []))} versions:")
        
        for version_entry in trip.get('version_history', []):
            print(f"  • v{version_entry['version']}: {', '.join(version_entry['changes'])} ({version_entry['timestamp']})")
    else:
        print("No trips with version history found.")
    
    print("\n🎉 Query examples complete!")
    print("\nNext steps:")
    print("- Try updating a trip: trips_manager.update_trip(trip_id, {'status': 'cancelled'})")
    print("- Create a new trip: trips_manager.create_trip(your_trip_data)")
    print("- Explore the source code in trips.py for more operations")

if __name__ == "__main__":
    main()