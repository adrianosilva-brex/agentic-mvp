# Trip Examples

This directory contains sample JSON trip data that demonstrates the simplified DynamoDB schema for the Trip Management System.

## Example Files

### `basic_trip.json`
- **Purpose**: Demonstrates a typical trip with flight and hotel bookings
- **Features**: 
  - Explicit trip (user-created)
  - Air travel (Southwest flight)
  - Lodging (Marriott hotel)
  - Source document tracking

### `auto_generated_trip.json`
- **Purpose**: Shows an auto-generated trip from a standalone booking
- **Features**:
  - Derived trip (auto-generated from booking)
  - Lower confidence score (0.75)
  - Merge candidates for potential trip consolidation
  - Single air booking (Delta flight)

### `complex_trip.json`
- **Purpose**: Multi-city business trip with various bookings
- **Features**:
  - Multi-segment air travel (United flights)
  - Ground transportation (Avis rental)
  - Complex itinerary spanning multiple cities

### `tmc_integration_trip.json`
- **Purpose**: Demonstrates TMC (Travel Management Company) integration
- **Features**:
  - TMC integration (Concur data)
  - Air travel (American Airlines)
  - Lodging with loyalty program (Hilton)

### `versioned_trip.json`
- **Purpose**: Shows version management and change tracking
- **Features**:
  - Multiple versions (v1 → v3)
  - Detailed version history
  - Change tracking with before/after values
  - Multiple source documents

### `multi_modal_trip.json`
- **Purpose**: Demonstrates a complex trip using multiple transportation types
- **Features**:
  - Air travel (Alaska Airlines)
  - Rail travel (Amtrak Coast Starlight)
  - Ground transportation (Hertz rental + Uber ride)
  - Multiple lodging options (Airbnb + Marriott)

## Schema Features Demonstrated

### Core Trip Fields
- `trip_id`: Unique identifier
- `traveler_id`: User association
- `start_date`/`end_date`: Trip duration
- `status`: Trip status (confirmed, tentative, cancelled)
- `origin_type`: "explicit" (user-created) vs "derived" (auto-generated)
- `trip_confidence`: Confidence score (0.0-1.0)

### Flexible Extensions (Organized by Type)
- **Air travel**: `air.southwest`, `air.delta`, `air.united`, `air.american`
- **Lodging**: `lodging.marriott`, `lodging.hilton`, `lodging.airbnb`
- **Ground transport**: `ground.avis`, `ground.hertz`, `ground.uber`, `ground.lyft`
- **Rail travel**: `rail.amtrak`, `rail.via_rail`

### Version Management
- `version`: Current version number
- `version_history`: Array of version entries with changes
- `updated_at`: Last modification timestamp

### Source Tracking
- `source_documents`: Array of contributing documents
- Document confidence scores
- Field attribution tracking

## Usage

Load these examples into your DynamoDB table using:

```bash
# Load all examples
python setup.py load-examples

# Or load individual files
python -c "
from trips import TripsManager
import json

trips_manager = TripsManager()
with open('examples/basic_trip.json') as f:
    trip_data = json.load(f)
    trips_manager.create_trip(trip_data)
"
```

## Testing Queries

After loading the examples, you can test various query patterns:

```python
from trips import TripsManager

trips_manager = TripsManager()

# Get all trips for a user
user_trips = trips_manager.get_user_trips("user-789")

# Get upcoming trips
upcoming = trips_manager.get_user_trips("user-789", "2025-09-01")

# Get trips by status
confirmed_trips = trips_manager.get_trips_by_status("confirmed")

# Find auto-generated trips for merging
merge_candidates = trips_manager.find_merge_candidates("user-789")

# Get specific trip
trip = trips_manager.get_trip("trip-12345")
```

These examples showcase the flexibility of the namespaced schema and demonstrate how different data sources can be integrated without schema changes.