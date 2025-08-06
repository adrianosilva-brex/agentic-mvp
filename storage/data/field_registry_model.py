import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import Counter
import json

try:
    from .db_config import DynamoDBHelper
except ImportError:
    from db_config import DynamoDBHelper

class FieldDataType(Enum):
    """Field data type enumeration."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    CURRENCY = "currency"
    AIRPORT_CODE = "airport_code"
    CONFIRMATION_CODE = "confirmation_code"
    UNKNOWN = "unknown"

class FieldStability(Enum):
    """Field stability enumeration."""
    STABLE = "stable"      # Appears in >80% of documents
    COMMON = "common"      # Appears in 40-80% of documents
    OCCASIONAL = "occasional"  # Appears in 10-40% of documents
    RARE = "rare"         # Appears in <10% of documents

@dataclass
class FieldExample:
    """Example value for a field."""
    value: str
    source_document_id: str
    extracted_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class FieldStatistics:
    """Statistical information about a field."""
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None
    unique_values_count: int = 0
    most_common_values: List[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def __post_init__(self):
        if self.most_common_values is None:
            self.most_common_values = []

class FieldRegistryEntry:
    """
    Field registry entry for tracking observed fields across trips.
    
    This model manages:
    - Field metadata and classification
    - Usage statistics and patterns
    - Example values and validation rules
    - Relationships between fields
    """
    
    def __init__(self, field_id: Optional[str] = None, **kwargs):
        # Core identification
        self.field_id = field_id or kwargs.get('field_id', self._generate_field_id(kwargs.get('path', '')))
        self.path = kwargs.get('path', '')
        self.field_name = kwargs.get('field_name') or self._extract_field_name(self.path)
        
        # Data type and classification
        self.data_type = kwargs.get('data_type', FieldDataType.UNKNOWN.value)
        self.inferred_type = kwargs.get('inferred_type', self.data_type)
        self.type_confidence = kwargs.get('type_confidence', 0.0)
        
        # Source information
        self.source_namespace = kwargs.get('source_namespace', '')
        self.first_seen = kwargs.get('first_seen', DynamoDBHelper.current_timestamp())
        self.last_seen = kwargs.get('last_seen', DynamoDBHelper.current_timestamp())
        
        # Usage statistics
        self.occurrence_count = kwargs.get('occurrence_count', 0)
        self.total_documents = kwargs.get('total_documents', 0)
        self.occurrence_percentage = kwargs.get('occurrence_percentage', 0.0)
        
        # Field metadata
        self.description = kwargs.get('description', '')
        self.is_required = kwargs.get('is_required', False)
        self.is_indexed = kwargs.get('is_indexed', False)
        self.is_searchable = kwargs.get('is_searchable', True)
        
        # Examples and statistics
        self.examples = []
        examples_data = kwargs.get('examples', [])
        for example in examples_data:
            if isinstance(example, dict):
                self.examples.append(FieldExample(**example))
            else:
                self.examples.append(example)
        
        # Field statistics
        stats_data = kwargs.get('statistics', {})
        if isinstance(stats_data, dict):
            self.statistics = FieldStatistics(**stats_data)
        else:
            self.statistics = stats_data or FieldStatistics()
        
        # Relationships
        self.related_fields = kwargs.get('related_fields', [])  # Fields that often appear together
        self.parent_field = kwargs.get('parent_field')  # Parent field if this is nested
        self.child_fields = kwargs.get('child_fields', [])  # Child fields if this is an object
        
        # Validation rules
        self.validation_rules = kwargs.get('validation_rules', {})
        self.validation_patterns = kwargs.get('validation_patterns', [])
        
        # Metadata
        self.tags = kwargs.get('tags', [])
        self.custom_metadata = kwargs.get('custom_metadata', {})
        
        # Stability classification
        self._update_stability()
    
    @staticmethod
    def _generate_field_id(path: str) -> str:
        """Generate a field ID based on the path."""
        if path:
            # Use the path as the ID for consistency
            return path
        return f"field-{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    def _extract_field_name(path: str) -> str:
        """Extract field name from path."""
        if not path:
            return "unknown"
        
        # Handle array indices
        path = path.replace('[0]', '[]').replace('[1]', '[]').replace('[2]', '[]')
        
        # Get the last part of the path
        parts = path.split('.')
        return parts[-1] if parts else path
    
    def add_occurrence(self, document_id: str, value: Any, total_docs: int = None):
        """
        Record a new occurrence of this field.
        
        Args:
            document_id: ID of the document containing this field
            value: The field value
            total_docs: Total number of documents processed (for percentage calculation)
        """
        self.occurrence_count += 1
        self.last_seen = DynamoDBHelper.current_timestamp()
        
        # Update total documents count if provided
        if total_docs is not None:
            self.total_documents = total_docs
            self.occurrence_percentage = (self.occurrence_count / total_docs) * 100
        
        # Add example if we don't have too many
        if len(self.examples) < 5:
            example = FieldExample(
                value=str(value),
                source_document_id=document_id,
                extracted_at=DynamoDBHelper.current_timestamp()
            )
            self.examples.append(example)
        
        # Update statistics
        self._update_statistics(str(value))
        
        # Update stability classification
        self._update_stability()
        
        # Infer data type if not already classified
        if self.data_type == FieldDataType.UNKNOWN.value:
            self._infer_data_type(value)
    
    def _update_statistics(self, value: str):
        """Update field statistics with new value."""
        if not value:
            return
        
        value_length = len(value)
        
        # Update length statistics
        if self.statistics.min_length is None or value_length < self.statistics.min_length:
            self.statistics.min_length = value_length
        
        if self.statistics.max_length is None or value_length > self.statistics.max_length:
            self.statistics.max_length = value_length
        
        # Update average length
        if self.statistics.avg_length is None:
            self.statistics.avg_length = value_length
        else:
            # Simple running average
            self.statistics.avg_length = (
                (self.statistics.avg_length * (self.occurrence_count - 1) + value_length) / 
                self.occurrence_count
            )
        
        # Track unique values (keep only top 10 most common)
        if not self.statistics.most_common_values:
            self.statistics.most_common_values = []
        
        # Simple tracking of common values
        if value not in self.statistics.most_common_values:
            if len(self.statistics.most_common_values) < 10:
                self.statistics.most_common_values.append(value)
    
    def _update_stability(self):
        """Update field stability classification based on occurrence percentage."""
        if self.occurrence_percentage >= 80:
            self.stability = FieldStability.STABLE.value
        elif self.occurrence_percentage >= 40:
            self.stability = FieldStability.COMMON.value
        elif self.occurrence_percentage >= 10:
            self.stability = FieldStability.OCCASIONAL.value
        else:
            self.stability = FieldStability.RARE.value
    
    def _infer_data_type(self, value: Any):
        """Infer data type from value."""
        if value is None:
            return
        
        str_value = str(value).strip()
        
        # Check for specific patterns
        if self._is_email(str_value):
            self.data_type = FieldDataType.EMAIL.value
            self.type_confidence = 0.9
        elif self._is_phone(str_value):
            self.data_type = FieldDataType.PHONE.value
            self.type_confidence = 0.8
        elif self._is_airport_code(str_value):
            self.data_type = FieldDataType.AIRPORT_CODE.value
            self.type_confidence = 0.9
        elif self._is_confirmation_code(str_value):
            self.data_type = FieldDataType.CONFIRMATION_CODE.value
            self.type_confidence = 0.7
        elif self._is_currency(str_value):
            self.data_type = FieldDataType.CURRENCY.value
            self.type_confidence = 0.8
        elif self._is_date(str_value):
            self.data_type = FieldDataType.DATE.value
            self.type_confidence = 0.8
        elif self._is_datetime(str_value):
            self.data_type = FieldDataType.DATETIME.value
            self.type_confidence = 0.9
        elif self._is_number(str_value):
            self.data_type = FieldDataType.NUMBER.value
            self.type_confidence = 0.9
        elif self._is_boolean(str_value):
            self.data_type = FieldDataType.BOOLEAN.value
            self.type_confidence = 0.9
        elif isinstance(value, (list, tuple)):
            self.data_type = FieldDataType.ARRAY.value
            self.type_confidence = 1.0
        elif isinstance(value, dict):
            self.data_type = FieldDataType.OBJECT.value
            self.type_confidence = 1.0
        else:
            self.data_type = FieldDataType.STRING.value
            self.type_confidence = 0.6
    
    @staticmethod
    def _is_email(value: str) -> bool:
        """Check if value is an email address."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def _is_phone(value: str) -> bool:
        """Check if value is a phone number."""
        import re
        # Simple phone number patterns
        patterns = [
            r'^\d{3}-\d{3}-\d{4}$',
            r'^\(\d{3}\)\s*\d{3}-\d{4}$',
            r'^\d{3}\.\d{3}\.\d{4}$',
            r'^\+\d{1,3}\s*\d{3,4}\s*\d{3,4}\s*\d{3,4}$'
        ]
        return any(re.match(pattern, value) for pattern in patterns)
    
    @staticmethod
    def _is_airport_code(value: str) -> bool:
        """Check if value is an airport code."""
        return len(value) == 3 and value.isalpha() and value.isupper()
    
    @staticmethod
    def _is_confirmation_code(value: str) -> bool:
        """Check if value is a confirmation code."""
        # Alphanumeric, 4-8 characters
        return (4 <= len(value) <= 8 and 
                value.isalnum() and 
                any(c.isalpha() for c in value) and 
                any(c.isdigit() for c in value))
    
    @staticmethod
    def _is_currency(value: str) -> bool:
        """Check if value is a currency amount."""
        import re
        patterns = [
            r'^\$\d+(\.\d{2})?$',
            r'^\d+(\.\d{2})?\s*(USD|EUR|GBP|CAD)$',
            r'^\d+(\.\d{2})?$'
        ]
        return any(re.match(pattern, value, re.IGNORECASE) for pattern in patterns)
    
    @staticmethod
    def _is_date(value: str) -> bool:
        """Check if value is a date."""
        import re
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{1,2}/\d{1,2}/\d{4}$',
            r'^\d{1,2}-\d{1,2}-\d{4}$',
            r'^[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}$'
        ]
        return any(re.match(pattern, value) for pattern in date_patterns)
    
    @staticmethod
    def _is_datetime(value: str) -> bool:
        """Check if value is a datetime."""
        import re
        # ISO 8601 and common datetime patterns
        patterns = [
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
            r'^\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}',
        ]
        return any(re.match(pattern, value) for pattern in patterns)
    
    @staticmethod
    def _is_number(value: str) -> bool:
        """Check if value is a number."""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _is_boolean(value: str) -> bool:
        """Check if value is a boolean."""
        return value.lower() in ['true', 'false', 'yes', 'no', '1', '0']
    
    def add_related_field(self, field_path: str, correlation_strength: float = 1.0):
        """
        Add a related field.
        
        Args:
            field_path: Path of the related field
            correlation_strength: Strength of correlation (0.0 to 1.0)
        """
        relation = {
            'field_path': field_path,
            'correlation_strength': correlation_strength,
            'discovered_at': DynamoDBHelper.current_timestamp()
        }
        
        # Avoid duplicates
        existing = next((r for r in self.related_fields if r['field_path'] == field_path), None)
        if not existing:
            self.related_fields.append(relation)
    
    def set_validation_rule(self, rule_type: str, rule_value: Any):
        """
        Set a validation rule for this field.
        
        Args:
            rule_type: Type of validation rule (e.g., 'min_length', 'max_length', 'pattern')
            rule_value: Value for the validation rule
        """
        self.validation_rules[rule_type] = rule_value
    
    def add_tag(self, tag: str):
        """Add a tag to this field."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from this field."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def get_stability_level(self) -> FieldStability:
        """Get the field stability level."""
        return FieldStability(getattr(self, 'stability', FieldStability.RARE.value))
    
    def is_stable(self) -> bool:
        """Check if field is stable (appears in >80% of documents)."""
        return self.occurrence_percentage >= 80
    
    def is_common(self) -> bool:
        """Check if field is common (appears in >40% of documents)."""
        return self.occurrence_percentage >= 40
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """
        Convert to DynamoDB item format.
        
        Returns:
            Dict[str, Any]: DynamoDB item representation
        """
        item = {
            'field_id': self.field_id,
            'path': self.path,
            'field_name': self.field_name,
            'data_type': self.data_type,
            'inferred_type': self.inferred_type,
            'type_confidence': self.type_confidence,
            'source_namespace': self.source_namespace,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'occurrence_count': self.occurrence_count,
            'total_documents': self.total_documents,
            'occurrence_percentage': self.occurrence_percentage,
            'stability': getattr(self, 'stability', FieldStability.RARE.value),
            'is_required': self.is_required,
            'is_indexed': self.is_indexed,
            'is_searchable': self.is_searchable,
            'tags': self.tags
        }
        
        # Add optional fields
        if self.description:
            item['description'] = self.description
        if self.parent_field:
            item['parent_field'] = self.parent_field
        
        # Add complex fields
        if self.examples:
            item['examples'] = [
                example.to_dict() if isinstance(example, FieldExample) else example
                for example in self.examples
            ]
        
        if self.statistics:
            item['statistics'] = self.statistics.to_dict()
        
        if self.related_fields:
            item['related_fields'] = self.related_fields
        
        if self.child_fields:
            item['child_fields'] = self.child_fields
        
        if self.validation_rules:
            item['validation_rules'] = self.validation_rules
        
        if self.validation_patterns:
            item['validation_patterns'] = self.validation_patterns
        
        if self.custom_metadata:
            item['custom_metadata'] = self.custom_metadata
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'FieldRegistryEntry':
        """
        Create FieldRegistryEntry from DynamoDB item.
        
        Args:
            item: DynamoDB item
            
        Returns:
            FieldRegistryEntry: Field registry entry instance
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
        Convert to summary dictionary (without detailed statistics).
        
        Returns:
            Dict[str, Any]: Summary dictionary representation
        """
        return {
            'field_id': self.field_id,
            'path': self.path,
            'field_name': self.field_name,
            'data_type': self.data_type,
            'source_namespace': self.source_namespace,
            'occurrence_count': self.occurrence_count,
            'occurrence_percentage': self.occurrence_percentage,
            'stability': getattr(self, 'stability', FieldStability.RARE.value),
            'is_required': self.is_required,
            'is_indexed': self.is_indexed,
            'description': self.description
        }
    
    def __str__(self) -> str:
        return f"Field(path={self.path}, type={self.data_type}, occurrences={self.occurrence_count})"
    
    def __repr__(self) -> str:
        return f"FieldRegistryEntry(field_id='{self.field_id}', path='{self.path}', data_type='{self.data_type}')"

class FieldRegistry:
    """
    Field registry manager for tracking and analyzing fields across documents.
    
    This class provides:
    - Field discovery and registration
    - Statistical analysis of field usage
    - Field relationship detection
    - Schema evolution tracking
    """
    
    def __init__(self):
        self.fields: Dict[str, FieldRegistryEntry] = {}
        self.namespaces: Set[str] = set()
        self.total_documents_processed = 0
    
    def register_field(self, path: str, value: Any, document_id: str, 
                      namespace: str = "", description: str = "") -> FieldRegistryEntry:
        """
        Register a field occurrence.
        
        Args:
            path: Field path (e.g., 'southwest_itinerary.confirmation_code')
            value: Field value
            document_id: Source document ID
            namespace: Field namespace
            description: Optional field description
            
        Returns:
            FieldRegistryEntry: The field registry entry
        """
        field_id = path
        
        if field_id not in self.fields:
            # Create new field entry
            self.fields[field_id] = FieldRegistryEntry(
                field_id=field_id,
                path=path,
                source_namespace=namespace,
                description=description
            )
        
        # Record occurrence
        self.fields[field_id].add_occurrence(document_id, value, self.total_documents_processed)
        
        # Track namespace
        if namespace:
            self.namespaces.add(namespace)
        
        return self.fields[field_id]
    
    def register_document_fields(self, document_data: Dict[str, Any], document_id: str):
        """
        Register all fields from a document.
        
        Args:
            document_data: Document data dictionary
            document_id: Source document ID
        """
        self.total_documents_processed += 1
        
        def register_nested_fields(data: Any, prefix: str = "", namespace: str = ""):
            """Recursively register nested fields."""
            if isinstance(data, dict):
                for key, value in data.items():
                    field_path = f"{prefix}.{key}" if prefix else key
                    
                    # Extract namespace from first-level keys
                    current_namespace = namespace or (key if not prefix else namespace)
                    
                    if isinstance(value, (dict, list)):
                        # Register the container field
                        self.register_field(field_path, value, document_id, current_namespace)
                        # Recursively register nested fields
                        register_nested_fields(value, field_path, current_namespace)
                    else:
                        # Register leaf field
                        self.register_field(field_path, value, document_id, current_namespace)
            
            elif isinstance(data, list) and data:
                # For arrays, process the first item to understand structure
                if isinstance(data[0], dict):
                    for key, value in data[0].items():
                        field_path = f"{prefix}[].{key}" if prefix else f"[].{key}"
                        self.register_field(field_path, value, document_id, namespace)
        
        register_nested_fields(document_data)
        
        # Update occurrence percentages for all fields
        self._update_all_percentages()
    
    def _update_all_percentages(self):
        """Update occurrence percentages for all fields."""
        for field in self.fields.values():
            if self.total_documents_processed > 0:
                field.occurrence_percentage = (field.occurrence_count / self.total_documents_processed) * 100
                field._update_stability()
    
    def get_field(self, path: str) -> Optional[FieldRegistryEntry]:
        """Get a field by path."""
        return self.fields.get(path)
    
    def get_fields_by_namespace(self, namespace: str) -> List[FieldRegistryEntry]:
        """Get all fields in a namespace."""
        return [field for field in self.fields.values() if field.source_namespace == namespace]
    
    def get_fields_by_type(self, data_type: Union[str, FieldDataType]) -> List[FieldRegistryEntry]:
        """Get all fields of a specific type."""
        type_str = data_type.value if isinstance(data_type, FieldDataType) else data_type
        return [field for field in self.fields.values() if field.data_type == type_str]
    
    def get_stable_fields(self) -> List[FieldRegistryEntry]:
        """Get all stable fields (>80% occurrence)."""
        return [field for field in self.fields.values() if field.is_stable()]
    
    def get_common_fields(self) -> List[FieldRegistryEntry]:
        """Get all common fields (>40% occurrence)."""
        return [field for field in self.fields.values() if field.is_common()]
    
    def get_searchable_fields(self) -> List[FieldRegistryEntry]:
        """Get all searchable fields."""
        return [field for field in self.fields.values() if field.is_searchable]
    
    def get_indexed_fields(self) -> List[FieldRegistryEntry]:
        """Get all indexed fields."""
        return [field for field in self.fields.values() if field.is_indexed]
    
    def suggest_indexes(self) -> List[str]:
        """Suggest fields that should be indexed based on usage patterns."""
        suggestions = []
        
        for field in self.fields.values():
            # Suggest indexing for stable fields that are searchable
            if (field.is_stable() and 
                field.is_searchable and 
                not field.is_indexed and
                field.data_type not in [FieldDataType.OBJECT.value, FieldDataType.ARRAY.value]):
                suggestions.append(field.path)
        
        return suggestions
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """Get a summary of the discovered schema."""
        return {
            'total_fields': len(self.fields),
            'total_documents_processed': self.total_documents_processed,
            'namespaces': list(self.namespaces),
            'fields_by_stability': {
                'stable': len(self.get_stable_fields()),
                'common': len(self.get_common_fields()),
                'occasional': len([f for f in self.fields.values() 
                                 if f.get_stability_level() == FieldStability.OCCASIONAL]),
                'rare': len([f for f in self.fields.values() 
                           if f.get_stability_level() == FieldStability.RARE])
            },
            'fields_by_type': {
                data_type.value: len(self.get_fields_by_type(data_type))
                for data_type in FieldDataType
            },
            'suggested_indexes': self.suggest_indexes()
        }
    
    def export_schema(self) -> Dict[str, Any]:
        """Export the complete field registry as a dictionary."""
        return {
            'metadata': {
                'total_fields': len(self.fields),
                'total_documents_processed': self.total_documents_processed,
                'namespaces': list(self.namespaces),
                'exported_at': DynamoDBHelper.current_timestamp()
            },
            'fields': {
                field_id: field.to_dict() for field_id, field in self.fields.items()
            }
        }
    
    def __len__(self) -> int:
        return len(self.fields)
    
    def __contains__(self, path: str) -> bool:
        return path in self.fields
    
    def __iter__(self):
        return iter(self.fields.values())

class FieldAnalyzer:
    """Helper class for field analysis and insights."""
    
    @staticmethod
    def detect_field_relationships(registry: FieldRegistry) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect relationships between fields based on co-occurrence patterns.
        
        Args:
            registry: Field registry to analyze
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Field relationships
        """
        relationships = {}
        
        # Simple co-occurrence analysis
        # In a full implementation, this would analyze actual document co-occurrences
        for field in registry:
            relationships[field.path] = []
            
            # Find fields in the same namespace
            same_namespace = [
                f for f in registry 
                if f.source_namespace == field.source_namespace and f.path != field.path
            ]
            
            for related_field in same_namespace[:5]:  # Limit to top 5
                relationships[field.path].append({
                    'field_path': related_field.path,
                    'relationship_type': 'same_namespace',
                    'strength': 0.7,
                    'reason': f'Both fields belong to namespace: {field.source_namespace}'
                })
        
        return relationships
    
    @staticmethod
    def suggest_field_improvements(field: FieldRegistryEntry) -> List[Dict[str, Any]]:
        """
        Suggest improvements for a field based on its usage patterns.
        
        Args:
            field: Field to analyze
            
        Returns:
            List[Dict[str, Any]]: List of improvement suggestions
        """
        suggestions = []
        
        # Suggest indexing for frequently used fields
        if field.is_stable() and not field.is_indexed:
            suggestions.append({
                'type': 'indexing',
                'priority': 'high',
                'suggestion': 'Consider adding database index for this stable field',
                'reason': f'Field appears in {field.occurrence_percentage:.1f}% of documents'
            })
        
        # Suggest better type classification
        if field.type_confidence < 0.5:
            suggestions.append({
                'type': 'type_classification',
                'priority': 'medium',
                'suggestion': 'Improve data type classification',
                'reason': f'Type confidence is low ({field.type_confidence:.2f})'
            })
        
        # Suggest adding description
        if not field.description and field.is_common():
            suggestions.append({
                'type': 'documentation',
                'priority': 'low',
                'suggestion': 'Add field description for better documentation',
                'reason': 'Common fields should be well documented'
            })
        
        return suggestions