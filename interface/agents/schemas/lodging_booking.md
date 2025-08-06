# Lodging Booking Schema

## Definition
A hotel or other accommodation reservation that forms part of a [Trip](./trip.md).

## Core Fields
- `booking_id`: string (required) - Unique identifier for the booking
- `version`: number (required) - Current version of the booking
- `status`: string (required) - Booking status (confirmed, tentative, cancelled)
- `confirmation_number`: string (required) - Hotel confirmation number
- `provider`: string (required) - Hotel/lodging provider name
- `chain_code`: string (optional) - Hotel chain code (e.g., MAR for Marriott)

## Stay Details
- `check_in`: date (required) - Check-in date
- `check_out`: date (required) - Check-out date
- `room_type`: string (optional) - Type of room booked
- `number_of_rooms`: number (required) - Number of rooms booked
- `number_of_guests`: number (required) - Number of guests
- `rate`: object (required)
  - `amount`: number (required) - Rate per night
  - `currency`: string (required) - Currency code
  - `rate_code`: string (optional) - Rate plan code
- `total_cost`: object (optional)
  - `amount`: number (required)
  - `currency`: string (required)

## Property Information
- `property`: object (required)
  - `name`: string (required) - Property name
  - `address`: object (required)
    - `street`: string (required)
    - `city`: string (required)
    - `state`: string (optional)
    - `postal_code`: string (required)
    - `country`: string (required)
  - `phone`: string (optional)
  - `email`: string (optional)
  - `amenities`: Array<string> (optional)

## Guest Information
- `guest`: object (required)
  - `guest_id`: string (required) - Reference to traveler
  - `loyalty_program`: object (optional)
    - `program_name`: string
    - `member_number`: string
    - `status_level`: string

## Cancellation Policy
- `cancellation_policy`: object (optional)
  - `deadline`: datetime (optional)
  - `penalty`: object (optional)
    - `amount`: number
    - `currency`: string
  - `description`: string (optional)

## Change History
- `change_history`: Array<object> (required)
  - `change_type`: string (required)
  - `changed_at`: datetime (required)
  - `source_document_id`: string (required)
  - `previous_values`: object (required)
  - `change_reason`: string (optional)

## Relationships
- Must be associated with a [Trip](./trip.md)
- Stay dates must fall within trip dates
- Guest must match trip traveler