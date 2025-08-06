# Ground Booking Schema

## Definition
A ground transportation reservation (car rental, train, etc.) that forms part of a [Trip](./trip.md).

## Core Fields
- `booking_id`: string (required) - Unique identifier for the booking
- `version`: number (required) - Current version of the booking
- `status`: string (required) - Booking status (confirmed, tentative, cancelled)
- `type`: string (required) - Type of ground transport (car_rental, train, bus, etc.)
- `confirmation_number`: string (required) - Booking confirmation number
- `provider`: string (required) - Service provider name

## Rental Car Specific
- `vehicle`: object (optional)
  - `class`: string - Vehicle class (economy, compact, etc.)
  - `make`: string - Vehicle make
  - `model`: string - Vehicle model
  - `transmission`: string - Automatic/Manual
  - `features`: Array<string> - Special features/requirements

## Train/Bus Specific
- `route`: object (optional)
  - `train_number`: string - Train/bus number
  - `class`: string - Travel class
  - `seat_assignment`: string - Assigned seat
  - `carriage`: string - Train car/bus number

## Service Period
- `pickup`: object (required)
  - `location`: string (required) - Pickup location
  - `date`: date (required) - Pickup date
  - `time`: time (required) - Pickup time
  - `instructions`: string (optional) - Special instructions
- `dropoff`: object (required)
  - `location`: string (required) - Drop-off location
  - `date`: date (required) - Drop-off date
  - `time`: time (required) - Drop-off time
  - `instructions`: string (optional) - Special instructions

## Cost Information
- `rate`: object (required)
  - `amount`: number (required) - Base rate
  - `currency`: string (required) - Currency code
  - `rate_code`: string (optional) - Rate plan code
  - `period`: string (optional) - Rate period (daily, hourly)
- `estimated_total`: object (optional)
  - `amount`: number (required)
  - `currency`: string (required)

## Traveler Details
- `primary_driver`: object (required)
  - `driver_id`: string (required) - Reference to traveler
  - `loyalty_program`: object (optional)
    - `program_name`: string
    - `member_number`: string
    - `status_level`: string

## Insurance and Protection
- `insurance`: object (optional)
  - `coverage_type`: string
  - `policy_number`: string
  - `cost`: object
    - `amount`: number
    - `currency`: string

## Change History
- `change_history`: Array<object> (required)
  - `change_type`: string (required)
  - `changed_at`: datetime (required)
  - `source_document_id`: string (required)
  - `previous_values`: object (required)
  - `change_reason`: string (optional)

## Relationships
- Must be associated with a [Trip](./trip.md)
- Service period must fall within trip dates
- Primary driver must match trip traveler