# Activity Schema

## Definition
A business activity or event that is part of a [Trip](./trip.md), such as meetings, conferences, or other scheduled events.

## Core Fields
- `activity_id`: string (required) - Unique identifier for the activity
- `version`: number (required) - Current version of the activity
- `status`: string (required) - Activity status (confirmed, tentative, cancelled)
- `type`: string (required) - Type of activity (meeting, conference, dinner, etc.)
- `title`: string (required) - Activity title/name

## Timing
- `start`: object (required)
  - `date`: date (required) - Start date
  - `time`: time (required) - Start time
  - `timezone`: string (required) - Timezone identifier
- `end`: object (required)
  - `date`: date (required) - End date
  - `time`: time (required) - End time
  - `timezone`: string (required) - Timezone identifier
- `duration`: number (optional) - Duration in minutes

## Location
- `location`: object (required)
  - `name`: string (optional) - Venue/location name
  - `address`: object (required)
    - `street`: string (required)
    - `city`: string (required)
    - `state`: string (optional)
    - `postal_code`: string (required)
    - `country`: string (required)
  - `room`: string (optional) - Room/suite number
  - `instructions`: string (optional) - Access instructions

## Participants
- `organizer`: object (optional)
  - `name`: string
  - `email`: string
  - `phone`: string
- `attendees`: Array<object> (optional)
  - `name`: string (required)
  - `email`: string (optional)
  - `role`: string (optional)

## Additional Details
- `description`: string (optional) - Detailed description
- `agenda`: string (optional) - Meeting agenda
- `dress_code`: string (optional) - Required dress code
- `materials`: Array<string> (optional) - Required materials/documents
- `cost`: object (optional)
  - `amount`: number (required)
  - `currency`: string (required)
  - `payment_status`: string (optional)

## Change History
- `change_history`: Array<object> (required)
  - `change_type`: string (required)
  - `changed_at`: datetime (required)
  - `source_document_id`: string (required)
  - `previous_values`: object (required)
  - `change_reason`: string (optional)

## Relationships
- Must be associated with a [Trip](./trip.md)
- Activity timing must fall within trip dates
- At least one attendee should match trip traveler