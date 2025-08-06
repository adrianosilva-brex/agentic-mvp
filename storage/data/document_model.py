import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import mimetypes

try:
    from .db_config import DynamoDBHelper
except ImportError:
    from db_config import DynamoDBHelper

class DocumentSourceType(Enum):
    """Document source type enumeration."""
    EMAIL_ATTACHMENT = "email_attachment"
    EMAIL_BODY = "email_body"
    DIRECT_UPLOAD = "direct_upload"
    API_IMPORT = "api_import"
    TMC_REPORT = "tmc_report"
    RECEIPT_SCAN = "receipt_scan"
    PDF_UPLOAD = "pdf_upload"

class ProcessingStatus(Enum):
    """Document processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class DocumentType(Enum):
    """Document type enumeration based on content."""
    ITINERARY = "itinerary"
    FLIGHT_UPDATE = "flight_update"
    HOTEL_CONFIRMATION = "hotel_confirmation"
    RECEIPT = "receipt"
    INVOICE = "invoice"
    CANCELLATION = "cancellation"
    GENERIC_TRAVEL = "generic_travel"
    UNKNOWN = "unknown"

@dataclass
class ExtractionResult:
    """Result of document extraction process."""
    extracted_at: str
    confidence_score: float
    extracted_data: Dict[str, Any]
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

class DocumentMetadata:
    """
    Document metadata model for tracking uploaded documents.
    
    This model manages:
    - Document identification and storage references
    - Processing status and metadata
    - Extraction results and trip associations
    - Version tracking for document updates
    """
    
    def __init__(self, document_id: Optional[str] = None, **kwargs):
        # Core identification
        self.document_id = document_id or self._generate_document_id()
        self.filename = kwargs.get('filename', '')
        self.original_filename = kwargs.get('original_filename') or self.filename
        
        # File metadata
        self.mime_type = kwargs.get('mime_type', self._detect_mime_type(self.filename))
        self.size_bytes = kwargs.get('size_bytes', 0)
        self.md5_hash = kwargs.get('md5_hash', '')
        
        # Source information
        self.source_type = kwargs.get('source_type', DocumentSourceType.DIRECT_UPLOAD.value)
        self.source_metadata = kwargs.get('source_metadata', {})  # Additional source-specific data
        
        # Timestamps
        self.upload_timestamp = kwargs.get('upload_timestamp', DynamoDBHelper.current_timestamp())
        self.last_processed = kwargs.get('last_processed')
        
        # Processing status
        self.processing_status = kwargs.get('processing_status', ProcessingStatus.PENDING.value)
        self.processing_attempts = kwargs.get('processing_attempts', 0)
        self.processing_errors = kwargs.get('processing_errors', [])
        
        # Document classification
        self.document_type = kwargs.get('document_type', DocumentType.UNKNOWN.value)
        self.confidence_score = kwargs.get('confidence_score', 0.0)
        
        # Storage references
        self.s3_bucket = kwargs.get('s3_bucket', '')
        self.s3_key = kwargs.get('s3_key', '')
        self.s3_version_id = kwargs.get('s3_version_id')
        
        # Extraction results
        self.extraction_results = []
        extraction_data = kwargs.get('extraction_results', [])
        for result in extraction_data:
            if isinstance(result, dict):
                self.extraction_results.append(ExtractionResult(**result))
            else:
                self.extraction_results.append(result)
        
        # Trip associations
        self.extracted_trip_ids = kwargs.get('extracted_trip_ids', [])
        
        # Text content (for search/indexing)
        self.extracted_text = kwargs.get('extracted_text', '')
        self.text_preview = kwargs.get('text_preview', '')  # First 500 chars for preview
        
        # Tags and metadata
        self.tags = kwargs.get('tags', [])
        self.custom_metadata = kwargs.get('custom_metadata', {})
    
    @staticmethod
    def _generate_document_id() -> str:
        """Generate a unique document ID."""
        return f"doc-{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def _detect_mime_type(filename: str) -> str:
        """Detect MIME type from filename."""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    @staticmethod
    def calculate_md5_hash(content: bytes) -> str:
        """Calculate MD5 hash of document content."""
        return hashlib.md5(content).hexdigest()
    
    def set_s3_location(self, bucket: str, key: str, version_id: Optional[str] = None):
        """
        Set S3 storage location.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            version_id: Optional S3 version ID
        """
        self.s3_bucket = bucket
        self.s3_key = key
        self.s3_version_id = version_id
    
    def update_processing_status(self, status: Union[str, ProcessingStatus], error_message: Optional[str] = None):
        """
        Update processing status.
        
        Args:
            status: New processing status
            error_message: Optional error message if status is FAILED
        """
        if isinstance(status, ProcessingStatus):
            self.processing_status = status.value
        else:
            self.processing_status = status
        
        self.processing_attempts += 1
        self.last_processed = DynamoDBHelper.current_timestamp()
        
        if error_message:
            self.processing_errors.append({
                'timestamp': self.last_processed,
                'error': error_message
            })
    
    def add_extraction_result(self, extraction_result: Union[Dict, ExtractionResult]):
        """
        Add an extraction result.
        
        Args:
            extraction_result: Extraction result data
        """
        if isinstance(extraction_result, dict):
            extraction_result = ExtractionResult(**extraction_result)
        
        self.extraction_results.append(extraction_result)
        self.last_processed = DynamoDBHelper.current_timestamp()
        
        # Update confidence score with latest result
        if extraction_result.confidence_score is not None:
            self.confidence_score = extraction_result.confidence_score
    
    def associate_with_trip(self, trip_id: str):
        """
        Associate document with a trip.
        
        Args:
            trip_id: ID of the trip to associate with
        """
        if trip_id not in self.extracted_trip_ids:
            self.extracted_trip_ids.append(trip_id)
    
    def remove_trip_association(self, trip_id: str):
        """
        Remove association with a trip.
        
        Args:
            trip_id: ID of the trip to remove association with
        """
        if trip_id in self.extracted_trip_ids:
            self.extracted_trip_ids.remove(trip_id)
    
    def set_document_type(self, doc_type: Union[str, DocumentType], confidence: float = 0.0):
        """
        Set document type classification.
        
        Args:
            doc_type: Document type
            confidence: Classification confidence score
        """
        if isinstance(doc_type, DocumentType):
            self.document_type = doc_type.value
        else:
            self.document_type = doc_type
        
        if confidence > 0:
            self.confidence_score = confidence
    
    def set_extracted_text(self, text: str, preview_length: int = 500):
        """
        Set extracted text content.
        
        Args:
            text: Full extracted text
            preview_length: Length of preview text
        """
        self.extracted_text = text
        self.text_preview = text[:preview_length] + "..." if len(text) > preview_length else text
    
    def add_tag(self, tag: str):
        """
        Add a tag to the document.
        
        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """
        Remove a tag from the document.
        
        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
    
    def get_latest_extraction_result(self) -> Optional[ExtractionResult]:
        """
        Get the most recent extraction result.
        
        Returns:
            Optional[ExtractionResult]: Latest extraction result or None
        """
        if not self.extraction_results:
            return None
        
        # Sort by extracted_at timestamp and return the latest
        sorted_results = sorted(
            self.extraction_results,
            key=lambda x: x.extracted_at,
            reverse=True
        )
        return sorted_results[0]
    
    def is_successfully_processed(self) -> bool:
        """
        Check if document was successfully processed.
        
        Returns:
            bool: True if processing completed successfully
        """
        return (self.processing_status == ProcessingStatus.COMPLETED.value and 
                len(self.extraction_results) > 0)
    
    def get_processing_errors(self) -> List[Dict[str, str]]:
        """
        Get all processing errors.
        
        Returns:
            List[Dict[str, str]]: List of processing errors with timestamps
        """
        return self.processing_errors
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """
        Convert to DynamoDB item format.
        
        Returns:
            Dict[str, Any]: DynamoDB item representation
        """
        item = {
            'document_id': self.document_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'mime_type': self.mime_type,
            'size_bytes': self.size_bytes,
            'md5_hash': self.md5_hash,
            'source_type': self.source_type,
            'upload_timestamp': self.upload_timestamp,
            'processing_status': self.processing_status,
            'processing_attempts': self.processing_attempts,
            'document_type': self.document_type,
            'confidence_score': self.confidence_score,
            'extracted_trip_ids': self.extracted_trip_ids,
            'tags': self.tags
        }
        
        # Add optional fields
        if self.last_processed:
            item['last_processed'] = self.last_processed
        if self.s3_bucket:
            item['s3_bucket'] = self.s3_bucket
        if self.s3_key:
            item['s3_key'] = self.s3_key
        if self.s3_version_id:
            item['s3_version_id'] = self.s3_version_id
        if self.extracted_text:
            item['extracted_text'] = self.extracted_text
        if self.text_preview:
            item['text_preview'] = self.text_preview
        
        # Add complex fields
        if self.source_metadata:
            item['source_metadata'] = self.source_metadata
        if self.processing_errors:
            item['processing_errors'] = self.processing_errors
        if self.custom_metadata:
            item['custom_metadata'] = self.custom_metadata
        
        # Add extraction results
        if self.extraction_results:
            item['extraction_results'] = [
                result.to_dict() if isinstance(result, ExtractionResult) else result
                for result in self.extraction_results
            ]
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'DocumentMetadata':
        """
        Create DocumentMetadata from DynamoDB item.
        
        Args:
            item: DynamoDB item
            
        Returns:
            DocumentMetadata: Document metadata instance
        """
        return cls(**item)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format.
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return self.to_dynamodb_item()
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """
        Convert to summary dictionary (without full text content).
        
        Returns:
            Dict[str, Any]: Summary dictionary representation
        """
        summary = self.to_dict().copy()
        # Remove large text fields from summary
        summary.pop('extracted_text', None)
        return summary
    
    def __str__(self) -> str:
        return f"Document(id={self.document_id}, filename={self.filename}, status={self.processing_status})"
    
    def __repr__(self) -> str:
        return f"DocumentMetadata(document_id='{self.document_id}', filename='{self.filename}', processing_status='{self.processing_status}')"

class DocumentBuilder:
    """Builder class for creating DocumentMetadata instances."""
    
    def __init__(self, filename: str):
        self.data = {'filename': filename}
    
    def with_content(self, content: bytes):
        """Set document content and calculate hash."""
        self.data['size_bytes'] = len(content)
        self.data['md5_hash'] = DocumentMetadata.calculate_md5_hash(content)
        return self
    
    def with_source(self, source_type: Union[str, DocumentSourceType], metadata: Optional[Dict] = None):
        """Set source type and metadata."""
        if isinstance(source_type, DocumentSourceType):
            self.data['source_type'] = source_type.value
        else:
            self.data['source_type'] = source_type
        
        if metadata:
            self.data['source_metadata'] = metadata
        return self
    
    def with_s3_location(self, bucket: str, key: str, version_id: Optional[str] = None):
        """Set S3 storage location."""
        self.data['s3_bucket'] = bucket
        self.data['s3_key'] = key
        if version_id:
            self.data['s3_version_id'] = version_id
        return self
    
    def with_document_type(self, doc_type: Union[str, DocumentType], confidence: float = 0.0):
        """Set document type and confidence."""
        if isinstance(doc_type, DocumentType):
            self.data['document_type'] = doc_type.value
        else:
            self.data['document_type'] = doc_type
        self.data['confidence_score'] = confidence
        return self
    
    def with_extracted_text(self, text: str):
        """Set extracted text content."""
        self.data['extracted_text'] = text
        self.data['text_preview'] = text[:500] + "..." if len(text) > 500 else text
        return self
    
    def with_tags(self, tags: List[str]):
        """Set document tags."""
        self.data['tags'] = tags
        return self
    
    def build(self) -> DocumentMetadata:
        """Build the DocumentMetadata instance."""
        return DocumentMetadata(**self.data)

# Document classification helpers
class DocumentClassifier:
    """Helper class for document classification."""
    
    @staticmethod
    def classify_by_content(text: str, filename: str = "") -> tuple[DocumentType, float]:
        """
        Classify document type based on content and filename.
        
        Args:
            text: Document text content
            filename: Document filename
            
        Returns:
            tuple[DocumentType, float]: Document type and confidence score
        """
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Define classification patterns
        patterns = {
            DocumentType.ITINERARY: [
                'itinerary', 'flight confirmation', 'booking confirmation',
                'departure', 'arrival', 'flight number', 'confirmation code'
            ],
            DocumentType.FLIGHT_UPDATE: [
                'flight change', 'schedule change', 'delay notification',
                'cancellation notice', 'gate change', 'time change'
            ],
            DocumentType.HOTEL_CONFIRMATION: [
                'hotel confirmation', 'reservation confirmed', 'check-in',
                'check-out', 'hotel booking', 'room reservation'
            ],
            DocumentType.RECEIPT: [
                'receipt', 'payment confirmation', 'transaction', 'paid',
                'total amount', 'subtotal'
            ],
            DocumentType.INVOICE: [
                'invoice', 'billing', 'amount due', 'payment terms',
                'invoice number'
            ],
            DocumentType.CANCELLATION: [
                'cancellation', 'cancelled', 'refund', 'booking canceled'
            ]
        }
        
        best_match = DocumentType.UNKNOWN
        best_score = 0.0
        
        # Check patterns in both text and filename
        for doc_type, keywords in patterns.items():
            score = 0.0
            total_keywords = len(keywords)
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 0.8  # Higher weight for text content
                if keyword in filename_lower:
                    score += 0.2  # Lower weight for filename
            
            # Normalize score
            normalized_score = min(score / total_keywords, 1.0)
            
            if normalized_score > best_score:
                best_match = doc_type
                best_score = normalized_score
        
        # If no good match, classify as generic travel
        if best_score < 0.3:
            travel_keywords = ['travel', 'trip', 'booking', 'reservation', 'airline', 'hotel']
            travel_score = sum(1 for keyword in travel_keywords if keyword in text_lower)
            
            if travel_score > 0:
                return DocumentType.GENERIC_TRAVEL, min(travel_score / len(travel_keywords), 0.5)
        
        return best_match, best_score
    
    @staticmethod
    def extract_key_entities(text: str) -> Dict[str, List[str]]:
        """
        Extract key entities from document text.
        
        Args:
            text: Document text content
            
        Returns:
            Dict[str, List[str]]: Dictionary of entity types and values
        """
        import re
        
        entities = {
            'confirmation_codes': [],
            'flight_numbers': [],
            'airports': [],
            'dates': [],
            'emails': [],
            'phone_numbers': []
        }
        
        # Confirmation codes (alphanumeric, 4-8 characters)
        conf_codes = re.findall(r'\b[A-Z0-9]{4,8}\b', text.upper())
        entities['confirmation_codes'] = list(set(conf_codes))
        
        # Flight numbers (2-3 letters + 1-4 digits)
        flight_nums = re.findall(r'\b[A-Z]{2,3}\s*\d{1,4}\b', text.upper())
        entities['flight_numbers'] = list(set(flight_nums))
        
        # Airport codes (3 letters, uppercase)
        airports = re.findall(r'\b[A-Z]{3}\b', text.upper())
        entities['airports'] = list(set(airports))
        
        # Dates (various formats)
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'\b\w{3,9}\s+\d{1,2},?\s+\d{4}\b',
            r'\d{4}-\d{2}-\d{2}'
        ]
        for pattern in date_patterns:
            dates = re.findall(pattern, text)
            entities['dates'].extend(dates)
        
        # Email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        entities['emails'] = list(set(emails))
        
        # Phone numbers
        phone_patterns = [
            r'\b\d{3}-\d{3}-\d{4}\b',
            r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',
            r'\b\d{3}\.\d{3}\.\d{4}\b'
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            entities['phone_numbers'].extend(phones)
        
        # Remove duplicates and empty values
        for key in entities:
            entities[key] = list(set(filter(None, entities[key])))
        
        return entities