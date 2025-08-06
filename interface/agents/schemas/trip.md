# Trip Schema

## Definition
A collection of related travel activities, typically involving transportation, accommodations, and business activities, that forms a coherent journey.

## Core Fields
- `trip_id`: string (required) - Unique identifier for the trip
- `version`: number (required) - Current version of the trip data
- `status`: string (required) - Overall trip status (confirmed, tentative, cancelled)
- `purpose`: string (optional) - Business purpose of the trip
- `start_date`: date (required) - Trip start date
- `end_date`: date (required) - Trip end date

## Traveler Information
- `traveler`: object (required)
  - `id`: string (required) - Unique identifier for the traveler
  - `name`: string (required) - Full name of the traveler
  - `email`: string (required) - Email address of the traveler

## Related Components
- `air_bookings`: Array<[AirBooking](./air_booking.md)> (optional)
- `lodging_bookings`: Array<[LodgingBooking](./lodging_booking.md)> (optional)
- `ground_bookings`: Array<[GroundBooking](./ground_booking.md)> (optional)
- `activities`: Array<[Activity](./activity.md)> (optional)

## Metadata
- `created_at`: datetime (required) - When the trip was first created
- `updated_at`: datetime (required) - When the trip was last modified
- `source_documents`: Array<object> (required) - List of documents that contributed to this trip
  - `document_id`: string (required)
  - `type`: string (required)
  - `confidence_score`: number (required)
  - `extracted_at`: datetime (required)
  - `contributed_fields`: Array<string> (required)

## Version Control
- `version_history`: Array<object> (required) - History of changes to the trip
  - `version`: number (required)
  - `timestamp`: datetime (required)
  - `document_id`: string (required)
  - `change_type`: string (required)
  - `changed_fields`: Array<string> (required)

## Relationships
- Each trip can have multiple bookings of each type
- All bookings must fall within trip start_date and end_date
- At least one booking component must exist for a valid trip