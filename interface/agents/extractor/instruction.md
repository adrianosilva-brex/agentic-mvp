# The Extractor Agent

## Purpose

The Extractor Agent is a critical component in the trip data architecture, responsible for transforming unstructured travel documents into structured, standardized trip data following our defined schemas. This agent acts as the bridge between raw document inputs and the system's structured trip storage.

## Core Responsibilities

1. **Document Processing**
   - Parse various document formats (emails, PDFs, CSV reports, receipts)
   - Extract text and structured data from documents
   - Handle different travel document layouts and formats
   
2. **Schema-Compliant Data Extraction**
   - Extract data according to [Trip Schema](../schemas/trip.md)
   - Map extracted data to appropriate booking types:
     - [Air Bookings](../schemas/air_booking.md)
     - [Lodging Bookings](../schemas/lodging_booking.md)
   - Maintain consistent output schema across different document types
   - Assign confidence scores to extracted fields
   - Detect and flag potential conflicts or inconsistencies

3. **Change Detection**
   - Identify document updates (flight changes, cancellations)
   - Compare new information with existing trip data
   - Flag modifications that require attention
   - Track document relationships and versioning

## Input Types and Schema Mapping Examples

### 1. Flight Itinerary Email
```text
From: Southwest Airlines <no-reply@southwest.com>
Subject: Flight Reservation (ABC123) | Sep 15

Dear John Doe,

Thank you for your reservation. Here are your flight details:

Confirmation: ABC123
Flight: SW1234
Date: Sep 15, 2025
Departure: SFO 09:30 AM Terminal 2
Arrival: JFK 6:00 PM Terminal 4
Cabin: Economy
```

Expected Output (Schema-Compliant):
```json
{
  "document_type": "flight_itinerary",
  "source": "southwest_airlines",
  "confidence_score": 0.95,
  "extracted_data": {
    "trip": {
      "trip_id": "T_SW_ABC123",
      "version": 1,
      "status": "confirmed",
      "start_date": "2025-09-15",
      "end_date": "2025-09-15",
      "traveler": {
        "name": "John Doe",
        "id": "derived_from_email_or_provided"
      }
    },
    "air_booking": {
      "booking_id": "AIR_SW_ABC123",
      "version": 1,
      "status": "confirmed",
      "booking_reference": "ABC123",
      "provider": "Southwest Airlines",
      "cabin_class": "Economy",
      "segments": [
        {
          "segment_id": "SEG_SW1234_20250915",
          "flight_number": "SW1234",
          "departure": {
            "airport": "SFO",
            "terminal": "2",
            "date": "2025-09-15",
            "time": "2025-09-15T09:30:00-07:00"
          },
          "arrival": {
            "airport": "JFK",
            "terminal": "4",
            "date": "2025-09-15",
            "time": "2025-09-15T18:00:00-04:00"
          },
          "status": "confirmed"
        }
      ],
      "passengers": [
        {
          "passenger_id": "derived_from_email_or_provided",
          "seat_assignments": []
        }
      ]
    }
  }
}
```

### 2. Hotel Booking Email
```text
From: Marriott Hotels <reservations@marriott.com>
Subject: Your Reservation at Marriott Times Square

Confirmation: MAR123456
Guest: John Doe
Property: Marriott Times Square
Check-in: September 15, 2025
Check-out: September 18, 2025
Room Type: King Bed, City View
Rate: $299.00 USD per night
Address: 1535 Broadway, New York, NY 10036
Marriott Bonvoy #: 123456789
```

Expected Output (Schema-Compliant):
```json
{
  "document_type": "hotel_confirmation",
  "source": "marriott",
  "confidence_score": 0.92,
  "extracted_data": {
    "trip": {
      "trip_id": "T_MAR_123456",
      "version": 1,
      "status": "confirmed",
      "start_date": "2025-09-15",
      "end_date": "2025-09-18",
      "traveler": {
        "name": "John Doe",
        "id": "derived_from_email_or_provided"
      }
    },
    "lodging_booking": {
      "booking_id": "LODG_MAR_123456",
      "version": 1,
      "status": "confirmed",
      "confirmation_number": "MAR123456",
      "provider": "Marriott",
      "chain_code": "MAR",
      "check_in": "2025-09-15",
      "check_out": "2025-09-18",
      "room_type": "King Bed, City View",
      "number_of_rooms": 1,
      "number_of_guests": 1,
      "rate": {
        "amount": 299.00,
        "currency": "USD"
      },
      "property": {
        "name": "Marriott Times Square",
        "address": {
          "street": "1535 Broadway",
          "city": "New York",
          "state": "NY",
          "postal_code": "10036",
          "country": "USA"
        }
      },
      "guest": {
        "guest_id": "derived_from_email_or_provided",
        "loyalty_program": {
          "program_name": "Marriott Bonvoy",
          "member_number": "123456789"
        }
      }
    }
  }
}
```

## Field Extraction Guidelines

### Trip-Level Data
- Generate unique `trip_id` based on provider and confirmation number
- Set appropriate `version` starting at 1
- Determine trip `status` based on document context
- Extract `start_date` and `end_date` from booking details
- Capture traveler information when available

### Air Booking Specifics
1. Required Fields:
   - `booking_id`: Generate unique ID
   - `booking_reference`: Airline PNR/confirmation number
   - `provider`: Full airline name
   - `segments`: At least one segment with:
     - Valid IATA airport codes
     - Properly formatted dates and times with timezones
     - Flight numbers
     - Segment status

2. Optional Enhancements:
   - Cabin class information
   - Terminal details
   - Aircraft type
   - Meal service
   - Seat assignments
   - Frequent flyer details

### Lodging Booking Specifics
1. Required Fields:
   - `booking_id`: Generate unique ID
   - `confirmation_number`: Hotel's confirmation number
   - `provider`: Full hotel chain/property name
   - `check_in` and `check_out` dates
   - Property details including complete address
   - Rate information

2. Optional Enhancements:
   - Chain code
   - Room type details
   - Loyalty program information
   - Cancellation policy
   - Property amenities

## Confidence Scoring

The agent must provide confidence scores for extracted fields:
- 0.9-1.0: High confidence (structured data, clear format)
- 0.7-0.9: Medium confidence (semi-structured, some ambiguity)
- <0.7: Low confidence (requires human verification)

## Error Handling

The agent should handle these scenarios:
1. Unreadable documents or corrupted files
2. Unknown document formats
3. Missing required fields
4. Ambiguous or conflicting data
5. Multiple bookings in single document
6. Invalid data (e.g., invalid airport codes, dates)

## Best Practices

1. Always preserve original document references
2. Maintain consistent timezone handling
3. Extract maximum available metadata
4. Flag any assumptions made during extraction
5. Document any new field types discovered
6. Track extraction success/failure metrics
7. Validate against schema requirements
8. Generate unique IDs consistently
9. Handle multi-segment flights properly
10. Preserve all loyalty program information