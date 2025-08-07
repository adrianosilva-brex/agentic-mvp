import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

try:
    from .db_config import DynamoDBHelper
except ImportError:
    from db_config import DynamoDBHelper

class TripStatus(Enum):
    """Trip status enumeration."""
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class OriginType(Enum):
    """Trip origin type enumeration."""
    EXPLICIT = "explicit"
    DERIVED = "derived" 

class ChangeType(Enum):
    """Change type enumeration."""
    CREATION = "creation"
    ADDITION = "addition"
    MODIFICATION = "modification"
    DELETION = "deletion"
    CANCELLATION = "cancellation"

@dataclass
class Traveler:
    """Traveler information."""
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class ChangeEntry:
    """Individual change entry for trip components."""
    change_type: str
    changed_at: str
    source_document_id: str
    previous_values: Dict[str, Any]
    change_reason: str
    confidence_score: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class FlightSegment:
    """Flight segment information."""
    segment_id: str
    version: int
    status: str
    flight_number: str
    departure: Dict[str, Any]  # airport, time
    arrival: Dict[str, Any]    # airport, time
    change_history: List[ChangeEntry] = field(default_factory=list)
    seat: Optional[str] = None
    fare_class: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        # Convert change_history to list of dicts
        data['change_history'] = [change.to_dict() if isinstance(change, ChangeEntry) else change 
                                 for change in self.change_history]
        return data

@dataclass
class SourceDocument:
    """Source document reference."""
    document_id: str
    type: str
    confidence_score: float
    extracted_at: str
    contributed_fields: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class VersionEntry:
    """Version history entry."""
    version: int
    timestamp: str
    document_id: str
    change_type: str
    changed_fields: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class MergeCandidate:
    """Trip merge candidate information."""
    trip_id: str
    similarity_score: float
    match_reasons: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)

class Trip:
    """
    Trip data model for flexible schema storage in DynamoDB.
    
    This model supports:
    - Core trip fields (always present)
    - Flexible namespaced extensions for different booking types
    - Version tracking and change history
    - Source document references
    - Merge candidate tracking
    """
    
    def __init__(self, trip_id: Optional[str] = None, **kwargs):
        # Core fields (always present)
        self.trip_id = trip_id or self._generate_trip_id()
        self.version = kwargs.get('version', 1)
        self.created_at = kwargs.get('created_at', DynamoDBHelper.current_timestamp())
        self.updated_at = kwargs.get('updated_at', DynamoDBHelper.current_timestamp())
        
        # Traveler information
        self.traveler = kwargs.get('traveler', {})
        if isinstance(self.traveler, dict) and self.traveler:
            self.traveler = Traveler(**self.traveler)
        
        # Core trip metadata
        self.status = kwargs.get('status', TripStatus.CONFIRMED.value)
        self.start_date = kwargs.get('start_date')
        self.end_date = kwargs.get('end_date')
        self.purpose = kwargs.get('purpose')
        
        # Trip metadata
        self.origin_type = kwargs.get('origin_type', OriginType.EXPLICIT.value)
        self.trip_confidence = kwargs.get('trip_confidence', 1.0)
        
        # Flexible extensions (namespaced)
        self.extensions = {}
        
        # Source document references
        self.source_documents = []
        source_docs = kwargs.get('source_documents', [])
        for doc in source_docs:
            if isinstance(doc, dict):
                self.source_documents.append(SourceDocument(**doc))
            else:
                self.source_documents.append(doc)
        
        # Version tracking
        self.version_history = []
        version_hist = kwargs.get('version_history', [])
        for entry in version_hist:
            if isinstance(entry, dict):
                self.version_history.append(VersionEntry(**entry))
            else:
                self.version_history.append(entry)
        
        # Merge candidates
        self.merge_candidates = []
        merge_cands = kwargs.get('merge_candidates', [])
        for candidate in merge_cands:
            if isinstance(candidate, dict):
                self.merge_candidates.append(MergeCandidate(**candidate))
            else:
                self.merge_candidates.append(candidate)
        
        # Load any remaining kwargs as extensions
        excluded_fields = {
            'trip_id', 'version', 'created_at', 'updated_at', 'traveler',
            'status', 'start_date', 'end_date', 'purpose', 'origin_type',
            'trip_confidence', 'source_documents', 'version_history', 'merge_candidates'
        }
        
        for key, value in kwargs.items():
            if key not in excluded_fields:
                self.extensions[key] = value
    
    @staticmethod
    def _generate_trip_id() -> str:
        """Generate a unique trip ID."""
        return f"trip-{uuid.uuid4().hex[:12]}"
    
    def add_extension(self, namespace: str, data: Dict[str, Any]):
        """
        Add a namespaced extension to the trip.
        
        Args:
            namespace: The namespace for the extension (e.g., 'southwest_itinerary')
            data: The extension data
        """
        self.extensions[namespace] = data
        self._update_timestamp()
    
    def get_extension(self, namespace: str) -> Optional[Dict[str, Any]]:
        """
        Get a namespaced extension from the trip.
        
        Args:
            namespace: The namespace to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: The extension data or None if not found
        """
        return self.extensions.get(namespace)
    
    def add_source_document(self, document: Union[Dict, SourceDocument]):
        """
        Add a source document reference.
        
        Args:
            document: Source document information
        """
        if isinstance(document, dict):
            document = SourceDocument(**document)
        
        self.source_documents.append(document)
        self._update_timestamp()
    
    def add_version_entry(self, document_id: str, change_type: str, changed_fields: List[str]):
        """
        Add a version history entry.
        
        Args:
            document_id: ID of the document that caused the change
            change_type: Type of change (creation, addition, modification, etc.)
            changed_fields: List of fields that were changed
        """
        self.version += 1
        
        version_entry = VersionEntry(
            version=self.version,
            timestamp=DynamoDBHelper.current_timestamp(),
            document_id=document_id,
            change_type=change_type,
            changed_fields=changed_fields
        )
        
        self.version_history.append(version_entry)
        self._update_timestamp()
    
    def add_merge_candidate(self, candidate: Union[Dict, MergeCandidate]):
        """
        Add a merge candidate.
        
        Args:
            candidate: Merge candidate information
        """
        if isinstance(candidate, dict):
            candidate = MergeCandidate(**candidate)
        
        self.merge_candidates.append(candidate)
        self._update_timestamp()
    
    def remove_merge_candidate(self, trip_id: str):
        """
        Remove a merge candidate by trip ID.
        
        Args:
            trip_id: ID of the trip to remove from candidates
        """
        self.merge_candidates = [
            candidate for candidate in self.merge_candidates 
            if candidate.trip_id != trip_id
        ]
        self._update_timestamp()
    
    def _update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = DynamoDBHelper.current_timestamp()
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """
        Convert the trip to a DynamoDB item format.
        
        Returns:
            Dict[str, Any]: DynamoDB item representation
        """
        item = {
            'trip_id': self.trip_id,
            'version': self.version,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status,
            'origin_type': self.origin_type,
            'trip_confidence': Decimal(str(self.trip_confidence))
        }
        
        # Add optional core fields
        if self.start_date:
            item['start_date'] = self.start_date
        if self.end_date:
            item['end_date'] = self.end_date
        if self.purpose:
            item['purpose'] = self.purpose
        
        # Add traveler information
        if self.traveler:
            if isinstance(self.traveler, Traveler):
                item['traveler'] = self.traveler.to_dict()
                # Add traveler_id for GSI
                item['traveler_id'] = self.traveler.id
            else:
                item['traveler'] = self.traveler
                item['traveler_id'] = self.traveler.get('id', '')
        
        # Add extensions
        for namespace, data in self.extensions.items():
            item[namespace] = DynamoDBHelper.float_to_decimal(data)
        
        # Add source documents
        if self.source_documents:
            item['source_documents'] = [
                doc.to_dict() if isinstance(doc, SourceDocument) else doc
                for doc in self.source_documents
            ]
        
        # Add version history
        if self.version_history:
            item['version_history'] = [
                entry.to_dict() if isinstance(entry, VersionEntry) else entry
                for entry in self.version_history
            ]
        
        # Add merge candidates
        if self.merge_candidates:
            item['merge_candidates'] = [
                candidate.to_dict() if isinstance(candidate, MergeCandidate) else candidate
                for candidate in self.merge_candidates
            ]
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'Trip':
        """
        Create a Trip instance from a DynamoDB item.
        
        Args:
            item: DynamoDB item
            
        Returns:
            Trip: Trip instance
        """
        # Convert Decimal objects to float
        item = DynamoDBHelper.decimal_to_float(item)
        
        return cls(**item)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the trip to a dictionary format.
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return DynamoDBHelper.decimal_to_float(self.to_dynamodb_item())
    
    def to_json(self) -> str:
        """
        Convert the trip to JSON format.
        
        Returns:
            str: JSON representation
        """
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def get_flight_segments(self) -> List[FlightSegment]:
        """
        Get all flight segments from various airline extensions.
        
        Returns:
            List[FlightSegment]: List of all flight segments
        """
        segments = []
        
        # Look through all extensions for flight data
        for namespace, data in self.extensions.items():
            if isinstance(data, dict) and 'segments' in data:
                namespace_segments = data['segments']
                for segment_data in namespace_segments:
                    if isinstance(segment_data, dict):
                        # Convert change_history if present
                        if 'change_history' in segment_data:
                            change_history = []
                            for change in segment_data['change_history']:
                                if isinstance(change, dict):
                                    change_history.append(ChangeEntry(**change))
                                else:
                                    change_history.append(change)
                            segment_data['change_history'] = change_history
                        
                        segments.append(FlightSegment(**segment_data))
        
        return segments
    
    def get_hotel_bookings(self) -> List[Dict[str, Any]]:
        """
        Get all hotel bookings from extensions.
        
        Returns:
            List[Dict[str, Any]]: List of hotel bookings
        """
        bookings = []
        
        # Look for hotel_booking extensions
        if 'hotel_booking' in self.extensions:
            bookings.append(self.extensions['hotel_booking'])
        
        # Look for other hotel-related extensions
        for namespace, data in self.extensions.items():
            if 'hotel' in namespace.lower() and namespace != 'hotel_booking':
                bookings.append(data)
        
        return bookings
    
    def get_all_airports(self) -> List[str]:
        """
        Get all airports mentioned in the trip.
        
        Returns:
            List[str]: List of unique airport codes
        """
        airports = set()
        
        # Get airports from flight segments
        for segment in self.get_flight_segments():
            if isinstance(segment.departure, dict) and 'airport' in segment.departure:
                airports.add(segment.departure['airport'])
            if isinstance(segment.arrival, dict) and 'airport' in segment.arrival:
                airports.add(segment.arrival['airport'])
        
        return list(airports)
    
    def __str__(self) -> str:
        return f"Trip(id={self.trip_id}, traveler={getattr(self.traveler, 'name', 'Unknown')}, dates={self.start_date} to {self.end_date})"
    
    def __repr__(self) -> str:
        return f"Trip(trip_id='{self.trip_id}', version={self.version}, status='{self.status}')"

class TripBuilder:
    """Builder class for creating Trip instances with validation."""
    
    def __init__(self):
        self.data = {}
    
    def with_traveler(self, traveler_id: str, name: str, email: str, phone: Optional[str] = None):
        """Set traveler information."""
        self.data['traveler'] = {
            'id': traveler_id,
            'name': name,
            'email': email,
            'phone': phone
        }
        return self
    
    def with_dates(self, start_date: str, end_date: str):
        """Set trip dates."""
        self.data['start_date'] = start_date
        self.data['end_date'] = end_date
        return self
    
    def with_purpose(self, purpose: str):
        """Set trip purpose."""
        self.data['purpose'] = purpose
        return self
    
    def with_status(self, status: Union[str, TripStatus]):
        """Set trip status."""
        if isinstance(status, TripStatus):
            self.data['status'] = status.value
        else:
            self.data['status'] = status
        return self
    
    def with_origin_type(self, origin_type: Union[str, OriginType], confidence: float = 1.0):
        """Set origin type and confidence."""
        if isinstance(origin_type, OriginType):
            self.data['origin_type'] = origin_type.value
        else:
            self.data['origin_type'] = origin_type
        self.data['trip_confidence'] = confidence
        return self
    
    def with_extension(self, namespace: str, data: Dict[str, Any]):
        """Add a namespaced extension."""
        self.data[namespace] = data
        return self
    
    def build(self) -> Trip:
        """Build the Trip instance."""
        return Trip(**self.data)