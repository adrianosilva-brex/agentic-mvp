# Air Booking Schema

## Definition
An air travel reservation consisting of one or more flight segments that form part of a [Trip](./trip.md).

## Core Fields
- `booking_id`: string (required) - Unique identifier for the booking
- `version`: number (required) - Current version of the booking
- `status`: string (required) - Booking status (confirmed, tentative, cancelled)
- `booking_reference`: string (required) - Airline confirmation/PNR
- `provider`: string (required) - Airline name
- `cabin_class`: string (optional) - Economy, Business, First, etc.
- `cost`: object (optional)
  - `amount`: number (required)
  - `currency`: string (required)

## Flight Segments
- `segments`: Array<object> (required) - Individual flight segments
  - `segment_id`: string (required) - Unique identifier for the segment
  - `flight_number`: string (required) - Airline flight number
  - `departure`: object (required)
    - `airport`: string (required) - IATA airport code
    - `terminal`: string (optional) - Terminal number/letter
    - `date`: date (required) - Departure date
    - `time`: time (required) - Departure time with timezone
  - `arrival`: object (required)
    - `airport`: string (required) - IATA airport code
    - `terminal`: string (optional) - Terminal number/letter
    - `date`: date (required) - Arrival date
    - `time`: time (required) - Arrival time with timezone
  - `duration`: number (optional) - Flight duration in minutes
  - `aircraft_type`: string (optional) - Type of aircraft
  - `meal_service`: string (optional) - Type of meal service
  - `status`: string (required) - Segment status

## Passenger Details
- `passengers`: Array<object> (required)
  - `passenger_id`: string (required) - Reference to traveler
  - `seat_assignments`: Array<object> (optional)
    - `segment_id`: string (required)
    - `seat_number`: string (optional)
  - `frequent_flyer`: object (optional)
    - `program`: string
    - `number`: string
    - `status_level`: string

## Change History
- `change_history`: Array<object> (required)
  - `change_type`: string (required)
  - `changed_at`: datetime (required)
  - `source_document_id`: string (required)
  - `previous_values`: object (required)
  - `change_reason`: string (optional)

## Relationships
- Must be associated with a [Trip](./trip.md)
- Each segment must have valid airport codes
- Segments must be chronologically ordered
- Passenger must match trip traveler